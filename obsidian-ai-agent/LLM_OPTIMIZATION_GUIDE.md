# LLM Optimization Guide

Complete guide to optimizing the Local LLM Server for maximum performance.

---

## 🚀 Quick Start (Optimized)

```powershell
# Use the optimized launcher
.\start-optimized.ps1

# With benchmarking
.\start-optimized.ps1 -Benchmark

# Force CPU mode
.\start-optimized.ps1 -CpuOnly
```

---

## 📊 Performance Features

### 1. Model Caching

The optimized server keeps up to **2 models in memory** simultaneously:

```python
# Automatic LRU cache - most recently used models stay loaded
model_manager = ModelManager(max_cache_size=2)
```

**Benefits:**
- Switch between models instantly
- No reload time for frequently used models
- Automatic eviction of old models

### 2. Prompt Caching

Repeated prompts are cached for **100x speedup** on identical queries:

```python
# First call: ~2 seconds
response = llm.chat("What is Docker?")

# Second call: ~0.01 seconds (cached)
response = llm.chat("What is Docker?")  # Instant!
```

Clear cache via admin endpoint:
```bash
curl -X POST http://127.0.0.1:8000/admin/clear-cache
```

### 3. GPU Auto-Detection

Automatically detects and optimizes for your GPU:

```python
# Auto-detect optimal GPU layers
vram = detect_vram()  # e.g., 8192 MB for RTX 3060

if model_size < vram * 0.5:
    gpu_layers = 100  # Full GPU offload
elif model_size < vram:
    gpu_layers = 50   # Partial offload
else:
    gpu_layers = 0    # CPU only
```

### 4. Multi-Threading

Automatic CPU thread optimization:

```python
# Uses (CPU cores - 1) threads by default
n_threads = multiprocessing.cpu_count() - 1
```

---

## 🔧 Configuration Options

Edit `ai_stack/config.yaml`:

```yaml
performance:
  context_size: 4096      # Larger = more memory but longer context
  batch_size: 512         # Larger = faster but more VRAM
  threads: null           # null = auto-detect
  gpu_layers: -1          # -1 = auto-detect, 0 = CPU only
  
generation:
  default_temperature: 0.7
  default_max_tokens: 2048
  top_p: 0.95
  top_k: 40
  repeat_penalty: 1.1

cache:
  model_cache_size: 2     # Number of models to keep loaded
  prompt_cache_size: 100  # Number of prompts to cache
```

---

## 🎯 Model Selection Guide

### Download Models

```powershell
# See recommendations
python ai_stack/model_manager_cli.py recommend

# List available models
python ai_stack/model_manager_cli.py list

# Download a model
python ai_stack/model_manager_cli.py download llama-2-7b-chat --quant Q4_K_M

# Verify download
python ai_stack/model_manager_cli.py verify
```

### Model Comparison

| Model | Size | Quality | Speed | VRAM Needed | Best For |
|-------|------|---------|-------|-------------|----------|
| **Phi-2** | 1.6GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 2GB | Fast experimentation |
| **Llama-2-7B** | 4GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | 4GB | Balanced use |
| **Mistral-7B** | 4.5GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 4GB | High quality |
| **Llama-2-13B** | 8GB | ⭐⭐⭐⭐⭐ | ⭐⭐ | 8GB | Best quality |

### Quantization Guide

| Level | Size | Quality | Use Case |
|-------|------|---------|----------|
| **Q4_K_M** | 100% | 90% | Default - best balance |
| **Q5_K_M** | 125% | 95% | Better quality |
| **Q6_K** | 150% | 97% | Near-lossless |
| **Q8_0** | 200% | 99% | Maximum quality |

**Recommendation:** Start with Q4_K_M, upgrade if you need better quality and have VRAM to spare.

---

## 📈 Benchmarking

### Run Benchmark

```powershell
# Basic benchmark
python ai_stack/benchmark.py

# Save results
python ai_stack/benchmark.py -o results.json
```

### Expected Performance

**CPU-Only (8 cores):**
- Phi-2: 25-35 tokens/sec
- Llama-2-7B: 10-15 tokens/sec
- Llama-2-13B: 5-8 tokens/sec

