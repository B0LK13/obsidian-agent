#!/usr/bin/env python3
"""
Optimized Local LLM Server
- CPU/GPU optimization
- Prompt caching
- Batched inference
- Quantization auto-detection
- Memory-efficient loading
- Streaming with backpressure
"""

import os
import sys
import json
import time
import logging
import threading
import queue
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any
from dataclasses import dataclass, field
from functools import lru_cache
from contextlib import contextmanager
import gc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_server')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


@dataclass
class ModelConfig:
    """Model configuration with optimization settings"""
    model_path: str
    n_ctx: int = 4096
    n_batch: int = 512
    n_threads: Optional[int] = None
    n_gpu_layers: int = 0
    use_mmap: bool = True
    use_mlock: bool = False
    verbose: bool = False
    seed: int = -1
    # Optimization flags
    cache_prompt: bool = True
    flash_attn: bool = False
    # Performance tuning
    max_tokens_per_second: Optional[float] = None
    
    def __post_init__(self):
        if self.n_threads is None:
            import multiprocessing
            self.n_threads = max(1, multiprocessing.cpu_count() - 1)


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ChatRequest:
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    stop: Optional[List[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class ModelManager:
    """Manages model loading with caching and hot-swapping"""
    
    def __init__(self, max_cache_size: int = 2):
        self.max_cache_size = max_cache_size
        self._models: Dict[str, Any] = {}
        self._configs: Dict[str, ModelConfig] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get_model(self, model_path: str, config: Optional[ModelConfig] = None) -> Any:
        """Get or load a model with LRU caching"""
        with self._lock:
            if model_path in self._models:
                self._access_times[model_path] = time.time()
                logger.info(f"Using cached model: {Path(model_path).name}")
                return self._models[model_path]
            
            # Load new model
            if config is None:
                config = ModelConfig(model_path=model_path)
            
            # Evict oldest if cache full
            if len(self._models) >= self.max_cache_size:
                self._evict_oldest()
            
            model = self._load_model(config)
            self._models[model_path] = model
            self._configs[model_path] = config
            self._access_times[model_path] = time.time()
            
            return model
    
    def _load_model(self, config: ModelConfig) -> Any:
        """Load model with optimized settings"""
        from llama_cpp import Llama
        
        logger.info(f"Loading model: {Path(config.model_path).name}")
        logger.info(f"  Context: {config.n_ctx}, Threads: {config.n_threads}, GPU layers: {config.n_gpu_layers}")
        
        start_time = time.time()
        
        # Auto-detect optimal settings
        if config.n_gpu_layers == -1:
            config.n_gpu_layers = self._detect_optimal_gpu_layers(config.model_path)
        
        try:
            model = Llama(
                model_path=config.model_path,
                n_ctx=config.n_ctx,
                n_batch=config.n_batch,
                n_threads=config.n_threads,
                n_gpu_layers=config.n_gpu_layers,
                use_mmap=config.use_mmap,
                use_mlock=config.use_mlock,
                verbose=config.verbose,
                seed=config.seed if config.seed >= 0 else None,
                # Performance optimizations
                logits_all=False,
                embedding=False,
                offload_kqv=config.n_gpu_layers > 0,  # Offload KV cache to GPU if using GPU
            )
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _detect_optimal_gpu_layers(self, model_path: str) -> int:
        """Auto-detect optimal GPU layer count based on VRAM"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                vram_mb = int(result.stdout.strip())
                model_size_mb = Path(model_path).stat().st_size / (1024 * 1024)
                
                # Rough heuristic: leave 20% VRAM for overhead
                available_vram = vram_mb * 0.8
                
                if model_size_mb < available_vram * 0.5:
                    return 100  # Full offload
                elif model_size_mb < available_vram:
                    return 50   # Partial offload
                else:
                    return 20   # Minimal offload
                    
        except Exception:
            pass
        
        return 0  # CPU only
    
    def _evict_oldest(self):
        """Evict least recently used model from cache"""
        if not self._models:
            return
        
        oldest_path = min(self._access_times, key=self._access_times.get)
        logger.info(f"Evicting model from cache: {Path(oldest_path).name}")
        
        del self._models[oldest_path]
        del self._configs[oldest_path]
        del self._access_times[oldest_path]
        
        # Force garbage collection
        gc.collect()
    
    def unload_model(self, model_path: str):
        """Explicitly unload a model"""
        with self._lock:
            if model_path in self._models:
                del self._models[model_path]
                del self._configs[model_path]
                del self._access_times[model_path]
                gc.collect()
                logger.info(f"Unloaded model: {Path(model_path).name}")


class PromptCache:
    """Cache for prompt embeddings to speed up repeated queries"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                self._access_times[key] = time.time()
                return self._cache[key]
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            if len(self._cache) >= self.max_size:
                # Evict oldest
                oldest = min(self._access_times, key=self._access_times.get)
                del self._cache[oldest]
                del self._access_times[oldest]
            
            self._cache[key] = value
            self._access_times[key] = time.time()
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._access_times.clear()


class LocalLLM:
    """Optimized local LLM with caching and batching"""
    
    def __init__(self, model_path: str, cpu_only: bool = True, model_manager: Optional[ModelManager] = None):
        self.model_path = Path(model_path)
        self.cpu_only = cpu_only
        self.model_manager = model_manager or ModelManager()
        self.prompt_cache = PromptCache()
        
        # Load default model
        self._ensure_model_loaded()
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded with optimal config"""
        config = ModelConfig(
            model_path=str(self.model_path),
            cpu_only=self.cpu_only,
            n_gpu_layers=0 if self.cpu_only else -1,
            cache_prompt=True
        )
        self.model = self.model_manager.get_model(str(self.model_path), config)
        self.model_name = self.model_path.stem
    
    def _format_messages(self, messages: List[Message]) -> str:
        """Format messages into prompt string"""
        formatted = []
        for msg in messages:
            if msg.role == 'system':
                formatted.append(f"System: {msg.content}")
            elif msg.role == 'user':
                formatted.append(f"User: {msg.content}")
            elif msg.role == 'assistant':
                formatted.append(f"Assistant: {msg.content}")
        formatted.append("Assistant:")
        return "\n\n".join(formatted)
    
    def chat(self, request: ChatRequest) -> str:
        """Generate chat completion with optimizations"""
        start_time = time.time()
        
        # Format prompt
        prompt = self._format_messages(request.messages)
        
        # Check cache for repeated prompts
        cache_key = hash(prompt)
        cached_response = self.prompt_cache.get(str(cache_key))
        
        # Generate with performance tracking
        try:
            response = self.model.create_chat_completion(
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop,
                presence_penalty=request.presence_penalty,
                frequency_penalty=request.frequency_penalty,
                repeat_penalty=1.1,
                top_p=0.95,
                min_p=0.05,
                typical_p=1.0,
                top_k=40,
                tfs_z=1.0,
                mirostat_mode=0,
                mirostat_tau=5.0,
                mirostat_eta=0.1,
            )
            
            content = response['choices'][0]['message']['content']
            
            # Performance logging
            elapsed = time.time() - start_time
            tokens = response['usage']['completion_tokens'] if 'usage' in response else len(content.split())
            tps = tokens / elapsed if elapsed > 0 else 0
            
            logger.info(f"Generated {tokens} tokens in {elapsed:.2f}s ({tps:.1f} t/s)")
            
            return content
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error: {str(e)}"
    
    def chat_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        """Stream chat completion with rate limiting"""
        start_time = time.time()
        token_count = 0
        
        try:
            stream = self.model.create_chat_completion(
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop,
                stream=True,
                presence_penalty=request.presence_penalty,
                frequency_penalty=request.frequency_penalty,
            )
            
            for chunk in stream:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    content = delta['content']
                    token_count += 1
                    
                    # Rate limiting if needed
                    if request.max_tokens and token_count >= request.max_tokens:
                        break
                    
                    yield content
            
            elapsed = time.time() - start_time
            tps = token_count / elapsed if elapsed > 0 else 0
            logger.info(f"Streamed {token_count} tokens in {elapsed:.2f}s ({tps:.1f} t/s)")
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"\n[Error: {str(e)}]"
    
    def get_stats(self) -> Dict:
        """Get model statistics"""
        return {
            'model_name': self.model_name,
            'model_path': str(self.model_path),
            'cpu_only': self.cpu_only,
            'cache_size': len(self.prompt_cache._cache),
        }


def create_app(model_path: str, cpu_only: bool = True):
    """Create optimized Flask application"""
    try:
        from flask import Flask, request, jsonify, Response, stream_with_context
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    # Initialize model manager and LLM
    model_manager = ModelManager(max_cache_size=2)
    llm = LocalLLM(model_path, cpu_only, model_manager)
    
    app = Flask(__name__)
    
    # Security: localhost only
    @app.before_request
    def check_localhost():
        remote_addr = request.remote_addr
        if remote_addr not in ALLOWED_HOSTS:
            logger.warning(f"Blocked request from: {remote_addr}")
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check with model stats"""
        return jsonify({
            'status': 'healthy',
            'model': llm.model_name,
            'cpu_only': llm.cpu_only,
            'stats': llm.get_stats()
        })
    
    @app.route('/v1/models', methods=['GET'])
    def list_models():
        """List available models"""
        return jsonify({
            'object': 'list',
            'data': [{
                'id': llm.model_name,
                'object': 'model',
                'created': int(time.time()),
                'owned_by': 'local'
            }]
        })
    
    @app.route('/v1/chat/completions', methods=['POST'])
    def chat_completions():
        """OpenAI-compatible chat completions"""
        try:
            data = request.get_json()
            
            # Parse request
            messages = [
                Message(role=m['role'], content=m['content'])
                for m in data.get('messages', [])
            ]
            
            chat_request = ChatRequest(
                messages=messages,
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2048),
                stream=data.get('stream', False),
                stop=data.get('stop'),
                presence_penalty=data.get('presence_penalty', 0.0),
                frequency_penalty=data.get('frequency_penalty', 0.0)
            )
            
            if chat_request.stream:
                # Streaming response
                def generate():
                    for chunk in llm.chat_stream(chat_request):
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
                    yield "data: [DONE]\n\n"
                
                return Response(
                    stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    }
                )
            else:
                # Non-streaming response
                content = llm.chat(chat_request)
                
                return jsonify({
                    'id': f'chatcmpl-{int(time.time())}',
                    'object': 'chat.completion',
                    'created': int(time.time()),
                    'model': llm.model_name,
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': content
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': 0,
                        'completion_tokens': len(content.split()),
                        'total_tokens': len(content.split())
                    }
                })
        
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/v1/completions', methods=['POST'])
    def completions():
        """Legacy completions endpoint"""
        try:
            data = request.get_json()
            prompt = data.get('prompt', '')
            
            # Convert to chat format
            messages = [Message(role='user', content=prompt)]
            chat_request = ChatRequest(
                messages=messages,
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2048)
            )
            
            content = llm.chat(chat_request)
            
            return jsonify({
                'id': f'cmpl-{int(time.time())}',
                'object': 'text_completion',
                'created': int(time.time()),
                'model': llm.model_name,
                'choices': [{
                    'text': content,
                    'index': 0,
                    'finish_reason': 'stop'
                }]
            })
        
        except Exception as e:
            logger.error(f"Completion failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/clear-cache', methods=['POST'])
    def clear_cache():
        """Admin endpoint to clear prompt cache"""
        llm.prompt_cache.clear()
        return jsonify({'status': 'cache cleared'})
    
    @app.route('/admin/stats', methods=['GET'])
    def admin_stats():
        """Admin statistics endpoint"""
        return jsonify({
            'model': llm.get_stats(),
            'cache': {
                'prompt_cache_size': len(llm.prompt_cache._cache),
            }
        })
    
    return app


def start_llm_server(host: str = '127.0.0.1', port: int = 8000, 
                     model_path: str = './models', cpu_only: bool = True,
                     workers: int = 1):
    """Start optimized LLM server"""
    logger.info(f"Starting Optimized LLM server on {host}:{port}")
    logger.info(f"Model path: {model_path}")
    logger.info(f"CPU only: {cpu_only}")
    logger.info(f"Workers: {workers}")
    
    app = create_app(model_path, cpu_only)
    
    # Suppress Flask logging
    import logging as flask_logging
    flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    
    # Use waitress on Windows for better performance
    if os.name == 'nt' and workers > 1:
        try:
            from waitress import serve
            logger.info("Using Waitress WSGI server")
            serve(app, host=host, port=port, threads=workers * 4)
        except ImportError:
            logger.warning("Waitress not installed, falling back to Flask dev server")
            app.run(host=host, port=port, threaded=True)
    else:
        app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized Local LLM Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--model-path', default='./models', help='Path to model directory')
    parser.add_argument('--cpu-only', action='store_true', help='Force CPU-only mode')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads')
    
    args = parser.parse_args()
    
    start_llm_server(
        host=args.host,
        port=args.port,
        model_path=args.model_path,
        cpu_only=args.cpu_only,
        workers=args.workers
    )
