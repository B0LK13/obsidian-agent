#!/usr/bin/env python3
"""
Optimized Vector Database Server
- HNSW indexing for fast approximate nearest neighbor search
- Lazy loading for large datasets
- Background indexing
- Batch operations
- Persistent storage with ChromaDB or LanceDB fallback
"""

import os
import json
import logging
import threading
import time
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('vector_server_optimized')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


class HNSWIndex:
    """
    HNSW (Hierarchical Navigable Small World) index for fast ANN search
    Fallback to linear search if hnswlib not available
    """
    
    def __init__(self, dim: int = 384, max_elements: int = 100000, 
                 ef_construction: int = 200, M: int = 16):
        self.dim = dim
        self.max_elements = max_elements
        self.ef_construction = ef_construction
        self.M = M
        self._index = None
        self._id_to_label: Dict[str, int] = {}
        self._label_to_id: Dict[int, str] = {}
        self._current_label = 0
        self._use_hnsw = False
        
        self._init_index()
    
    def _init_index(self):
        """Initialize HNSW index if available"""
        try:
            import hnswlib
            self._index = hnswlib.Index(space='cosine', dim=self.dim)
            self._index.init_index(
                max_elements=self.max_elements,
                ef_construction=self.ef_construction,
                M=self.M
            )
            self._index.set_ef(50)  # Search time accuracy/speed tradeoff
            self._use_hnsw = True
            logger.info(f"HNSW index initialized (dim={self.dim})")
        except ImportError:
            logger.warning("hnswlib not available, using linear search fallback")
            self._use_hnsw = False
    
    def add_items(self, embeddings: List[List[float]], ids: List[str]):
        """Add items to index"""
        if not embeddings:
            return
        
        if self._use_hnsw:
            # Map IDs to integer labels
            labels = []
            for doc_id in ids:
                if doc_id not in self._id_to_label:
                    self._id_to_label[doc_id] = self._current_label
                    self._label_to_id[self._current_label] = doc_id
                    labels.append(self._current_label)
                    self._current_label += 1
                else:
                    labels.append(self._id_to_label[doc_id])
            
            # Add to HNSW index
            import numpy as np
            embeddings_array = np.array(embeddings).astype('float32')
            self._index.add_items(embeddings_array, labels)
            logger.debug(f"Added {len(ids)} items to HNSW index")
        
        else:
            # Linear search fallback - store in dict
            for doc_id, emb in zip(ids, embeddings):
                self._id_to_label[doc_id] = emb
    
    def knn_query(self, query_embedding: List[float], k: int = 5) -> Tuple[List[str], List[float]]:
        """Query k nearest neighbors"""
        if self._use_hnsw and self._index:
            import numpy as np
            query = np.array([query_embedding]).astype('float32')
            labels, distances = self._index.knn_query(query, k=k)
            
            ids = [self._label_to_id.get(int(l), str(l)) for l in labels[0]]
            return ids, distances[0].tolist()
        
        else:
            # Linear search fallback
            import math
            
            def cosine_distance(a, b):
                dot = sum(x*y for x, y in zip(a, b))
                norm_a = math.sqrt(sum(x*x for x in a))
                norm_b = math.sqrt(sum(x*x for x in b))
                if norm_a == 0 or norm_b == 0:
                    return 1.0
                return 1 - (dot / (norm_a * norm_b))
            
            scores = []
            for doc_id, emb in self._id_to_label.items():
                if isinstance(emb, list):
                    dist = cosine_distance(query_embedding, emb)
                    scores.append((doc_id, dist))
            
            scores.sort(key=lambda x: x[1])
            top_k = scores[:k]
            return [s[0] for s in top_k], [s[1] for s in top_k]
    
    def save(self, path: Path):
        """Save index to disk"""
        if self._use_hnsw and self._index:
            index_path = path / "hnsw_index.bin"
            self._index.save_index(str(index_path))
            
            # Save mappings
            mappings = {
                'id_to_label': self._id_to_label,
                'label_to_id': self._label_to_id,
                'current_label': self._current_label,
                'dim': self.dim
            }
            with open(path / "hnsw_mappings.pkl", 'wb') as f:
                pickle.dump(mappings, f)
        
        else:
            # Save linear index
            with open(path / "linear_index.pkl", 'wb') as f:
                pickle.dump(self._id_to_label, f)
    
    def load(self, path: Path):
        """Load index from disk"""
        index_file = path / "hnsw_index.bin"
        mappings_file = path / "hnsw_mappings.pkl"
        linear_file = path / "linear_index.pkl"
        
        if index_file.exists() and mappings_file.exists():
            try:
                self._index.load_index(str(index_file))
                with open(mappings_file, 'rb') as f:
                    mappings = pickle.load(f)
                    self._id_to_label = mappings['id_to_label']
                    self._label_to_id = mappings['label_to_id']
                    self._current_label = mappings['current_label']
                    self.dim = mappings.get('dim', self.dim)
                self._use_hnsw = True
                logger.info(f"Loaded HNSW index with {len(self._id_to_label)} items")
            except Exception as e:
                logger.error(f"Failed to load HNSW index: {e}")
        
        elif linear_file.exists():
            with open(linear_file, 'rb') as f:
                self._id_to_label = pickle.load(f)
            self._use_hnsw = False
            logger.info(f"Loaded linear index with {len(self._id_to_label)} items")


