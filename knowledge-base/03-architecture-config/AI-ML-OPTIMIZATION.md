# 🚀 AI/ML Development Optimization Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Performance Optimization](#performance-optimization)
3. [AI/ML Stack Setup](#aiml-stack-setup)
4. [Development Workflow](#development-workflow)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **CPU:** 4 cores, 2.5 GHz+
- **RAM:** 8 GB (16 GB recommended)
- **Storage:** 50 GB free space (SSD recommended)
- **OS:** Windows 10/11, macOS, or Linux
- **Python:** 3.10 or higher

### Recommended for AI/ML
- **CPU:** 8+ cores (Intel i7/i9 or AMD Ryzen 7/9)
- **RAM:** 16-32 GB
- **GPU:** NVIDIA GPU with 8+ GB VRAM (for CUDA acceleration)
- **Storage:** 100+ GB SSD
- **Internet:** Stable connection for API calls

---

## Performance Optimization

### 1. Hardware Optimization

#### CPU Optimization
```cmd
REM Set environment variables for optimal CPU usage
setx OMP_NUM_THREADS 4
setx MKL_NUM_THREADS 4
setx NUMEXPR_NUM_THREADS 4
setx TORCH_NUM_THREADS 4
```

#### Memory Optimization
- Close unnecessary applications
- Use virtual environment to isolate dependencies
- Implement efficient caching strategies
- Use memory-mapped files for large datasets

#### Disk Optimization
- Use SSD for project files and databases
- Enable TRIM for SSDs
- Regular cleanup of temporary files
- Consider disabling hibernation (if 16GB+ RAM)

### 2. Software Optimization

#### Python Configuration
```python
# In your code, optimize NumPy/SciPy operations
import os
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'

# Use efficient data types
import numpy as np
data = np.array(data, dtype=np.float32)  # Use float32 instead of float64
```

#### PyTorch Optimization
```python
import torch

# Enable cuDNN auto-tuner (if using GPU)
torch.backends.cudnn.benchmark = True

# Use mixed precision training
torch.set_float32_matmul_precision('high')

# Optimize for CPU if no GPU
torch.set_num_threads(4)
```

#### Vector Database Optimization
```python
# ChromaDB optimization
import chromadb

client = chromadb.PersistentClient(
    path="./data/vector_db",
    settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Use batching for bulk operations
collection.add(
    documents=documents,
    ids=ids,
    metadatas=metadatas,
    embeddings=embeddings
)
```

### 3. Code Optimization

#### Efficient Indexing
```python
# Incremental indexing (from PROJECT-TODO.md P1)
class IncrementalIndexer:
    def __init__(self):
        self.change_tracker = {}
        
    def track_changes(self, file_path):
        """Track file modifications using hash comparison"""
        import hashlib
        
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        if self.change_tracker.get(file_path) != file_hash:
            self.change_tracker[file_path] = file_hash
            return True  # File changed
        return False  # No change
    
    def update_index(self, changed_files):
        """Update only changed files"""
        for file_path in changed_files:
            if self.track_changes(file_path):
                self._index_file(file_path)
```

#### Caching Strategy
```python
# Implement caching (from PROJECT-TODO.md P2)
from functools import lru_cache
import pickle

class CacheManager:
    def __init__(self, cache_size=1000):
        self.cache_size = cache_size
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def get_embedding(self, text):
        """Cache embeddings to avoid recomputation"""
        return self.model.encode(text)
    
    def save_cache(self, filepath):
        """Persist cache to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def load_cache(self, filepath):
        """Load cache from disk"""
        with open(filepath, 'rb') as f:
            self.cache = pickle.load(f)
```

#### Async Operations
```python
# Asynchronous processing (from PROJECT-TODO.md P2)
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_notes_async(notes):
    """Process notes asynchronously"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, process_note, note)
            for note in notes
        ]
        results = await asyncio.gather(*tasks)
    return results
```

---

## AI/ML Stack Setup

### Core Stack

#### 1. Vector Embeddings
```python
# sentence-transformers for embeddings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, efficient
# OR for better quality:
# model = SentenceTransformer('all-mpnet-base-v2')

embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
```

#### 2. Vector Database
```python
# ChromaDB for vector storage
import chromadb

client = chromadb.PersistentClient(path="./data/vector_db")
collection = client.create_collection(
    name="notes",
    metadata={"hnsw:space": "cosine"}
)

# Add documents with embeddings
collection.add(
    documents=texts,
    embeddings=embeddings,
    ids=ids,
    metadatas=metadatas
)

# Query
results = collection.query(
    query_embeddings=query_embedding,
    n_results=5
)
```

#### 3. LLM Integration
```python
# OpenAI for advanced tasks
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You are a PKM assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=1000
)

# Anthropic Claude for alternative
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": prompt}]
)
```

### Performance Benchmarking

```python
import time
import numpy as np

class PerformanceBenchmark:
    """Benchmark AI/ML operations against targets"""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_indexing(self, indexer, notes):
        """Target: 1000 notes in <10s"""
        start = time.time()
        indexer.index_batch(notes)
        elapsed = time.time() - start
        
        notes_per_sec = len(notes) / elapsed
        self.results['indexing'] = {
            'elapsed': elapsed,
            'notes_per_sec': notes_per_sec,
            'target_met': elapsed < 10 if len(notes) == 1000 else 'N/A'
        }
        return self.results['indexing']
    
    def benchmark_search(self, search_engine, queries):
        """Target: <2s response time"""
        times = []
        for query in queries:
            start = time.time()
            search_engine.search(query)
            times.append(time.time() - start)
        
        avg_time = np.mean(times)
        self.results['search'] = {
            'avg_response_time': avg_time,
            'max_response_time': np.max(times),
            'target_met': avg_time < 2
        }
        return self.results['search']
    
    def benchmark_embeddings(self, model, texts):
        """Target: 1000 texts in <60s"""
        start = time.time()
        embeddings = model.encode(texts, batch_size=32)
        elapsed = time.time() - start
        
        self.results['embeddings'] = {
            'elapsed': elapsed,
            'texts_per_sec': len(texts) / elapsed,
            'target_met': elapsed < 60 if len(texts) == 1000 else 'N/A'
        }
        return self.results['embeddings']
    
    def print_report(self):
        """Print benchmark report"""
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK REPORT")
        print("="*60)
        
        for component, metrics in self.results.items():
            print(f"\n{component.upper()}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value}")
```

---

## Development Workflow

### Daily Workflow

```bash
# 1. Activate virtual environment
venv\Scripts\activate.bat

# 2. Pull latest changes
git pull

# 3. Start development server (in one terminal)
python src\main.py

# 4. Start Jupyter (in another terminal)
jupyter notebook

# 5. Run tests before committing
pytest tests/ -v --cov=src

# 6. Format code
black src/ tests/

# 7. Lint code
pylint src/

# 8. Commit with issue reference
git commit -m "feat: implement vector search (#2)"
```

### Testing Strategy

```python
# tests/test_vector_search.py
import pytest
from src.search.vector_search import VectorSearch

class TestVectorSearch:
    def test_search_performance(self):
        """Ensure search meets performance target (<2s)"""
        searcher = VectorSearch()
        
        import time
        start = time.time()
        results = searcher.search("machine learning", top_k=5)
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Search took {elapsed}s, target is <2s"
        assert len(results) <= 5
    
    def test_search_relevance(self):
        """Ensure relevance score >= 0.8"""
        searcher = VectorSearch()
        results = searcher.search("AI and neural networks")
        
        for result in results:
            assert result['score'] >= 0.8, "Relevance score below target"
```

---

## Best Practices

### 1. Error Handling (from PROJECT-TODO.md P2)

```python
class RobustIndexer:
    """Defensive coding with comprehensive error handling"""
    
    def index_file(self, file_path):
        """Index file with robust error handling"""
        # Input validation
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file path")
        
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None
        
        try:
            # Permission check
            if not os.access(file_path, os.R_OK):
                logging.error(f"Permission denied: {file_path}")
                return None
            
            # File integrity check
            file_hash = self._compute_hash(file_path)
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Boundary check
            if len(content) > self.max_file_size:
                logging.warning(f"File too large: {file_path}")
                content = content[:self.max_file_size]
            
            return self._process_content(content)
            
        except UnicodeDecodeError:
            logging.error(f"Encoding error: {file_path}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error indexing {file_path}: {e}")
            return None
```

### 2. API Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    """Rate limit API calls"""
    
    def __init__(self, max_calls=60, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove old calls
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            # Check rate limit
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.time_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Make call
            self.calls.append(time.time())
            return func(*args, **kwargs)
        
        return wrapper

@RateLimiter(max_calls=60, time_window=60)
def call_openai_api(prompt):
    """Rate-limited OpenAI API call"""
    # API call implementation
    pass
```

### 3. Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure comprehensive logging"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler (rotating)
    fh = RotatingFileHandler(
        'logs/pkm_agent.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger
```

---

## Troubleshooting

### Common Issues

#### 1. Out of Memory
```python
# Solution 1: Process in batches
def process_in_batches(items, batch_size=100):
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        yield process_batch(batch)

# Solution 2: Use generators
def read_large_file(file_path):
    with open(file_path) as f:
        for line in f:
            yield line.strip()

# Solution 3: Clear cache periodically
import gc
gc.collect()
```

#### 2. Slow Performance
```python
# Profile code to find bottlenecks
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
process_notes()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

#### 3. API Timeouts
```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_retry_session():
    """Create session with retry logic"""
    session = requests.Session()
    
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session
```

---

## Quick Reference

### Performance Targets (from PROJECT-TODO.md)
- **Indexing:** 1000 notes in <10s
- **Search:** Response <2s
- **Embeddings:** 1000 notes in <60s
- **Cache hit rate:** >80%

### Useful Commands
```bash
# Check system resources
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().percent}%')"

# Monitor GPU (if NVIDIA)
nvidia-smi -l 1

# Profile Python code
python -m cProfile -s cumulative src/main.py

# Memory profiling
python -m memory_profiler src/main.py

# Benchmark
python -m pytest tests/benchmarks/ -v --benchmark-only
```

### Environment Variables
```bash
# CPU optimization
OMP_NUM_THREADS=4
MKL_NUM_THREADS=4
NUMEXPR_NUM_THREADS=4
TORCH_NUM_THREADS=4

# Python optimization
PYTHONUNBUFFERED=1
PYTHONHASHSEED=0

# GPU (if available)
CUDA_VISIBLE_DEVICES=0
```

---

## Additional Resources

- [PROJECT-TODO.md](PROJECT-TODO.md) - Complete task list
- [DEV-GUIDE.md](DEV-GUIDE.md) - Development workflow
- [PyTorch Performance Tuning](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

---

**Ready to optimize! Run `optimize-system.ps1` to diagnose your system and apply optimizations.**
