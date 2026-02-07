"""Notes API endpoints."""

import datetime
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from pkm_agent.api.server import get_pkm_app
from pkm_agent.app import PKMAgentApp
from pkm_agent.data.models import Note, NoteMetadata

router = APIRouter()

class NoteResponse(BaseModel):
    id: str
    title: str
    path: str
    content: str
    metadata: dict
    created_at: str
    modified_at: str
    
class NoteUpdate(BaseModel):
    content: str

class NoteCreate(BaseModel):
    title: str
    content: str
    path: str | None = None
    tags: list[str] = []

def _validate_path(path_str: str, root_dir: str | os.PathLike) -> bool:
    """Validate that path is within root_dir."""
    from pathlib import Path
    try:
        root = Path(root_dir).resolve()
        path = (root / path_str).resolve()
        return path.is_relative_to(root)
    except (ValueError, TypeError):
        return False

@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    limit: int = 50,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """List recent notes."""
    notes = app.db.get_all_notes(limit=limit)
    return [note.to_dict() for note in notes]

@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Create a new note."""
    from pathlib import Path
    import hashlib
    
    # Determine path
    if note_in.path:
        # Validate user-provided path
        if not _validate_path(note_in.path, app.config.pkm_root):
            raise HTTPException(status_code=400, detail="Invalid path")
        rel_path = Path(note_in.path)
    else:
        # Auto-generate filename from title
        safe_title = "".join(c for c in note_in.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '-')
        rel_path = Path(f"{safe_title}.md")
        
    full_path = app.config.pkm_root / rel_path
    
    if full_path.exists():
        raise HTTPException(status_code=409, detail="File already exists")
        
    # Ensure parent dir exists
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid directory structure")
    
    # Create content with frontmatter if tags provided
    content = note_in.content
    if note_in.tags:
        tags_str = "\n".join(f"  - {t}" for t in note_in.tags)
        frontmatter = f"---\ntags:\n{tags_str}\n---\n\n"
        content = frontmatter + content
        
    # Write file
    try:
        full_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")
        
    # Index immediately (though watcher will catch it too)
    note = app.indexer.index_file(full_path)
    if not note:
        # Fallback if indexing failed or wasn't instant
        stat = full_path.stat()
        note = Note(
            id=hashlib.md5(str(rel_path).encode()).hexdigest()[:12],
            path=rel_path,
            title=note_in.title,
            content=content,
            metadata=NoteMetadata(title=note_in.title, tags=note_in.tags),
            created_at=datetime.datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.datetime.fromtimestamp(stat.st_mtime)
        )
        
    return note.to_dict()

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Get a note by ID."""
    note = app.db.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()

@router.put("/{note_id}")
async def update_note(
    note_id: str,
    update: NoteUpdate,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Update a note (content only for now)."""
    note = app.db.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update content on disk
    try:
        filepath = app.config.pkm_root / note.path
        
        # Security check: ensure path is still valid inside root
        if not _validate_path(str(note.path), app.config.pkm_root):
             raise HTTPException(status_code=400, detail="Invalid note path")
             
        if not filepath.exists():
             raise HTTPException(status_code=404, detail="File not found on disk")
             
        filepath.write_text(update.content, encoding="utf-8")
        return {"status": "updated", "id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Delete a note."""
    note = app.db.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    try:
        filepath = app.config.pkm_root / note.path
        
        # Security check
        if not _validate_path(str(note.path), app.config.pkm_root):
             raise HTTPException(status_code=400, detail="Invalid note path")
             
        if filepath.exists():
            filepath.unlink()
            
        # Delete from DB and Vector Store
        app.db.delete_note(note_id)
        app.vectorstore.delete_note(note_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")
