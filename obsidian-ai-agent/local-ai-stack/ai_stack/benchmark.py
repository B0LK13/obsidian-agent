#!/usr/bin/env python3
"""
LLM Benchmark Tool
Measures performance of different configurations
"""

import time
import json
import statistics
from typing import List, Dict
from dataclasses import dataclass
import requests


@dataclass
class BenchmarkResult:
    config_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_time: float
    tokens_per_second: float
    first_token_time: float
    memory_mb: float


class LLMBenchmark:
    """Benchmark LLM performance"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
    
    def check_health(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_prompt_benchmark(self, prompt: str, max_tokens: int = 256, 
                             iterations: int = 3) -> BenchmarkResult:
        """Benchmark a single prompt"""
        times = []
        tokens_generated = []
        first_token_times = []
        
        for i in range(iterations):
            start_time = time.time()
            first_token_time = None
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "local-llm",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=300
            )
            
            total_time = time.time() - start_time
            times.append(total_time)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                tokens = len(content.split())
                tokens_generated.append(tokens)
            else:
                tokens_generated.append(0)
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        avg_tokens = statistics.mean(tokens_generated)
        tps = avg_tokens / avg_time if avg_time > 0 else 0
        
        # Get model info
        health = requests.get(f"{self.base_url}/health").json()
        model_name = health.get('model', 'unknown')
        
        return BenchmarkResult(
            config_name="default",
            model_name=model_name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=int(avg_tokens),
            total_time=avg_time,
            tokens_per_second=tps,
            first_token_time=statistics.mean(first_token_times) if first_token_times else 0,
            memory_mb=0  # Would need to query system
        )
    
    def run_suite(self) -> List[BenchmarkResult]:
        """Run comprehensive benchmark suite"""
        
        print("=" * 70)
        print("LLM PERFORMANCE BENCHMARK")
        print("=" * 70)
        
        if not self.check_health():
            print("ERROR: LLM server not running!")
            print(f"Start it with: python llm_server_optimized.py")
            return []
        
        # Test prompts of varying complexity
        test_prompts = [
            ("Short question", "What is Docker?"),
            ("Medium explanation", "Explain the concept of containerization and how Docker implements it."),
            ("Long analysis", """Analyze the following text and provide a detailed summary:
                
Containerization has become a fundamental technology in modern software development. 
It allows applications to be packaged with their dependencies into isolated units called containers. 
Unlike virtual machines, containers share the host OS kernel, making them lightweight and efficient.

Docker is the most popular containerization platform, providing tools for building, 
running, and managing containers. It uses a client-server architecture with the Docker daemon
managing container lifecycle operations.

Key benefits include:
- Consistent environments across development and production
- Efficient resource utilization
- Rapid deployment and scaling
- Isolation and security""", 512),
        ]
        
        results = []
        
        for name, prompt in test_prompts:
            print(f"\nBenchmarking: {name}")
            print("-" * 70)
            
            result = self.run_prompt_benchmark(prompt)
            results.append(result)
            
            print(f"  Prompt length: {result.prompt_tokens} tokens")
            print(f"  Generated: {result.completion_tokens} tokens")
            print(f"  Time: {result.total_time:.2f}s")
            print(f"  Speed: {result.tokens_per_second:.1f} tokens/sec")
        
        # Print summary
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        
        avg_tps = statistics.mean([r.tokens_per_second for r in results])
        print(f"Average speed: {avg_tps:.1f} tokens/sec")
        
        if avg_tps < 5:
            print("⚠️  Performance: SLOW - Consider using a smaller model or enabling GPU")
        elif avg_tps < 20:
            print("✓ Performance: ACCEPTABLE - Good for interactive use")
        else:
            print("✓ Performance: FAST - Excellent for real-time applications")
        
        print("=" * 70)
        
        return results
    
    def compare_quantizations(self, model_base: str) -> None:
        """Compare different quantization levels"""
        # This would require multiple model files
        print("\nQuantization comparison requires multiple model files")
        print("Download different Q-levels of the same model to compare")


def main():
    """Run benchmark"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark LLM performance')
    parser.add_argument('--url', default='http://127.0.0.1:8000', help='LLM server URL')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    benchmark = LLMBenchmark(args.url)
    results = benchmark.run_suite()
    
    if args.output and results:
        with open(args.output, 'w') as f:
            json.dump([{
                'config_name': r.config_name,
                'model_name': r.model_name,
                'prompt_tokens': r.prompt_tokens,
                'completion_tokens': r.completion_tokens,
                'total_time': r.total_time,
                'tokens_per_second': r.tokens_per_second
            } for r in results], f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()
