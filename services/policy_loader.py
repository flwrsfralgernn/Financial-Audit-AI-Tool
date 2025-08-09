from functools import lru_cache
from typing import Optional
from pathlib import Path
from config.settings import POLICIES_DIR, DEFAULT_POLICY_FILE, MAX_POLICY_CHARS

def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def _read_pdf(path: Path) -> str:
    try:
        import PyPDF2
    except ImportError:
        return ""
    text_chunks = []
    with path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            try:
                text_chunks.append(page.extract_text() or "")
            except Exception:
                pass
    return "\n".join(text_chunks)

def _clean(s: str) -> str:
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())

@lru_cache(maxsize=64)
def load_policy_text(policy_path: Optional[str] = None) -> str:
    """
    Load a single policy file (txt/pdf). If none given, use DEFAULT_POLICY_FILE.
    Trims to MAX_POLICY_CHARS.
    """
    p = Path(policy_path) if policy_path else Path(DEFAULT_POLICY_FILE)
    if not p.exists():
        return ""  # fine: prompt will still work, just without external policy
    raw = _read_txt(p) if p.suffix.lower() == ".txt" else _read_pdf(p)
    cleaned = _clean(raw)
    if len(cleaned) > MAX_POLICY_CHARS:
        cleaned = cleaned[:MAX_POLICY_CHARS] + "\n\n[...truncated...]"
    return cleaned
