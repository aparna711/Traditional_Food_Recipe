from pathlib import Path
from pypdf import PdfReader

def extract_pages(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Recipe PDF not found: {path}")

    reader = PdfReader(str(path))
    pages = []

    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", " ").strip()
        if text:
            pages.append({"page_number": page_no, "text": text})

    if not pages:
        raise ValueError("The recipe PDF contains no extractable text.")

    return pages
