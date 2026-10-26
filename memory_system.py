#!/usr/bin/env python3
"""GroqChatbot long-term memory.

SQLite is the source of truth. When ``sqlite-vec`` and a sentence-transformer
model are available, memories are also indexed as 384-dimensional vectors and
recalled semantically. When they are not installed the exact same API keeps
working with a fast keyword fallback, so the assistant never silently loses
its memory features.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app_paths import memory_db, readable_size

try:  # lightweight import; the heavy model itself is loaded lazily
    import sqlite_vec

    SQLITE_VEC_AVAILABLE = True
except Exception:  # noqa: BLE001 - optional native extension
    sqlite_vec = None
    SQLITE_VEC_AVAILABLE = False

try:
    from importlib.util import find_spec

    SENTENCE_TRANSFORMERS_AVAILABLE = find_spec("sentence_transformers") is not None
except Exception:  # noqa: BLE001
    SENTENCE_TRANSFORMERS_AVAILABLE = False

EMBEDDING_DIM = 384
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

FACT_PATTERNS = [
    re.compile(r"\bmy name is\s+([^.!?\n]{2,60})", re.I),
    re.compile(r"\bcall me\s+([^.!?\n]{2,40})", re.I),
    re.compile(r"\bi(?:'m| am) (?:a|an)?\s*([^.!?\n]{3,70})", re.I),
    re.compile(r"\bi (?:like|love|prefer|enjoy|use)\s+([^.!?\n]{2,80})", re.I),
    re.compile(r"\bmy (?:favorite|favourite)\s+([^.!?\n]{2,70})", re.I),
    re.compile(r"\bi (?:live|work) in\s+([^.!?\n]{2,60})", re.I),
    re.compile(r"\bremember (?:that )?(.{3,180})", re.I),
    re.compile(r"আমার নাম\s+([^।.!?\n]{2,60})"),
    re.compile(r"আমি\s+([^।.!?\n]{3,80})\s*(?:পছন্দ|ভালোবাসি)"),
]


class MemorySystem:
    """Conversation + fact store with optional semantic recall."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        enable_embeddings: bool = True,
    ) -> None:
        self.db_path = str(db_path or memory_db())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.embedding_dim = EMBEDDING_DIM
        self.enable_embeddings = bool(enable_embeddings and SENTENCE_TRANSFORMERS_AVAILABLE)
        self.model = None
        self._model_state = "idle"  # idle | loading | ready | unavailable
        self._model_lock = threading.Lock()
        self._vec_available = False
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
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL DEFAULT (strftime('%s','now')),
                    metadata TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact TEXT NOT NULL UNIQUE,
                    category TEXT,
                    confidence REAL DEFAULT 1.0,
                    timestamp REAL DEFAULT (strftime('%s','now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_map (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vec_rowid INTEGER,
                    type TEXT,
                    ref_id INTEGER,
                    content TEXT
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_time ON conversations(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_map_type ON memory_map(type)")
            conn.commit()
        finally:
            conn.close()

    def _ensure_vec_table(self, conn: sqlite3.Connection) -> bool:
        if not (self._vec_available and self.enable_embeddings):
            return False
        try:
            conn.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0("
                f"embedding FLOAT[{self.embedding_dim}])"
            )
            return True
        except Exception:
            self._vec_available = False
            return False

    # ------------------------------------------------------------- embedder
    def warmup_embeddings(self) -> None:
        """Load the embedding model off the UI thread. Safe to call twice."""
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
        """Return float32 bytes, or None when the model isn't ready yet.

        Never blocks: the UI warms the model in the background and the keyword
        index covers the gap. That keeps the composer instant on first launch.
        """
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

    # --------------------------------------------------------------- writes
    def add_conversation(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> int:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO conversations(session_id, role, content, metadata) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role, content, json.dumps(metadata) if metadata else None),
            )
            conv_id = int(cur.lastrowid)
            conn.commit()
        finally:
            conn.close()
        self.add_embedding(content, "conversation", conv_id)
        return conv_id

    def add_embedding(self, text: str, mem_type: str, ref_id: int) -> Optional[int]:
        blob = self._encode(text)
        if blob is None:
            return None
        conn = self._connect()
        try:
            if not self._ensure_vec_table(conn):
                return None
            cur = conn.cursor()
            cur.execute("INSERT INTO vec_memories(embedding) VALUES (?)", (blob,))
            vec_rowid = int(cur.lastrowid)
            cur.execute(
                "INSERT INTO memory_map(vec_rowid, type, ref_id, content) VALUES (?, ?, ?, ?)",
                (vec_rowid, mem_type, ref_id, text[:1200]),
            )
            conn.commit()
            return vec_rowid
        except Exception:
            return None
        finally:
            conn.close()

    def add_fact(
        self, fact: str, category: str = "general", confidence: float = 1.0
    ) -> Optional[int]:
        fact = (fact or "").strip()
        if not fact:
            return None
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO facts(fact, category, confidence) VALUES (?, ?, ?)",
                (fact[:500], category, float(confidence)),
            )
            if cur.rowcount:
                fact_id = int(cur.lastrowid)
                created = True
            else:
                cur.execute("SELECT id FROM facts WHERE fact = ?", (fact[:500],))
                row = cur.fetchone()
                fact_id = int(row[0]) if row else None
                created = False
            conn.commit()
        finally:
            conn.close()
        if fact_id and created:
            self.add_embedding(fact, "fact", fact_id)
        return fact_id

    def extract_facts(self, text: str, limit: int = 3) -> List[str]:
        """Cheap, transparent heuristic extraction (no extra model needed)."""
        found: List[str] = []
        for pattern in FACT_PATTERNS:
            for match in pattern.finditer(text or ""):
                value = match.group(1).strip(" ,;:-")
                if not value or len(value) < 2:
                    continue
                fact = match.group(0).strip()
                if fact.lower().startswith("remember that"):
                    fact = value
                elif fact.lower().startswith("remember"):
                    fact = value
                if fact not in found:
                    found.append(fact[:300])
                if len(found) >= limit:
                    return found
        return found

    def remember_from_message(self, text: str) -> List[str]:
        saved = []
        for fact in self.extract_facts(text):
            if self.add_fact(fact, category="auto"):
                saved.append(fact)
        return saved

    # --------------------------------------------------------------- reads
    def get_facts(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            if category:
                cur.execute(
                    "SELECT * FROM facts WHERE category = ? ORDER BY confidence DESC, id DESC LIMIT ?",
                    (category, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM facts ORDER BY confidence DESC, id DESC LIMIT ?", (limit,)
                )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []
        blob = self._encode(query)
        if blob is not None:
            vector_results = self._vector_search(blob, limit)
            if vector_results:
                return vector_results
        return self._keyword_search(query, limit)

    def _vector_search(self, blob: bytes, limit: int) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            if not self._ensure_vec_table(conn):
                return []
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.rowid, m.distance, mm.type, mm.ref_id, mm.content
                FROM vec_memories m
                JOIN memory_map mm ON m.rowid = mm.vec_rowid
                WHERE m.embedding MATCH ?
                ORDER BY m.distance LIMIT ?
                """,
                (blob, int(limit)),
            )
            return [
                {
                    "rowid": row[0],
                    "distance": row[1],
                    "type": row[2],
                    "ref_id": row[3],
                    "content": row[4],
                    "mode": "vector",
                }
                for row in cur.fetchall()
            ]
        except Exception:
            return []
        finally:
            conn.close()

    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2][:8]
        if not terms:
            terms = [query.lower()]
        pattern = "%" + terms[0] + "%"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT rowid, type, ref_id, content FROM memory_map "
                "WHERE content LIKE ? ORDER BY rowid DESC LIMIT ?",
                (pattern, max(limit * 4, 20)),
            )
            rows = cur.fetchall()
            if len(rows) < limit:
                cur.execute(
                    "SELECT id, 'conversation', id, content FROM conversations "
                    "WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                    (pattern, max(limit, 10)),
                )
                rows += cur.fetchall()
        finally:
            conn.close()

        scored = []
        seen = set()
        for row in rows:
            content = row[3] or ""
            key = content[:80]
            if key in seen:
                continue
            seen.add(key)
            low = content.lower()
            score = sum(1 for term in terms if term in low)
            if score:
                scored.append(
                    {
                        "rowid": row[0],
                        "distance": 1.0 - min(score / max(len(terms), 1), 0.95),
                        "type": row[1],
                        "ref_id": row[2],
                        "content": content,
                        "mode": "keyword",
                        "score": score,
                    }
                )
        scored.sort(key=lambda item: (-item["score"], item["distance"]))
        return scored[:limit]

    def get_memory_context(self, query: str, max_items: int = 8, max_chars: int = 3500) -> str:
        facts = self.get_facts(limit=12)
        memories = self.search_memories(query, limit=max_items)
        parts: List[str] = []
        if facts:
            parts.append("## Known facts about the user")
            parts.extend(f"- {fact['fact']}" for fact in facts[:8])
            parts.append("")
        if memories:
            parts.append("## Relevant memories")
            for mem in memories[:max_items]:
                content = " ".join((mem.get("content") or "").split())
                parts.append(f"- [{mem.get('type', 'memory')}] {content[:400]}")
        text = "\n".join(parts).strip()
        return text[:max_chars]

    def recent_conversations(self, limit: int = 100) -> List[Dict]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, session_id, role, content, timestamp, metadata "
                "FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def search_conversations(self, query: str, limit: int = 200) -> List[Dict]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            if query:
                cur.execute(
                    "SELECT id, session_id, role, content, timestamp, metadata "
                    "FROM conversations WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                    (f"%{query}%", limit),
                )
            else:
                cur.execute(
                    "SELECT id, session_id, role, content, timestamp, metadata "
                    "FROM conversations ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_memories(self, limit: int = 500) -> List[Dict]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, vec_rowid, type, ref_id, content FROM memory_map "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            def count(table: str) -> int:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    return int(cur.fetchone()[0])
                except Exception:
                    return 0

            vector_rows = count("vec_memories") if self._vec_available else 0
            try:
                cur.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
                sessions = int(cur.fetchone()[0])
            except Exception:
                sessions = 0
            size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            return {
                "conversations": count("conversations"),
                "facts": count("facts"),
                "vectors": vector_rows,
                "sessions": sessions,
                "size": size,
                "size_text": readable_size(size),
                "path": self.db_path,
                "vector_ready": bool(self._vec_available and self._model_state == "ready"),
                "vector_installed": SQLITE_VEC_AVAILABLE,
                "embeddings_installed": SENTENCE_TRANSFORMERS_AVAILABLE,
                "memory_mode": "semantic" if (self._vec_available and self._model_state == "ready") else "keyword",
            }
        finally:
            conn.close()

    # -------------------------------------------------------------- deletes
    def delete_conversation(self, conv_id: int) -> bool:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def delete_fact(self, fact_id: int) -> bool:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def clear_all(self, keep_facts: bool = False) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM conversations")
            cur.execute("DELETE FROM memory_map")
            try:
                cur.execute("DELETE FROM vec_memories")
            except Exception:
                pass
            if not keep_facts:
                cur.execute("DELETE FROM facts")
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------- exports
    def export_json(self, path: str) -> Dict[str, Any]:
        payload = {
            "exported": datetime.now().isoformat(timespec="seconds"),
            "stats": self.stats(),
            "facts": self.get_facts(limit=5000),
            "conversations": self.recent_conversations(limit=5000),
        }
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return payload

    def export_markdown(self, path: str) -> int:
        rows = list(reversed(self.recent_conversations(limit=5000)))
        lines = [
            "# GroqChatbot memory export",
            "",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        facts = self.get_facts(limit=5000)
        if facts:
            lines += ["## Facts", ""] + [f"- {f['fact']}" for f in facts] + [""]
        lines += ["## Conversations", ""]
        for row in rows:
            stamp = datetime.fromtimestamp(row["timestamp"]).strftime("%Y-%m-%d %H:%M")
            lines += [f"### {row['role']} · {stamp}", "", row["content"], ""]
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines))
        return len(rows)


if __name__ == "__main__":
    mem = MemorySystem("test_memory.db", enable_embeddings=False)
    mem.add_conversation("demo", "user", "Hello, my name is Rahim and I love tea.")
    mem.remember_from_message("Hello, my name is Rahim and I love tea.")
    print(json.dumps(mem.stats(), indent=2))
    print(mem.get_memory_context("tea"))
