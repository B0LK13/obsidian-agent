#!/usr/bin/env python3
"""
Advanced RAG System with Multi-Hop Retrieval
Features:
- Query rewriting and expansion
- Multi-hop retrieval (follow relationships)
- Re-ranking with cross-encoders
- Hybrid search (dense + sparse/BM25)
- Result fusion and deduplication
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('advanced_rag')


@dataclass
class RetrievedDocument:
    """A retrieved document with metadata"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0
    retrieval_method: str = "unknown"
    hop: int = 0  # Which retrieval hop this came from
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content[:500],  # Truncate for display
            'metadata': self.metadata,
            'score': self.score,
            'method': self.retrieval_method,
            'hop': self.hop
        }


class QueryRewriter:
    """
    Rewrite queries for better retrieval
    - Expands abbreviations
    - Adds synonyms
    - Breaks down complex queries
    - Generates sub-questions
    """
    
    def __init__(self):
        self.expansion_patterns = {
            r'\bAI\b': ['artificial intelligence', 'machine learning', 'deep learning'],
            r'\bML\b': ['machine learning', 'statistical learning'],
            r'\bDL\b': ['deep learning', 'neural networks'],
            r'\bNLP\b': ['natural language processing', 'text processing'],
            r'\bCV\b': ['computer vision', 'image processing'],
            r'\bDB\b': ['database', 'data storage'],
            r'\bAPI\b': ['application programming interface', 'web service'],
        }
    
    def rewrite(self, query: str) -> List[str]:
        """Generate multiple rewritten versions of the query"""
        variations = [query]
        
        # 1. Original query
        variations.append(query)
        
        # 2. Expanded abbreviations
        expanded = self._expand_abbreviations(query)
        if expanded != query:
            variations.append(expanded)
        
        # 3. Keyword extraction
        keywords = self._extract_keywords(query)
        if keywords:
            variations.append(" ".join(keywords))
        
        # 4. Question transformation
        if not query.endswith('?'):
            variations.append(f"What is {query}?")
            variations.append(f"Explain {query}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for v in variations:
            v_lower = v.lower().strip()
            if v_lower not in seen:
                seen.add(v_lower)
                unique.append(v)
        
        return unique[:5]  # Max 5 variations
    
    def generate_sub_questions(self, query: str) -> List[str]:
        """Break complex queries into sub-questions"""
        sub_questions = []
        
        # Pattern: "Compare X and Y"
        compare_match = re.search(r'compare\s+(\w+)\s+(?:and|vs\.?)\s+(\w+)', query, re.IGNORECASE)
        if compare_match:
            x, y = compare_match.groups()
            sub_questions.extend([
                f"What is {x}?",
                f"What is {y}?",
                f"What are the differences between {x} and {y}?",
                f"When to use {x}?",
                f"When to use {y}?"
            ])
        
        # Pattern: "How to X"
        howto_match = re.search(r'how\s+(?:to|do)\s+(.+)', query, re.IGNORECASE)
        if howto_match:
            action = howto_match.group(1)
            sub_questions.extend([
                f"What is needed to {action}?",
                f"What are the steps to {action}?",
                f"Common problems when trying to {action}"
            ])
        
        # Pattern: "What is X in Y context"
        context_match = re.search(r'what\s+is\s+(.+?)\s+(?:in|for)\s+(.+)', query, re.IGNORECASE)
        if context_match:
            concept, context = context_match.groups()
            sub_questions.extend([
                f"What is {concept}?",
                f"How does {concept} apply to {context}?",
                f"Examples of {concept} in {context}"
            ])
        
        return sub_questions if sub_questions else [query]
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations"""
        result = text
        for pattern, expansions in self.expansion_patterns.items():
            if re.search(pattern, text):
                # Add expansion in parentheses
                expansion = expansions[0]
                result = re.sub(pattern, f'\\g<0> ({expansion})', result, count=1)
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords"""
        # Simple keyword extraction (could use NLP library)
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        # Filter common stop words
        stop_words = {'what', 'when', 'where', 'which', 'how', 'does', 'this', 'that', 'with', 'from', 'have', 'been'}
        return [w for w in words if w.lower() not in stop_words][:10]


class HybridRetriever:
    """
    Hybrid retrieval combining dense and sparse methods
    - Dense: Vector similarity
    - Sparse: BM25/TF-IDF
    """
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.bm25_index = {}
        self.doc_freqs = defaultdict(int)
        self.total_docs = 0
        self.avg_doc_length = 0
        self.k1 = 1.5  # BM25 parameter
        self.b = 0.75  # BM25 parameter
    
    def index_document(self, doc_id: str, content: str, metadata: Dict):
        """Add document to BM25 index"""
        # Tokenize
        tokens = self._tokenize(content)
        
        # Store term frequencies
        term_freqs = defaultdict(int)
        for token in tokens:
            term_freqs[token] += 1
            self.doc_freqs[token] += 1
        
        self.bm25_index[doc_id] = {
            'tokens': tokens,
            'term_freqs': dict(term_freqs),
            'length': len(tokens),
            'content': content,
            'metadata': metadata
        }
        
        # Update stats
        self.total_docs += 1
        self.avg_doc_length = (
            (self.avg_doc_length * (self.total_docs - 1) + len(tokens)) / self.total_docs
        )
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[RetrievedDocument]:
        """BM25 sparse retrieval"""
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)
        
        for doc_id, doc_data in self.bm25_index.items():
            score = 0.0
            doc_length = doc_data['length']
            
            for term in query_tokens:
                if term not in doc_data['term_freqs']:
                    continue
                
                # BM25 formula
                tf = doc_data['term_freqs'][term]
                df = self.doc_freqs[term]
                idf = max(0.1, log((self.total_docs - df + 0.5) / (df + 0.5)))
                
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                score += idf * (numerator / denominator)
            
            if score > 0:
                scores[doc_id] = score
        
        # Return top-k
        top_docs = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])
        
        results = []
        for doc_id, score in top_docs:
            doc_data = self.bm25_index[doc_id]
            results.append(RetrievedDocument(
                id=doc_id,
                content=doc_data['content'],
                metadata=doc_data['metadata'],
                score=score,
                retrieval_method="bm25"
            ))
        
        return results
    
    def hybrid_search(self, query: str, query_embedding: List[float], 
                      top_k: int = 10, alpha: float = 0.7) -> List[RetrievedDocument]:
        """
        Combine dense and sparse retrieval
        alpha: weight for dense scores (1-alpha for sparse)
        """
        # Get results from both methods
        dense_results = []
        if self.vector_store and query_embedding:
            # Assume vector_store has a query method
            dense_results = self.vector_store.query(query_embedding, n_results=top_k*2)
        
        sparse_results = self.bm25_search(query, top_k=top_k*2)
        
        # Normalize scores
        all_scores = {}
        
        # Dense scores
        if dense_results:
            dense_max = max(r['score'] for r in dense_results) if isinstance(dense_results[0], dict) else 1.0
            for r in dense_results:
                if isinstance(r, dict):
                    doc_id = r['id']
                    score = (r['score'] / dense_max) * alpha
                else:
                    doc_id = r.id
                    score = (r.score / dense_max) * alpha
                all_scores[doc_id] = all_scores.get(doc_id, 0) + score
        
        # Sparse scores
        if sparse_results:
            sparse_max = max(r.score for r in sparse_results) if sparse_results else 1.0
            for r in sparse_results:
                score = (r.score / sparse_max) * (1 - alpha)
                all_scores[r.id] = all_scores.get(r.id, 0) + score
        
        # Re-rank by combined score
        sorted_docs = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Build final results
        results = []
        for doc_id, score in sorted_docs:
            if doc_id in self.bm25_index:
                doc_data = self.bm25_index[doc_id]
                results.append(RetrievedDocument(
                    id=doc_id,
                    content=doc_data['content'],
                    metadata=doc_data['metadata'],
                    score=score,
                    retrieval_method="hybrid"
                ))
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Simple stemming (could use Porter Stemmer)
        # Remove common suffixes
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ness']
        stemmed = []
        for token in tokens:
            for suffix in suffixes:
                if token.endswith(suffix) and len(token) > len(suffix) + 2:
                    token = token[:-len(suffix)]
                    break
            stemmed.append(token)
        
        return stemmed


