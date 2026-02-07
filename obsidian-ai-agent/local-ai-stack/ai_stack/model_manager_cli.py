#!/usr/bin/env python3
"""
Model Manager CLI
Download, convert, and manage LLM models
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List


class ModelManager:
    """Manage local LLM models"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model registry
        self.registry = {
            "llama-2-7b-chat": {
                "name": "Llama-2-7B-Chat",
                "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF",
                "files": {
                    "Q4_K_M": "llama-2-7b-chat.Q4_K_M.gguf",
                    "Q5_K_M": "llama-2-7b-chat.Q5_K_M.gguf",
                    "Q6_K": "llama-2-7b-chat.Q6_K.gguf",
                },
                "description": "Meta's Llama 2 7B chat model",
                "size_gb": 4.0
            },
            "llama-2-13b-chat": {
                "name": "Llama-2-13B-Chat",
                "url": "https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF",
                "files": {
                    "Q4_K_M": "llama-2-13b-chat.Q4_K_M.gguf",
                    "Q5_K_M": "llama-2-13b-chat.Q5_K_M.gguf",
                },
                "description": "Meta's Llama 2 13B chat model",
                "size_gb": 8.0
            },
            "mistral-7b-instruct": {
                "name": "Mistral-7B-Instruct",
                "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                "files": {
                    "Q4_K_M": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                    "Q5_K_M": "mistral-7b-instruct-v0.2.Q5_K_M.gguf",
                },
                "description": "Mistral AI's 7B instruct model",
                "size_gb": 4.5
            },
            "phi-2": {
                "name": "Phi-2",
                "url": "https://huggingface.co/TheBloke/phi-2-GGUF",
                "files": {
                    "Q4_K_M": "phi-2.Q4_K_M.gguf",
                    "Q5_K_M": "phi-2.Q5_K_M.gguf",
                },
                "description": "Microsoft's Phi-2 (2.7B parameters)",
                "size_gb": 1.6
            },
            "neural-chat-7b": {
                "name": "Neural-Chat-7B",
                "url": "https://huggingface.co/TheBloke/neural-chat-7B-v3-1-GGUF",
                "files": {
                    "Q4_K_M": "neural-chat-7b-v3-1.Q4_K_M.gguf",
                },
                "description": "Intel's Neural Chat 7B (optimized for conversation)",
                "size_gb": 4.0
            }
        }
    
    def list_available(self) -> None:
        """List available models in registry"""
        print("\n" + "=" * 70)
        print("AVAILABLE MODELS")
        print("=" * 70)
        
        for key, info in self.registry.items():
            print(f"\n{info['name']} ({key})")
            print(f"  Description: {info['description']}")
            print(f"  Size: ~{info['size_gb']} GB")
            print(f"  URL: {info['url']}")
            print(f"  Quantizations: {', '.join(info['files'].keys())}")
        
        print("\n" + "=" * 70)
    
    def list_local(self) -> List[Path]:
        """List locally available models"""
        models = list(self.models_dir.glob("*.gguf"))
        
        print("\n" + "=" * 70)
        print("LOCAL MODELS")
        print("=" * 70)
        
        if not models:
            print("\nNo models found in:", self.models_dir)
            print("\nDownload a model with:")
            print(f"  python model_manager_cli.py download <model_key> --quant Q4_K_M")
        else:
            for i, model in enumerate(models, 1):
                size_mb = model.stat().st_size / (1024 * 1024)
                size_gb = size_mb / 1024
                print(f"\n{i}. {model.name}")
                print(f"   Size: {size_gb:.2f} GB ({size_mb:.0f} MB)")
                print(f"   Path: {model}")
        
        print("\n" + "=" * 70)
        return models
    
    def download(self, model_key: str, quantization: str = "Q4_K_M",
                 method: str = "huggingface") -> bool:
        """Download a model"""
        if model_key not in self.registry:
            print(f"Error: Unknown model '{model_key}'")
            print(f"Run 'list' to see available models")
            return False
        
        model_info = self.registry[model_key]
        
        if quantization not in model_info['files']:
            print(f"Error: Quantization '{quantization}' not available")
            print(f"Available: {', '.join(model_info['files'].keys())}")
            return False
        
        filename = model_info['files'][quantization]
        output_path = self.models_dir / filename
        
        if output_path.exists():
            print(f"Model already exists: {output_path}")
            return True
        
        print(f"\nDownloading {model_info['name']} ({quantization})...")
        print(f"URL: {model_info['url']}")
        print(f"File: {filename}")
        print(f"Size: ~{model_info['size_gb']} GB")
        print()
        
        if method == "huggingface":
            return self._download_hf(model_info['url'], filename, output_path)
        else:
            print(f"Download method '{method}' not implemented")
            print(f"Please download manually from: {model_info['url']}")
            return False
    
    def _download_hf(self, repo_url: str, filename: str, output_path: Path) -> bool:
        """Download from HuggingFace"""
        try:
            from huggingface_hub import hf_hub_download
            
            # Extract repo ID from URL
            repo_id = repo_url.replace("https://huggingface.co/", "")
            
            print(f"Downloading from HuggingFace: {repo_id}")
            
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False
            )
            
            print(f"✓ Downloaded to: {downloaded_path}")
            return True
            
        except ImportError:
            print("Error: huggingface_hub not installed")
            print("Install with: pip install huggingface_hub")
            print("\nOr download manually from the URL above")
            return False
        except Exception as e:
            print(f"Error downloading: {e}")
            return False
    
    def recommend(self, vram_gb: Optional[float] = None, 
                  ram_gb: Optional[float] = None,
                  priority: str = "balanced") -> None:
        """Recommend model based on hardware"""
        print("\n" + "=" * 70)
        print("MODEL RECOMMENDATION")
        print("=" * 70)
        
        # Auto-detect hardware
        if vram_gb is None:
            vram_gb = self._detect_vram()
        
        if ram_gb is None:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
        
        print(f"\nDetected Hardware:")
        print(f"  RAM: {ram_gb:.1f} GB")
        print(f"  VRAM: {vram_gb:.1f} GB" if vram_gb else "  VRAM: None (CPU only)")
        print(f"  Priority: {priority}")
        
        print(f"\nRecommendations:")
        
        if vram_gb and vram_gb >= 8:
            print("\n  ✓ Llama-2-13B (Q4_K_M) - Best quality")
            print("    GPU accelerated, excellent for complex tasks")
            
        if vram_gb and vram_gb >= 4 or ram_gb >= 16:
            print("\n  ✓ Llama-2-7B (Q4_K_M) - Best balance")
            print("    Good quality, fast inference")
            print("    Can run on GPU (4GB+) or CPU")
            
        if ram_gb >= 8:
            print("\n  ✓ Mistral-7B-Instruct (Q4_K_M) - Great alternative")
            print("    Modern architecture, very capable")
            
        print("\n  ✓ Phi-2 (Q4_K_M) - Fastest option")
        print("    Smallest model, runs well on CPU")
        print("    Good for simple tasks and experimentation")
        
        print("\n" + "=" * 70)
    
    def _detect_vram(self) -> Optional[float]:
        """Detect available VRAM in GB"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip()) / 1024
        except:
            pass
        return None
    
    def verify(self, model_path: Optional[str] = None) -> bool:
        """Verify a model file is valid"""
        if model_path is None:
            models = list(self.models_dir.glob("*.gguf"))
            if not models:
                print("No models found to verify")
                return False
            model_path = str(models[0])
        
        path = Path(model_path)
        if not path.exists():
            print(f"Model not found: {path}")
            return False
        
        print(f"\nVerifying: {path.name}")
        print(f"Size: {path.stat().st_size / (1024**3):.2f} GB")
        
        # Try to load with llama.cpp
        try:
            from llama_cpp import Llama
            
            print("Loading model...")
            model = Llama(
                model_path=str(path),
                n_ctx=512,  # Small context for verification
                verbose=False
            )
            
            print("Testing inference...")
            response = model("Hello", max_tokens=10)
            
            print("✓ Model is valid and working!")
            return True
            
        except Exception as e:
            print(f"✗ Model verification failed: {e}")
            return False


def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(description='Model Manager CLI')
    parser.add_argument('--models-dir', default='./models', help='Models directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List available models')
    subparsers.add_parser('local', help='List local models')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a model')
    download_parser.add_argument('model', help='Model key (e.g., llama-2-7b-chat)')
    download_parser.add_argument('--quant', default='Q4_K_M', help='Quantization level')
    
    # Recommend command
    recommend_parser = subparsers.add_parser('recommend', help='Get model recommendation')
    recommend_parser.add_argument('--vram', type=float, help='Available VRAM in GB')
    recommend_parser.add_argument('--ram', type=float, help='Available RAM in GB')
    recommend_parser.add_argument('--priority', default='balanced', 
                                   choices=['speed', 'quality', 'balanced'])
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a model')
    verify_parser.add_argument('--model', help='Path to model file')
    
    args = parser.parse_args()
    
    manager = ModelManager(args.models_dir)
    
    if args.command == 'list':
        manager.list_available()
    elif args.command == 'local':
        manager.list_local()
    elif args.command == 'download':
        success = manager.download(args.model, args.quant)
        sys.exit(0 if success else 1)
    elif args.command == 'recommend':
        manager.recommend(args.vram, args.ram, args.priority)
    elif args.command == 'verify':
        success = manager.verify(args.model)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
