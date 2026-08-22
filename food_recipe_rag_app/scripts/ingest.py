import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag.ingestion import ingest

if __name__ == "__main__":
    force = "--force" in sys.argv
    print(ingest(force=force))
