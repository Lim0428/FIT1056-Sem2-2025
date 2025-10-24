# app/storage.py — tiny, safe JSON persistence helpers
from __future__ import annotations
import json, os, tempfile, shutil, threading
from pathlib import Path
from typing import Any, Dict, Optional

# Default main DB (patient side already uses carelog.json)
MAIN_DB = Path("data/carelog.json")
_lock = threading.Lock()

def _resolve_path(path: Optional[str | os.PathLike]) -> Path:
    if path is None:
        return MAIN_DB
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def read_db(path: Optional[str | os.PathLike] = None) -> Dict[str, Any]:
    """
    Read a JSON file safely. If missing/empty/corrupt, return {}.
    Default path is data/carelog.json to match existing patient code.
    """
    fp = _resolve_path(path)
    if not fp.exists():
        return {}
    try:
        with fp.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt or empty file — fail soft
        return {}

def write_db(path: Optional[str | os.PathLike], obj: Dict[str, Any]) -> None:
    """
    Atomically write JSON to disk (write to a temp file, then replace).
    Creates parent folders as needed.
    """
    if path is None:
        raise ValueError("write_db(path, obj): 'path' must not be None")
    fp = _resolve_path(path)
    tmp_dir = fp.parent
    with _lock:
        fd, tmp_name = tempfile.mkstemp(dir=tmp_dir, prefix=fp.stem + "_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            shutil.move(tmp_name, fp)
        finally:
            # Clean up temp file if something failed before move
            if os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass

def ensure_db(path: Optional[str | os.PathLike], seed: Optional[Dict[str, Any]] = None) -> None:
    """Create the JSON file if missing, with optional seed content."""
    if path is None:
        raise ValueError("ensure_db(path, seed): 'path' must not be None")
    fp = _resolve_path(path)
    if not fp.exists():
        write_db(fp, seed or {})
