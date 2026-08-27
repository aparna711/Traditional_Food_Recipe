from dataclasses import dataclass
from pathlib import Path
import os
import streamlit as st

ROOT = Path(__file__).resolve().parent

def _secret(name, default=None):
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

@dataclass(frozen=True)
class Settings:
    app_title: str = "Recipe RAG Kitchen"
    llm_model: str = _secret("LLM_MODEL", "gemini-3.5-flash")
    embedding_model: str = _secret("EMBEDDING_MODEL", "gemini-embedding-2")
    embedding_dimension: int = int(_secret("EMBEDDING_DIMENSION", "768"))
    chroma_path: str = _secret("CHROMA_PATH", str(ROOT / "data" / "chroma"))
    collection_name: str = _secret("COLLECTION_NAME", "food_recipes_v1")
    top_k: int = int(_secret("TOP_K", "3"))
    temperature: float = float(_secret("TEMPERATURE", "0.2"))
    chunk_min_tokens: int = 300
    chunk_max_tokens: int = 600
    chunk_overlap_ratio: float = 0.10
    source_pdf: str = _secret("SOURCE_PDF", str(ROOT / "data" / "source" / "food recipe.pdf"))
    fridge_ingredients: tuple = (
        "Potato", "Tomato", "Onion", "Garlic", "Ginger", "Green chilli",
        "Paneer", "Milk", "Curd/Yogurt", "Egg", "Rice", "Wheat flour",
        "Maida", "Besan", "Dal", "Chickpeas", "Lentils", "Carrot",
        "Capsicum", "Spinach", "Peas", "Cauliflower", "Cabbage",
        "Mushroom", "Corn", "Coconut", "Lemon", "Coriander",
    )
    dietary_filters: tuple = (
        "Vegetarian", "Vegan", "Gluten-free", "Dairy-free",
        "Egg-free", "Nut-free", "Jain",
    )

settings = Settings()