def log(x):
    """Safe log function"""
    import math
    return math.log(x) if x > 0 else 0


class MultiHopRetriever:
    """
    Multi-hop retrieval that follows relationships between documents
    Useful for complex questions requiring multiple pieces of information
    """
    
    def __init__(self, base_retriever: HybridRetriever, max_hops: int = 2):
        self.base_retriever = base_retriever
        self.max_hops = max_hops
        self.relationship_graph = defaultdict(list)  # doc_id -> [(related_doc_id, relation_type, strength)]
    
    def add_relationship(self, doc_id: str, related_doc_id: str, 
                         relation_type: str = "related", strength: float = 1.0):
        """Add a relationship between documents"""
        self.relationship_graph[doc_id].append((related_doc_id, relation_type, strength))
    
    def extract_relationships_from_content(self, doc_id: str, content: str):
        """Auto-extract relationships based on content (simplified)"""
        # Look for wiki-style links: [[Note Title]]
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in links:
            # Find doc_id for this link title
            for other_id, doc_data in self.base_retriever.bm25_index.items():
                if link.lower() in doc_data['metadata'].get('title', '').lower():
                    self.add_relationship(doc_id, other_id, "links_to", 0.8)
                    break
    
    def retrieve(self, query: str, query_embedding: Optional[List[float]] = None,
                 top_k_per_hop: int = 5) -> List[RetrievedDocument]:
        """
        Multi-hop retrieval
        Returns documents from multiple hops with hop number annotated
        """
        all_results = []
        visited = set()
        current_query = query
        
        for hop in range(self.max_hops):
            # Retrieve for current query
            if hop == 0:
                results = self.base_retriever.hybrid_search(
                    current_query, query_embedding, top_k=top_k_per_hop
                )
            else:
                # For subsequent hops, use related documents
                results = self._get_related_documents(
                    [r.id for r in all_results if r.hop == hop - 1],
                    top_k=top_k_per_hop
                )
            
            # Add hop annotation
            for r in results:
                if r.id not in visited:
                    r.hop = hop
                    all_results.append(r)
                    visited.add(r.id)
            
            # Generate follow-up query based on what we found
            if hop < self.max_hops - 1 and results:
                current_query = self._generate_followup_query(query, results)
        
        # Re-rank all results
        return self._rerank_results(all_results, query)
    
    def _get_related_documents(self, source_doc_ids: List[str], 
                               top_k: int) -> List[RetrievedDocument]:
        """Get documents related to source documents"""
        related_scores = defaultdict(float)
        
        for doc_id in source_doc_ids:
            for related_id, rel_type, strength in self.relationship_graph[doc_id]:
                related_scores[related_id] += strength
        
        # Get top related documents
        top_related = heapq.nlargest(top_k, related_scores.items(), key=lambda x: x[1])
        
        results = []
        for doc_id, score in top_related:
            if doc_id in self.base_retriever.bm25_index:
                doc_data = self.base_retriever.bm25_index[doc_id]
                results.append(RetrievedDocument(
                    id=doc_id,
                    content=doc_data['content'],
                    metadata=doc_data['metadata'],
                    score=score,
                    retrieval_method=f"related_from_{source_doc_ids[0]}"
                ))
        
        return results
    
    def _generate_followup_query(self, original_query: str, 
                                  current_results: List[RetrievedDocument]) -> str:
        """Generate a follow-up query based on retrieved context"""
        # Extract key entities from results
        entities = set()
        for r in current_results:
            # Simple entity extraction: capitalized phrases
            found = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', r.content)
            entities.update(found)
        
        if entities:
            entity_str = ", ".join(list(entities)[:3])
            return f"{original_query} related to {entity_str}"
        
        return original_query
    
    def _rerank_results(self, results: List[RetrievedDocument], 
                        query: str) -> List[RetrievedDocument]:
        """Re-rank results using additional signals"""
        # Boost based on hop (earlier hops are more relevant)
        for r in results:
            hop_penalty = 0.9 ** r.hop  # Slight penalty for later hops
            r.score *= hop_penalty
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results


