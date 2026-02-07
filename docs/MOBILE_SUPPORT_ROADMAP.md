# Mobile Support - Research & Implementation Roadmap

**GitHub Issue**: [#106 - Mobile Support](https://github.com/B0LK13/obsidian-agent/issues/106)  
**Priority**: Medium 🟡  
**Target Version**: v2.0  
**Status**: 🔬 Research & Planning

---

## Overview

Enable AI-powered PKM features on Obsidian Mobile (iOS & Android) to provide seamless cross-platform experience.

### Current Limitations
- Python backend cannot run natively on mobile
- Obsidian Mobile API has differences from desktop
- Resource constraints (CPU, memory, battery)
- No local model inference on mobile devices

---

## Solution Architectures

### Option A: Remote Server Architecture (Recommended for v2.0)

**Architecture**:
```
Mobile Device              Home Server/Cloud
├─ Obsidian Mobile        ├─ PKM Agent Backend
│  └─ Plugin (TS/JS)      │  └─ Python Services
│                         │     ├─ LLM Server
│                         │     ├─ RAG Pipeline
└─ API Client ────────────┼──> └─ Vector DB
                          │
                          └─ Secure Gateway
```

**Advantages**:
- ✅ Works on all mobile devices
- ✅ Full feature parity with desktop
- ✅ Lower battery consumption
- ✅ Uses existing backend code

**Disadvantages**:
- ❌ Requires internet connection
- ❌ Server setup/hosting costs
- ❌ Network latency
- ❌ Privacy concerns (data leaves device)

**Implementation Complexity**: Medium (6-8 weeks)

---

### Option B: On-Device Inference (Future v3.0)

**Architecture**:
```
Mobile Device
├─ Obsidian Mobile
│  └─ Plugin (TS/JS)
│     ├─ WebAssembly LLM
│     ├─ Mobile Embeddings
│     └─ IndexedDB/SQLite
└─ Native Bindings (optional)
   ├─ CoreML (iOS)
   └─ TensorFlow Lite (Android)
```

**Advantages**:
- ✅ Works offline
- ✅ Complete privacy
- ✅ No server costs
- ✅ Lower latency

**Disadvantages**:
- ❌ Limited to small models (1-3B params)
- ❌ High battery drain
- ❌ Complex implementation
- ❌ Platform-specific code

**Implementation Complexity**: High (12-16 weeks)

---

### Option C: Hybrid Architecture (Best Long-term)

**Architecture**:
```
Mobile Device              Server (Optional)
├─ Lightweight Features   ├─ Heavy Processing
│  ├─ Basic Q&A          │  ├─ Large Models
│  ├─ Search             │  ├─ Fine-tuning
│  └─ Note Linking       │  └─ Batch Processing
└─ Fallback to Server ───┘
```

**Advantages**:
- ✅ Best of both worlds
- ✅ Graceful degradation
- ✅ Adaptive based on connectivity

**Implementation Complexity**: Very High (16-20 weeks)

---

## Recommended Implementation Plan (Option A)

### Phase 1: Server API (4 weeks)

#### Week 1-2: REST API Development
```python
# FastAPI backend
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    vault_id: str

class ChatRequest(BaseModel):
    messages: list
    vault_id: str
    context_enabled: bool = True

@app.post("/api/v1/search")
async def search_notes(request: SearchRequest):
    """Search notes in vault."""
    # Use existing RAG pipeline
    pass

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Chat with AI assistant."""
    # Use existing LLM with RAG
    pass

@app.post("/api/v1/index")
async def trigger_index(vault_id: str):
    """Trigger vault re-indexing."""
    pass
```

**Endpoints to Implement**:
- `POST /api/v1/search` - Semantic search
- `POST /api/v1/chat` - AI chat with context
- `POST /api/v1/index` - Trigger indexing
- `GET /api/v1/notes/{id}` - Get note details
- `POST /api/v1/link-suggestions` - Auto-link suggestions
- `GET /api/v1/health` - Server health check

#### Week 3: Authentication & Security
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    # Implement JWT validation
    pass

@app.post("/api/v1/auth/login")
async def login(username: str, password: str):
    """User login."""
    # Generate JWT
    pass
```

**Security Features**:
- JWT authentication
- API key management
- Rate limiting
- HTTPS enforcement
- CORS configuration

#### Week 4: Mobile Sync Protocol
```python
@app.post("/api/v1/sync")
async def sync_vault(vault_id: str, last_sync: datetime):
    """Sync vault changes since last sync."""
    # Delta sync to reduce bandwidth
    pass
```

---

### Phase 2: Mobile Plugin (6 weeks)

#### Week 5-6: Plugin Foundation (TypeScript)
```typescript
// Mobile plugin for Obsidian
import { Plugin, TFile } from 'obsidian';
import { APIClient } from './api-client';

export default class MobilePKMPlugin extends Plugin {
    private apiClient: APIClient;
    
    async onload() {
        // Initialize API client
        this.apiClient = new APIClient(this.settings);
        
        // Register commands
        this.addCommand({
            id: 'ai-search',
            name: 'AI Search',
            callback: () => this.showSearchModal()
        });
        
        this.addCommand({
            id: 'ai-chat',
            name: 'AI Chat',
            callback: () => this.showChatView()
        });
    }
}
```

#### Week 7-8: Core Features
```typescript
// API Client
export class APIClient {
    private baseURL: string;
    private token: string;
    
    async search(query: string): Promise<SearchResult[]> {
        const response = await fetch(`${this.baseURL}/api/v1/search`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query, vault_id: this.vaultId })
        });
        
        return response.json();
    }
    
    async chat(messages: Message[]): Promise<string> {
        // Implement chat with streaming
        pass
    }
}
```

**Features**:
- AI-powered search
- Chat interface
- Link suggestions
- Settings panel

#### Week 9-10: UI/UX Optimization
```typescript
// Mobile-optimized search modal
export class MobileSearchModal extends Modal {
    async onOpen() {
        const { contentEl } = this;
        
        // Touch-friendly UI
        const searchInput = contentEl.createEl('input', {
            type: 'text',
            placeholder: 'Search with AI...',
            cls: 'mobile-search-input'
        });
        
        // Debounced search
        searchInput.addEventListener('input', 
            debounce(() => this.performSearch(), 300)
        );
    }
    
