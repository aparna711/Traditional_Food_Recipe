# 🍲 Recipe RAG Kitchen

Production-oriented Streamlit RAG application using:

- Streamlit
- Gemini 3.5 Flash
- Gemini Embedding 2
- ChromaDB
- Pydantic

## 1. Put the knowledge base in place

Copy the recipe PDF to:

`data/source/food recipe.pdf`

The application does not ingest it automatically during normal startup.

## 2. Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Configure secrets

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Set `GEMINI_API_KEY`.

Generate a password hash:

```bash
python scripts/hash_password.py
```

Put the printed value into `AUTH_PASSWORD_HASH`.

Never commit `secrets.toml`.

## 4. One-time indexing

```bash
python scripts/ingest.py
```

If the PDF and ingestion configuration are unchanged, subsequent executions skip extraction and embeddings.

Force a rebuild only when required:

```bash
python scripts/ingest.py --force
```

## 5. Run

```bash
streamlit run app.py
```

## 6. Architecture

```text
food recipe.pdf
    ↓
page extraction
    ↓
recipe-aware chunks (300–600 approximate tokens, 10% overlap)
    ↓
Gemini Embedding 2 / 768 dimensions
    ↓
persistent ChromaDB
    ↓
query embedding
    ↓
Top-K=3
    ↓
relevance gate
    ↓
Gemini 3.5 Flash
    ↓
Pydantic validation
    ↓
Streamlit recipe UI
```

## 7. Why ingestion is separate

Streamlit reruns the Python script after interactions. The application therefore never calls the ingestion pipeline from `app.py`. ChromaDB is persistent, while `st.cache_resource` is used only to reuse resource objects such as the Chroma collection/client.

## 8. Streamlit caching

Use `st.cache_resource` for reusable clients/resources such as the Gemini client and Chroma collection. Do not use it as the permanent database. Streamlit's resource cache is in-memory and can be cleared/recreated.

Do not cache generated recipe responses as permanent knowledge because responses depend on user queries.

## 9. Streamlit Community Cloud

Community Cloud secrets should be entered in the app's Secrets settings rather than committing `secrets.toml`.

For a small demo, package the PDF and prebuilt Chroma data with the repository if the resulting repository size is acceptable. However, local filesystem persistence on a hosted runtime should not be treated as a durable production database. Redeployments/restarts can require rebuilding/restoring the index.

For durable production retrieval, keep ChromaDB as the required local/development store and plan a durable externally hosted vector store if the deployment platform cannot guarantee persistent storage.

## 10. Docker

Build:

```bash
docker build -t recipe-rag .
```

Create persistent storage:

```bash
docker volume create recipe-chroma
```

Run:

```bash
docker run --rm \
  -p 8501:8501 \
  -e GEMINI_API_KEY="YOUR_KEY" \
  -e AUTH_USERNAME="admin" \
  -e AUTH_PASSWORD_HASH="YOUR_HASH" \
  -v recipe-chroma:/data/chroma \
  recipe-rag
```

For production, use Docker/host secret management rather than putting secrets directly into shell history.

The PDF must be present in the image or mounted into the expected source path. Run indexing once against the persistent volume:

```bash
docker run --rm \
  -e GEMINI_API_KEY="YOUR_KEY" \
  -v recipe-chroma:/data/chroma \
  recipe-rag \
  python scripts/ingest.py
```

Then start the normal Streamlit container using the same volume.

## 11. Security

- Never commit API keys.
- Never commit `.streamlit/secrets.toml`.
- Never bake credentials into the Dockerfile.
- Use a PBKDF2 password hash rather than plaintext application passwords.
- Use HTTPS behind a reverse proxy in public production.
- Add rate limiting at the proxy/application boundary for public deployments.
- Do not log prompts containing secrets.
- Treat PDF/user content as untrusted context.
- Keep retrieved context separate from system instructions.
- Validate every LLM response with Pydantic.
- Back up persistent ChromaDB before upgrades.

## 12. Gemini Embedding 2 note

`gemini-embedding-2` supports flexible dimensions and 768 is a recommended dimension. For text retrieval, the current Gemini documentation recommends expressing retrieval intent in the input formatting rather than using the old `task_type` parameter. This project therefore uses:

```text
task: search result | query: ...
```

for queries and:

```text
title: ... | text: ...
```

for indexed documents.

## 13. Gemini 3.5 Flash note

The current Gemini 3.5 Flash API documentation identifies `gemini-3.5-flash` as the stable model ID and recommends structured outputs. Current Gemini 3.5 guidance no longer recommends legacy sampling parameters such as temperature. The app therefore keeps `TEMPERATURE=0.2` as configuration compatibility with the requested design but does not send the deprecated parameter to the current SDK.

## 14. Production checklist

Before public deployment:

- [ ] Build and test the index separately.
- [ ] Confirm PDF hash/config metadata.
- [ ] Confirm `collection.count()` is non-zero.
- [ ] Test relevant and irrelevant queries.
- [ ] Test prompt-injection strings.
- [ ] Test malformed model output.
- [ ] Test page attribution.
- [ ] Test login/logout.
- [ ] Test Docker restart with the same Chroma volume.
- [ ] Back up ChromaDB.
- [ ] Configure HTTPS.
- [ ] Configure rate limiting.
- [ ] Rotate API credentials if exposed.
- [ ] Pin dependency versions after validation.

## 15. Important limitation

The supplied build specification names `food recipe.pdf`, but this source package does not contain that PDF. Put the actual PDF at `data/source/food recipe.pdf` before running ingestion.
