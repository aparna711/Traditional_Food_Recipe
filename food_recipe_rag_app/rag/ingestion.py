from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import chromadb

from config import settings
from rag.chunking import chunk_text
from rag.pdf_loader import extract_pages
from rag.embeddings import embed_documents

META_PATH = Path(settings.chroma_path).parent / "metadata" / "ingestion.json"

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def _recipe_name(text: str) -> str:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return lines[0][:200] if lines else "Unknown recipe"

def _config(pdf_hash: str):
    return {
        "document_hash": pdf_hash,
        "embedding_model": settings.embedding_model,
        "embedding_dimension": settings.embedding_dimension,
        "chunk_min_tokens": settings.chunk_min_tokens,
        "chunk_max_tokens": settings.chunk_max_tokens,
        "chunk_overlap_ratio": settings.chunk_overlap_ratio,
        "collection_name": settings.collection_name,
        "version": 1,
    }

def index_is_current(pdf_path: str) -> bool:
    meta = META_PATH
    if not meta.exists():
        return False
    try:
        saved = json.loads(meta.read_text())
        return saved.get("config") == _config(file_sha256(pdf_path))
    except Exception:
        return False

def ingest(force=False):
    pdf_path = settings.source_pdf
    if not force and index_is_current(pdf_path):
        return {"status": "unchanged", "message": "Index is already current; no embeddings generated."}

    pdf_hash = file_sha256(pdf_path)
    pages = extract_pages(pdf_path)

    documents = []
    for page in pages:
        name = _recipe_name(page["text"])
        chunks = chunk_text(
            page["text"],
            settings.chunk_min_tokens,
            settings.chunk_max_tokens,
            settings.chunk_overlap_ratio,
        )
        for i, chunk in enumerate(chunks):
            documents.append({
                "recipe_name": name,
                "text": chunk,
                "page_number": page["page_number"],
                "section": "recipe",
                "chunk_id": f"{pdf_hash[:12]}-{page['page_number']}-{i}",
            })

    if not documents:
        raise ValueError("No chunks were generated from the PDF.")

    embeddings = []
    batch_size = 32
    for start in range(0, len(documents), batch_size):
        embeddings.extend(embed_documents(documents[start:start + batch_size]))

    client = chromadb.PersistentClient(path=settings.chroma_path)
    try:
        client.delete_collection(settings.collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[d["chunk_id"] for d in documents],
        documents=[d["text"] for d in documents],
        embeddings=embeddings,
        metadatas=[
            {
                "recipe_name": d["recipe_name"],
                "source_pdf": Path(pdf_path).name,
                "page_number": d["page_number"],
                "chunk_id": d["chunk_id"],
                "section": d["section"],
                "document_hash": pdf_hash,
            }
            for d in documents
        ],
    )

    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(json.dumps({
        "config": _config(pdf_hash),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "chunk_count": len(documents),
    }, indent=2))

    return {"status": "indexed", "chunks": len(documents)}

if __name__ == "__main__":
    print(ingest())
