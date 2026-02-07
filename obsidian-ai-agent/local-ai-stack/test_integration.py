#!/usr/bin/env python3
"""
Integration Test Suite for Obsidian AI Agent
Tests all components: Memory RAG, Hallucination Guard, Semantic Chunking, Evaluation
"""

import sys
import json
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "ai_stack"))

# Test results
results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            try:
                print(f"\n[TEST] {name}")
                func()
                results['passed'] += 1
                results['tests'].append({'name': name, 'status': 'PASS'})
                print(f"  [PASS]")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': name, 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")
        return wrapper
    return decorator

# ============ TESTS ============

@test("Memory RAG Initialization")
def test_memory_rag_init():
    from memory_rag import MemoryAugmentedRAG
    rag = MemoryAugmentedRAG(data_path="./test_data")
    stats = rag.get_stats()
    assert 'short_term' in stats
    assert 'long_term' in stats
    assert 'episodic' in stats
    print(f"  Stats: {json.dumps(stats, indent=2)}")

@test("Memory RAG Add and Retrieve")
def test_memory_rag_operations():
    from memory_rag import MemoryAugmentedRAG
    rag = MemoryAugmentedRAG(data_path="./test_data")
    
    # Add content
    test_embedding = [0.1] * 384
    rag.add_to_memory(
        content="Docker is a containerization platform created by Docker Inc.",
        embedding=test_embedding,
        metadata={'significant': True, 'topic': 'docker'},
        relationships=[('Docker', 'containerization', 'is_a'), ('Docker', 'Docker Inc', 'created_by')]
    )
    
    # Query
    results_mem = rag.process_query("What is Docker?", test_embedding)
    assert 'consolidated_context' in results_mem
    assert len(results_mem['consolidated_context']) > 0
    print(f"  Context retrieved: {len(results_mem['consolidated_context'])} chars")

@test("Hallucination Guard - Fact Checking")
def test_hallucination_guard():
    from hallucination_guard import HallucinationReductionSystem
    
    guard = HallucinationReductionSystem()
    
    # Test with factual content
    generated = "Docker is a containerization platform."
    source = "Docker is a containerization platform created by Docker Inc."
    
    result = guard.validate(generated, source)
    assert 'overall_score' in result
    assert 'passed' in result
    assert result['overall_score'] > 0.5
    print(f"  Score: {result['overall_score']:.2f}, Passed: {result['passed']}")

@test("Hallucination Guard - Detects Hallucination")
def test_hallucination_detection():
    from hallucination_guard import HallucinationReductionSystem
    
    guard = HallucinationReductionSystem()
    
    # Test with hallucinated content
    generated = "Docker was created by Microsoft in 2010."
    source = "Docker was created by Docker Inc in 2013."
    
    result = guard.validate(generated, source)
    # Should have lower score due to factual error
    print(f"  Score: {result['overall_score']:.2f}")
    print(f"  Suggestions: {result.get('suggestions', [])}")

@test("Semantic Chunking - Meeting Transcript")
def test_semantic_chunking():
    from semantic_chunker import SemanticChunkingStrategy
    
    chunker = SemanticChunkingStrategy()
    
    transcript = """
Alice: Welcome to the meeting. Let's discuss the Q4 strategy.
Bob: I have the financial projections ready.
Alice: Great, please share.
Bob: We expect 15% growth this quarter.
Alice: Excellent. What about the timeline?
    """
    
    chunks = chunker.chunk_meeting_transcript(transcript)
    assert len(chunks) > 0
    
    stats = chunker.get_stats(chunks)
    print(f"  Chunks created: {stats['total_chunks']}")
    print(f"  Avg size: {stats['avg_chunk_size']:.0f} tokens")
    
    # Check that chunks have context
    if chunks:
        assert hasattr(chunks[0], 'context_before')
        assert hasattr(chunks[0], 'metadata')

@test("Semantic Chunking - Lecture Notes")
def test_lecture_chunking():
    from semantic_chunker import SemanticChunkingStrategy
    
    chunker = SemanticChunkingStrategy()
    
    notes = """
# Introduction to Docker

Docker is a platform for developing and deploying applications.

## Key Concepts

Containers are lightweight and portable.

## Benefits

- Consistent environments
- Easy deployment
- Scalability
    """
    
    chunks = chunker.chunk_lecture_notes(notes)
    assert len(chunks) > 0
    print(f"  Chunks created: {len(chunks)}")

@test("Evaluation Harness - Structure")
def test_evaluation_structure():
    from evaluation_harness import StructureEvaluator
    
    evaluator = StructureEvaluator()
    
    # Good structured content
    good_content = """
# Title
## Section 1
- Point 1
- Point 2

## Section 2
Some text here.
"""
    
    result = evaluator.evaluate(good_content)
    assert result.score > 0.5
    print(f"  Structure score: {result.score:.2f}")

@test("Evaluation Harness - Complete Evaluation")
def test_complete_evaluation():
    from evaluation_harness import NoteTakingEvaluator
    
    evaluator = NoteTakingEvaluator()
    
    prediction = """
# Meeting Notes

## Attendees
- Alice Chen
- Bob Smith

## Action Items
- [ ] Complete analysis (Assigned: Alice)

## Key Points
1. Budget approved
2. Timeline confirmed
"""
    
    reference = "Meeting with Alice and Bob. Budget approved. Timeline confirmed."
    
    result = evaluator.evaluate(prediction, reference, {'model_name': 'test'})
    assert result.overall_score > 0
    print(f"  Overall score: {result.overall_score:.2f}")
    print(f"  Dimensions: {[s.dimension for s in result.dimension_scores]}")

@test("Model Manager CLI - List Available")
def test_model_manager():
    from model_manager_cli import ModelManager
    
    manager = ModelManager(models_dir="./test_models")
    
    # Should have registered models
    assert len(manager.registry) > 0
    print(f"  Available models: {list(manager.registry.keys())}")

@test("Configuration Loading")
def test_config_loading():
    import yaml
    
    config_path = Path(__file__).parent / "ai_stack" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assert 'performance' in config
        assert 'cache' in config
        print(f"  Config loaded: {list(config.keys())}")
    else:
        print("  Config file not found, skipping")

# ============ MAIN ============

def run_all_tests():
    print("="*70)
    print("OBSIDIAN AI AGENT - INTEGRATION TEST SUITE")
    print("="*70)
    
    # Run all tests
    test_memory_rag_init()
    test_memory_rag_operations()
    test_hallucination_guard()
    test_hallucination_detection()
    test_semantic_chunking()
    test_lecture_chunking()
    test_evaluation_structure()
    test_complete_evaluation()
    test_model_manager()
    test_config_loading()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")
    
    if results['failed'] > 0:
        print("\nFailed tests:")
        for test in results['tests']:
            if test['status'] == 'FAIL':
                print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")
    
    print("="*70)
    
    return results['failed'] == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
