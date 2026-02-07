#!/usr/bin/env python3
"""Local Embeddings Server - Platform Independent"""

import logging
from pathlib import Path
from typing import List, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('embed_server')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


class LocalEmbeddings:
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path) if model_path else None
        self.model = None
        self.model_name = "all-MiniLM-L6-v2"
        self._load_model()
    
    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            
            if self.model_path and self.model_path.exists():
                model_files = list(self.model_path.glob("*embed*"))
                if model_files:
                    self.model = SentenceTransformer(str(model_files[0]))
                    self.model_name = model_files[0].stem
                else:
                    self.model = SentenceTransformer(self.model_name)
            else:
                self.model = SentenceTransformer(self.model_name)
            
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        else:
            # Fallback: simple hash-based embeddings
            import hashlib
            results = []
            for text in texts:
                hash_obj = hashlib.sha256(text.encode())
                vector = []
                for i in range(384):
                    hash_obj.update(str(i).encode())
                    vector.append(int(hash_obj.hexdigest()[:8], 16) / 2**32)
                results.append(vector)
            return results


def create_app(model_path: str = None):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    embedder = LocalEmbeddings(model_path)
    app = Flask(__name__)
    
    @app.before_request
    def check_localhost():
        if request.remote_addr not in ALLOWED_HOSTS:
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'model': embedder.model_name,
            'using_fallback': embedder.model is None
        })
    
    @app.route('/embed', methods=['POST'])
    @app.route('/v1/embeddings', methods=['POST'])
    def embed():
        try:
            data = request.get_json()
            texts = data.get('input', [])
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = embedder.embed(texts)
            
            return jsonify({
                'object': 'list',
                'data': [
                    {'object': 'embedding', 'embedding': emb, 'index': i}
                    for i, emb in enumerate(embeddings)
                ],
                'model': embedder.model_name
            })
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app


def start_embed_server(host: str = '127.0.0.1', port: int = 8001, model_path: str = None):
    logger.info(f"Starting Embeddings server on {host}:{port}")
    app = create_app(model_path)
    import logging as flask_logging
    flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--model-path', default=None)
    args = parser.parse_args()
    start_embed_server(args.host, args.port, args.model_path)
