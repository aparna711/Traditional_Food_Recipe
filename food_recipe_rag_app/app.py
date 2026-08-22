import streamlit as st
from config import settings
from auth import require_login
from rag.vector_store import get_collection
from rag.embeddings import embed_query
from rag.retriever import retrieve
from rag.generator import generate_recipe
from ui.styles import inject_css
from ui.components import (
    render_header, render_recipe, render_sources,
    render_cooking_mode, render_scaled_ingredients, render_login_hint
)

st.set_page_config(
    page_title=settings.app_title,
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

if not require_login():
    render_login_hint()
    st.stop()

collection = get_collection()

if collection.count() == 0:
    st.error("The recipe index is empty. Run `python scripts/ingest.py` before using the app.")
    st.stop()

render_header()

with st.sidebar:
    st.markdown("### 🍽️ Recipe Explorer")
    query = st.text_area(
        "What would you like to cook?",
        placeholder="e.g. What can I cook with tomatoes and paneer?",
        height=100,
    )
    fridge = st.multiselect(
        "What's in my fridge?",
        settings.fridge_ingredients,
    )
    custom = st.text_input("Add another ingredient")
    if custom.strip():
        fridge = list(dict.fromkeys(fridge + [custom.strip()]))

    dietary = st.multiselect(
        "Dietary filters",
        settings.dietary_filters,
        help="Filters are applied only when the retrieved recipe evidence supports them.",
    )

    servings = st.number_input("Target servings", min_value=1, max_value=50, value=4)

    search = st.button("🔎 Find Recipe", type="primary", use_container_width=True)

    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

if search:
    parts = []
    if query.strip():
        parts.append(query.strip())
    if fridge:
        parts.append("Available ingredients: " + ", ".join(fridge))
    if dietary:
        parts.append("Dietary requirements: " + ", ".join(dietary))

    user_query = "\n".join(parts).strip()

    if not user_query:
        st.warning("Enter a recipe question or select ingredients.")
        st.stop()

    with st.spinner("Searching the recipe book..."):
        qvec = embed_query(user_query)
        hits = retrieve(collection, qvec, user_query, top_k=settings.top_k)

    if not hits:
        st.warning("No sufficiently relevant recipe information was found in the recipe book.")
        st.stop()

    with st.spinner("Preparing the recipe..."):
        recipe = generate_recipe(user_query, hits)

    st.session_state.recipe = recipe
    st.session_state.sources = hits
    st.session_state.target_servings = int(servings)

if "recipe" in st.session_state:
    recipe = st.session_state.recipe
    target_servings = st.session_state.get("target_servings", 4)

    render_recipe(recipe)

    st.divider()
    render_scaled_ingredients(recipe, target_servings)

    st.divider()
    render_cooking_mode(recipe)

    st.divider()
    render_sources(st.session_state.get("sources", []))
