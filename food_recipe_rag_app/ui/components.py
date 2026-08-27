import html
import re
import streamlit as st
import streamlit.components.v1 as components

def render_login_hint():
    st.info("Log in to access the recipe application.")

def render_header():
    st.markdown("# 🍲 Recipe RAG Kitchen")
    st.caption("Grounded recipe search powered by your recipe book.")

def render_recipe(recipe):
    st.markdown(
        f'<div class="recipe-card"><div class="recipe-title">{html.escape(recipe.get("recipe_name","Recipe"))}</div>'
        f'<b>Prep:</b> {html.escape(recipe.get("prep_time","—"))} &nbsp; '
        f'<b>Cook:</b> {html.escape(recipe.get("cook_time","—"))} &nbsp; '
        f'<b>Servings:</b> {html.escape(recipe.get("servings","—"))}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ingredients")
        for item in recipe.get("ingredients", []):
            st.markdown(f"- {item}")
    with col2:
        st.subheader("Chef notes")
        st.write(recipe.get("chef_notes") or "—")

    st.subheader("Instructions")
    for i, step in enumerate(recipe.get("instructions", []), start=1):
        st.markdown(f"**{i}.** {step}")

def _parse_qty(item):
    # Handles simple leading decimals/fractions such as 1, 1.5, 1/2, 1 1/2.
    m = re.match(r"^\s*((?:\d+(?:\.\d+)?(?:\s+\d+/\d+)?)|(?:\d+/\d+))(\s+.*)$", item)
    if not m:
        return None
    raw, rest = m.groups()
    try:
        parts = raw.split()
        if len(parts) == 2:
            value = float(parts[0]) + float(parts[1].split("/")[0]) / float(parts[1].split("/")[1])
        elif "/" in raw:
            a, b = raw.split("/")
            value = float(a) / float(b)
        else:
            value = float(raw)
        return value, rest
    except Exception:
        return None

def render_scaled_ingredients(recipe, target_servings):
    original = recipe.get("servings", "")
    m = re.search(r"\d+(?:\.\d+)?", original)
    base = float(m.group()) if m else None

    st.subheader("🥄 Portion Scaling")
    if not base or base <= 0:
        st.info("Serving count is not numeric, so automatic scaling is disabled.")
        return

    ratio = target_servings / base
    rows = []
    for item in recipe.get("ingredients", []):
        parsed = _parse_qty(item)
        if not parsed:
            rows.append(item)
            continue
        qty, rest = parsed
        scaled = qty * ratio
        display = f"{scaled:.2f}".rstrip("0").rstrip(".")
        rows.append(display + rest)

    st.caption(f"{int(base) if base.is_integer() else base:g} → {target_servings} servings")
    for item in rows:
        st.markdown(f"- {item}")

def _seconds(text):
    m = re.search(r"(\d+)\s*(hour|hr|hours|minute|minutes|min|mins|second|seconds|sec|secs)", text.lower())
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit.startswith("hour") or unit.startswith("hr"):
        return n * 3600
    if unit.startswith("min"):
        return n * 60
    return n

def render_cooking_mode(recipe):
    st.subheader("👩‍🍳 Cooking Mode")
    steps = recipe.get("instructions", [])
    if not steps:
        return

    idx = st.number_input(
        "Step",
        min_value=1,
        max_value=len(steps),
        value=1,
        step=1,
        key="cooking_step",
    )
    step = steps[idx - 1]
    st.progress(idx / len(steps))
    st.markdown(f"### Step {idx} of {len(steps)}")
    st.markdown(f"## {step}")

    seconds = _seconds(step)
    if seconds:
        components.html(f"""
        <div style="font-family:system-ui;padding:12px;border-radius:14px;background:#fff8ef">
          <strong>⏱ Timer detected from source step</strong>
          <div id="timer" style="font-size:34px;font-weight:800;margin:8px 0">--:--</div>
          <button onclick="startTimer()">Start</button>
          <button onclick="pauseTimer()">Pause</button>
          <button onclick="resetTimer()">Reset</button>
        </div>
        <script>
          let remaining={seconds}, timer=null, initial={seconds};
          function fmt(s) {{
            let m=Math.floor(s/60), sec=s%60;
            return String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');
          }}
          function draw() {{ document.getElementById('timer').textContent=fmt(remaining); }}
          function startTimer() {{
            if(timer) return;
            timer=setInterval(()=>{{
              if(remaining<=0) {{ clearInterval(timer); timer=null; return; }}
              remaining--; draw();
            }},1000);
          }}
          function pauseTimer() {{ if(timer) {{clearInterval(timer); timer=null;}} }}
          function resetTimer() {{ pauseTimer(); remaining=initial; draw(); }}
          draw();
        </script>
        """, height=150)

def render_sources(hits):
    st.subheader("📚 Sources")
    if not hits:
        st.caption("No source metadata available.")
        return
    pages = []
    for hit in hits:
        m = hit["metadata"]
        pages.append((m.get("source_pdf", "food recipe.pdf"), m.get("page_number", "?")))
    unique = list(dict.fromkeys(pages))
    for pdf, page in unique:
        st.markdown(f'<span class="source-chip">Source: {html.escape(str(pdf))} · Page {html.escape(str(page))}</span>', unsafe_allow_html=True)