class OptimizedVectorStore:
    """High-performance vector store with HNSW indexing"""
    
    def __init__(self, data_path: str = "./data", embedding_dim: int = 384):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = embedding_dim
        
        # Document storage
        self.collection: Dict[str, Dict] = {}
        self.embeddings: Dict[str, List[float]] = {}
        
        # HNSW index
        self.index = HNSWIndex(dim=embedding_dim)
        
        # Threading
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._index_dirty = False
        self._last_save = 0
        
        # Lazy loading
        self._loaded = False
        self._load_queue = []
        
        # Stats
        self._query_count = 0
        self._total_query_time = 0
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from disk (lazy)"""
        data_file = self.data_path / "vectors_optimized.json"
        
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.collection = data.get('documents', {})
                    # Embeddings stored separately for efficiency
                logger.info(f"Loaded metadata for {len(self.collection)} documents")
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
        
        # Try to load HNSW index
        index_path = self.data_path / "index"
        if index_path.exists():
            try:
                self.index.load(index_path)
                self._loaded = True
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
    
    def _save_data(self, force: bool = False):
        """Save data to disk with debouncing"""
        current_time = time.time()
        
        # Debounce: only save every 5 seconds unless forced
        if not force and current_time - self._last_save < 5:
            return
        
        with self._lock:
            try:
                # Save metadata
                data_file = self.data_path / "vectors_optimized.json"
                with open(data_file, 'w') as f:
                    json.dump({
                        'documents': self.collection,
                        'count': len(self.collection)
                    }, f)
                
                # Save embeddings (batched for efficiency)
                emb_file = self.data_path / "embeddings.pkl"
                with open(emb_file, 'wb') as f:
                    pickle.dump(self.embeddings, f)
                
                # Save HNSW index
                index_path = self.data_path / "index"
                index_path.mkdir(exist_ok=True)
                self.index.save(index_path)
                
                self._last_save = current_time
                self._index_dirty = False
                logger.debug(f"Saved {len(self.collection)} documents")
                
            except Exception as e:
                logger.error(f"Failed to save data: {e}")
    
    def add(self, documents: List[Document], batch_size: int = 100):
        """Add documents with batching"""
        if not documents:
            return
        
        with self._lock:
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                
                embeddings = []
                ids = []
                
                for doc in batch:
                    self.collection[doc.id] = {
                        'content': doc.content,
                        'metadata': doc.metadata
                    }
                    if doc.embedding:
                        self.embeddings[doc.id] = doc.embedding
                        embeddings.append(doc.embedding)
                        ids.append(doc.id)
                
                # Add to index
                if embeddings:
                    self.index.add_items(embeddings, ids)
                
                logger.debug(f"Added batch of {len(batch)} documents")
            
            self._index_dirty = True
        
        # Trigger async save
        self._executor.submit(self._save_data)
    
    def query(self, query_embedding: List[float], n_results: int = 5,
              filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """Fast similarity search with optional filtering"""
        start_time = time.time()
        
        # Get candidates from HNSW index
        ids, distances = self.index.knn_query(query_embedding, k=n_results * 2)
        
        results = []
        with self._lock:
            for doc_id, distance in zip(ids, distances):
                if doc_id not in self.collection:
                    continue
                
                doc = self.collection[doc_id]
                
                # Apply metadata filter if specified
                if filter_metadata:
                    meta = doc.get('metadata', {})
                    if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                        continue
                
                results.append({
                    'id': doc_id,
                    'content': doc.get('content', ''),
                    'metadata': doc.get('metadata', {}),
                    'distance': distance,
                    'score': 1 - distance  # Convert distance to similarity score
                })
                
                if len(results) >= n_results:
                    break
        
        # Update stats
        query_time = time.time() - start_time
        self._query_count += 1
        self._total_query_time += query_time
        
        logger.debug(f"Query returned {len(results)} results in {query_time*1000:.2f}ms")
        
        return results
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document"""
        with self._lock:
            if doc_id in self.collection:
                del self.collection[doc_id]
                if doc_id in self.embeddings:
                    del self.embeddings[doc_id]
                self._index_dirty = True
                
                # Trigger async save
                self._executor.submit(self._save_data)
                return True
            return False
    
    def get(self, doc_id: str) -> Optional[Document]:
        """Get a specific document"""
        with self._lock:
            if doc_id in self.collection:
                doc_data = self.collection[doc_id]
                return Document(
                    id=doc_id,
                    content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {}),
                    embedding=self.embeddings.get(doc_id)
                )
            return None
    
    def count(self) -> int:
        return len(self.collection)
    
    def get_stats(self) -> Dict:
        """Get store statistics"""
        avg_query_time = (self._total_query_time / self._query_count * 1000) if self._query_count > 0 else 0
        return {
            'documents': len(self.collection),
            'embeddings': len(self.embeddings),
            'queries': self._query_count,
            'avg_query_time_ms': round(avg_query_time, 2),
            'using_hnsw': self.index._use_hnsw,
            'index_size': self.index._current_label
        }
    
    def optimize(self):
        """Optimize storage and index"""
        logger.info("Optimizing vector store...")
        
        # Force save
        self._save_data(force=True)
        
        # Garbage collection
        gc.collect()
        
        logger.info("Optimization complete")
    
    def close(self):
        """Clean shutdown"""
        logger.info("Shutting down vector store...")
        self._save_data(force=True)
        self._executor.shutdown(wait=True)


