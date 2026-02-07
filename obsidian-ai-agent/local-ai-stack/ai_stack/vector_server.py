#!/usr/bin/env python3
"""
Local Vector Database Server - Platform Independent
Uses ChromaDB or LanceDB for local vector storage
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('vector_server')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


class LocalVectorStore:
    """Local vector store using ChromaDB or file-based fallback"""
    
    def __init__(self, data_path: str = "./data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.collection = {}
        self.embeddings = {}
        self._load_data()
    
    def _load_data(self):
        """Load existing data from disk"""
        data_file = self.data_path / "vectors.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.collection = data.get('documents', {})
                    self.embeddings = data.get('embeddings', {})
                logger.info(f"Loaded {len(self.collection)} documents")
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
    
    def _save_data(self):
        """Save data to disk"""
        data_file = self.data_path / "vectors.json"
        try:
            with open(data_file, 'w') as f:
                json.dump({
                    'documents': self.collection,
                    'embeddings': self.embeddings
                }, f)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def add(self, documents: List[Document]):
        """Add documents to the store"""
        for doc in documents:
            self.collection[doc.id] = {
                'content': doc.content,
                'metadata': doc.metadata
            }
            if doc.embedding:
                self.embeddings[doc.id] = doc.embedding
        
        self._save_data()
        logger.info(f"Added {len(documents)} documents")
    
    def query(self, query_embedding: List[float], n_results: int = 5) -> List[Dict]:
        """Similarity search using cosine similarity"""
        import math
        
        def cosine_similarity(a, b):
            dot = sum(x*y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x*x for x in a))
            norm_b = math.sqrt(sum(x*x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0
        
        scores = []
        for doc_id, emb in self.embeddings.items():
            score = cosine_similarity(query_embedding, emb)
            scores.append((doc_id, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in scores[:n_results]:
            doc = self.collection.get(doc_id, {})
            results.append({
                'id': doc_id,
                'content': doc.get('content', ''),
                'metadata': doc.get('metadata', {}),
                'distance': 1 - score  # Convert similarity to distance
            })
        
        return results
    
    def get(self, doc_id: str) -> Optional[Document]:
        """Get a specific document"""
        if doc_id in self.collection:
            doc_data = self.collection[doc_id]
            return Document(
                id=doc_id,
                content=doc_data.get('content', ''),
                metadata=doc_data.get('metadata', {}),
                embedding=self.embeddings.get(doc_id)
            )
        return None
    
    def delete(self, doc_id: str):
        """Delete a document"""
        if doc_id in self.collection:
            del self.collection[doc_id]
            if doc_id in self.embeddings:
                del self.embeddings[doc_id]
            self._save_data()
            return True
        return False
    
    def count(self) -> int:
        return len(self.collection)


def create_app(data_path: str = "./data"):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    store = LocalVectorStore(data_path)
    app = Flask(__name__)
    
    @app.before_request
    def check_localhost():
        if request.remote_addr not in ALLOWED_HOSTS:
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'documents': store.count()
        })
    
    @app.route('/add', methods=['POST'])
    def add_documents():
        try:
            data = request.get_json()
            docs_data = data.get('documents', [])
            
            documents = [
                Document(
                    id=d.get('id'),
                    content=d.get('content', ''),
                    metadata=d.get('metadata', {}),
                    embedding=d.get('embedding')
                )
                for d in docs_data
            ]
            
            store.add(documents)
            return jsonify({'status': 'success', 'added': len(documents)})
        except Exception as e:
            logger.error(f"Add failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/query', methods=['POST'])
    def query():
        try:
            data = request.get_json()
            embedding = data.get('embedding', [])
            n_results = data.get('n_results', 5)
            
            results = store.query(embedding, n_results)
            return jsonify({'results': results})
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/get/<doc_id>', methods=['GET'])
    def get_document(doc_id: str):
        doc = store.get(doc_id)
        if doc:
            return jsonify(asdict(doc))
        return jsonify({'error': 'Not found'}), 404
    
    @app.route('/delete/<doc_id>', methods=['DELETE'])
    def delete_document(doc_id: str):
        if store.delete(doc_id):
            return jsonify({'status': 'deleted'})
        return jsonify({'error': 'Not found'}), 404
    
    @app.route('/count', methods=['GET'])
    def count():
        return jsonify({'count': store.count()})
    
    return app


def start_vector_server(host: str = '127.0.0.1', port: int = 8002, data_path: str = "./data"):
    logger.info(f"Starting Vector DB server on {host}:{port}")
    app = create_app(data_path)
    import logging as flask_logging
    flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8002)
    parser.add_argument('--data-path', default='./data')
    args = parser.parse_args()
    start_vector_server(args.host, args.port, args.data_path)
