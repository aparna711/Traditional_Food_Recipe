from functools import lru_cache
from google import genai
from google.genai import types
import os
import streamlit as st
from config import settings

def _api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        return key

@lru_cache(maxsize=1)
def get_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def _document_text(title: str, text: str) -> str:
    return f"title: {title} | text: {text}"

def _query_text(query: str) -> str:
    # Gemini Embedding 2 does not use the old task_type parameter.
    # Retrieval intent is expressed in the input format.
    return f"task: search result | query: {query}"

# def embed_documents(items):
#     if not items:
#         return []

#     client = get_client()
#     contents = [_document_text(x["recipe_name"], x["text"]) for x in items]

#     # Keep requests bounded to avoid very large API payloads.
#     result = client.models.embed_content(
#         model=settings.embedding_model,
#         contents=contents,
#         config=types.EmbedContentConfig(
#             output_dimensionality=settings.embedding_dimension
#         ),
#     )
#     return [e.values for e in result.embeddings]


def embed_documents(items):
    if not items:
        return []

    client = get_client()

    contents = [
        types.Content(
            parts=[
                types.Part.from_text(
                    text=_document_text(x["recipe_name"], x["text"])
                )
            ]
        )
        for x in items
    ]

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=contents,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimension
        ),
    )

    embeddings = [e.values for e in result.embeddings]

    if len(embeddings) != len(items):
        raise RuntimeError(
            f"Embedding count mismatch: "
            f"expected {len(items)}, got {len(embeddings)}"
        )

    return embeddings
def embed_query(query: str):
    client = get_client()
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=_query_text(query),
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimension
        ),
    )
    return result.embeddings[0].values
