import json
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
import streamlit as st

from config import settings
from rag.embeddings import get_client
from rag.prompts import SYSTEM_PROMPT

class Recipe(BaseModel):
    recipe_name: str = ""
    prep_time: str = ""
    cook_time: str = ""
    servings: str = ""
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    chef_notes: str = ""

def _context(hits):
    blocks = []
    for i, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        blocks.append(
            f"[SOURCE {i} | page={m.get('page_number')} | recipe={m.get('recipe_name')}]\n"
            f"{hit['text']}"
        )
    return "\n\n".join(blocks)

def _call(user_query, context):
    client = get_client()
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"RECIPE CONTEXT:\n{context}\n\n"
        f"USER REQUEST:\n{user_query}\n\n"
        f"Return only the requested JSON object."
    )

    response = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Recipe,
        ),
    )
    return response.text

def generate_recipe(user_query, hits):
    if not hits:
        return Recipe(chef_notes="Insufficient context from recipe book.").model_dump()

    context = _context(hits)

    try:
        raw = _call(user_query, context)
        return Recipe.model_validate_json(raw).model_dump()
    except (ValidationError, ValueError, json.JSONDecodeError) as first_error:
        # One bounded correction retry; never parse arbitrary prose.
        try:
            correction = (
                "Return a valid JSON object matching exactly this schema. "
                "Use only the supplied context. No extra keys.\n"
                f"SCHEMA:\n{Recipe.model_json_schema()}\n"
                f"INVALID OUTPUT:\n{raw if 'raw' in locals() else str(first_error)}"
            )
            client = get_client()
            response = client.models.generate_content(
                model=settings.llm_model,
                contents=correction + "\n\nCONTEXT:\n" + context,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Recipe,
                ),
            )
            return Recipe.model_validate_json(response.text).model_dump()
        except Exception:
            return Recipe(chef_notes="The recipe response could not be validated safely.").model_dump()
    except Exception as exc:
        raise RuntimeError(f"Recipe generation failed: {exc}") from exc
