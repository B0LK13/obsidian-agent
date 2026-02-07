#!/usr/bin/env python3
"""
Local LLM Server - Platform Independent
Uses llama.cpp Python bindings for CPU/GPU inference
OpenAI-compatible API endpoint
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llm_server')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


@dataclass
class Message:
    role: str
    content: str


class LocalLLM:
    """Local LLM wrapper using llama.cpp"""
    
    def __init__(self, model_path: str, cpu_only: bool = True):
        self.model_path = Path(model_path)
        self.cpu_only = cpu_only
        self.model = None
        self.model_name = None
        self._load_model()
    
    def _load_model(self):
        try:
            from llama_cpp import Llama
            
            if self.model_path.is_dir():
                model_files = list(self.model_path.glob("*.gguf"))
                if not model_files:
                    raise FileNotFoundError(f"No .gguf files found in {self.model_path}")
                model_file = model_files[0]
            else:
                model_file = self.model_path
            
            logger.info(f"Loading model: {model_file}")
            self.model_name = model_file.stem
            
            kwargs = {
                "model_path": str(model_file),
                "verbose": False,
            }
            
            if self.cpu_only:
                kwargs["n_gpu_layers"] = 0
            else:
                kwargs["n_gpu_layers"] = -1
            
            self.model = Llama(**kwargs)
            logger.info("Model loaded successfully")
            
        except ImportError:
            logger.error("llama-cpp-python not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def chat(self, messages: List[Message], temperature: float = 0.7, 
             max_tokens: int = 2048) -> str:
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = self.model.create_chat_completion(
                messages=chat_history,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error: {str(e)}"


def create_app(model_path: str, cpu_only: bool = True):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.error("Flask not installed")
        raise
    
    llm = LocalLLM(model_path, cpu_only)
    
    app = Flask(__name__)
    
    @app.before_request
    def check_localhost():
        remote_addr = request.remote_addr
        if remote_addr not in ALLOWED_HOSTS:
            return jsonify({'error': 'Access denied - localhost only'}), 403
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'model': llm.model_name,
            'cpu_only': llm.cpu_only
        })
    
    @app.route('/v1/models', methods=['GET'])
    def list_models():
        return jsonify({
            'object': 'list',
            'data': [{
                'id': llm.model_name or 'local-llm',
                'object': 'model',
                'created': int(__import__('time').time()),
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
            
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 2048)
            
            content = llm.chat(messages, temperature, max_tokens)
            
            return jsonify({
                'id': 'chatcmpl-local',
                'object': 'chat.completion',
                'created': int(__import__('time').time()),
                'model': llm.model_name,
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': content
                    },
                    'finish_reason': 'stop'
                }]
            })
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app


def start_llm_server(host: str = '127.0.0.1', port: int = 8000, 
                     model_path: str = './models', cpu_only: bool = True):
    logger.info(f"Starting LLM server on {host}:{port}")
    app = create_app(model_path, cpu_only)
    import logging as flask_logging
    flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--model-path', default='./models')
    parser.add_argument('--cpu-only', action='store_true')
    args = parser.parse_args()
    start_llm_server(args.host, args.port, args.model_path, args.cpu_only)
