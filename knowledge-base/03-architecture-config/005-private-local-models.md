# Private Local Model Setup - Ollama Integration

## Overview
Configured Agent Zero to use local Ollama models for full privacy, keeping all AI processing local without external API calls.

## Why Local Models?

- **Privacy:** No data leaves your system
- **Cost:** No API charges
- **Speed:** No network latency
- **Offline:** Works without internet
- **Control:** Full model and version control

## Ollama Container Status

### Container Information
- **Name:** agent-zero-ollama
- **Image:** ollama/ollama:latest
- **Port:** 11434
- **Status:** Running

### Network
```bash
docker exec agent-zero-ollama ollama list
```

## Models Installed

### 1. llama3.2
```bash
docker exec agent-zero-ollama ollama pull llama3.2
```

**Purpose:** Main chat model for Agent Zero

### 2. nomic-embed-text
```bash
docker exec agent-zero-ollama ollama pull nomic-embed-text
```

**Purpose:** Embedding model for semantic search and RAG

## Configuration

### Environment Variables
```env
PRIMARY_MODEL_PROVIDER=ollama
MODEL_NAME=llama3.2
OLLAMA_ENABLED=true
OLLAMA_HOST=http://ollama:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_STREAM=true
```

### Model Selection
To use local model exclusively:

1. **In Agent Zero UI:**
   - Settings → Model Configuration
   - Set provider to "Ollama"
   - Set model to "llama3.2"

2. **In .env file:**
   ```env
   MODEL_NAME=llama3.2
   MODEL_PROVIDER=ollama
   OLLAMA_HOST=http://ollama:11434
   ```

## Testing Local Model

### Manual Test
```bash
# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello, how are you?"
}'
```

### Test in Agent Zero
```bash
# Send message through Agent Zero UI
# Should use local Ollama if configured correctly
curl -X POST http://localhost:50001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "model": "ollama/llama3.2"
  }'
```

## Performance Considerations

### Hardware Requirements
- **CPU:** 8+ cores recommended
- **RAM:** 8GB minimum, 16GB recommended
- **Model Size:** llama3.2 is ~4GB
- **GPU:** Optional but recommended for speed

### Performance Metrics (CPU-only)
- **Token Generation:** ~5-10 tokens/sec
- **First Token:** <1 second
- **Memory Usage:** ~6GB for llama3.2

### GPU Acceleration (Optional)
To enable GPU:
```bash
# Set Ollama environment variable
docker exec agent-zero-ollama bash -c 'echo OLLAMA_VULKAN=1 >> /etc/environment'
```

## Monitoring

### Logs
```bash
docker logs agent-zero-ollama --tail 50
```

### Status Check
```bash
docker exec agent-zero-ollama ollama list
curl -s http://localhost:11434/api/tags | python -m json.tool
```

## Troubleshooting

### Issue: Local model not selected
**Solution:** Ensure `MODEL_PROVIDER=ollama` is set in `.env`

### Issue: Models not available
**Solution:**
```bash
docker exec agent-zero-ollama ollama pull llama3.2
docker exec agent-zero-ollama ollama pull nomic-embed-text
```

### Issue: Slow response
**Solutions:**
1. Enable GPU (if available)
2. Use smaller models (llama2 instead of llama3.2)
3. Increase system RAM
4. Close other resource-intensive processes

### Issue: Model returns errors
**Solution:** Check model installation:
```bash
docker exec agent-zero-ollama ollama list
```

## Available Models

### Recommended for Agent Zero

| Model | Size | Speed | Context | Best For |
|-------|------|------|---------|----------|
| llama3.2 | 4GB | Fast | 128k | General purpose |
| llama2 | 2GB | Fast | 4k | Simple tasks |
| mistral | 4GB | Fast | 32k | Better than llama2 |
| codellama | 4GB | Fast | 16k | Coding tasks |
| nomic-embed-text | 200MB | Very fast | - | Embeddings |

### Pull Additional Models
```bash
docker exec agent-zero-ollama ollama pull mistral
docker exec agent-zero-ollama ollama pull codellama
```

## Privacy Benefits

1. **No Data Exfiltration**
   - All processing happens locally
   - No logs sent to external servers

2. **Full Control**
   - Know exactly what models you run
   - Can update/replace models anytime

3. **Offline Capability**
   - Works without internet connection
   - No dependency on external services

4. **Cost Savings**
   - No per-token or per-call charges
   - Run as much as you want

## Integration with Agent Zero

### Seamless Switching
Agent Zero can:
- Switch between local (Ollama) and cloud (OpenAI/OpenRouter) models
- Use local for sensitive data, cloud for speed
- Fallback to local models if cloud API fails

### Configuration
```env
# Primary: Local
PRIMARY_PROVIDER=ollama
MODEL_NAME=llama3.2

# Fallback: Cloud
FALLBACK_PROVIDER=openai
FALLBACK_MODEL=gpt-4o
```

## Future Enhancements

1. **Model Fine-tuning** - Customize models with your data
2. **Model Quantization** - Reduce model size for faster inference
3. **Multi-GPU Support** - Use multiple GPUs for faster processing
4. **Dynamic Model Selection** - Automatically select best model for task

## Files Modified

- `/a0/.env` - Added Ollama provider settings
- Docker pulls completed for models

## Status

✅ Ollama container running  
✅ Models installed (llama3.2, nomic-embed-text)  
✅ Configuration in place  
✅ Testing required (to confirm local model works in Agent Zero)