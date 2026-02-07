#!/usr/bin/env python3
"""
GPU-Safe Local LLM Server
- Dynamic GPU memory monitoring
- Graceful OOM handling with automatic CPU fallback
- VRAM-aware layer allocation
- Auto-recovery from CUDA errors
"""

import os
import sys
import json
import time
import logging
import threading
import gc
import warnings
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any, Tuple
from dataclasses import dataclass, field
from functools import lru_cache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_server_gpu_safe')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


class GPUMemoryMonitor:
    """Monitor GPU memory and provide allocation recommendations"""
    
    def __init__(self):
        self.vram_total = 0
        self.vram_free = 0
        self.vram_used = 0
        self.has_gpu = False
        self._detect_gpu()
    
    def _detect_gpu(self) -> bool:
        """Detect GPU and get VRAM info"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total,memory.free,memory.used', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 3:
                    self.vram_total = int(parts[0].strip())
                    self.vram_free = int(parts[1].strip())
                    self.vram_used = int(parts[2].strip())
                    self.has_gpu = True
                    logger.info(f"GPU detected: {self.vram_total}MB total VRAM")
                    return True
        except Exception as e:
            logger.debug(f"GPU detection failed: {e}")
        
        self.has_gpu = False
        return False
    
    def refresh(self):
        """Refresh GPU memory stats"""
        self._detect_gpu()
    
    def get_recommended_gpu_layers(self, model_path: str) -> Tuple[int, str]:
        """
        Get recommended GPU layer count based on available VRAM
        Returns: (n_gpu_layers, reason)
        """
        if not self.has_gpu:
            return 0, "No GPU detected"
        
        try:
            model_size_mb = Path(model_path).stat().st_size / (1024 * 1024)
            
            # Leave 15% buffer for overhead
            available_vram = self.vram_free * 0.85
            
            # Rough estimate: model needs ~1.2x its size in VRAM for full offload
            required_for_full = model_size_mb * 1.2
            
            # **ENHANCED**: Warn user if model is very large for their GPU
            if model_size_mb > self.vram_total:
                logger.warning(
                    f"⚠️  Model size ({model_size_mb:.0f}MB) exceeds total GPU memory ({self.vram_total}MB)! "
                    f"Recommend using a smaller quantized model (Q4 instead of Q5/Q6)."
                )
            
            if required_for_full < available_vram:
                logger.info(f"✅ Full GPU offload recommended ({model_size_mb:.0f}MB < {available_vram:.0f}MB free)")
                return -1, f"Full GPU offload possible ({model_size_mb:.0f}MB < {available_vram:.0f}MB free)"
            
            # Calculate partial offload
            # Each layer is roughly model_size / (num_layers) where num_layers is typically 32-40
            estimated_layers = 32  # Conservative estimate
            mb_per_layer = model_size_mb / estimated_layers
            
            # Leave 500MB buffer
            layers_that_fit = int((available_vram - 500) / mb_per_layer)
            layers_that_fit = max(0, min(layers_that_fit, estimated_layers))
            
            if layers_that_fit > 0:
                logger.warning(
                    f"⚠️  Partial GPU offload: {layers_that_fit}/{estimated_layers} layers "
                    f"(~{layers_that_fit * mb_per_layer:.0f}MB / {model_size_mb:.0f}MB total)"
                )
                return layers_that_fit, f"Partial offload: {layers_that_fit} layers (~{layers_that_fit * mb_per_layer:.0f}MB)"
            
            logger.error(
                f"❌ Insufficient VRAM for GPU acceleration!\n"
                f"   Model: {model_size_mb:.0f}MB | Free VRAM: {available_vram:.0f}MB\n"
                f"   Recommendation: Use CPU-only mode or smaller model"
            )
            return 0, f"Insufficient VRAM ({model_size_mb:.0f}MB needed, {available_vram:.0f}MB free)"
            
        except Exception as e:
            logger.warning(f"Could not calculate GPU layers: {e}")
            return 0, f"Calculation error: {e}"
    
    def check_oom_risk(self, context_size: int = 4096) -> Tuple[bool, str]:
        """
        Check if there's risk of OOM with given context size
        Returns: (is_risky, message)
        """
        if not self.has_gpu:
            return False, "No GPU"
        
        # Rough estimate: context needs ~2MB per 1K tokens
        estimated_context_memory = (context_size / 1024) * 2
        
        if self.vram_free < estimated_context_memory:
            return True, f"Low VRAM: {self.vram_free}MB free, ~{estimated_context_memory:.0f}MB needed for context"
        
        return False, f"VRAM OK: {self.vram_free}MB free"


@dataclass
class ModelConfig:
    """Model configuration with GPU safety"""
    model_path: str
    n_ctx: int = 4096
    n_batch: int = 512
    n_threads: Optional[int] = None
    n_gpu_layers: int = 0
    use_mmap: bool = True
    use_mlock: bool = False
    verbose: bool = False
    seed: int = -1
    cache_prompt: bool = True
    flash_attn: bool = False
    max_tokens_per_second: Optional[float] = None
    # OOM recovery
    fallback_to_cpu_on_oom: bool = True
    auto_reduce_context: bool = True
    
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


class SafeModelLoader:
    """Load models with OOM protection and fallback"""
    
    def __init__(self):
        self.gpu_monitor = GPUMemoryMonitor()
        self._current_model = None
        self._current_config = None
        self._lock = threading.RLock()
    
    def load_model(self, config: ModelConfig) -> Any:
        """
        Load model with automatic GPU layer detection and OOM fallback
        """
        with self._lock:
            from llama_cpp import Llama
            
            # Auto-detect GPU layers if set to -1
            if config.n_gpu_layers == -1:
                config.n_gpu_layers, reason = self.gpu_monitor.get_recommended_gpu_layers(
                    config.model_path
                )
                logger.info(f"GPU layer recommendation: {reason}")
            
            # Check OOM risk
            is_risky, msg = self.gpu_monitor.check_oom_risk(config.n_ctx)
            if is_risky and config.auto_reduce_context:
                original_ctx = config.n_ctx
                config.n_ctx = 2048  # Reduce context
                logger.warning(f"OOM risk detected: {msg}")
                logger.warning(f"Reducing context size: {original_ctx} -> {config.n_ctx}")
            
            try:
                logger.info(f"Loading model with {config.n_gpu_layers} GPU layers...")
                
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
                    logits_all=False,
                    embedding=False,
                    offload_kqv=config.n_gpu_layers > 0,
                )
                
                self._current_model = model
                self._current_config = config
                logger.info("Model loaded successfully")
                return model
                
            except RuntimeError as e:
                if "CUDA out of memory" in str(e) or "out of memory" in str(e).lower():
                    return self._handle_oom_error(config, e)
                raise
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
    
    def _handle_oom_error(self, config: ModelConfig, error: Exception) -> Any:
        """Handle OOM by falling back to CPU or reducing GPU layers"""
        logger.error(f"OOM Error: {error}")
        
        if not config.fallback_to_cpu_on_oom:
            raise error
        
        if config.n_gpu_layers > 0:
            # Try with fewer GPU layers
            logger.warning("Attempting fallback with reduced GPU layers...")
            config.n_gpu_layers = max(0, config.n_gpu_layers // 2)
            return self.load_model(config)
        
        # Fall back to CPU
        logger.warning("Falling back to CPU-only mode...")
        config.n_gpu_layers = 0
        config.use_mmap = True
        config.use_mlock = False
        
        # Force garbage collection
        gc.collect()
        
        try:
            from llama_cpp import Llama
            model = Llama(
                model_path=config.model_path,
                n_ctx=config.n_ctx,
                n_batch=config.n_batch,
                n_threads=config.n_threads,
                n_gpu_layers=0,  # CPU only
                use_mmap=True,
                use_mlock=False,
                verbose=config.verbose,
                seed=config.seed if config.seed >= 0 else None,
            )
            
            self._current_model = model
            self._current_config = config
            logger.info("Model loaded successfully on CPU")
            return model
            
        except Exception as e2:
            logger.error(f"CPU fallback also failed: {e2}")
            raise RuntimeError(
                f"Failed to load model on both GPU and CPU. "
                f"Original error: {error}, CPU error: {e2}"
            )
    
    def reload_with_cpu(self):
        """Force reload current model on CPU"""
        if self._current_config:
            self._current_config.n_gpu_layers = 0
            return self.load_model(self._current_config)
        raise RuntimeError("No model currently loaded")


class SafeLocalLLM:
    """LLM with OOM protection and auto-recovery"""
    
    def __init__(self, model_path: str, cpu_only: bool = False):
        self.model_path = Path(model_path)
        self.cpu_only = cpu_only
        self.model_loader = SafeModelLoader()
        self.model = None
        self.model_name = None
        self._is_cpu_fallback = False
        self._load()
    
    def _load(self):
        """Initial model load"""
        config = ModelConfig(
            model_path=str(self.model_path),
            cpu_only=self.cpu_only,
            n_gpu_layers=0 if self.cpu_only else -1,  # -1 triggers auto-detection
            fallback_to_cpu_on_oom=True,
            auto_reduce_context=True,
        )
        
        self.model = self.model_loader.load_model(config)
        self.model_name = self.model_path.stem
        self._is_cpu_fallback = config.n_gpu_layers == 0
        
        if self._is_cpu_fallback:
            logger.info("Model running on CPU (GPU fallback)")
    
    def _safe_chat_completion(self, **kwargs) -> Dict:
        """
        Wrapper for chat completion with OOM recovery
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                return self.model.create_chat_completion(**kwargs)
                
            except RuntimeError as e:
                if "CUDA out of memory" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"OOM during inference (attempt {attempt + 1})")
                    
                    # Try to recover
                    if not self._is_cpu_fallback:
                        logger.warning("Switching to CPU mode...")
                        self.model = self.model_loader.reload_with_cpu()
                        self._is_cpu_fallback = True
                    else:
                        # Already on CPU, reduce context
                        logger.warning("Already on CPU, reducing max_tokens...")
                        if 'max_tokens' in kwargs and kwargs['max_tokens'] > 512:
                            kwargs['max_tokens'] = 512
                    
                    gc.collect()
                    continue
                    
                raise
        
        raise RuntimeError("Max retries exceeded")
    
    def chat(self, request: ChatRequest) -> str:
        """Generate chat completion with OOM protection"""
        try:
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            
            response = self._safe_chat_completion(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop,
                presence_penalty=request.presence_penalty,
                frequency_penalty=request.frequency_penalty,
                repeat_penalty=1.1,
                top_p=0.95,
                min_p=0.05,
                top_k=40,
            )
            
            return response['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error: {str(e)}. Try reducing context size or using a smaller model."
    
    def chat_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        """Stream chat completion with OOM protection"""
        try:
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            
            stream = self.model.create_chat_completion(
                messages=messages,
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
                    yield delta['content']
                    
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                logger.error("OOM during streaming")
                yield "\n[Error: Out of GPU memory. Switching to CPU mode...]\n"
                
                # Try to recover
                if not self._is_cpu_fallback:
                    self.model = self.model_loader.reload_with_cpu()
                    self._is_cpu_fallback = True
                    yield "[Switched to CPU. Please retry your query.]"
                else:
                    yield "[Out of memory. Try a shorter query or smaller model.]"
            else:
                yield f"\n[Error: {str(e)}]"
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"\n[Error: {str(e)}]"
    
    def get_stats(self) -> Dict:
        """Get model statistics"""
        gpu_monitor = self.model_loader.gpu_monitor
        return {
            'model_name': self.model_name,
            'model_path': str(self.model_path),
            'cpu_only': self.cpu_only,
            'is_cpu_fallback': self._is_cpu_fallback,
            'gpu': {
                'available': gpu_monitor.has_gpu,
                'vram_total_mb': gpu_monitor.vram_total,
                'vram_free_mb': gpu_monitor.vram_free,
            } if gpu_monitor.has_gpu else None
        }


def create_app(model_path: str, cpu_only: bool = False):
    """Create GPU-safe Flask application"""
    try:
        from flask import Flask, request, jsonify, Response, stream_with_context
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    # Initialize LLM with OOM protection
    logger.info("Initializing GPU-safe LLM server...")
    llm = SafeLocalLLM(model_path, cpu_only)
    
    app = Flask(__name__)
    
    @app.before_request
    def check_localhost():
        remote_addr = request.remote_addr
        if remote_addr not in ALLOWED_HOSTS:
            logger.warning(f"Blocked request from: {remote_addr}")
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check with GPU info"""
        return jsonify({
            'status': 'healthy',
            'model': llm.model_name,
            'cpu_only': llm.cpu_only,
            'is_cpu_fallback': llm._is_cpu_fallback,
            'stats': llm.get_stats()
        })
    
    @app.route('/v1/models', methods=['GET'])
    def list_models():
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
        try:
            data = request.get_json()
            
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
            return jsonify({
                'error': str(e),
                'message': 'If this is an OOM error, try reducing max_tokens or context size'
            }), 500
    
    return app


def start_server(host: str = '127.0.0.1', port: int = 8000, 
                 model_path: str = './models', cpu_only: bool = False):
    """Start GPU-safe LLM server"""
    logger.info(f"Starting GPU-safe LLM server on {host}:{port}")
    logger.info(f"Model path: {model_path}")
    logger.info(f"CPU only: {cpu_only}")
    
    # Pre-warm GPU memory check
    monitor = GPUMemoryMonitor()
    if monitor.has_gpu:
        logger.info(f"GPU Status: {monitor.vram_free}MB free / {monitor.vram_total}MB total")
    else:
        logger.info("No GPU detected - will use CPU")
    
    app = create_app(model_path, cpu_only)
    
    import logging as flask_logging
    flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU-Safe Local LLM Server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--model-path', default='./models')
    parser.add_argument('--cpu-only', action='store_true')
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        model_path=args.model_path,
        cpu_only=args.cpu_only
    )
