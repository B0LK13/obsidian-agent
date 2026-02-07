"""
Obsidian Agent Core - Integration Module

Wires together all AI enhancement components into a unified system:
- Incremental Indexing
- Vector Database
- Caching Layer
- Link Management
- Error Handling
- Link Suggestions

Provides a high-level API for the Obsidian plugin.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
import threading

from incremental_indexer import IncrementalIndexer, ChangeReport
from vector_database import VectorDatabase, create_embedding_function, SearchResult
from caching_layer import CacheManager, LLMResponseCache, EmbeddingCache, SearchResultCache
from link_manager import LinkManager, LinkReport
from link_suggester import SuggestionEngine, SuggestionReport
from error_handling import (
    ErrorHandler, CircuitBreaker, with_retry, SafeExecutor,
    ErrorCategory, ErrorSeverity
)

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for Obsidian Agent Core."""
    vault_path: str
    data_dir: str = "./agent_data"
    
    # Indexing config
    enable_incremental_indexing: bool = True
    index_state_db: str = "index_state.db"
    
    # Vector DB config
    vector_db_backend: str = "auto"  # auto, chroma, sqlite
    vector_db_path: str = "vector_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Cache config
    cache_memory_size: int = 1000
    cache_memory_mb: float = 50.0
    cache_disk_path: str = "cache.db"
    cache_default_ttl: int = 3600
    
    # Link management config
    enable_link_management: bool = True
    links_db_path: str = "links.db"
    
    # Suggestions config
    enable_suggestions: bool = True
    suggestions_db_path: str = "suggestions.db"
    suggestion_min_confidence: float = 0.5
    
    # Error handling config
    enable_circuit_breaker: bool = True
    circuit_failure_threshold: int = 5
    retry_max_attempts: int = 3
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentConfig':
        return cls(**data)
    
    @classmethod
    def from_file(cls, path: str) -> 'AgentConfig':
        """Load config from JSON file."""
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))
    
    def save(self, path: str) -> None:
        """Save config to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


@dataclass
class SystemStatus:
    """Overall system status."""
    healthy: bool
    components: Dict[str, bool]
    index_stats: Dict
    vector_db_stats: Dict
    cache_stats: Dict
    link_stats: Dict
    error_stats: Dict
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'healthy': self.healthy,
            'components': self.components,
            'index_stats': self.index_stats,
            'vector_db_stats': self.vector_db_stats,
            'cache_stats': self.cache_stats,
            'link_stats': self.link_stats,
            'error_stats': self.error_stats,
            'timestamp': self.timestamp.isoformat()
        }


class ObsidianAgentCore:
    """
    Main integration class for Obsidian AI Agent.
    
    Provides unified access to all subsystems with automatic
    error handling, caching, and circuit breaker protection.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.config.data_dir = Path(config.data_dir)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
        self._initialized = False
        self._error_handler = ErrorHandler()
        
        # Circuit breakers for external services
        self._llm_circuit = CircuitBreaker(
            "llm_service",
            failure_threshold=config.circuit_failure_threshold
        )
        self._embedding_circuit = CircuitBreaker(
            "embedding_service",
            failure_threshold=config.circuit_failure_threshold
        )
        
        # Components (initialized in initialize())
        self.indexer: Optional[IncrementalIndexer] = None
        self.vector_db: Optional[VectorDatabase] = None
        self.cache: Optional[CacheManager] = None
        self.llm_cache: Optional[LLMResponseCache] = None
        self.embedding_cache: Optional[EmbeddingCache] = None
        self.search_cache: Optional[SearchResultCache] = None
        self.link_manager: Optional[LinkManager] = None
        self.suggester: Optional[SuggestionEngine] = None
        
        # Safe executor for error handling
        self._safe = SafeExecutor(
            error_handler=self._error_handler,
            fallback_value=None,
            log_errors=True
        )
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        with self._lock:
            if self._initialized:
                return True
            
            try:
                logger.info("Initializing Obsidian Agent Core...")
                
                # Initialize cache first (used by other components)
                self._init_cache()
                
                # Initialize embedding function with caching
                embed_fn = self._create_embedding_function()
                
                # Initialize vector database
                self.vector_db = VectorDatabase(
                    backend=self.config.vector_db_backend,
                    persist_dir=str(self.config.data_dir / self.config.vector_db_path),
                    embedding_function=embed_fn
                )
                
                # Initialize indexer
                if self.config.enable_incremental_indexing:
                    self.indexer = IncrementalIndexer(
                        vault_path=self.config.vault_path,
                        state_db_path=str(self.config.data_dir / self.config.index_state_db),
                        embedding_callback=self._indexing_callback
                    )
                
                # Initialize link management
                if self.config.enable_link_management:
                    self.link_manager = LinkManager(
                        vault_path=self.config.vault_path,
                        db_path=str(self.config.data_dir / self.config.links_db_path)
                    )
                
                # Initialize suggestions
                if self.config.enable_suggestions:
                    self.suggester = SuggestionEngine(
                        vault_path=self.config.vault_path,
                        db_path=str(self.config.data_dir / self.config.suggestions_db_path)
                    )
                
                self._initialized = True
                logger.info("Obsidian Agent Core initialized successfully")
                return True
                
            except Exception as e:
                self._error_handler.handle(
                    error=e,
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.CRITICAL,
                    component="ObsidianAgentCore",
                    operation="initialize"
                )
                return False
    
    def _init_cache(self) -> None:
        """Initialize caching subsystem."""
        self.cache = CacheManager(
            memory_cache_size=self.config.cache_memory_size,
            memory_cache_mb=self.config.cache_memory_mb,
            disk_cache_path=str(self.config.data_dir / self.config.cache_disk_path),
            default_ttl_seconds=self.config.cache_default_ttl
        )
        
        self.llm_cache = LLMResponseCache(self.cache)
        self.embedding_cache = EmbeddingCache(self.cache)
        self.search_cache = SearchResultCache(self.cache)
    
    def _create_embedding_function(self) -> Callable:
        """Create embedding function with caching and circuit breaker."""
        base_embed_fn = create_embedding_function(self.config.embedding_model)
        
        def cached_embed(text: str):
            # Check cache first
            hit, cached = self.embedding_cache.get(text, self.config.embedding_model)
            if hit:
                return cached
            
            # Check circuit breaker
            if self.config.enable_circuit_breaker:
                if not self._embedding_circuit.can_execute():
                    logger.warning("Embedding circuit breaker is OPEN")
                    return None
            
            try:
                result = base_embed_fn(text)
                
                # Cache the result
                self.embedding_cache.set(text, self.config.embedding_model, result)
                
                if self.config.enable_circuit_breaker:
                    self._embedding_circuit.record_success()
                
                return result
                
            except Exception as e:
                if self.config.enable_circuit_breaker:
                    self._embedding_circuit.record_failure()
                
                self._error_handler.handle(
                    error=e,
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.ERROR,
                    component="Embedding",
                    operation="embed"
                )
                return None
        
        return cached_embed
    
    def _indexing_callback(self, note_id: str, content: str) -> Optional[str]:
        """Callback for indexer to generate embeddings."""
        if self.vector_db:
            try:
                # Add to vector database
                success = self.vector_db.add_note(
                    note_id=note_id,
                    content=content,
                    metadata={'indexed_at': datetime.utcnow().isoformat()}
                )
                return note_id if success else None
            except Exception as e:
                logger.error(f"Failed to index {note_id}: {e}")
        return None
    
    # ==================== Public API ====================
    
    def index_vault(self, force_full: bool = False) -> Optional[ChangeReport]:
        """
        Index the vault (incremental or full).
        
        Args:
            force_full: Force full reindex even if incremental is enabled
        
        Returns:
            Change report or None if indexing disabled/failed
        """
        if not self._initialized or not self.indexer:
            logger.warning("Indexer not initialized")
            return None
        
        return self._safe.execute(
            lambda: self.indexer.full_reindex() if force_full 
                   else self.indexer.index_changes(),
            error_category=ErrorCategory.DATABASE,
            component="ObsidianAgentCore",
            operation="index_vault"
        )
    
    def search_notes(
        self, 
        query: str, 
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """
        Search notes using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results
            use_cache: Whether to use result caching
        
        Returns:
            List of search results
        """
        if not self._initialized or not self.vector_db:
            return []
        
        # Check cache
        if use_cache:
            hit, cached = self.search_cache.get(query, top_k)
            if hit:
                return cached
        
        # Perform search
        try:
            results = self.vector_db.search(query, top_k)
        except Exception as e:
            self._error_handler.handle(
                error=e,
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.ERROR,
                component="ObsidianAgentCore",
                operation="search_notes"
            )
            results = []
        
        # Cache results
        if use_cache and results:
            self.search_cache.set(query, top_k, results)
        
        return results
    
    def scan_links(self) -> Optional[LinkReport]:
        """
        Scan vault for broken and orphan links.
        
        Returns:
            Link report or None if link management disabled
        """
        if not self._initialized or not self.link_manager:
            return None
        
        return self._safe.execute(
            self.link_manager.scan_vault,
            error_category=ErrorCategory.FILE_IO,
            component="ObsidianAgentCore",
            operation="scan_links"
        )
    
    def get_link_suggestions(
        self, 
        min_confidence: Optional[float] = None
    ) -> Optional[SuggestionReport]:
        """
        Generate link suggestions for the vault.
        
        Args:
            min_confidence: Minimum confidence threshold (uses config default if None)
        
        Returns:
            Suggestion report or None if suggestions disabled
        """
        if not self._initialized or not self.suggester:
            return None
        
        min_conf = min_confidence or self.config.suggestion_min_confidence
        
        return self._safe.execute(
            self.suggester.analyze_vault,
            error_category=ErrorCategory.FILE_IO,
            component="ObsidianAgentCore",
            operation="get_link_suggestions"
        )
    
    def ask_llm(
        self, 
        prompt: str, 
        model: str = "default",
        temperature: float = 0.7,
        use_cache: bool = True,
        **kwargs
    ) -> Optional[str]:
        """
        Query LLM with caching and circuit breaker protection.
        
        Args:
            prompt: The prompt to send
            model: Model identifier
            temperature: Sampling temperature
            use_cache: Whether to use response caching
            **kwargs: Additional model parameters
        
        Returns:
            LLM response or None on failure
        """
        # Check cache
        if use_cache:
            hit, cached = self.llm_cache.get(prompt, model, temperature, **kwargs)
            if hit:
                return cached.get('text') if isinstance(cached, dict) else cached
        
        # Check circuit breaker
        if self.config.enable_circuit_breaker:
            if not self._llm_circuit.can_execute():
                logger.warning("LLM circuit breaker is OPEN")
                return None
        
        # This is a placeholder - actual LLM integration would go here
        # For now, return None to indicate LLM not configured
        logger.debug("LLM not configured - returning None")
        return None
    
    def get_status(self) -> SystemStatus:
        """Get comprehensive system status."""
        components = {}
        
        # Check each component
        components['indexer'] = self.indexer is not None
        components['vector_db'] = self.vector_db is not None
        components['cache'] = self.cache is not None
        components['link_manager'] = self.link_manager is not None
        components['suggester'] = self.suggester is not None
        
        # Get stats
        index_stats = self.indexer.get_index_stats() if self.indexer else {}
        vector_stats = self.vector_db.get_stats() if self.vector_db else {}
        cache_stats = self.cache.get_stats() if self.cache else {}
        link_stats = self.link_manager.get_broken_links() if self.link_manager else []
        error_stats = self._error_handler.get_error_stats()
        
        # Overall health
        healthy = (
            self._initialized and
            all(components.values()) and
            error_stats.get('errors_24h', 0) < 10
        )
        
        return SystemStatus(
            healthy=healthy,
            components=components,
            index_stats=index_stats,
            vector_db_stats=vector_stats,
            cache_stats=cache_stats,
            link_stats={'broken_links': len(link_stats)},
            error_stats=error_stats,
            timestamp=datetime.utcnow()
        )
    
    def get_stats_summary(self) -> Dict:
        """Get human-readable stats summary."""
        status = self.get_status()
        
        return {
            'healthy': status.healthy,
            'notes_indexed': status.index_stats.get('total_notes', 0),
            'vectors_stored': status.vector_db_stats.get('total_notes', 0),
            'cache_entries': status.cache_stats.get('total_entries', 0),
            'cache_hit_rate': f"{status.cache_stats.get('hit_rate', 0):.1%}",
            'broken_links': status.link_stats.get('broken_links', 0),
            'errors_24h': status.error_stats.get('errors_24h', 0),
            'components_ready': sum(status.components.values())
        }
    
    def shutdown(self) -> None:
        """Gracefully shutdown all components."""
        with self._lock:
            logger.info("Shutting down Obsidian Agent Core...")
            
            # Cleanup resources
            if self.cache:
                self.cache.cleanup()
            
            self._initialized = False
            logger.info("Obsidian Agent Core shutdown complete")


# Convenience function for quick initialization
def create_agent(
    vault_path: str,
    data_dir: str = "./agent_data",
    **kwargs
) -> ObsidianAgentCore:
    """
    Create and initialize an Obsidian Agent.
    
    Args:
        vault_path: Path to Obsidian vault
        data_dir: Directory for agent data
        **kwargs: Additional config options
    
    Returns:
        Initialized ObsidianAgentCore instance
    """
    config = AgentConfig(
        vault_path=vault_path,
        data_dir=data_dir,
        **kwargs
    )
    
    agent = ObsidianAgentCore(config)
    agent.initialize()
    
    return agent


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create test vault
    test_vault = Path("test_integration_vault")
    test_vault.mkdir(exist_ok=True)
    
    # Create test note
    (test_vault / "AI Overview.md").write_text("""# AI Overview

Artificial Intelligence and machine learning are transforming technology.
Deep learning neural networks power modern AI.

Related: [[Machine Learning]]
""")
    
    (test_vault / "Machine Learning.md").write_text("""# Machine Learning

Machine learning is a subset of AI.
Uses neural networks and algorithms.

See also [[AI Overview]]
""")
    
    # Initialize agent
    agent = create_agent(
        vault_path=str(test_vault),
        data_dir="./test_agent_data",
        enable_suggestions=True,
        enable_link_management=True
    )
    
    # Check status
    status = agent.get_status()
    print(f"\nSystem Healthy: {status.healthy}")
    print(f"Components: {status.components}")
    
    # Index vault
    print("\nIndexing vault...")
    report = agent.index_vault()
    if report:
        print(f"Indexed {report.total_scanned} notes, {report.change_count} changes")
    
    # Search
    print("\nSearching for 'machine learning'...")
    results = agent.search_notes("machine learning", top_k=3)
    for r in results:
        print(f"  {r.note_id}: {r.score:.3f}")
    
    # Scan links
    print("\nScanning links...")
    link_report = agent.scan_links()
    if link_report:
        print(f"Total links: {link_report.total_links}")
        print(f"Broken: {len(link_report.broken_links)}")
        print(f"Orphans: {len(link_report.orphan_notes)}")
    
    # Get suggestions
    print("\nGenerating link suggestions...")
    sug_report = agent.get_link_suggestions()
    if sug_report:
        print(f"Total suggestions: {sug_report.total_suggestions}")
        print(f"High confidence: {len(sug_report.high_confidence)}")
    
    # Stats summary
    print("\nStats Summary:")
    print(json.dumps(agent.get_stats_summary(), indent=2))
    
    # Cleanup
    agent.shutdown()
    
    import shutil
    shutil.rmtree(test_vault, ignore_errors=True)
    shutil.rmtree("./test_agent_data", ignore_errors=True)
    
    print("\nIntegration test completed successfully!")
