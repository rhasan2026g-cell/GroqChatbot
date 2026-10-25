#!/usr/bin/env python3
"""
GroqChatbot Memory System
SQLite + sqlite-vec for long-term semantic memory
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import sqlite_vec
    SQLITE_VEC_AVAILABLE = True
except ImportError:
    SQLITE_VEC_AVAILABLE = False

class MemorySystem:
    def __init__(self, db_path: str = "memory.db", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.embedding_dim = 384
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
            except:
                self.model = None
        else:
            self.model = None
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database with tables and vector store"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        if SQLITE_VEC_AVAILABLE and self.model is not None:
            try:
                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
                conn.enable_load_extension(False)
                
                cur.execute(f'''
                    CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
                        embedding FLOAT[{self.embedding_dim}]
                    )
                ''')
            except Exception as e:
                print(f"Could not load sqlite-vec: {e}")
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL DEFAULT (strftime('%s','now')),
                metadata TEXT
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL UNIQUE,
                category TEXT,
                confidence REAL DEFAULT 1.0,
                timestamp REAL DEFAULT (strftime('%s','now'))
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS memory_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vec_rowid INTEGER,
                type TEXT,
                ref_id INTEGER,
                content TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Memory system initialized: {self.db_path}")
    
    def add_embedding(self, text: str, mem_type: str, ref_id: int):
        if not SQLITE_VEC_AVAILABLE or self.model is None:
            return None
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            embedding_bytes = embedding.astype(np.float32).tobytes()
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('INSERT INTO vec_memories(embedding) VALUES (?)', (embedding_bytes,))
            vec_rowid = cur.lastrowid
            cur.execute('INSERT INTO memory_map(vec_rowid, type, ref_id, content) VALUES (?, ?, ?, ?)', 
                        (vec_rowid, mem_type, ref_id, text[:500]))
            conn.commit()
            conn.close()
            return vec_rowid
        except Exception as e:
            print(f"Error adding embedding: {e}")
            return None
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not SQLITE_VEC_AVAILABLE or self.model is None:
            return []
        try:
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            query_bytes = query_embedding.astype(np.float32).tobytes()
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('''
                SELECT m.rowid, distance, mm.type, mm.ref_id, mm.content
                FROM vec_memories m
                JOIN memory_map mm ON m.rowid = mm.vec_rowid
                WHERE embedding MATCH ?
                ORDER BY distance LIMIT ?
            ''', (query_bytes, limit))
            results = []
            for row in cur.fetchall():
                results.append({'rowid': row[0], 'distance': row[1], 'type': row[2], 'ref_id': row[3], 'content': row[4]})
            conn.close()
            return results
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def add_conversation(self, session_id: str, role: str, content: str, metadata: Dict = None):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('INSERT INTO conversations(session_id, role, content, metadata) VALUES (?, ?, ?, ?)',
                    (session_id, role, content, json.dumps(metadata) if metadata else None))
        conv_id = cur.lastrowid
        conn.commit()
        conn.close()
        self.add_embedding(content, 'conversation', conv_id)
        return conv_id
    
    def add_fact(self, fact: str, category: str = "general", confidence: float = 1.0):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute('INSERT OR IGNORE INTO facts(fact, category, confidence) VALUES (?, ?, ?)', (fact, category, confidence))
            fact_id = cur.lastrowid
            if fact_id == 0:
                cur.execute('SELECT id FROM facts WHERE fact = ?', (fact,))
                row = cur.fetchone()
                fact_id = row[0] if row else None
            conn.commit()
            conn.close()
            if fact_id:
                self.add_embedding(fact, 'fact', fact_id)
            return fact_id
        except Exception as e:
            print(f"Error adding fact: {e}")
            conn.close()
            return None
    
    def get_facts(self, category: str = None, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if category:
            cur.execute('SELECT * FROM facts WHERE category = ? ORDER BY confidence DESC LIMIT ?', (category, limit))
        else:
            cur.execute('SELECT * FROM facts ORDER BY confidence DESC LIMIT ?', (limit,))
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results
    
    def get_memory_context(self, query: str, max_items: int = 8) -> str:
        memories = self.search_memories(query, limit=max_items)
        facts = self.get_facts(limit=10)
        context_parts = []
        if facts:
            context_parts.append("## Known Facts About User:")
            for fact in facts[:5]:
                context_parts.append(f"- {fact['fact']}")
            context_parts.append("")
        if memories:
            context_parts.append("## Relevant Past Conversations:")
            for mem in memories:
                context_parts.append(f"- [{mem['type']}] {mem['content']}")
            context_parts.append("")
        return "\n".join(context_parts) if context_parts else ""
