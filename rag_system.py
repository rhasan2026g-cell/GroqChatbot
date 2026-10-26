#!/usr/bin/env python3
"""GroqChatbot document intelligence (RAG).

PDF, DOCX, TXT, Markdown, HTML, CSV, JSON and source files can be ingested.
Retrieval is hybrid: vector similarity when the optional embedding stack is
ready, SQLite FTS5 (or a LIKE fallback) otherwise. Documents are always
searchable — nothing fails silently.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import sqlite3
import threading
import zipfile
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app_paths import DOCS_DIR, rag_db, readable_size

try:
    import sqlite_vec

    SQLITE_VEC_AVAILABLE = True
except Exception:  # noqa: BLE001
    sqlite_vec = None
    SQLITE_VEC_AVAILABLE = False

try:
    from importlib.util import find_spec

    SENTENCE_TRANSFORMERS_AVAILABLE = find_spec("sentence_transformers") is not None
except Exception:  # noqa: BLE001
    SENTENCE_TRANSFORMERS_AVAILABLE = False

EMBEDDING_DIM = 384
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TEXT_SUFFIXES = {
    ".txt", ".md", ".markdown", ".rst", ".log", ".py", ".js", ".ts", ".tsx",
    ".jsx", ".html", ".htm", ".css", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".xml", ".csv", ".sql", ".java", ".c", ".cpp", ".h", ".cs", ".go",
    ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".tex",
}
MAX_FILE_BYTES = 30 * 1024 * 1024


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(filepath: str) -> str:
    """Best-effort text extraction with useful errors instead of silence."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(filepath)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"File is larger than {readable_size(MAX_FILE_BYTES)}")
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf to read PDF files: pip install pypdf") from exc
        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages):
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n\n".join(pages)
        if not text.strip():
            raise RuntimeError("No selectable text found. The PDF may be a scanned image.")
        return _clean_text(text)

    if suffix == ".docx":
        # stdlib fallback: pull the visible runs out of word/document.xml
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", "ignore")
            xml = re.sub(r"</w:p>", "\n", xml)
            xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
            xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
            xml = re.sub(r"<[^>]+>", "", xml)
            return _clean_text(html.unescape(xml))
        except Exception as exc:
            raise RuntimeError(f"Could not read DOCX: {exc}") from exc

    if suffix == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise RuntimeError("Install openpyxl for spreadsheets: pip install openpyxl") from exc
        wb = load_workbook(str(path), read_only=True, data_only=True)
        rows = []
        for sheet in wb.worksheets:
            rows.append(f"# Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None]
                if cells:
                    rows.append(" | ".join(cells))
        return _clean_text("\n".join(rows))

    if suffix == ".csv":
        with open(path, "r", encoding="utf-8", errors="ignore", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel
            rows = []
            for row in csv.reader(handle, dialect):
                rows.append(" | ".join(row))
        return _clean_text("\n".join(rows))

    if suffix in (".html", ".htm"):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return _clean_text(soup.get_text("\n"))
        except Exception:
            raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.I | re.S)
            return _clean_text(html.unescape(re.sub(r"<[^>]+>", " ", raw)))

    if suffix == ".json":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            return _clean_text(json.dumps(json.loads(raw), ensure_ascii=False, indent=2))
        except Exception:
            return _clean_text(raw)

    if suffix in TEXT_SUFFIXES or suffix == "":
        return _clean_text(path.read_text(encoding="utf-8", errors="ignore"))

    # Last resort: try UTF-8, then reject with a clear message.
    try:
        return _clean_text(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Unsupported file type: {suffix or 'unknown'}") from exc


class RAGSystem:
    """Document store with chunking, FTS and optional vector recall."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        chunk_size: int = 1200,
        chunk_overlap: int = 160,
        model_name: str = DEFAULT_MODEL,
        enable_embeddings: bool = True,
    ) -> None:
        self.db_path = str(db_path or rag_db())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.chunk_size = max(300, int(chunk_size))
        self.chunk_overlap = max(0, min(int(chunk_overlap), self.chunk_size // 2))
        self.model_name = model_name
        self.embedding_dim = EMBEDDING_DIM
        self.enable_embeddings = bool(enable_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE)
        self.model = None
        self._model_state = "idle"
        self._model_lock = threading.Lock()
        self._vec_available = False
        self._fts_available = False
        self.init_db()

    # ------------------------------------------------------------------ db
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        if SQLITE_VEC_AVAILABLE:
            try:
                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
                conn.enable_load_extension(False)
                self._vec_available = True
            except Exception:
                self._vec_available = False
        return conn

    def init_db(self) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    filepath TEXT UNIQUE,
                    content_hash TEXT,
                    file_type TEXT,
                    upload_date REAL DEFAULT (strftime('%s','now')),
                    chunk_count INTEGER,
                    char_count INTEGER,
                    size_bytes INTEGER
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_text TEXT,
                    chunk_index INTEGER,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_map (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vec_rowid INTEGER,
                    chunk_id INTEGER,
                    FOREIGN KEY(chunk_id) REFERENCES chunks(id)
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)")
            try:
                cur.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(chunk_text)"
                )
                self._fts_available = True
            except Exception:
                self._fts_available = False
            conn.commit()
        finally:
            conn.close()

    def _ensure_vec_table(self, conn: sqlite3.Connection) -> bool:
        if not (self._vec_available and self.enable_embeddings):
            return False
        try:
            conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING vec0("
                f"embedding FLOAT[{self.embedding_dim}])"
            )
            return True
        except Exception:
            self._vec_available = False
            return False

    # ------------------------------------------------------------- embedder
    def warmup_embeddings(self) -> None:
        if not self.enable_embeddings:
            self._model_state = "unavailable"
            return
        with self._model_lock:
            if self._model_state in ("ready", "loading"):
                return
            self._model_state = "loading"
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            dim = model.get_sentence_embedding_dimension()
            if dim:
                self.embedding_dim = int(dim)
            with self._model_lock:
                self.model = model
                self._model_state = "ready"
            conn = self._connect()
            try:
                self._ensure_vec_table(conn)
                conn.commit()
            finally:
                conn.close()
        except Exception:
            with self._model_lock:
                self.model = None
                self._model_state = "unavailable"

    def _encode(self, text: str) -> Optional[bytes]:
        if not self.enable_embeddings:
            return None
        model = self.model
        if model is None:
            if self._model_state == "idle":
                threading.Thread(target=self.warmup_embeddings, daemon=True).start()
            return None
        try:
            embedding = model.encode(text, convert_to_numpy=True)
            return array("f", [float(x) for x in embedding]).tobytes()
        except Exception:
            return None

    # -------------------------------------------------------------- ingest
    def chunk_text(self, text: str) -> List[str]:
        text = _clean_text(text)
        if not text:
            return []
        chunks: List[str] = []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if buffer:
                    chunks.append(buffer.strip())
                    buffer = ""
                start = 0
                step = max(1, self.chunk_size - self.chunk_overlap)
                while start < len(paragraph):
                    chunks.append(paragraph[start:start + self.chunk_size].strip())
                    start += step
                continue
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = paragraph
        if buffer:
            chunks.append(buffer.strip())
        return [c for c in chunks if c]

    def add_document(self, filepath: str, copy_into_library: bool = False) -> Dict[str, Any]:
        try:
            path = Path(filepath).expanduser().resolve()
            content = extract_text(str(path))
            if not content:
                return {"success": False, "error": "The document contains no readable text."}
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute("SELECT id FROM documents WHERE filepath = ?", (str(path),))
                existing = cur.fetchone()
                if existing:
                    return {
                        "success": True,
                        "duplicate": True,
                        "document_id": int(existing[0]),
                        "chunks": 0,
                        "message": "Document already in the library.",
                    }

                chunks = self.chunk_text(content)
                cur.execute(
                    "INSERT INTO documents(filename, filepath, content_hash, file_type, "
                    "chunk_count, char_count, size_bytes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        path.name, str(path), content_hash, path.suffix.lower(),
                        len(chunks), len(content), path.stat().st_size,
                    ),
                )
                doc_id = int(cur.lastrowid)

                for idx, chunk in enumerate(chunks):
                    cur.execute(
                        "INSERT INTO chunks(document_id, chunk_text, chunk_index) "
                        "VALUES (?, ?, ?)",
                        (doc_id, chunk, idx),
                    )
                    chunk_id = int(cur.lastrowid)
                    if self._fts_available:
                        try:
                            cur.execute(
                                "INSERT INTO chunks_fts(rowid, chunk_text) VALUES (?, ?)",
                                (chunk_id, chunk),
                            )
                        except Exception:
                            self._fts_available = False
                    blob = self._encode(chunk)
                    if blob is not None and self._ensure_vec_table(conn):
                        try:
                            cur.execute(
                                "INSERT INTO rag_chunks(embedding) VALUES (?)", (blob,)
                            )
                            vec_rowid = int(cur.lastrowid)
                            cur.execute(
                                "INSERT INTO chunk_map(vec_rowid, chunk_id) VALUES (?, ?)",
                                (vec_rowid, chunk_id),
                            )
                        except Exception:
                            pass
                conn.commit()
            finally:
                conn.close()

            return {
                "success": True,
                "document_id": doc_id,
                "chunks": len(chunks),
                "chars": len(content),
                "filename": path.name,
            }
        except Exception as exc:  # noqa: BLE001 - returned to the UI
            return {"success": False, "error": str(exc)}

    def add_text(self, text: str, name: str = "Pasted note") -> Dict[str, Any]:
        """Ingest a pasted block without needing a file on disk."""
        try:
            from app_paths import data_path

            safe = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip() or "note"
            if not safe.lower().endswith(".txt"):
                safe += ".txt"
            path = Path(data_path("documents", safe))
            path.write_text(text, encoding="utf-8")
            return self.add_document(str(path))
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------- retrieve
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []
        results: List[Dict[str, Any]] = []
        blob = self._encode(query)
        if blob is not None:
            results = self._vector_search(blob, limit)
        keyword = self._keyword_search(query, limit)
        if not results:
            return keyword
        # Merge by chunk text, preferring vector relevance but boosting exact hits.
        seen = {r["text"][:120] for r in results}
        for item in keyword:
            if item["text"][:120] not in seen:
                item["relevance"] = min(0.99, item["relevance"])
                results.append(item)
        results.sort(key=lambda r: r["relevance"], reverse=True)
        return results[:limit]

    def _vector_search(self, blob: bytes, limit: int) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            if not self._ensure_vec_table(conn):
                return []
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.chunk_text, d.filename, d.filepath, r.distance
                FROM rag_chunks r
                JOIN chunk_map cm ON r.rowid = cm.vec_rowid
                JOIN chunks c ON cm.chunk_id = c.id
                JOIN documents d ON c.document_id = d.id
                WHERE r.embedding MATCH ?
                ORDER BY r.distance LIMIT ?
                """,
                (blob, int(limit)),
            )
            return [
                {
                    "text": row[0],
                    "filename": row[1],
                    "filepath": row[2],
                    "relevance": max(0.0, 1.0 - float(row[3])),
                    "mode": "vector",
                }
                for row in cur.fetchall()
            ]
        except Exception:
            return []
        finally:
            conn.close()

    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            rows = []
            if self._fts_available:
                safe_terms = [re.sub(r"[^\w]", "", t) for t in query.split() if len(t) > 1]
                fts_query = " OR ".join(f'"{t}"' for t in safe_terms if t)
                if fts_query:
                    try:
                        cur.execute(
                            """
                            SELECT c.chunk_text, d.filename, d.filepath, bm25(chunks_fts) AS rank
                            FROM chunks_fts f
                            JOIN chunks c ON c.id = f.rowid
                            JOIN documents d ON c.document_id = d.id
                            WHERE chunks_fts MATCH ?
                            ORDER BY rank LIMIT ?
                            """,
                            (fts_query, int(limit)),
                        )
                        rows = cur.fetchall()
                    except Exception:
                        rows = []
            if not rows:
                terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2][:5]
                pattern = f"%{terms[0]}%" if terms else f"%{query}%"
                cur.execute(
                    """
                    SELECT c.chunk_text, d.filename, d.filepath
                    FROM chunks c JOIN documents d ON c.document_id = d.id
                    WHERE c.chunk_text LIKE ? LIMIT ?
                    """,
                    (pattern, int(limit) * 4),
                )
                rows = cur.fetchall()
                terms = terms or [query.lower()]
                scored = []
                for row in rows:
                    low = row[0].lower()
                    score = sum(1 for t in terms if t in low)
                    if score:
                        scored.append((score, row))
                scored.sort(key=lambda pair: -pair[0])
                rows = [row for _, row in scored[:limit]]

            results = []
            for index, row in enumerate(rows):
                relevance = 0.72 - index * 0.04
                if len(row) > 3 and isinstance(row[3], (int, float)):
                    relevance = max(0.35, min(0.95, 0.95 - float(row[3]) / 20))
                results.append(
                    {
                        "text": row[0],
                        "filename": row[1],
                        "filepath": row[2],
                        "relevance": relevance,
                        "mode": "keyword",
                    }
                )
            return results
        finally:
            conn.close()

    def get_context(self, query: str, max_chunks: int = 3, max_chars: int = 6000) -> str:
        results = self.search(query, limit=max_chunks)
        if not results:
            return ""
        parts = ["## Relevant information from the user's documents"]
        for result in results:
            parts.append(
                f"### {result['filename']} (relevance {result['relevance']:.2f})\n"
                f"{result['text'][:2400]}"
            )
        return "\n\n".join(parts)[:max_chars]

    # ---------------------------------------------------------------- stats
    def list_documents(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, filename, filepath, file_type, upload_date, chunk_count, "
                "char_count, size_bytes FROM documents ORDER BY id DESC"
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_chunks(self, limit: int = 400) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT c.id, c.document_id, d.filename, c.chunk_index, c.chunk_text "
                "FROM chunks c JOIN documents d ON c.document_id = d.id "
                "ORDER BY c.id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            def count(sql: str) -> int:
                try:
                    cur.execute(sql)
                    return int(cur.fetchone()[0])
                except Exception:
                    return 0

            size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            return {
                "documents": count("SELECT COUNT(*) FROM documents"),
                "chunks": count("SELECT COUNT(*) FROM chunks"),
                "vectors": count("SELECT COUNT(*) FROM chunk_map"),
                "size": size,
                "size_text": readable_size(size),
                "path": self.db_path,
                "fts": self._fts_available,
                "vector_ready": bool(self._vec_available and self._model_state == "ready"),
                "vector_installed": SQLITE_VEC_AVAILABLE,
                "embeddings_installed": SENTENCE_TRANSFORMERS_AVAILABLE,
                "search_mode": "hybrid" if (self._vec_available and self._model_state == "ready") else ("full-text" if self._fts_available else "keyword"),
            }
        finally:
            conn.close()

    def delete_document(self, document_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,))
            chunk_ids = [int(row[0]) for row in cur.fetchall()]
            if self._fts_available:
                for chunk_id in chunk_ids:
                    try:
                        cur.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
                    except Exception:
                        self._fts_available = False
            for chunk_id in chunk_ids:
                try:
                    cur.execute(
                        "DELETE FROM rag_chunks WHERE rowid IN "
                        "(SELECT vec_rowid FROM chunk_map WHERE chunk_id = ?)",
                        (chunk_id,),
                    )
                except Exception:
                    pass
                cur.execute("DELETE FROM chunk_map WHERE chunk_id = ?", (chunk_id,))
            cur.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            cur.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def clear_all(self) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            for table in ("chunk_map", "chunks", "documents"):
                cur.execute(f"DELETE FROM {table}")
            try:
                cur.execute("DELETE FROM rag_chunks")
            except Exception:
                pass
            if self._fts_available:
                try:
                    cur.execute("DELETE FROM chunks_fts")
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()

    def export_json(self, path: str) -> Dict[str, Any]:
        payload = {
            "exported": datetime.now().isoformat(timespec="seconds"),
            "stats": self.stats(),
            "documents": self.list_documents(),
        }
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return payload

    def reindex_embeddings(self, progress: Optional[Callable[[int, int], None]] = None) -> int:
        """Embed chunks that predate the model being available."""
        if self._model_state != "ready":
            self.warmup_embeddings()
        if self.model is None:
            return 0
        conn = self._connect()
        try:
            if not self._ensure_vec_table(conn):
                return 0
            cur = conn.cursor()
            cur.execute(
                "SELECT c.id, c.chunk_text FROM chunks c "
                "LEFT JOIN chunk_map cm ON cm.chunk_id = c.id WHERE cm.id IS NULL"
            )
            rows = cur.fetchall()
            total = len(rows)
            done = 0
            for chunk_id, text in rows:
                blob = self._encode(text)
                if blob is None:
                    break
                cur.execute("INSERT INTO rag_chunks(embedding) VALUES (?)", (blob,))
                vec_rowid = int(cur.lastrowid)
                cur.execute(
                    "INSERT INTO chunk_map(vec_rowid, chunk_id) VALUES (?, ?)",
                    (vec_rowid, chunk_id),
                )
                done += 1
                if progress and done % 20 == 0:
                    progress(done, total)
            conn.commit()
            if progress:
                progress(done, total)
            return done
        finally:
            conn.close()


if __name__ == "__main__":
    rag = RAGSystem(enable_embeddings=False)
    print(json.dumps(rag.stats(), indent=2))
