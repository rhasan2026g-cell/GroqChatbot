#!/usr/bin/env python3
"""
GroqChatbot RAG System
Retrieval-Augmented Generation with document ingestion
"""

import os
import json
import sqlite3
import hashlib
from typing import List, Dict, Any
from pathlib import Path

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

class RAGSystem:
    def __init__(self, db_path: str = "rag.db", chunk_size: int = 500, chunk_overlap: int = 50):
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_dim = 384
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
            except:
                self.model = None
        else:
            self.model = None
        
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        if SQLITE_VEC_AVAILABLE and self.model:
            try:
                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
                conn.enable_load_extension(False)
                cur.execute(f'''
                    CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING vec0(
                        embedding FLOAT[{self.embedding_dim}]
                    )
                ''')
            except Exception as e:
                print(f"Vector table error: {e}")
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                content_hash TEXT,
                file_type TEXT,
                upload_date REAL DEFAULT (strftime('%s','now')),
                chunk_count INTEGER
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                chunk_text TEXT,
                chunk_index INTEGER,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS chunk_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vec_rowid INTEGER,
                chunk_id INTEGER,
                FOREIGN KEY(chunk_id) REFERENCES chunks(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def chunk_text(self, text: str) -> List[str]:
        chunks = []
        words = text.split()
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    def add_document(self, filepath: str) -> Dict[str, Any]:
        try:
            path = Path(filepath)
            if not path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('SELECT id FROM documents WHERE filepath = ?', (filepath,))
            if cur.fetchone():
                conn.close()
                return {"success": False, "error": "Document already exists"}
            
            cur.execute('INSERT INTO documents(filename, filepath, content_hash, file_type, chunk_count) VALUES (?, ?, ?, ?, ?)',
                        (path.name, filepath, content_hash, path.suffix, 0))
            doc_id = cur.lastrowid
            
            chunks = self.chunk_text(content)
            for idx, chunk in enumerate(chunks):
                cur.execute('INSERT INTO chunks(document_id, chunk_text, chunk_index) VALUES (?, ?, ?)',
                            (doc_id, chunk, idx))
                chunk_id = cur.lastrowid
                
                if SQLITE_VEC_AVAILABLE and self.model:
                    try:
                        embedding = self.model.encode(chunk, convert_to_numpy=True)
                        embedding_bytes = embedding.astype('float32').tobytes()
                        conn.enable_load_extension(True)
                        sqlite_vec.load(conn)
                        conn.enable_load_extension(False)
                        cur.execute('INSERT INTO rag_chunks(embedding) VALUES (?)', (embedding_bytes,))
                        vec_rowid = cur.lastrowid
                        cur.execute('INSERT INTO chunk_map(vec_rowid, chunk_id) VALUES (?, ?)', (vec_rowid, chunk_id))
                    except:
                        pass
            
            cur.execute('UPDATE documents SET chunk_count = ? WHERE id = ?', (len(chunks), doc_id))
            conn.commit()
            conn.close()
            
            return {"success": True, "document_id": doc_id, "chunks": len(chunks)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not SQLITE_VEC_AVAILABLE or not self.model:
            return []
        try:
            query_emb = self.model.encode(query, convert_to_numpy=True)
            query_bytes = query_emb.astype('float32').tobytes()
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute('''
                SELECT c.chunk_text, d.filename, d.filepath, distance
                FROM rag_chunks r
                JOIN chunk_map cm ON r.rowid = cm.vec_rowid
                JOIN chunks c ON cm.chunk_id = c.id
                JOIN documents d ON c.document_id = d.id
                WHERE embedding MATCH ?
                ORDER BY distance LIMIT ?
            ''', (query_bytes, limit))
            results = []
            for row in cur.fetchall():
                results.append({
                    'text': row[0],
                    'filename': row[1],
                    'filepath': row[2],
                    'relevance': 1 - row[3]
                })
            conn.close()
            return results
        except Exception as e:
            print(f"RAG search error: {e}")
            return []
    
    def get_context(self, query: str, max_chunks: int = 3) -> str:
        results = self.search(query, limit=max_chunks)
        if not results:
            return ""
        context = "## Relevant Information from Documents:\n\n"
        for i, r in enumerate(results):
            context += f"### From {r['filename']} (relevance: {r['relevance']:.2f})\n{r['text']}\n\n"
        return context

if __name__ == "__main__":
    rag = RAGSystem()
    print("RAG system initialized")
