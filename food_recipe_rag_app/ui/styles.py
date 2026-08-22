import streamlit as st

def inject_css():
    st.markdown("""
    <style>
    :root {
      --warm-bg: #fff8ef;
      --warm-card: #fffdf9;
      --warm-accent: #b45309;
      --warm-text: #2d241f;
    }
    .stApp {
      background: var(--warm-bg);
      color: var(--warm-text);
    }
    .recipe-card {
      background: var(--warm-card);
      border: 1px solid rgba(120,80,40,.16);
      border-radius: 18px;
      padding: 1.25rem 1.4rem;
      margin: .5rem 0 1rem 0;
      box-shadow: 0 8px 30px rgba(80,45,15,.06);
    }
    .recipe-title {
      font-size: 2.2rem;
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: .4rem;
    }
    .source-chip {
      display: inline-block;
      padding: .3rem .65rem;
      border-radius: 999px;
      background: rgba(180,83,9,.10);
      margin: .15rem;
      font-size: .85rem;
    }
    @media print {
      [data-testid="stSidebar"], header, footer,
      [data-testid="stToolbar"], button, .stButton {
        display: none !important;
      }
      .stApp { background: white !important; }
      .recipe-card { box-shadow: none; border: none; }
    }
    </style>
    """, unsafe_allow_html=True)
