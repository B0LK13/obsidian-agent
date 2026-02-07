#!/usr/bin/env python3
"""
Automatic Model Download Tool for Obsidian AI Agent
Downloads GGUF models from HuggingFace Hub with progress tracking

GitHub Issue: https://github.com/B0LK13/obsidian-agent/issues/105
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List
import hashlib
import json

try:
    from huggingface_hub import hf_hub_download, list_repo_files, model_info
    from tqdm import tqdm
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  huggingface_hub not installed. Install with: pip install huggingface_hub tqdm")


# Popular model configurations
POPULAR_MODELS = {
    "llama-2-7b": {
        "repo": "TheBloke/Llama-2-7B-Chat-GGUF",
        "files": {
            "Q4_K_M": "llama-2-7b-chat.Q4_K_M.gguf",
            "Q5_K_M": "llama-2-7b-chat.Q5_K_M.gguf",
            "Q6_K": "llama-2-7b-chat.Q6_K.gguf",
        },
        "description": "Llama 2 7B - balanced performance",
        "size_range": "4-6 GB"
    },
    "llama-2-13b": {
        "repo": "TheBloke/Llama-2-13B-Chat-GGUF",
        "files": {
            "Q4_K_M": "llama-2-13b-chat.Q4_K_M.gguf",
            "Q5_K_M": "llama-2-13b-chat.Q5_K_M.gguf",
        },
        "description": "Llama 2 13B - higher quality, more VRAM",
        "size_range": "7-10 GB"
    },
    "phi-2": {
        "repo": "TheBloke/phi-2-GGUF",
        "files": {
            "Q4_K_M": "phi-2.Q4_K_M.gguf",
            "Q5_K_M": "phi-2.Q5_K_M.gguf",
        },
        "description": "Phi-2 2.7B - very fast, CPU-friendly",
        "size_range": "1.5-2 GB"
    },
    "mistral-7b": {
        "repo": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "files": {
            "Q4_K_M": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "Q5_K_M": "mistral-7b-instruct-v0.2.Q5_K_M.gguf",
        },
        "description": "Mistral 7B - excellent quality/speed ratio",
        "size_range": "4-6 GB"
    },
}


class ModelDownloader:
    """Download and manage GGUF models from HuggingFace"""
    
    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.models_dir / ".download_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load download cache"""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text())
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save download cache"""
        self.cache_file.write_text(json.dumps(self.cache, indent=2))
    
    def list_popular_models(self):
        """List popular pre-configured models"""
        print("\n📚 Popular Models:\n")
        for model_id, config in POPULAR_MODELS.items():
            print(f"  {model_id:20} - {config['description']}")
            print(f"  {'':20}   Size: {config['size_range']}")
            print(f"  {'':20}   Quantizations: {', '.join(config['files'].keys())}")
            print()
    
    def download_model(
        self,
        model_id: str,
        quantization: str = "Q4_K_M",
        repo_id: Optional[str] = None,
        filename: Optional[str] = None,
        resume: bool = True
    ) -> Path:
        """
        Download a model from HuggingFace Hub
        
        Args:
            model_id: Model identifier (e.g., 'llama-2-7b')
            quantization: Quantization level (Q4_K_M, Q5_K_M, Q6_K)
            repo_id: Override HuggingFace repo ID
            filename: Override specific filename
            resume: Resume interrupted downloads
            
        Returns:
            Path to downloaded model file
        """
        if not HF_AVAILABLE:
            raise ImportError("Install huggingface_hub: pip install huggingface_hub tqdm")
        
        # Resolve model configuration
        if model_id in POPULAR_MODELS:
            config = POPULAR_MODELS[model_id]
            repo_id = repo_id or config["repo"]
            filename = filename or config["files"].get(quantization)
            
            if not filename:
                available = ', '.join(config["files"].keys())
                raise ValueError(
                    f"Quantization '{quantization}' not available for {model_id}. "
                    f"Available: {available}"
                )
        else:
            if not repo_id or not filename:
                raise ValueError(
                    f"Unknown model '{model_id}'. "
                    "Provide --repo and --filename or use a popular model."
                )
        
        output_path = self.models_dir / filename
        
        # Check if already downloaded
        cache_key = f"{repo_id}/{filename}"
        if output_path.exists() and cache_key in self.cache:
            print(f"✅ Model already downloaded: {output_path}")
            print(f"   To re-download, delete the file and run again.")
            return output_path
        
        print(f"\n📥 Downloading model:")
        print(f"   Repository: {repo_id}")
        print(f"   File: {filename}")
        print(f"   Destination: {output_path}\n")
        
        try:
            # Download with progress bar
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=self.models_dir,
                local_dir_use_symlinks=False,
                resume_download=resume,
            )
            
            # Verify download
            if Path(downloaded_path).exists():
                file_size = Path(downloaded_path).stat().st_size / (1024**3)
                print(f"\n✅ Download complete: {file_size:.2f} GB")
                
                # Update cache
                self.cache[cache_key] = {
                    "path": str(downloaded_path),
                    "size_gb": file_size,
                    "quantization": quantization
                }
                self._save_cache()
                
                return Path(downloaded_path)
            else:
                raise FileNotFoundError(f"Download failed: {downloaded_path}")
                
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            raise
    
    def list_available_files(self, repo_id: str):
        """List all GGUF files in a repository"""
        print(f"\n📋 Available files in {repo_id}:\n")
        try:
            files = list_repo_files(repo_id)
            gguf_files = [f for f in files if f.endswith('.gguf')]
            
            if not gguf_files:
                print("   No GGUF files found in this repository")
                return
            
            for file in sorted(gguf_files):
                print(f"   - {file}")
                
        except Exception as e:
            print(f"❌ Error listing files: {e}")
    
    def list_downloaded(self):
        """List all downloaded models"""
        gguf_files = list(self.models_dir.glob("*.gguf"))
        
        if not gguf_files:
            print("\n📁 No models downloaded yet")
            return
        
        print(f"\n📁 Downloaded models in {self.models_dir}:\n")
        for file in sorted(gguf_files):
            size_gb = file.stat().st_size / (1024**3)
            print(f"   {file.name:50} ({size_gb:.2f} GB)")


def main():
    parser = argparse.ArgumentParser(
        description="Download GGUF models for Obsidian AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List popular models
  python model_downloader.py list
  
  # Download Llama 2 7B with Q4 quantization (recommended)
  python model_downloader.py download llama-2-7b --quant Q4_K_M
  
  # Download Phi-2 (fast, CPU-friendly)
  python model_downloader.py download phi-2
  
  # Download from custom repo
  python model_downloader.py download custom --repo TheBloke/CodeLlama-7B-GGUF --filename codellama-7b.Q4_K_M.gguf
  
  # List downloaded models
  python model_downloader.py downloaded
        """
    )
    
    parser.add_argument(
        "command",
        choices=["list", "download", "downloaded", "list-repo"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "model",
        nargs="?",
        help="Model ID (e.g., llama-2-7b, phi-2, mistral-7b)"
    )
    
    parser.add_argument(
        "--quant", "--quantization",
        default="Q4_K_M",
        help="Quantization level (default: Q4_K_M)"
    )
    
    parser.add_argument(
        "--repo",
        help="HuggingFace repository ID (e.g., TheBloke/Llama-2-7B-GGUF)"
    )
    
    parser.add_argument(
        "--filename",
        help="Specific filename to download"
    )
    
    parser.add_argument(
        "--models-dir",
        default="./models",
        help="Models directory (default: ./models)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't resume interrupted downloads"
    )
    
    args = parser.parse_args()
    
    downloader = ModelDownloader(Path(args.models_dir))
    
    if args.command == "list":
        downloader.list_popular_models()
        
    elif args.command == "downloaded":
        downloader.list_downloaded()
        
    elif args.command == "list-repo":
        if not args.repo:
            print("❌ --repo required for list-repo command")
            sys.exit(1)
        downloader.list_available_files(args.repo)
        
    elif args.command == "download":
        if not args.model:
            print("❌ Model ID required for download command")
            print("   Use 'list' command to see available models")
            sys.exit(1)
            
        try:
            path = downloader.download_model(
                model_id=args.model,
                quantization=args.quant,
                repo_id=args.repo,
                filename=args.filename,
                resume=not args.no_resume
            )
            
            print(f"\n✅ Model ready to use:")
            print(f"   Path: {path}")
            print(f"\n💡 Update your config.yaml with:")
            print(f'   path: "{path}"')
            
        except Exception as e:
            print(f"\n❌ Failed to download model: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
