"""Test vault fixtures for E2E testing.

Small vault: 10 notes
Medium vault: 100 notes  
Large vault: 1000 notes
"""

from pathlib import Path
from datetime import datetime, timedelta
import random


def create_note(title: str, content: str, tags: list[str], date: datetime) -> str:
    """Create a markdown note with front matter."""
    frontmatter = f"""---
title: {title}
date: {date.isoformat()}
tags: {tags}
---

{content}
"""
    return frontmatter


def generate_small_vault(vault_path: Path):
    """Generate 10 notes for quick testing."""
    notes = [
        ("Introduction to Machine Learning", 
         "Machine learning is a subset of artificial intelligence that focuses on developing algorithms and statistical models that enable computers to improve their performance on a specific task through experience.",
         ["ai", "ml", "basics"]),
        
        ("Deep Learning Fundamentals",
         "Deep learning is a subset of machine learning that uses neural networks with multiple layers. These networks can learn hierarchical representations of data.",
         ["ai", "deep-learning", "neural-networks"]),
        
        ("Python for Data Science",
         "Python is the most popular programming language for data science due to libraries like NumPy, Pandas, and Scikit-learn.",
         ["python", "data-science", "programming"]),
        
        ("Neural Network Architectures",
         "Common neural network architectures include feedforward networks, convolutional neural networks (CNNs), and recurrent neural networks (RNNs).",
         ["neural-networks", "architectures", "deep-learning"]),
        
        ("Natural Language Processing",
         "NLP is a field of AI that focuses on the interaction between computers and human language. It includes tasks like sentiment analysis, translation, and text generation.",
         ["nlp", "ai", "language"]),
        
        ("Computer Vision Basics",
         "Computer vision enables machines to interpret and understand visual information from the world. Applications include object detection, facial recognition, and image segmentation.",
         ["computer-vision", "ai", "image-processing"]),
        
        ("Reinforcement Learning",
         "Reinforcement learning is a type of machine learning where an agent learns to make decisions by interacting with an environment and receiving rewards or penalties.",
         ["reinforcement-learning", "ai", "agents"]),
        
        ("Data Preprocessing",
         "Data preprocessing is crucial for machine learning. It includes cleaning, normalization, feature engineering, and handling missing values.",
         ["data-science", "preprocessing", "ml"]),
        
        ("Model Evaluation Metrics",
         "Common metrics for evaluating ML models include accuracy, precision, recall, F1-score, ROC-AUC, and mean squared error.",
         ["ml", "evaluation", "metrics"]),
        
        ("Ethics in AI",
         "AI ethics addresses concerns about bias, fairness, transparency, privacy, and the societal impact of artificial intelligence systems.",
         ["ai", "ethics", "society"]),
    ]
    
    vault_path.mkdir(parents=True, exist_ok=True)
    
    for i, (title, content, tags) in enumerate(notes):
        date = datetime.now() - timedelta(days=i)
        filename = f"{date.strftime('%Y%m%d')}-{title.lower().replace(' ', '-')}.md"
        note_path = vault_path / filename
        note_path.write_text(create_note(title, content, tags, date), encoding="utf-8")
    
    return len(notes)


def generate_medium_vault(vault_path: Path):
    """Generate 100 notes with varied content."""
    vault_path.mkdir(parents=True, exist_ok=True)
    
    topics = [
        ("Machine Learning", ["supervised learning", "unsupervised learning", "regression", "classification"]),
        ("Deep Learning", ["CNNs", "RNNs", "transformers", "attention mechanisms"]),
        ("Data Science", ["statistics", "visualization", "exploratory analysis", "feature engineering"]),
        ("Programming", ["Python", "algorithms", "data structures", "optimization"]),
        ("AI Applications", ["robotics", "autonomous vehicles", "healthcare", "finance"]),
    ]
    
    count = 0
    for topic_idx, (topic, subtopics) in enumerate(topics):
        for i in range(20):  # 20 notes per topic
            subtopic = subtopics[i % len(subtopics)]
            title = f"{topic}: {subtopic.title()} - Part {i+1}"
            content = f"""This note discusses {subtopic} in the context of {topic}.

## Overview
{subtopic.title()} is an important concept that relates to several other ideas in this domain.

## Key Points
- Point 1: Fundamental principles of {subtopic}
- Point 2: Practical applications
- Point 3: Common challenges and solutions

## Related Concepts
This connects to other notes about {topic} and {random.choice(subtopics)}.

## References
- See also: [[{topic} Fundamentals]]
- Related: [[{random.choice(subtopics).title()}]]
"""
            
            tags = [topic.lower().replace(" ", "-"), subtopic.lower().replace(" ", "-")]
            date = datetime.now() - timedelta(days=count)
            filename = f"{date.strftime('%Y%m%d')}-{title.lower().replace(' ', '-').replace(':', '')}.md"
            note_path = vault_path / filename
            note_path.write_text(create_note(title, content, tags, date), encoding="utf-8")
            count += 1
    
    return count


def generate_large_vault(vault_path: Path):
    """Generate 1000 notes for performance testing."""
    vault_path.mkdir(parents=True, exist_ok=True)
    
    # Start with medium vault
    count = generate_medium_vault(vault_path)
    
    # Add 900 more synthetic notes
    domains = ["Technology", "Science", "Business", "Health", "Education"]
    concepts = ["Analysis", "Framework", "Strategy", "Method", "Theory", "Practice", "Research"]
    
    for i in range(900):
        domain = random.choice(domains)
        concept = random.choice(concepts)
        number = i + 101
        
        title = f"{domain} {concept} {number}"
        content = f"""# {title}

This is a synthetic note created for testing purposes.

## Summary
This note explores {concept.lower()} within the {domain.lower()} domain.

## Content
{'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 10}

## Tags
- {domain.lower()}
- {concept.lower()}
- test-data

## Links
- See: [[{random.choice(domains)} Overview]]
- Related: [[{random.choice(concepts)} Basics]]
"""
        
        tags = [domain.lower(), concept.lower(), "synthetic"]
        date = datetime.now() - timedelta(days=count)
        filename = f"{date.strftime('%Y%m%d')}-{title.lower().replace(' ', '-')}.md"
        note_path = vault_path / filename
        note_path.write_text(create_note(title, content, tags, date), encoding="utf-8")
        count += 1
    
    return count


def setup_all_fixtures():
    """Set up all test vault fixtures."""
    base_path = Path(__file__).parent
    
    small_path = base_path / "vaults" / "small"
    medium_path = base_path / "vaults" / "medium"
    large_path = base_path / "vaults" / "large"
    
    print("Generating test vault fixtures...")
    
    small_count = generate_small_vault(small_path)
    print(f"✅ Small vault: {small_count} notes")
    
    medium_count = generate_medium_vault(medium_path)
    print(f"✅ Medium vault: {medium_count} notes")
    
    large_count = generate_large_vault(large_path)
    print(f"✅ Large vault: {large_count} notes")
    
    print(f"\n Total: {small_count + medium_count + large_count} notes across all fixtures")


if __name__ == "__main__":
    setup_all_fixtures()
