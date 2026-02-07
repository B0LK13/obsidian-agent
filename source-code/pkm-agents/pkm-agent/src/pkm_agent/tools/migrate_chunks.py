"""Migration script to update existing index with semantic chunking."""

import asyncio
import logging
from pkm_agent.config import load_config
from pkm_agent.data.database import Database
from pkm_agent.rag.embedding_engine import EmbeddingEngine
from pkm_agent.rag.semantic_chunker import SemanticChunker, SemanticChunkerConfig
from pkm_agent.rag.vectorstore import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    """Re-chunk all notes using SemanticChunker."""
    logger.info("Starting migration to semantic chunking...")
    
    config = load_config()
    db = Database(config.db_path)
    
    embedding_engine = EmbeddingEngine(
        model_name=config.rag.embedding_model,
        cache_dir=config.cache_path,
    )
    
    vectorstore = VectorStore(
        config.chroma_path,
        embedding_engine,
    )
    
    chunker = SemanticChunker(SemanticChunkerConfig())
    
    # Get all notes
    notes = db.get_all_notes(limit=100000)
    total = len(notes)
    logger.info(f"Found {total} notes to process")
    
    processed = 0
    total_chunks = 0
    
    for note in notes:
        try:
            # 1. Delete old chunks
            vectorstore.delete_note(note.id)
            
            # 2. Create new chunks
            chunks = chunker.chunk_note(note)
            
            # 3. Add to vectorstore
            if chunks:
                vectorstore.add_chunks(chunks)
                total_chunks += len(chunks)
            
            processed += 1
            if processed % 10 == 0:
                logger.info(f"Processed {processed}/{total} notes ({total_chunks} chunks generated)")
                
        except Exception as e:
            logger.error(f"Failed to process note {note.id} ({note.title}): {e}")

    logger.info("Migration complete!")
    logger.info(f"Total notes processed: {processed}")
    logger.info(f"Total chunks generated: {total_chunks}")

if __name__ == "__main__":
    asyncio.run(migrate())