    async performSearch() {
        const results = await this.apiClient.search(this.query);
        this.renderResults(results);
    }
}
```

**Mobile Optimizations**:
- Touch-friendly controls
- Responsive layouts
- Offline indicator
- Loading states
- Error handling

---

### Phase 3: Server Hosting (2 weeks)

#### Week 11: Docker Deployment
```dockerfile
# Dockerfile for mobile backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose API port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "mobile_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./models:/app/models
      - ./data:/app/data
  
  redis:
    image: redis:alpine
    
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pkm_mobile
```

#### Week 12: Cloud Deployment Options

**Option 1: Self-Hosted (Recommended)**
```bash
# Deploy to home server with Tailscale
# Secure tunnel without port forwarding

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start PKM backend
docker-compose up -d

# Access from mobile via Tailscale IP
# https://100.x.x.x:8000
```

**Option 2: Cloud Hosting**
- AWS Lightsail ($5-10/month)
- DigitalOcean Droplet ($6-12/month)
- Railway/Render free tier

**Option 3: Cloudflare Tunnel**
```bash
# Zero-trust tunnel without public IP
cloudflared tunnel create pkm-mobile
cloudflared tunnel route dns pkm-mobile api.yourdomain.com
cloudflared tunnel run pkm-mobile
```

---

## Technical Specifications

### API Design

#### Authentication Flow
```
1. Mobile app requests login
2. Server validates credentials
3. Server issues JWT (expires in 7 days)
4. Mobile stores token securely (keychain/keystore)
5. All requests include Bearer token
6. Server validates token on each request
```

#### Data Sync Protocol
```
1. Mobile requests sync since last_timestamp
2. Server returns delta (new/modified/deleted notes)
3. Mobile applies changes locally
4. Mobile sends local changes to server
5. Server processes and confirms
```

### Mobile-Specific Optimizations

**Request Batching**:
```typescript
class RequestQueue {
    private queue: Request[] = [];
    
    async add(request: Request) {
        this.queue.push(request);
        
        // Batch requests every 500ms
        if (!this.timer) {
            this.timer = setTimeout(() => this.flush(), 500);
        }
    }
    
    async flush() {
        const batch = this.queue.splice(0);
        await this.apiClient.batch(batch);
    }
}
```

**Caching Strategy**:
```typescript
class CacheManager {
    async get(key: string): Promise<any> {
        // Check IndexedDB first
        const cached = await this.db.get(key);
        
        if (cached && !this.isStale(cached)) {
            return cached.value;
        }
        
        // Fetch from server
        const fresh = await this.apiClient.fetch(key);
        await this.db.set(key, fresh);
        
        return fresh;
    }
}
```

**Offline Support**:
```typescript
class OfflineManager {
    async handleRequest(request: Request): Promise<Response> {
        if (navigator.onLine) {
            return this.onlineHandler(request);
        } else {
            return this.offlineHandler(request);
        }
    }
    
