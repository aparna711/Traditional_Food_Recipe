import re

def approx_tokens(text: str) -> int:
    # Conservative approximation suitable for chunk sizing without another tokenizer dependency.
    return max(1, round(len(text) / 4))

def split_sentences(text: str):
    text = re.sub(r"[ \t]+", " ", text).strip()
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", text) if x.strip()]

def chunk_text(text: str, min_tokens=300, max_tokens=600, overlap_ratio=0.10):
    sentences = split_sentences(text)
    chunks = []
    current = []
    current_tokens = 0

    for sentence in sentences:
        t = approx_tokens(sentence)
        if current and current_tokens + t > max_tokens:
            chunks.append(" ".join(current))

            overlap_tokens = max(1, round(current_tokens * overlap_ratio))
            tail = []
            tail_tokens = 0
            for s in reversed(current):
                st = approx_tokens(s)
                if tail_tokens + st > overlap_tokens:
                    break
                tail.insert(0, s)
                tail_tokens += st

            current = tail
            current_tokens = tail_tokens

        current.append(sentence)
        current_tokens += t

    if current:
        chunks.append(" ".join(current))

    # Merge very small trailing chunks where safe.
    merged = []
    for chunk in chunks:
        if merged and approx_tokens(chunk) < min_tokens:
            candidate = merged[-1] + " " + chunk
            if approx_tokens(candidate) <= max_tokens:
                merged[-1] = candidate
                continue
        merged.append(chunk)

    return merged