def create_app(data_path: str = "./data"):
    """Create optimized Flask application"""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    store = OptimizedVectorStore(data_path)
    app = Flask(__name__)
    
    @app.before_request
    def check_localhost():
        if request.remote_addr not in ALLOWED_HOSTS:
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'documents': store.count(),
            'stats': store.get_stats()
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
            return jsonify({
                'status': 'success',
                'added': len(documents),
                'total': store.count()
            })
        except Exception as e:
            logger.error(f"Add failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/query', methods=['POST'])
    def query():
        try:
            data = request.get_json()
            embedding = data.get('embedding', [])
            n_results = data.get('n_results', 5)
            filter_metadata = data.get('filter')
            
            results = store.query(embedding, n_results, filter_metadata)
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
        return jsonify({
            'count': store.count(),
            'stats': store.get_stats()
        })
    
    @app.route('/optimize', methods=['POST'])
    def optimize():
        store.optimize()
        return jsonify({'status': 'optimized', 'stats': store.get_stats()})
    
    @app.teardown_appcontext
    def cleanup(exception):
        store.close()
    
    return app


def start_server(host: str = '127.0.0.1', port: int = 8002, data_path: str = "./data"):
    """Start optimized vector server"""
    logger.info(f"Starting Optimized Vector DB server on {host}:{port}")
    
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
    
    start_server(args.host, args.port, args.data_path)