    private async offlineHandler(request: Request) {
        // Queue for later
        await this.queue.add(request);
        
        // Return cached response if available
        return this.cache.get(request.url);
    }
}
```

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **API Response Time** | <200ms | 95th percentile |
| **Search Latency** | <500ms | Including network |
| **Chat Response** | <2s | First token |
| **Sync Time** | <5s | For 100 notes |
| **Battery Impact** | <5% | Per hour of use |
| **Data Usage** | <10MB | Per day avg |

---

## Security Considerations

### Data Encryption
```python
from cryptography.fernet import Fernet

class VaultEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_note(self, content: str) -> bytes:
        """Encrypt note content."""
        return self.cipher.encrypt(content.encode())
    
    def decrypt_note(self, encrypted: bytes) -> str:
        """Decrypt note content."""
        return self.cipher.decrypt(encrypted).decode()
```

### Best Practices
- ✅ End-to-end encryption for notes
- ✅ Secure token storage (keychain)
- ✅ HTTPS only
- ✅ Certificate pinning
- ✅ Rate limiting per user
- ✅ Audit logging

---

## Testing Strategy

### Mobile Testing
```typescript
// Integration tests
describe('Mobile API Client', () => {
    it('should search notes', async () => {
        const results = await apiClient.search('test');
        expect(results.length).toBeGreaterThan(0);
    });
    
    it('should handle offline mode', async () => {
        // Simulate offline
        mockNetworkOffline();
        
        const result = await apiClient.search('test');
        expect(result).toEqual(cachedResults);
    });
});
```

### Performance Testing
```python
# Load testing with locust
from locust import HttpUser, task, between

class MobileUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def search(self):
        self.client.post("/api/v1/search", json={
            "query": "test query",
            "vault_id": "test"
        })
    
    @task(3)  # 3x more frequent
    def sync(self):
        self.client.post("/api/v1/sync", json={
            "vault_id": "test",
            "last_sync": "2024-01-01T00:00:00Z"
        })
```

---

## Cost Analysis

### Self-Hosted (Recommended)
- **Hardware**: $0 (use existing computer)
- **Electricity**: ~$2/month
- **Internet**: $0 (existing)
- **Total**: ~$2/month

### Cloud Hosted
- **Server**: $10/month (basic VPS)
- **Storage**: $5/month (100GB)
- **Bandwidth**: $2/month
- **Total**: ~$17/month

### Hybrid (Best)
- **Self-hosted primary**: $2/month
- **Cloud backup/failover**: $5/month
- **Total**: ~$7/month

---

## Migration Path

### From Desktop-Only to Mobile

**Phase 1**: Server Setup (1 week)
```bash
# Deploy server
docker-compose up -d

# Configure API
# Set up authentication
# Test endpoints
```

**Phase 2**: Plugin Installation (1 day)
```typescript
// Install on mobile
// Configure server URL
// Login with credentials
// Initial sync
```

**Phase 3**: Usage (ongoing)
```
1. Use normally on mobile
2. Changes sync automatically
3. Desktop and mobile stay in sync
```

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Server downtime | High | Local caching, queue requests |
| Network latency | Medium | Optimize payloads, CDN |
| Battery drain | Medium | Request batching, smart sync |
| Data privacy | High | E2E encryption, self-hosting |
| API breaking changes | Low | Versioned API, deprecation |

---

## Success Metrics

### v2.0 Launch Targets
- [ ] 90% feature parity with desktop
- [ ] <500ms average response time
- [ ] <2% error rate
- [ ] Support 1000+ concurrent users
- [ ] 95% user satisfaction

---

## Next Steps

1. **Community Feedback** (2 weeks)
   - Post RFC in GitHub Discussions
   - Gather user requirements
   - Prioritize features

2. **Prototype** (4 weeks)
   - Build minimal API
   - Create proof-of-concept plugin
   - Test with beta users

3. **Full Implementation** (8 weeks)
   - Follow plan above
   - Iterative releases
   - Continuous feedback

4. **Beta Release** (v2.0-beta)
   - Limited rollout
   - Monitor metrics
   - Fix issues

5. **Public Release** (v2.0)
   - Full documentation
   - Video tutorials
   - Community support

---

**Status**: 🔬 Research Complete  
**Next Action**: Community RFC & Prototype  
**Estimated Timeline**: 12-16 weeks to v2.0 beta  
**GitHub Issue**: [#106](https://github.com/B0LK13/obsidian-agent/issues/106)
