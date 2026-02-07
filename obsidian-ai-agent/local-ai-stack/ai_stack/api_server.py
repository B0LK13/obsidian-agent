#!/usr/bin/env python3
"""
Unified API Server
Combines all optimized components into a single server
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api_server')

# Import optimized components
try:
    from memory_rag import MemoryAugmentedRAG
    from hallucination_guard import HallucinationReductionSystem
    from semantic_chunker import SemanticChunkingStrategy
    from evaluation_harness import NoteTakingEvaluator
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some components not available: {e}")
    COMPONENTS_AVAILABLE = False

# Flask imports
try:
    from flask import Flask, request, jsonify, Response
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    logger.error("Flask not installed. Run: pip install flask flask-cors")
    FLASK_AVAILABLE = False
    sys.exit(1)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']

class OptimizedAPIServer:
    """Unified API server with all optimizations"""
    
    def __init__(self, data_path: str = "./data"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.memory_rag = None
        self.hallucination_guard = None
        self.chunker = None
        self.evaluator = None
        
        if COMPONENTS_AVAILABLE:
            self._init_components()
        
        self.app = self._create_app()
    
    def _init_components(self):
        """Initialize all optimized components"""
        try:
            self.memory_rag = MemoryAugmentedRAG(str(self.data_path))
            logger.info("Memory RAG initialized")
        except Exception as e:
            logger.error(f"Failed to init Memory RAG: {e}")
        
        try:
            self.hallucination_guard = HallucinationReductionSystem()
            logger.info("Hallucination guard initialized")
        except Exception as e:
            logger.error(f"Failed to init Hallucination guard: {e}")
        
        try:
            self.chunker = SemanticChunkingStrategy()
            logger.info("Semantic chunker initialized")
        except Exception as e:
            logger.error(f"Failed to init Semantic chunker: {e}")
        
        try:
            self.evaluator = NoteTakingEvaluator()
            logger.info("Evaluator initialized")
        except Exception as e:
            logger.error(f"Failed to init Evaluator: {e}")
    
    def _create_app(self) -> Flask:
        """Create Flask application"""
        app = Flask(__name__)
        CORS(app, resources={r"/api/*": {"origins": "http://localhost:*"}})
        
        # Security middleware
        @app.before_request
        def check_localhost():
            remote_addr = request.remote_addr
            if remote_addr not in ALLOWED_HOSTS:
                return jsonify({'error': 'Access denied - localhost only'}), 403
        
        # Health check
        @app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'components': {
                    'memory_rag': self.memory_rag is not None,
                    'hallucination_guard': self.hallucination_guard is not None,
                    'chunker': self.chunker is not None,
                    'evaluator': self.evaluator is not None
                }
            })
        
        # Memory RAG endpoints
        @app.route('/api/rag/query', methods=['POST'])
        def rag_query():
            if not self.memory_rag:
                return jsonify({'error': 'Memory RAG not available'}), 503
            
            try:
                data = request.get_json()
                query = data.get('query', '')
                query_embedding = data.get('query_embedding', [])
                
                results = self.memory_rag.process_query(query, query_embedding)
                return jsonify(results)
            except Exception as e:
                logger.error(f"RAG query error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/rag/add', methods=['POST'])
        def rag_add():
            if not self.memory_rag:
                return jsonify({'error': 'Memory RAG not available'}), 503
            
            try:
                data = request.get_json()
                self.memory_rag.add_to_memory(
                    content=data.get('content', ''),
                    embedding=data.get('embedding', []),
                    metadata=data.get('metadata', {}),
                    relationships=data.get('relationships')
                )
                return jsonify({'status': 'added'})
            except Exception as e:
                logger.error(f"RAG add error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/rag/stats', methods=['GET'])
        def rag_stats():
            if not self.memory_rag:
                return jsonify({'error': 'Memory RAG not available'}), 503
            
            return jsonify(self.memory_rag.get_stats())
        
        # Hallucination guard endpoints
        @app.route('/api/validate', methods=['POST'])
        def validate():
            if not self.hallucination_guard:
                return jsonify({'error': 'Hallucination guard not available'}), 503
            
            try:
                data = request.get_json()
                result = self.hallucination_guard.validate(
                    generated=data.get('generated', ''),
                    source=data.get('source')
                )
                return jsonify(result)
            except Exception as e:
                logger.error(f"Validation error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Chunking endpoints
        @app.route('/api/chunk', methods=['POST'])
        def chunk():
            if not self.chunker:
                return jsonify({'error': 'Chunker not available'}), 503
            
            try:
                data = request.get_json()
                text = data.get('text', '')
                doc_type = data.get('doc_type', 'generic')
                
                chunks = self.chunker.chunk_document(text, doc_type)
                
                return jsonify({
                    'chunks': [c.to_dict() for c in chunks],
                    'stats': self.chunker.get_stats(chunks)
                })
            except Exception as e:
                logger.error(f"Chunking error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Evaluation endpoints
        @app.route('/api/evaluate', methods=['POST'])
        def evaluate():
            if not self.evaluator:
                return jsonify({'error': 'Evaluator not available'}), 503
            
            try:
                data = request.get_json()
                result = self.evaluator.evaluate(
                    prediction=data.get('prediction', ''),
                    reference=data.get('reference'),
                    context=data.get('context')
                )
                return jsonify(result.to_dict())
            except Exception as e:
                logger.error(f"Evaluation error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Indexing endpoint (combines chunking + embedding + storage)
        @app.route('/api/index', methods=['POST'])
        def index_document():
            try:
                data = request.get_json()
                file_path = data.get('file_path', '')
                content = data.get('content', '')
                doc_type = data.get('doc_type', 'generic')
                
                # Step 1: Chunk the document
                if self.chunker:
                    chunks = self.chunker.chunk_document(content, doc_type)
                else:
                    # Simple fallback
                    chunks = [{'text': content, 'id': 'chunk_0'}]
                
                # Step 2: Add to memory RAG
                if self.memory_rag:
                    # Note: Would need embedding here in real implementation
                    dummy_embedding = [0.0] * 384
                    for chunk in chunks:
                        chunk_text = chunk.text if hasattr(chunk, 'text') else chunk['text']
                        self.memory_rag.add_to_memory(
                            content=chunk_text,
                            embedding=dummy_embedding,
                            metadata={'source': file_path, 'doc_type': doc_type}
                        )
                
                return jsonify({
                    'status': 'indexed',
                    'chunks': len(chunks),
                    'file': file_path
                })
            except Exception as e:
                logger.error(f"Indexing error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Admin endpoints
        @app.route('/api/admin/stats', methods=['GET'])
        def admin_stats():
            stats = {
                'components': {
                    'memory_rag': self.memory_rag.get_stats() if self.memory_rag else None,
                    'chunker': {'status': 'available' if self.chunker else 'unavailable'},
                    'evaluator': {'status': 'available' if self.evaluator else 'unavailable'},
                    'hallucination_guard': {'status': 'available' if self.hallucination_guard else 'unavailable'}
                }
            }
            return jsonify(stats)
        
        @app.route('/api/admin/clear-cache', methods=['POST'])
        def clear_cache():
            if self.memory_rag:
                self.memory_rag.short_term.clear()
            return jsonify({'status': 'cache cleared'})
        
        return app
    
    def run(self, host: str = '127.0.0.1', port: int = 8003):
        """Run the server"""
        logger.info(f"Starting Optimized API Server on {host}:{port}")
        self.app.run(host=host, port=port, threaded=True)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized API Server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8003)
    parser.add_argument('--data-path', default='./data')
    
    args = parser.parse_args()
    
    server = OptimizedAPIServer(data_path=args.data_path)
    server.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