class Reranker:
    """
    Re-rank retrieved documents using cross-encoder or other methods
    """
    
    def __init__(self):
        self.cross_encoder = None
        self._try_load_cross_encoder()
    
    def _try_load_cross_encoder(self):
        """Try to load a cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder
            # Use a small, fast model
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-encoder loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not available, using fallback reranking")
        except Exception as e:
            logger.warning(f"Could not load cross-encoder: {e}")
    
    def rerank(self, query: str, documents: List[RetrievedDocument], 
               top_k: int = 5) -> List[RetrievedDocument]:
        """Re-rank documents based on query relevance"""
        if not documents:
            return []
        
        if self.cross_encoder:
            return self._cross_encoder_rerank(query, documents, top_k)
        else:
            return self._fallback_rerank(query, documents, top_k)
    
    def _cross_encoder_rerank(self, query: str, documents: List[RetrievedDocument],
                              top_k: int) -> List[RetrievedDocument]:
        """Use cross-encoder for re-ranking"""
        pairs = [(query, doc.content[:512]) for doc in documents]
        scores = self.cross_encoder.predict(pairs)
        
        # Update scores
        for doc, score in zip(documents, scores):
            doc.score = float(score)
        
        # Sort and return top-k
        documents.sort(key=lambda x: x.score, reverse=True)
        return documents[:top_k]
    
    def _fallback_rerank(self, query: str, documents: List[RetrievedDocument],
                         top_k: int) -> List[RetrievedDocument]:
        """Fallback re-ranking using keyword matching"""
        query_terms = set(query.lower().split())
        
        for doc in documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)
            
            # Boost score based on term overlap
            overlap_boost = overlap / max(len(query_terms), 1)
            doc.score = doc.score * 0.7 + overlap_boost * 0.3
        
        documents.sort(key=lambda x: x.score, reverse=True)
        return documents[:top_k]


class AdvancedRAG:
    """
    Complete Advanced RAG pipeline
    Combines all components: query rewriting, hybrid retrieval, multi-hop, re-ranking
    """
    
    def __init__(self, vector_store=None, data_path: str = "./data"):
        self.data_path = Path(data_path)
        self.query_rewriter = QueryRewriter()
        self.hybrid_retriever = HybridRetriever(vector_store)
        self.multi_hop = MultiHopRetriever(self.hybrid_retriever)
        self.reranker = Reranker()
        
        logger.info("Advanced RAG initialized")
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None):
        """Add a document to the retrieval system"""
        self.hybrid_retriever.index_document(doc_id, content, metadata or {})
        self.multi_hop.extract_relationships_from_content(doc_id, content)
    
    def retrieve(self, query: str, query_embedding: Optional[List[float]] = None,
                 top_k: int = 5, use_multi_hop: bool = True) -> Dict:
        """
        Full retrieval pipeline
        
        Returns:
            {
                'original_query': str,
                'rewritten_queries': List[str],
                'documents': List[RetrievedDocument],
                'total_found': int,
                'retrieval_time_ms': float
            }
        """
        import time
        start_time = time.time()
        
        # 1. Rewrite query
        rewritten = self.query_rewriter.rewrite(query)
        logger.debug(f"Query rewritten to: {rewritten}")
        
        # 2. Retrieve (multi-hop or standard)
        all_results = []
        
        for q in rewritten[:2]:  # Limit to top 2 rewrites
            if use_multi_hop:
                results = self.multi_hop.retrieve(q, query_embedding, top_k_per_hop=top_k)
            else:
                results = self.hybrid_retriever.hybrid_search(q, query_embedding, top_k=top_k)
            
            all_results.extend(results)
        
        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for r in all_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
        
        # 3. Re-rank
        final_results = self.reranker.rerank(query, unique_results, top_k=top_k)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            'original_query': query,
            'rewritten_queries': rewritten,
            'documents': final_results,
            'total_found': len(unique_results),
            'retrieval_time_ms': elapsed_ms
        }
    
    def get_context_for_llm(self, retrieval_result: Dict, max_tokens: int = 2000) -> str:
        """Format retrieved documents as context for LLM"""
        context_parts = []
        total_length = 0
        
        for i, doc in enumerate(retrieval_result['documents']):
            doc_text = f"[Document {i+1}]\n{doc.content}\n\n"
            
            if total_length + len(doc_text) > max_tokens * 4:  # Rough token estimate
                break
            
            context_parts.append(doc_text)
            total_length += len(doc_text)
        
        return "\n".join(context_parts)


# Example usage
if __name__ == '__main__':
    # Demo
    rag = AdvancedRAG()
    
    # Add some test documents
    test_docs = [
        ("doc1", "Python is a high-level programming language known for its readability.", {"topic": "programming"}),
        ("doc2", "Docker containers allow applications to run consistently across environments.", {"topic": "devops"}),
        ("doc3", "Machine learning is a subset of AI that enables systems to learn from data.", {"topic": "ai"}),
        ("doc4", "Kubernetes orchestrates Docker containers at scale in production environments.", {"topic": "devops"}),
    ]
    
    for doc_id, content, meta in test_docs:
        rag.add_document(doc_id, content, meta)
    
    # Add relationship
    rag.multi_hop.add_relationship("doc2", "doc4", "orchestrates", 0.9)
    
    # Test retrieval
    result = rag.retrieve("How do I deploy containers?", use_multi_hop=True)
    
    print(f"Query: {result['original_query']}")
    print(f"Rewritten: {result['rewritten_queries']}")
    print(f"Retrieved {len(result['documents'])} documents in {result['retrieval_time_ms']:.2f}ms")
    print("\nTop results:")
    for doc in result['documents']:
        print(f"  [{doc.retrieval_method}, hop={doc.hop}] {doc.id}: {doc.content[:60]}... (score: {doc.score:.3f})")
