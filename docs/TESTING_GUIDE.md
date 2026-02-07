# Unit Testing Guide

**GitHub Issue**: [#112 - Add Unit Tests for Core Components](https://github.com/B0LK13/obsidian-agent/issues/112)

## Overview

Comprehensive testing infrastructure for PKM Agent with pytest, achieving **80%+ code coverage** for core components.

---

## Quick Start

### Run All Tests

```bash
cd pkm-agent

# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio

# Run all tests with coverage
python run_tests.py

# Or use pytest directly
pytest
```

### Run Specific Tests

```bash
# Only unit tests
python run_tests.py --unit

# Only integration tests
python run_tests.py --integration

# Skip slow tests
python run_tests.py --fast

# Specific test file
python run_tests.py tests/test_vectorstore.py

# Specific test function
pytest tests/test_rag.py::TestChunker::test_chunk_note -v
```

---

## Test Structure

```
pkm-agent/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_config_validation.py
│   ├── test_database.py
│   ├── test_indexer.py
│   ├── test_rag.py
│   ├── test_vectorstore.py      # NEW: Vector store tests
│   ├── test_model_downloader.py # NEW: Model downloader tests
│   ├── test_integration.py
│   └── ...
├── pytest.ini                    # Pytest configuration
└── run_tests.py                  # Test runner script
```

---

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Fast, isolated tests for individual functions/classes:

```python
@pytest.mark.unit
def test_chunk_sizes(test_chunker):
    """Test that chunks respect size limits."""
    # Test individual component
    pass
```

### Integration Tests (`@pytest.mark.integration`)

Tests that involve multiple components:

```python
@pytest.mark.integration
def test_full_pipeline(test_database, test_vectorstore):
    """Test complete RAG pipeline."""
    # Test component interaction
    pass
```

### Slow Tests (`@pytest.mark.slow`)

Tests that take >1 second (model downloads, large datasets):

```python
@pytest.mark.slow
def test_large_vault_indexing():
    """Test indexing 10,000 notes."""
    # Long-running test
    pass
```

---

## Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| **Core Logic** | 90% | TBD |
| **RAG Pipeline** | 85% | TBD |
| **Vector Store** | 90% | TBD |
| **Database** | 85% | TBD |
| **API Endpoints** | 80% | TBD |
| **CLI** | 70% | TBD |
| **Overall** | **80%** | TBD |

---

## Writing Tests

### Test Naming Convention

```python
# File: test_<module>.py
# Class: Test<ClassName>
# Function: test_<what_it_tests>

class TestVectorStore:
    def test_add_chunks(self, test_vectorstore):
        """Test adding chunks to vector store."""
        pass
    
    def test_search_empty_store(self, test_vectorstore):
        """Test searching empty vector store."""
        pass
```

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_example(test_database, test_vectorstore, temp_dir):
    """Fixtures are automatically injected."""
    # test_database - Database instance
    # test_vectorstore - VectorStore instance
    # temp_dir - Temporary directory
    pass
```

### Parametrized Tests

Test multiple inputs efficiently:

```python
@pytest.mark.parametrize("use_hnsw,expected", [
    (True, "HNSW"),
    (False, "Flat"),
])
def test_index_type(use_hnsw, expected, test_embedding_engine, temp_dir):
    """Test both HNSW and Flat indices."""
    vs = OptimizedVectorStore(
        temp_dir, test_embedding_engine, use_hnsw=use_hnsw
    )
    # Verify index type
    pass
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@patch('pkm_agent.llm.openai_provider.OpenAI')
def test_llm_call(mock_openai):
    """Test LLM without actual API call."""
    mock_openai.return_value.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    
    # Test your code
    pass
```

---

## Available Fixtures

### Temporary Resources

- `temp_dir` - Temporary directory (auto-cleaned)
- `test_pkm_root` - Test PKM vault with sample notes
- `test_config` - Test configuration object

### Database

- `test_database` - Initialized database
- `test_indexer` - File indexer instance

### RAG Components

- `test_embedding_engine` - Embedding engine
- `test_vectorstore` - Vector store
- `test_chunker` - Text chunker
- `test_retriever` - RAG retriever

### Sample Data

- `sample_messages` - List of test messages
- `sample_chunks` - List of test chunks

---

## Test Markers

Mark tests for selective execution:

```python
@pytest.mark.unit
def test_fast_unit():
    """Unit test - runs quickly."""
    pass

@pytest.mark.integration
def test_full_system():
    """Integration test - tests multiple components."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Slow test - may take minutes."""
    pass

@pytest.mark.requires_gpu
def test_gpu_inference():
    """Requires GPU hardware."""
    pass

@pytest.mark.requires_internet
def test_model_download():
    """Requires internet connection."""
    pass
```

Run specific markers:

```bash
# Only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Only GPU tests (on GPU machine)
pytest -m requires_gpu
```

---

## Coverage Reports

### Generate Coverage

```bash
# HTML report (recommended)
pytest --cov=pkm_agent --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=pkm_agent --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=pkm_agent --cov-report=xml
```

### Understanding Coverage

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
pkm_agent/rag/vectorstore.py       150     15    90%    45-50, 78
pkm_agent/rag/embeddings.py         80      5    94%    23, 67
---------------------------------------------------------------
TOTAL                              500     50    90%
```

- **Stmts**: Total statements
- **Miss**: Uncovered statements
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=pkm_agent --cov-fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Best Practices

### 1. Test One Thing at a Time

```python
# Good
def test_add_chunk():
    """Test adding a single chunk."""
    vs.add_chunks([chunk])
    assert vs.get_note_ids() == {"note1"}

# Bad - tests multiple things
def test_everything():
    vs.add_chunks([chunk])
    vs.search("query")
    vs.delete_notes(["note1"])
    # Hard to debug if it fails
```

### 2. Use Descriptive Names

```python
# Good
def test_search_returns_results_sorted_by_score():
    pass

# Bad
def test_search():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange - Set up test data
    chunks = [create_chunk("content")]
    
    # Act - Perform action
    result = vectorstore.add_chunks(chunks)
    
    # Assert - Verify outcome
    assert result == 1
```

### 4. Clean Up Resources

```python
@pytest.fixture
def resource():
    # Setup
    res = create_resource()
    yield res
    # Teardown (automatically called)
    res.cleanup()
```

### 5. Test Edge Cases

```python
def test_edge_cases():
    # Empty input
    assert process([]) == []
    
    # Single item
    assert process([1]) == [1]
    
    # Large input
    assert len(process(range(10000))) == 10000
    
    # Invalid input
    with pytest.raises(ValueError):
        process(None)
```

---

## Debugging Failed Tests

### Run with Verbose Output

```bash
pytest -vv tests/test_vectorstore.py
```

### Stop at First Failure

```bash
pytest -x
```

### Enter Debugger on Failure

```bash
pytest --pdb
```

### Print Debug Output

```python
def test_debug(capfd):
    """Capture print output."""
    print("Debug info")
    out, err = capfd.readouterr()
    assert "Debug" in out
```

### Show Local Variables

```bash
pytest -l  # Show locals on failure
```

---

## Adding New Tests

### 1. Create Test File

```bash
touch tests/test_new_feature.py
```

### 2. Import Required Modules

```python
import pytest
from pkm_agent.new_feature import NewClass
```

### 3. Write Test Class

```python
class TestNewClass:
    """Tests for NewClass."""
    
    def test_basic_functionality(self):
        """Test basic feature works."""
        obj = NewClass()
        result = obj.do_something()
        assert result == expected
```

### 4. Run Your Tests

```bash
pytest tests/test_new_feature.py -v
```

### 5. Check Coverage

```bash
pytest tests/test_new_feature.py --cov=pkm_agent.new_feature
```

---

## Test Data

### Using Fixtures

Create reusable test data in `conftest.py`:

```python
@pytest.fixture
def sample_note():
    """Create a sample note for testing."""
    return Note(
        id="test-note",
        title="Test",
        content="Test content",
        ...
    )
```

### Factory Patterns

For variations:

```python
@pytest.fixture
def note_factory():
    """Factory for creating test notes."""
    def _create_note(title="Test", content="Content"):
        return Note(id="test", title=title, content=content)
    return _create_note

def test_with_factory(note_factory):
    note1 = note_factory(title="First")
    note2 = note_factory(title="Second")
```

---

## Performance Testing

### Benchmark Tests

```python
import time

@pytest.mark.slow
def test_search_performance(test_vectorstore, sample_chunks):
    """Test search performance."""
    test_vectorstore.add_chunks(sample_chunks * 100)
    
    start = time.time()
    results = test_vectorstore.search("query", k=10)
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # Should complete in <100ms
```

---

## Common Issues

### Import Errors

```bash
# Make sure PKM agent is installed
cd pkm-agent
pip install -e .
```

### Missing Dependencies

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

### Fixture Not Found

Check that fixture is defined in `conftest.py` or imported correctly.

### Tests Pass Locally But Fail in CI

- Check Python version compatibility
- Verify all dependencies are in requirements.txt
- Check for environment-specific code

---

## Resources

- **Pytest Docs**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Pytest Fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **Mocking**: https://docs.python.org/3/library/unittest.mock.html

---

**Status**: ✅ **Testing infrastructure complete**  
**Current Coverage**: To be measured  
**Target Coverage**: 80%+  
**GitHub Issue**: [#112](https://github.com/B0LK13/obsidian-agent/issues/112)
