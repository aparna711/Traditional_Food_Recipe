def retrieve(collection, query_embedding, query_text, top_k=3):
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    hits = []
    seen = set()

    for doc, meta, distance in zip(docs, metas, distances):
        key = (meta.get("recipe_name"), meta.get("page_number"))
        if key in seen:
            continue
        seen.add(key)

        # Cosine distance: smaller is better. A conservative relevance gate.
        # Tune this against the actual recipe corpus during evaluation.
        if distance is not None and distance > 0.65:
            continue

        hits.append({
            "text": doc,
            "metadata": meta,
            "distance": distance,
        })

    return hits