**GPU (RTX 3060 12GB):**
- Llama-2-7B: 40-60 tokens/sec
- Llama-2-13B: 25-35 tokens/sec

**GPU (RTX 4090 24GB):**
- Llama-2-13B: 80-100 tokens/sec
- Llama-2-70B: 15-20 tokens/sec

### Interpret Results

| Tokens/sec | Rating | UX |
|------------|--------|-----|
| < 5 | 🐌 Slow | Unusable for chat |
| 5-15 | 🐢 Okay | Usable but slow |
| 15-30 | ✓ Good | Comfortable chat |
| 30-60 | ✓✓ Fast | Real-time feel |
| > 60 | 🚀 Excellent | Instant response |

---

## 💡 Optimization Tips

### For Maximum Speed

1. **Use smaller model** (Phi-2 instead of 7B)
2. **Enable GPU** (10x faster than CPU)
3. **Increase batch_size** (if you have VRAM)
4. **Use Q4_K_M quantization** (smaller = faster)

### For Maximum Quality

1. **Use larger model** (13B or 70B)
2. **Use Q6_K or Q8_0 quantization**
3. **Increase context_size** (for longer documents)
4. **Tune temperature/top_p**

### For Low RAM Systems

1. **Use mmap** (memory mapping - uses disk as swap):
   ```yaml
   performance:
     use_mmap: true
   ```

2. **Reduce context_size**:
   ```yaml
   performance:
     context_size: 2048  # Instead of 4096
   ```

3. **Use smaller model** (Phi-2 is 1.6GB vs 4GB for 7B)

### For Multiple Users

1. **Increase workers**:
   ```yaml
   server:
     workers: 4
   ```

2. **Use Waitress** (Windows) or Gunicorn (Linux):
   ```yaml
   server:
     use_waitress: true
   ```

---

## 🔍 Monitoring

### Admin Endpoints

```bash
# Server stats
curl http://127.0.0.1:8000/admin/stats

# Clear prompt cache
curl -X POST http://127.0.0.1:8000/admin/clear-cache

# Health check with model info
curl http://127.0.0.1:8000/health
```

### Log Analysis

Watch for these metrics in logs:

```
Generated 256 tokens in 12.5s (20.5 t/s)  # Good speed
Model loaded in 3.2s                       # Fast load
Using cached model: llama-2-7b            # Cache hit
```

---

## 🛠️ Troubleshooting

### Out of Memory

**Symptoms:** Process killed, "CUDA out of memory", slow swapping

**Solutions:**
1. Reduce `gpu_layers` to offload less to GPU
2. Reduce `batch_size` to 256 or 128
3. Use smaller model
4. Enable `use_mmap: true`

### Slow Performance

**Check:**
```bash
# Is GPU being used?
nvidia-smi  # Should show python process using GPU memory

# Check thread count
curl http://127.0.0.1:8000/admin/stats
```

**Fixes:**
1. Verify GPU layers > 0
2. Check CPU throttling (laptops on battery)
3. Close other applications
4. Use smaller model or Q4 quantization

### Model Loading Slow

**Enable memory mapping:**
```yaml
performance:
  use_mmap: true  # Uses disk as swap, faster loading
  use_mlock: false  # Set to true to prevent swapping (uses more RAM)
```

---

## 🎓 Advanced Configuration

### Custom Generation Parameters

```python
# In your request
{
  "temperature": 0.7,      # Randomness (0.0-2.0)
  "top_p": 0.95,          # Nucleus sampling
  "top_k": 40,            # Top-k sampling
  "repeat_penalty": 1.1,  # Penalize repetition
  "presence_penalty": 0.0, # Penalize new topics
  "frequency_penalty": 0.0 # Penalize frequency
}
```

### Multi-Model Setup

Switch between models without restarting:

```python
# Request specific model
{
  "model": "phi-2.Q4_K_M",
  "messages": [...]
}
```

The server caches multiple models and switches instantly.

---

## 📚 Further Reading

- [llama.cpp Documentation](https://github.com/ggerganov/llama.cpp)
- [GGUF Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [Quantization Guide](https://www.reddit.com/r/LocalLLaMA/wiki/guides/)

---

*Optimized for offline knowledge work* 🔒
