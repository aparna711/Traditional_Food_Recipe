from rag.chunking import chunk_text, approx_tokens

def test_chunking_nonempty():
    text = "This is a recipe sentence. " * 250
    chunks = chunk_text(text)
    assert chunks
    assert all(approx_tokens(x) <= 650 for x in chunks)

def test_empty():
    assert chunk_text("") == []
