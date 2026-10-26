"""Central place for every on-disk path the app uses.

Keeping data out of the source folder makes installs, the EXE and development
builds behave the same way, and gives the UI one place to show the user.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _data_root() -> Path:
    override = os.getenv("GROQCHATBOT_DATA")
    if override:
        return Path(override).expanduser()
    if getattr(sys, "frozen", False):
        local = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if local:
            return Path(local) / "GroqChatbot"
        return Path.home() / ".groqchatbot"
    return _base_dir() / "data"


BASE_DIR = _base_dir()
DATA_DIR = _data_root()
GENERATED_DIR = DATA_DIR / "generated"
SANDBOX_DIR = DATA_DIR / "sandbox"
DOCS_DIR = DATA_DIR / "documents"


def ensure_dirs() -> None:
    for folder in (DATA_DIR, GENERATED_DIR, SANDBOX_DIR, DOCS_DIR):
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass


def data_path(*parts: str) -> str:
    ensure_dirs()
    return str(DATA_DIR.joinpath(*parts))


def memory_db() -> str:
    return data_path("memory.db")


def rag_db() -> str:
    return data_path("rag.db")


def readable_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{int(num_bytes)} B"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


ensure_dirs()
