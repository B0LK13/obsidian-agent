# Obsidian Agent - Quick Fix Instructions

## Problem
Agent reports "no notes found" when asked for summaries because:
1. Embedding/indexing is disabled by default  
2. Context awareness features are disabled
3. Vault is not indexed on first load

## Quick Fix (5 minutes)

### Step 1: Edit `settings.ts`

Find line ~240 and change:
```typescript
// FROM:
systemPrompt: 'You are a helpful AI assistant integrated into Obsidian...',

// TO:
systemPrompt: 'You are an advanced AI assistant integrated into Obsidian with access to the user\'s complete vault. When asked for summaries or information: (1) Use search_vault to find relevant notes, (2) Use read_note to examine specific notes, (3) Use list_files to explore folders, (4) Always provide comprehensive answers with citations using [[note-path]] format.',
```

Find line ~255 and change ALL to `true`:
```typescript
// FROM:
contextConfig: {
    enableLinkedNotes: false,
    enableBacklinks: false,
    enableTagContext: false,
    enableFolderContext: false,
    maxNotesPerSource: 5,
    maxTokensPerNote: 1000,
    linkDepth: 1,
    excludeFolders: 'templates, .obsidian'
},

// TO:
contextConfig: {
    enableLinkedNotes: true,
    enableBacklinks: true,
    enableTagContext: true,
    enableFolderContext: true,
    maxNotesPerSource: 10,
    maxTokensPerNote: 2000,
    linkDepth: 2,
    excludeFolders: 'templates, .obsidian'
},
```

Find line ~290 and change enabled to `true`:
```typescript
// FROM:
embeddingConfig: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    enabled: false,
    autoRefresh: true
}

// TO:
embeddingConfig: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    enabled: true,
    autoRefresh: true
}
```

### Step 2: Add `size()` method to `src/services/vectorStore.ts`

After the `clear()` method (~line 102), add:
```typescript
size(): number {
    return this.vectors.size;
}
```

### Step 3: Add auto-indexing to `main.ts`

After line 161 (after `this.multiNoteSynthesizer = ...`), add:
```typescript
// Auto-index vault if embeddings are enabled and vector store is empty
if (this.settings.embeddingConfig.enabled) {
    this.app.workspace.onLayoutReady(async () => {
        if (this.vectorStore.size() === 0) {
            new Notice('Obsidian Agent: Starting initial vault indexing...');
            try {
                await this.indexingService.indexVault(false);
                new Notice('Obsidian Agent: Vault indexed successfully! Agent is ready.');
            } catch (error: any) {
                new Notice(`Obsidian Agent: Indexing failed - ${error.message}`);
                console.error('Auto-indexing error:', error);
            }
        }
    });
}
```

### Step 4: Build and Deploy

```bash
npm run build
```

Copy to Obsidian plugins folder:
```powershell
Copy-Item main.js, manifest.json, styles.css "C:\Users\Admin\Documents\B0LK13v2\.obsidian\plugins\obsidian-agent\" -Force
```

### Step 5: Restart Obsidian and Test

1. Restart Obsidian
2. Wait for "Vault indexed successfully" notice
3. Test: Ask agent "How many notes are in my vault?"
4. Should return: "I found 4,097 notes..."

## Alternative: Manual Enable (If Build Fails)

If you can't rebuild, enable in Obsidian settings:
1. Settings → Obsidian Agent
2. Enable "Embedding & Indexing"
3. Enable all "Context Sources"
4. Run command: "Obsidian Agent: Index Vault"
5. Wait for completion

## Verification

After fix, check:
- [ ] Settings show embeddings enabled
- [ ] Context sources all enabled
- [ ] Vector store has 4000+ entries
- [ ] Agent can list notes
- [ ] Agent can summarize topics

See `obsidian-agent-diagnostic-report.md` for complete documentation.
