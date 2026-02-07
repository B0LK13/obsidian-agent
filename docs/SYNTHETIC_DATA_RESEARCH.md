# Synthetic Data Generation - Research & Implementation Guide

**GitHub Issue**: [#109 - Synthetic Data Generation](https://github.com/B0LK13/obsidian-agent/issues/109)  
**Priority**: Low 🟢  
**Target Version**: v3.0  
**Status**: 🔬 Research & Planning

---

## Overview

Implement **synthetic data generation** to create high-quality training data for fine-tuning models, testing RAG pipelines, and improving AI agent performance.

### Why Synthetic Data?

**Challenges with Real Data**:
- ❌ Privacy concerns (user vaults are private)
- ❌ Limited diversity in single-user vaults
- ❌ Expensive to collect at scale
- ❌ Slow feedback loops for training

**Benefits of Synthetic Data**:
- ✅ Unlimited, diverse training examples
- ✅ Complete control over data distribution
- ✅ No privacy issues
- ✅ Rapid iteration and testing

---

## Use Cases

### 1. Model Fine-tuning Data
```python
# Generate Q&A pairs for model training
synthetic_data = [
    {
        "context": "[[Machine Learning]] is a subset of AI...",
        "question": "What is machine learning?",
        "answer": "Machine learning is a subset of AI that..."
    },
    # ... thousands more
]
```

### 2. RAG Pipeline Testing
```python
# Generate test vaults with known answers
test_vault = generate_vault(
    topics=["Python", "JavaScript", "Rust"],
    num_notes=1000,
    complexity="intermediate"
)

# Test retrieval accuracy
query = "How do I use async/await in Python?"
results = rag_pipeline.search(query, vault=test_vault)
assert "asyncio" in results[0].content
```

### 3. Preference Data for DPO
```python
# Generate preference pairs automatically
preferences = [
    {
        "prompt": "Explain decorators",
        "chosen": "Decorators wrap functions to modify behavior...",
        "rejected": "Decorators are complex Python features..."  # Too vague
    }
]
```

### 4. Stress Testing
```python
# Generate large vaults for performance testing
stress_vault = generate_vault(
    num_notes=100_000,
    avg_note_size=5000,  # chars
    link_density=0.3  # 30% of words are links
)

# Test indexing speed
start = time.time()
vectorstore.index(stress_vault)
duration = time.time() - start
assert duration < 60  # Should index in <60 seconds
```

---

## Technical Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│         Synthetic Data Generation Pipeline          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │  Topic   │───▶│   LLM    │───▶│ Validate │     │
│  │Templates │    │Generator │    │ & Filter │     │
│  └──────────┘    └──────────┘    └──────────┘     │
│       │                │                │          │
│       │                │                │          │
│       ▼                ▼                ▼          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│  │Knowledge │    │Synthetic │    │ Quality  │    │
│  │  Graph   │    │ Vault    │    │  Scores  │    │
│  │ (Schema) │    │  (MD)    │    │          │    │
│  └──────────┘    └──────────┘    └──────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Basic Generation (4 weeks)

#### Week 1-2: Note Generator

```python
# synthetic_generator.py
from typing import List, Dict, Optional
import random
from openai import OpenAI
import re

class SyntheticNoteGenerator:
    """Generate synthetic Obsidian notes."""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key)
        self.topics = self.load_topic_templates()
    
    def load_topic_templates(self) -> Dict[str, Dict]:
        """Load topic templates and schemas."""
        return {
            "programming": {
                "subtopics": ["python", "javascript", "rust", "go"],
                "note_types": ["concept", "tutorial", "reference", "example"],
                "keywords": ["function", "class", "variable", "loop"]
            },
            "machine_learning": {
                "subtopics": ["supervised", "unsupervised", "deep_learning", "nlp"],
                "note_types": ["algorithm", "paper_notes", "implementation"],
                "keywords": ["model", "training", "dataset", "accuracy"]
            },
            "productivity": {
                "subtopics": ["time_management", "note_taking", "workflows"],
                "note_types": ["method", "tips", "review"],
                "keywords": ["efficiency", "focus", "habits", "goals"]
            }
        }
    
    def generate_note(
        self,
        topic: str,
        note_type: str = "concept",
        length: str = "medium",
        link_density: float = 0.2
    ) -> Dict[str, str]:
        """
        Generate a single synthetic note.
        
        Args:
            topic: Main topic (e.g., "programming.python")
            note_type: Type of note (concept, tutorial, etc.)
            length: short (200-500), medium (500-2000), long (2000-5000)
            link_density: Proportion of keywords to convert to [[links]]
        
        Returns:
            {
                'title': '...',
                'content': '...',
                'tags': [...],
                'links': [...]
            }
        """
        # Parse topic
        domain, subtopic = topic.split(".")
        template = self.topics[domain]
        
        # Generate content length target
        length_map = {
            "short": (200, 500),
            "medium": (500, 2000),
            "long": (2000, 5000)
        }
        min_len, max_len = length_map[length]
        target_words = random.randint(min_len // 5, max_len // 5)
        
        # Create prompt
        prompt = self.create_generation_prompt(
            domain=domain,
            subtopic=subtopic,
            note_type=note_type,
            target_words=target_words,
            keywords=template['keywords']
        )
        
        # Generate with LLM
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert note-taker creating educational content."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        
        # Extract title from first line
        lines = content.strip().split('\n')
        title = lines[0].replace('#', '').strip()
        body = '\n'.join(lines[1:]).strip()
        
        # Add wikilinks
        body_with_links = self.add_wikilinks(
            body,
            density=link_density,
            keywords=template['keywords']
        )
        
        # Extract tags
        tags = self.extract_tags(body_with_links)
        
        # Extract links
        links = self.extract_links(body_with_links)
        
        return {
            'title': title,
            'content': f"# {title}\n\n{body_with_links}",
            'tags': tags,
            'links': links
        }
    
    def create_generation_prompt(
        self,
        domain: str,
        subtopic: str,
        note_type: str,
        target_words: int,
        keywords: List[str]
    ) -> str:
        """Create LLM prompt for note generation."""
        
        prompts = {
            "concept": f"""Write a {target_words}-word concept note about {subtopic} in {domain}.

Start with a # heading, then explain the concept clearly.
Include:
- Definition
- Key characteristics
- Common use cases
- Related concepts

Use these keywords naturally: {', '.join(keywords[:5])}
""",
            "tutorial": f"""Write a {target_words}-word tutorial about {subtopic} in {domain}.

Start with a # heading, then provide step-by-step instructions.
Include:
- Prerequisites
- Steps (numbered)
- Code examples (if applicable)
- Common pitfalls

Use these keywords: {', '.join(keywords[:5])}
""",
            "reference": f"""Write a {target_words}-word reference note about {subtopic} in {domain}.

Start with a # heading, then provide comprehensive reference info.
Include:
- Syntax/API
- Parameters/options
- Examples
- See also

Use these keywords: {', '.join(keywords[:5])}
"""
        }
        
        return prompts.get(note_type, prompts["concept"])
    
    def add_wikilinks(
        self,
        text: str,
        density: float,
        keywords: List[str]
    ) -> str:
        """Add [[wikilinks]] to keywords."""
        
        words = text.split()
        linked_text = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Check if word is a keyword and should be linked
            if clean_word in [k.lower() for k in keywords]:
                if random.random() < density:
                    # Add wikilink
                    linked_word = word.replace(clean_word, f"[[{clean_word.title()}]]")
                    linked_text.append(linked_word)
                    continue
            
            linked_text.append(word)
        
        return ' '.join(linked_text)
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract #tags from text."""
        return re.findall(r'#(\w+)', text)
    
    def extract_links(self, text: str) -> List[str]:
        """Extract [[wikilinks]] from text."""
        return re.findall(r'\[\[([^\]]+)\]\]', text)
    
    def generate_vault(
        self,
        topics: List[str],
        num_notes: int,
        output_dir: str = "./synthetic_vault"
    ) -> Dict:
        """
        Generate a complete synthetic vault.
        
        Args:
            topics: List of topics (e.g., ["programming.python", "ml.nlp"])
            num_notes: Total number of notes to generate
            output_dir: Where to save the vault
        
        Returns:
            Metadata about generated vault
        """
        from pathlib import Path
        import json
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        notes_per_topic = num_notes // len(topics)
        generated_notes = []
        
        print(f"Generating {num_notes} notes across {len(topics)} topics...")
        
        for topic in topics:
            print(f"  Generating {notes_per_topic} notes for {topic}...")
            
            for i in range(notes_per_topic):
                # Vary note type and length
                note_type = random.choice(["concept", "tutorial", "reference"])
                length = random.choice(["short", "medium", "long"])
                
                # Generate note
                note = self.generate_note(
                    topic=topic,
                    note_type=note_type,
                    length=length
                )
                
                # Save to file
                filename = f"{topic.replace('.', '_')}_{i:03d}.md"
                filepath = output_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(note['content'])
                
                generated_notes.append({
                    'filename': filename,
                    'topic': topic,
                    'type': note_type,
                    'length': length,
                    'tags': note['tags'],
                    'links': note['links']
                })
        
        # Save metadata
        metadata = {
            'num_notes': len(generated_notes),
            'topics': topics,
            'notes': generated_notes
        }
        
        with open(output_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Generated {len(generated_notes)} notes in {output_dir}")
        
        return metadata
```

**CLI Tool**:
```python
# generate_vault.py
import argparse
from synthetic_generator import SyntheticNoteGenerator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--topics",
        nargs="+",
        default=["programming.python", "ml.deep_learning"],
        help="Topics to generate"
    )
    parser.add_argument(
        "--num-notes",
        type=int,
        default=100,
        help="Number of notes to generate"
    )
    parser.add_argument(
        "--output",
        default="./synthetic_vault",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    generator = SyntheticNoteGenerator()
    generator.generate_vault(
        topics=args.topics,
        num_notes=args.num_notes,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Generate 500 notes on programming topics
python generate_vault.py \
    --topics programming.python programming.rust ml.nlp \
    --num-notes 500 \
    --output ./test_vault

# Generated vault structure:
# test_vault/
# ├── metadata.json
# ├── programming_python_001.md
# ├── programming_python_002.md
# ├── programming_rust_001.md
# ...
```

#### Week 3: Quality Validation

```python
# quality_validator.py
from typing import Dict, List
import re

class QualityValidator:
    """Validate synthetic data quality."""
    
    def __init__(self):
        self.min_word_count = 50
        self.max_word_count = 10000
        self.min_unique_ratio = 0.3  # 30% unique words
    
    def validate_note(self, note: Dict) -> Dict[str, any]:
        """
        Validate a single note.
        
        Returns:
            {
                'valid': bool,
                'issues': List[str],
                'quality_score': float (0-1)
            }
        """
        issues = []
        scores = []
        
        content = note['content']
        
        # 1. Length check
        words = content.split()
        word_count = len(words)
        
        if word_count < self.min_word_count:
            issues.append(f"Too short ({word_count} words)")
            scores.append(0.0)
        elif word_count > self.max_word_count:
            issues.append(f"Too long ({word_count} words)")
            scores.append(0.0)
        else:
            scores.append(1.0)
        
        # 2. Uniqueness check
        unique_words = len(set(words))
        unique_ratio = unique_words / word_count if word_count > 0 else 0
        
        if unique_ratio < self.min_unique_ratio:
            issues.append(f"Low uniqueness ({unique_ratio:.1%})")
            scores.append(0.0)
        else:
            scores.append(unique_ratio / self.min_unique_ratio)
        
        # 3. Structure check (has headings?)
        has_heading = bool(re.search(r'^#+\s+', content, re.MULTILINE))
        if not has_heading:
            issues.append("No headings found")
            scores.append(0.0)
        else:
            scores.append(1.0)
        
        # 4. Link density check
        links = note.get('links', [])
        link_density = len(links) / word_count if word_count > 0 else 0
        
        if link_density < 0.01:  # <1%
            issues.append("Very few links")
            scores.append(0.5)
        elif link_density > 0.5:  # >50%
            issues.append("Too many links")
            scores.append(0.5)
        else:
            scores.append(1.0)
        
        # 5. Coherence check (simple heuristic)
        avg_sentence_length = self.get_avg_sentence_length(content)
        
        if avg_sentence_length < 5:
            issues.append("Very short sentences")
            scores.append(0.5)
        elif avg_sentence_length > 50:
            issues.append("Very long sentences")
            scores.append(0.5)
        else:
            scores.append(1.0)
        
        # Calculate overall quality score
        quality_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'quality_score': quality_score,
            'metrics': {
                'word_count': word_count,
                'unique_ratio': unique_ratio,
                'link_density': link_density,
                'avg_sentence_length': avg_sentence_length
            }
        }
    
    def get_avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        lengths = [len(s.split()) for s in sentences]
        return sum(lengths) / len(lengths)
    
    def validate_vault(self, vault_dir: str) -> Dict:
        """Validate entire vault."""
        from pathlib import Path
        import json
        
        vault_path = Path(vault_dir)
        
        # Load metadata
        with open(vault_path / 'metadata.json') as f:
            metadata = json.load(f)
        
        results = []
        quality_scores = []
        
        for note_meta in metadata['notes']:
            filepath = vault_path / note_meta['filename']
            
            with open(filepath, encoding='utf-8') as f:
                content = f.read()
            
            note = {
                'content': content,
                'links': note_meta['links']
            }
            
            validation = self.validate_note(note)
            results.append({
                'filename': note_meta['filename'],
                **validation
            })
            
            quality_scores.append(validation['quality_score'])
        
        # Calculate vault-level metrics
        avg_quality = sum(quality_scores) / len(quality_scores)
        num_valid = sum(1 for r in results if r['valid'])
        
        return {
            'total_notes': len(results),
            'valid_notes': num_valid,
            'avg_quality_score': avg_quality,
            'results': results
        }
```

#### Week 4: Q&A Pair Generation

```python
# qa_generator.py
from typing import List, Dict
from openai import OpenAI

class QAPairGenerator:
    """Generate question-answer pairs from notes."""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key)
    
    def generate_qa_pairs(
        self,
        note_content: str,
        num_pairs: int = 5
    ) -> List[Dict]:
        """
        Generate Q&A pairs from a note.
        
        Args:
            note_content: Content of the note
            num_pairs: Number of Q&A pairs to generate
        
        Returns:
            List of {'question': '...', 'answer': '...'}
        """
        prompt = f"""Given the following note content, generate {num_pairs} question-answer pairs.

Make questions specific and answers concise but complete.
Format each pair as:
Q: [question]
A: [answer]

Note content:
{note_content[:2000]}  # Limit context

Generate {num_pairs} Q&A pairs:"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You generate educational Q&A pairs from notes."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # Parse response
        qa_text = response.choices[0].message.content
        pairs = self.parse_qa_pairs(qa_text)
        
        return pairs
    
    def parse_qa_pairs(self, text: str) -> List[Dict]:
        """Parse Q&A pairs from text."""
        pairs = []
        lines = text.strip().split('\n')
        
        current_q = None
        current_a = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Q:'):
                if current_q and current_a:
                    pairs.append({
                        'question': current_q,
                        'answer': current_a
                    })
                current_q = line[2:].strip()
                current_a = None
            elif line.startswith('A:'):
                current_a = line[2:].strip()
        
        # Add last pair
        if current_q and current_a:
            pairs.append({
                'question': current_q,
                'answer': current_a
            })
        
        return pairs
    
    def generate_qa_dataset(
        self,
        vault_dir: str,
        output_file: str = "qa_dataset.json"
    ) -> List[Dict]:
        """Generate Q&A dataset from entire vault."""
        from pathlib import Path
        import json
        
        vault_path = Path(vault_dir)
        all_pairs = []
        
        # Process all markdown files
        for md_file in vault_path.glob("*.md"):
            with open(md_file, encoding='utf-8') as f:
                content = f.read()
            
            # Generate pairs for this note
            pairs = self.generate_qa_pairs(content, num_pairs=3)
            
            # Add source metadata
            for pair in pairs:
                pair['source'] = md_file.name
            
            all_pairs.extend(pairs)
        
        # Save dataset
        with open(output_file, 'w') as f:
            json.dump(all_pairs, f, indent=2)
        
        print(f"✅ Generated {len(all_pairs)} Q&A pairs")
        
        return all_pairs
```

---

### Phase 2: Advanced Generation (4 weeks)

#### Week 5-6: Graph-Based Generation

```python
# graph_generator.py
import networkx as nx
from typing import List, Dict
import random

class GraphBasedGenerator:
    """Generate notes with realistic knowledge graph structure."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def create_knowledge_graph(
        self,
        domain: str,
        num_concepts: int = 100,
        edge_probability: float = 0.1
    ):
        """
        Create knowledge graph structure.
        
        Concepts are nodes, relationships are edges.
        """
        # Generate concepts
        concepts = self.generate_concepts(domain, num_concepts)
        
        # Add nodes
        for concept in concepts:
            self.graph.add_node(
                concept['name'],
                level=concept['level'],
                type=concept['type']
            )
        
        # Add edges (relationships)
        for concept1 in concepts:
            for concept2 in concepts:
                if concept1 == concept2:
                    continue
                
                # Higher level concepts link to lower level
                if concept1['level'] > concept2['level']:
                    if random.random() < edge_probability:
                        self.graph.add_edge(
                            concept1['name'],
                            concept2['name'],
                            type='depends_on'
                        )
        
        return self.graph
    
    def generate_concepts(
        self,
        domain: str,
        num_concepts: int
    ) -> List[Dict]:
        """Generate concept hierarchy."""
        
        # Define concept levels
        levels = {
            'fundamental': 0.3,  # 30% fundamentals
            'intermediate': 0.5,  # 50% intermediate
            'advanced': 0.2      # 20% advanced
        }
        
        concepts = []
        
        for level, proportion in levels.items():
            count = int(num_concepts * proportion)
            
            for i in range(count):
                concepts.append({
                    'name': f"{domain}_{level}_{i:03d}",
                    'level': list(levels.keys()).index(level),
                    'type': random.choice(['concept', 'method', 'tool'])
                })
        
        return concepts
    
    def generate_note_from_graph(
        self,
        concept: str,
        generator: 'SyntheticNoteGenerator'
    ) -> Dict:
        """Generate note with links based on graph structure."""
        
        # Get related concepts
        prerequisites = list(self.graph.predecessors(concept))
        related = list(self.graph.successors(concept))
        
        # Generate base note
        note = generator.generate_note(
            topic=f"custom.{concept}",
            note_type="concept"
        )
        
        # Add links section
        links_section = "\n\n## Related Concepts\n\n"
        
        if prerequisites:
            links_section += "**Prerequisites**:\n"
            for prereq in prerequisites:
                links_section += f"- [[{prereq}]]\n"
        
        if related:
            links_section += "\n**See Also**:\n"
            for rel in related:
                links_section += f"- [[{rel}]]\n"
        
        note['content'] += links_section
        
        return note
```

#### Week 7-8: Diversity & Realism

```python
# diversity_enhancer.py
from typing import List, Dict
import random

class DiversityEnhancer:
    """Enhance diversity of synthetic data."""
    
    def __init__(self):
        self.style_templates = self.load_style_templates()
    
    def load_style_templates(self) -> Dict:
        """Load different writing style templates."""
        return {
            "academic": {
                "intro": "This paper examines...",
                "tone": "formal",
                "citations": True
            },
            "casual": {
                "intro": "Let's talk about...",
                "tone": "informal",
                "citations": False
            },
            "tutorial": {
                "intro": "In this guide, we'll...",
                "tone": "instructional",
                "citations": False
            },
            "reference": {
                "intro": "Definition:",
                "tone": "concise",
                "citations": True
            }
        }
    
    def apply_style(
        self,
        content: str,
        style: str
    ) -> str:
        """Apply writing style to content."""
        
        template = self.style_templates.get(style, self.style_templates["casual"])
        
        # Modify intro
        lines = content.split('\n')
        if len(lines) > 2:
            # Replace first paragraph
            lines[2] = template["intro"] + " " + lines[2]
        
        styled_content = '\n'.join(lines)
        
        # Add citations if needed
        if template.get("citations"):
            styled_content += "\n\n## References\n\n"
            styled_content += "- [1] Smith et al. (2023)\n"
        
        return styled_content
    
    def add_variations(
        self,
        base_notes: List[Dict],
        num_variations: int = 3
    ) -> List[Dict]:
        """Create variations of existing notes."""
        
        varied_notes = []
        
        for note in base_notes:
            # Original
            varied_notes.append(note)
            
            # Create variations
            for i in range(num_variations - 1):
                style = random.choice(list(self.style_templates.keys()))
                
                varied_note = note.copy()
                varied_note['content'] = self.apply_style(
                    note['content'],
                    style
                )
                varied_note['title'] += f" ({style.title()} Version)"
                
                varied_notes.append(varied_note)
        
        return varied_notes
```

---

### Phase 3: Specialized Generators (2 weeks)

#### Week 9-10: Domain-Specific Generators

```python
# domain_generators.py

class CodeExampleGenerator:
    """Generate code examples with explanations."""
    
    def generate_code_note(
        self,
        language: str,
        topic: str
    ) -> Dict:
        """Generate note with code examples."""
        
        prompt = f"""Create a code tutorial about {topic} in {language}.

Include:
1. Brief explanation
2. Code example with comments
3. Common pitfalls
4. Best practices

Format as Markdown with code blocks."""
        
        # Use LLM to generate
        # ... (similar to previous generators)
        
        return note


class PaperNotesGenerator:
    """Generate research paper summaries."""
    
    def generate_paper_notes(
        self,
        paper_title: str,
        domain: str
    ) -> Dict:
        """Generate paper summary notes."""
        
        prompt = f"""Create research paper notes for: {paper_title}

Include:
## Summary
[Brief overview]

## Key Contributions
- [Contribution 1]
- [Contribution 2]

## Methodology
[Approach used]

## Results
[Main findings]

## Related Work
[[Related Paper 1]]
[[Related Paper 2]]"""
        
        # Generate with LLM
        # ...
        
        return note


class MeetingNotesGenerator:
    """Generate realistic meeting notes."""
    
    def generate_meeting_notes(
        self,
        meeting_type: str = "team_standup"
    ) -> Dict:
        """Generate meeting notes."""
        
        templates = {
            "team_standup": """# Team Standup - {date}

## Attendees
- Alice (PM)
- Bob (Engineer)
- Carol (Designer)

## Updates

**Alice**:
- Completed user research
- Started roadmap planning

**Bob**:
- Fixed bug #123
- Working on feature X

**Carol**:
- Mockups ready for review
- Waiting on feedback

## Blockers
- Need design review
- Waiting on API access

## Action Items
- [ ] Alice: Schedule design review
- [ ] Bob: Deploy hotfix
- [ ] Carol: Update wireframes
"""
        }
        
        template = templates.get(meeting_type)
        
        # Fill in template
        # ...
        
        return note
```

---

## Quality Metrics

### Automated Metrics

```python
def calculate_quality_metrics(synthetic_vault: str) -> Dict:
    """Calculate quality metrics for synthetic vault."""
    
    metrics = {
        # Coverage
        'topic_coverage': calculate_topic_coverage(synthetic_vault),
        'link_connectivity': calculate_connectivity(synthetic_vault),
        
        # Diversity
        'style_diversity': calculate_style_diversity(synthetic_vault),
        'length_variance': calculate_length_variance(synthetic_vault),
        
        # Realism
        'human_likeness': calculate_human_likeness(synthetic_vault),
        'coherence': calculate_coherence(synthetic_vault),
        
        # Utility
        'rag_performance': test_rag_performance(synthetic_vault),
        'searchability': test_search_quality(synthetic_vault)
    }
    
    return metrics
```

### Human Evaluation

```python
def run_human_evaluation(
    synthetic_notes: List[Dict],
    real_notes: List[Dict],
    num_evaluators: int = 5
) -> Dict:
    """Run blind human evaluation."""
    
    # Mix synthetic and real
    mixed_notes = synthetic_notes + real_notes
    random.shuffle(mixed_notes)
    
    # Evaluators rate each note
    ratings = []
    
    for evaluator in range(num_evaluators):
        for note in mixed_notes:
            rating = input(f"Rate this note (1-5): {note['title']}\n")
            
            ratings.append({
                'note_id': note['id'],
                'is_synthetic': note.get('is_synthetic', False),
                'rating': int(rating)
            })
    
    # Analyze results
    synthetic_avg = ...
    real_avg = ...
    
    # Synthetic data is good if:
    # - Avg rating >= 3.5/5
    # - <10% difference from real data
    
    return {
        'synthetic_avg': synthetic_avg,
        'real_avg': real_avg,
        'difference': abs(synthetic_avg - real_avg),
        'pass': synthetic_avg >= 3.5 and abs(synthetic_avg - real_avg) < 0.5
    }
```

---

## Cost Analysis

### Generation Costs

**Using GPT-4**:
- Cost: $0.03/1K input tokens, $0.06/1K output tokens
- Avg note: ~500 output tokens = $0.03
- 1000 notes: ~$30

**Using GPT-3.5**:
- Cost: $0.001/1K tokens
- 1000 notes: ~$0.50

**Using Open-Source (Llama 2)**:
- Cost: $0 (self-hosted)
- Time: ~2-3s per note

### Storage Costs

- 1000 notes: ~5MB
- 100K notes: ~500MB
- Negligible S3 costs (<$0.10/month)

---

## Best Practices

### 1. Start with Templates
```python
# Good: Use templates for consistency
generator = SyntheticNoteGenerator()
generator.add_template("concept", concept_template)

# Bad: Fully free-form generation
# (leads to inconsistent quality)
```

### 2. Validate Everything
```python
# Good: Validate before using
validator = QualityValidator()
if validator.validate_note(note)['valid']:
    use_note(note)

# Bad: Use without validation
```

### 3. Mix Synthetic and Real
```python
# Good: 80% real, 20% synthetic
training_data = real_data * 4 + synthetic_data

# Bad: 100% synthetic
# (may learn artifacts)
```

### 4. Iterative Improvement
```python
# Good: Generate → Evaluate → Refine → Repeat
for iteration in range(10):
    notes = generator.generate()
    metrics = evaluate(notes)
    generator.update_templates(metrics)

# Bad: One-shot generation
```

---

## Use Case Examples

### Example 1: RAG Testing

```python
# Generate test vault
generator = SyntheticNoteGenerator()
test_vault = generator.generate_vault(
    topics=["programming.python", "ml.nlp"],
    num_notes=500
)

# Create test queries with known answers
qa_gen = QAPairGenerator()
test_queries = qa_gen.generate_qa_dataset(test_vault)

# Test RAG pipeline
rag = RAGPipeline()
rag.index(test_vault)

accuracy = 0
for query in test_queries:
    result = rag.search(query['question'])
    if query['answer'] in result:
        accuracy += 1

print(f"RAG Accuracy: {accuracy / len(test_queries):.1%}")
```

### Example 2: Fine-tuning Data

```python
# Generate preference pairs for DPO
pref_gen = PreferenceGenerator()

preferences = []
for note in synthetic_vault:
    # Good answer: uses vault context
    good = generate_with_context(note)
    
    # Bad answer: generic (no context)
    bad = generate_without_context(note)
    
    preferences.append({
        'prompt': f"Summarize: {note.title}",
        'chosen': good,
        'rejected': bad
    })

# Use for DPO training
trainer = DPOTrainer()
trainer.train(preferences)
```

---

## Risks & Limitations

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quality drift | Medium | Continuous validation |
| Style artifacts | Medium | Diverse templates |
| Factual errors | High | Fact-checking, human review |
| High costs (GPT-4) | Low | Use GPT-3.5 or open-source |

### Limitations

- **Not a replacement for real data** - Use as supplement
- **May have subtle patterns** - Models might detect synthetic data
- **Domain knowledge required** - Need good templates
- **Quality variance** - Some notes better than others

---

## Next Steps

1. **Prototype** (4 weeks)
   - Build basic note generator
   - Generate 100-note test vault
   - Validate quality

2. **Evaluation** (2 weeks)
   - Human evaluation study
   - RAG performance testing
   - Refine templates

3. **Scale** (2 weeks)
   - Generate 10K note dataset
   - Optimize cost/quality tradeoff
   - Document best practices

4. **Integration** (2 weeks)
   - Add to testing suite
   - Create DPO training data
   - Performance benchmarks

---

**Status**: 🔬 Research Complete  
**Next Action**: Prototype Development  
**Estimated Timeline**: 10-12 weeks to production  
**GitHub Issue**: [#109](https://github.com/B0LK13/obsidian-agent/issues/109)
