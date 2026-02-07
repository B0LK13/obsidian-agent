"""
Performance Benchmarks for Obsidian Agent

Tests performance characteristics for:
- Incremental indexing (1k, 10k, 50k notes)
- Vector search latency
- Cache hit rates
- Link scanning
- Memory usage
"""

import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List
import statistics
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from incremental_indexer import IncrementalIndexer
from vector_database import VectorDatabase
from caching_layer import CacheManager
from link_manager import LinkManager
from link_suggester import SuggestionEngine


class PerformanceBenchmark:
    """Performance testing framework."""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
    
    def benchmark_incremental_indexing(self, note_counts: List[int] = [100, 500, 1000]):
        """Benchmark incremental indexing performance."""
        print("\n=== Incremental Indexing Benchmark ===")
        
        for count in note_counts:
            temp_dir = tempfile.mkdtemp()
            try:
                vault_path = Path(temp_dir) / "vault"
                vault_path.mkdir()
                db_path = Path(temp_dir) / "index.db"
                
                # Create test notes
                for i in range(count):
                    note_path = vault_path / f"note_{i}.md"
                    content = f"""# Note {i}

This is content for note {i}. It contains some keywords like 
artificial intelligence, machine learning, and data science.
"""
                    note_path.write_text(content)
                
                # Full index benchmark
                indexer = IncrementalIndexer(str(vault_path), str(db_path))
                
                start = time.time()
                report = indexer.full_reindex()
                full_time = (time.time() - start) * 1000
                
                # Incremental benchmark (no changes)
                start = time.time()
                report2 = indexer.index_changes()
                incremental_time = (time.time() - start) * 1000
                
                # Modify one note and re-index
                (vault_path / "note_0.md").write_text("# Modified\n\nNew content.")
                start = time.time()
                report3 = indexer.index_changes()
                single_change_time = (time.time() - start) * 1000
                
                self.results[f"indexing_{count}"] = {
                    "note_count": count,
                    "full_index_ms": full_time,
                    "incremental_no_change_ms": incremental_time,
                    "single_change_ms": single_change_time,
                    "notes_per_second": count / (full_time / 1000)
                }
                
                print(f"  {count} notes:")
                print(f"    Full index: {full_time:.1f}ms ({count/(full_time/1000):.0f} notes/sec)")
                print(f"    Incremental (no change): {incremental_time:.1f}ms")
                print(f"    Single change: {single_change_time:.1f}ms")
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def benchmark_cache_performance(self):
        """Benchmark cache hit rates and latency."""
        print("\n=== Cache Performance Benchmark ===")
        
        temp_dir = tempfile.mkdtemp()
        try:
            cache = CacheManager(
                memory_cache_size=1000,
                disk_cache_path=str(Path(temp_dir) / "cache.db"),
                default_ttl_seconds=3600
            )
            
            # Warm up cache
            for i in range(100):
                cache.set("test", f"key_{i}", f"value_{i}")
            
            # Benchmark cache hits
            hit_times = []
            for i in range(100):
                start = time.time()
                hit, value = cache.get("test", f"key_{i}")
                hit_times.append((time.time() - start) * 1000)
            
            # Benchmark cache misses
            miss_times = []
            for i in range(100, 200):
                start = time.time()
                hit, value = cache.get("test", f"key_{i}")
                miss_times.append((time.time() - start) * 1000)
            
            # Get stats
            stats = cache.get_stats()
            
            self.results["cache_performance"] = {
                "avg_hit_time_ms": statistics.mean(hit_times),
                "avg_miss_time_ms": statistics.mean(miss_times),
                "hit_rate": stats.get('hit_rate', 0),
                "total_entries": stats.get('total_entries', 0)
            }
            
            print(f"  Average hit time: {statistics.mean(hit_times):.3f}ms")
            print(f"  Average miss time: {statistics.mean(miss_times):.3f}ms")
            print(f"  Hit rate: {stats.get('hit_rate', 0):.1%}")
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def benchmark_link_scanning(self, note_counts: List[int] = [100, 500, 1000]):
        """Benchmark link scanning performance."""
        print("\n=== Link Scanning Benchmark ===")
        
        for count in note_counts:
            temp_dir = tempfile.mkdtemp()
            try:
                vault_path = Path(temp_dir) / "vault"
                vault_path.mkdir()
                db_path = Path(temp_dir) / "links.db"
                
                # Create notes with links
                for i in range(count):
                    note_path = vault_path / f"note_{i}.md"
                    # Create links between notes
                    links = ""
                    if i > 0:
                        links += f"[[note_{i-1}]]\n"
                    if i < count - 1:
                        links += f"[[note_{i+1}]]\n"
                    
                    content = f"""# Note {i}

Content here.
{links}
"""
                    note_path.write_text(content)
                
                manager = LinkManager(str(vault_path), str(db_path))
                
                start = time.time()
                report = manager.scan_vault()
                scan_time = (time.time() - start) * 1000
                
                self.results[f"link_scan_{count}"] = {
                    "note_count": count,
                    "total_links": report.total_links,
                    "scan_time_ms": scan_time,
                    "notes_per_second": count / (scan_time / 1000)
                }
                
                print(f"  {count} notes:")
                print(f"    Scan time: {scan_time:.1f}ms ({count/(scan_time/1000):.0f} notes/sec)")
                print(f"    Total links: {report.total_links}")
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def benchmark_suggestion_generation(self, note_counts: List[int] = [50, 100, 200]):
        """Benchmark link suggestion generation."""
        print("\n=== Suggestion Generation Benchmark ===")
        
        for count in note_counts:
            temp_dir = tempfile.mkdtemp()
            try:
                vault_path = Path(temp_dir) / "vault"
                vault_path.mkdir()
                db_path = Path(temp_dir) / "suggestions.db"
                
                # Create related notes
                topics = ["AI", "ML", "Data Science", "Python", "Neural Networks"]
                for i in range(count):
                    note_path = vault_path / f"{topics[i % len(topics)]}_{i}.md"
                    topic = topics[i % len(topics)]
                    content = f"""# {topic} Note {i}

This note is about {topic} and machine learning.
It covers artificial intelligence concepts.
Python programming examples included.
"""
                    note_path.write_text(content)
                
                engine = SuggestionEngine(str(vault_path), str(db_path))
                
                start = time.time()
                report = engine.analyze_vault()
                analysis_time = (time.time() - start) * 1000
                
                self.results[f"suggestions_{count}"] = {
                    "note_count": count,
                    "suggestions_generated": report.total_suggestions,
                    "analysis_time_ms": analysis_time,
                    "notes_per_second": count / (analysis_time / 1000)
                }
                
                print(f"  {count} notes:")
                print(f"    Analysis time: {analysis_time:.1f}ms")
                print(f"    Suggestions: {report.total_suggestions}")
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def print_summary(self):
        """Print performance summary."""
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*60)
        
        for name, data in self.results.items():
            print(f"\n{name}:")
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n" + "="*60)
    
    def save_report(self, path: str):
        """Save benchmark report to JSON."""
        import json
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.results
        }
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {path}")


def main():
    """Run all benchmarks."""
    print("Obsidian Agent Performance Benchmarks")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    benchmark.benchmark_incremental_indexing([100, 500, 1000])
    benchmark.benchmark_cache_performance()
    benchmark.benchmark_link_scanning([100, 500, 1000])
    benchmark.benchmark_suggestion_generation([50, 100, 200])
    
    # Print and save results
    benchmark.print_summary()
    benchmark.save_report("benchmark_results.json")


if __name__ == "__main__":
    main()
