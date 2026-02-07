# DPO Training Pipeline - Research & Implementation Plan

**GitHub Issue**: [#107 - DPO Training Pipeline](https://github.com/B0LK13/obsidian-agent/issues/107)  
**Priority**: Low 🟢  
**Target Version**: v2.5  
**Status**: 🔬 Research & Planning

---

## Overview

Implement **Direct Preference Optimization (DPO)** to fine-tune language models on user preferences without requiring reinforcement learning infrastructure (no separate reward model needed).

### What is DPO?

DPO is a simplified alternative to RLHF (Reinforcement Learning from Human Feedback) that:
- ✅ Directly optimizes policy using preference data
- ✅ No reward model training required
- ✅ More stable training than PPO
- ✅ Better compute efficiency

**Paper**: [Direct Preference Optimization](https://arxiv.org/abs/2305.18290) (Rafailov et al., 2023)

---

## Use Cases for Obsidian Agent

### 1. Personal Writing Style Adaptation
```
User preference data:
- Response A: "The meeting discussed..." ❌ (rejected)
- Response B: "We talked about..." ✅ (preferred)

→ Model learns user's informal style
```

### 2. Domain-Specific Knowledge
```
User vault focus: Software Engineering
- Generic response ❌
- Technical response with code examples ✅

→ Model learns technical communication
```

### 3. Length & Verbosity Preferences
```
User feedback:
- Long explanations ❌
- Concise bullet points ✅

→ Model learns brevity
```

### 4. Citation Style
```
Preferences:
- No sources ❌
- Always cite vault notes ✅

→ Model learns to reference notes
```

---

## DPO Algorithm Simplified

### Traditional RLHF
```
1. Supervised fine-tuning (SFT)
2. Train reward model on preferences
3. Use PPO to optimize policy against reward
4. Deal with instability and complexity
```

### DPO (Simpler!)
```
1. Supervised fine-tuning (SFT)
2. Collect preference pairs (chosen vs rejected)
3. Directly optimize policy with DPO loss
4. Done! No reward model needed
```

### DPO Loss Function
```python
# Simplified DPO loss
def dpo_loss(model, prompt, chosen, rejected, beta=0.1):
    """
    DPO loss function.
    
    Args:
        model: Language model to train
        prompt: Input prompt
        chosen: Preferred completion
        rejected: Rejected completion
        beta: Temperature parameter
    """
    # Get log probabilities
    logp_chosen = model.log_prob(prompt, chosen)
    logp_rejected = model.log_prob(prompt, rejected)
    
    # Reference model (frozen base model)
    logp_ref_chosen = ref_model.log_prob(prompt, chosen)
    logp_ref_rejected = ref_model.log_prob(prompt, rejected)
    
    # Compute DPO loss
    loss = -log_sigmoid(
        beta * ((logp_chosen - logp_ref_chosen) - 
                (logp_rejected - logp_ref_rejected))
    )
    
    return loss.mean()
```

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DPO Training Pipeline                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │   Obsidian   │───▶│  Preference  │───▶│   DPO    │  │
│  │  Vault Data  │    │  Collector   │    │ Trainer  │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│         │                    │                  │       │
│         │                    │                  │       │
│         ▼                    ▼                  ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  Synthetic   │    │  Preference  │    │  Fine-   │  │
│  │     Data     │    │   Dataset    │    │  Tuned   │  │
│  │  Generator   │    │   (JSON)     │    │  Model   │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Data Collection (4 weeks)

#### Week 1-2: Preference Collection UI

**In-App Feedback Interface**:
```typescript
// Obsidian plugin for preference collection
export class PreferenceCollector {
    async showFeedbackModal(prompt: string, response: string) {
        const modal = new Modal(this.app);
        
        // Show response
        modal.contentEl.createEl('h3', { text: 'AI Response' });
        modal.contentEl.createEl('p', { text: response });
        
        // Rating options
        const ratingDiv = modal.contentEl.createDiv();
        
        // 👍 Thumbs up
        const thumbsUp = ratingDiv.createEl('button', {
            text: '👍 Good',
            cls: 'feedback-btn'
        });
        thumbsUp.onclick = () => this.saveFeedback(prompt, response, 'positive');
        
        // 👎 Thumbs down
        const thumbsDown = ratingDiv.createEl('button', {
            text: '👎 Bad',
            cls: 'feedback-btn'
        });
        thumbsDown.onclick = () => {
            // Ask for alternative
            this.requestAlternative(prompt, response);
        };
    }
    
    async requestAlternative(prompt: string, rejected: string) {
        // Generate alternative response
        const alternative = await this.generateAlternative(prompt);
        
        // Save as preference pair
        await this.savePreferencePair({
            prompt: prompt,
            chosen: alternative,
            rejected: rejected,
            timestamp: Date.now()
        });
    }
}
```

**Data Format**:
```json
{
  "preferences": [
    {
      "id": "pref_001",
      "timestamp": "2024-01-15T10:30:00Z",
      "prompt": "Summarize my notes on machine learning",
      "chosen": "Here's a concise summary:\n\n• Supervised learning...",
      "rejected": "Machine learning is a vast field that encompasses...",
      "metadata": {
        "vault_context": ["ml_basics.md", "neural_networks.md"],
        "user_id": "user_123",
        "model_version": "llama-2-7b"
      }
    }
  ]
}
```

#### Week 3-4: Synthetic Data Generation

**Automatic Preference Creation**:
```python
class SyntheticPreferenceGenerator:
    """Generate preference pairs from vault data."""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.notes = self.load_notes()
    
    def generate_qa_pairs(self) -> List[Dict]:
        """Generate Q&A pairs from notes."""
        pairs = []
        
        for note in self.notes:
            # Extract headings as potential questions
            questions = self.extract_questions(note)
            
            for question in questions:
                # Good answer: from vault context
                good_answer = self.generate_with_context(
                    question, 
                    context=note.content
                )
                
                # Bad answer: without context (hallucination)
                bad_answer = self.generate_without_context(question)
                
                pairs.append({
                    'prompt': question,
                    'chosen': good_answer,
                    'rejected': bad_answer,
                    'source': note.path
                })
        
        return pairs
    
    def extract_questions(self, note: Note) -> List[str]:
        """Convert headings to questions."""
        questions = []
        
        for heading in note.headings:
            # "Machine Learning Basics" → 
            # "What are machine learning basics?"
            question = f"What are {heading.lower()}?"
            questions.append(question)
        
        return questions
    
    def generate_style_pairs(self) -> List[Dict]:
        """Generate pairs for style learning."""
        pairs = []
        
        # Analyze user's writing style
        style = self.analyze_writing_style()
        
        for note in self.notes[:100]:  # Sample
            prompt = f"Rewrite this in my style: {note.excerpt}"
            
            # Good: matches user style
            chosen = self.apply_style(note.content, style)
            
            # Bad: generic/formal style
            rejected = self.generic_rewrite(note.content)
            
            pairs.append({
                'prompt': prompt,
                'chosen': chosen,
                'rejected': rejected
            })
        
        return pairs
```

**Diversity Strategies**:
```python
def ensure_diversity(preferences: List[Dict]) -> List[Dict]:
    """Ensure diverse training data."""
    
    # 1. Topic diversity
    topics = cluster_by_topic(preferences)
    balanced = balance_topics(topics, max_per_topic=50)
    
    # 2. Length diversity
    short = [p for p in balanced if len(p['chosen']) < 100]
    medium = [p for p in balanced if 100 <= len(p['chosen']) < 500]
    long = [p for p in balanced if len(p['chosen']) >= 500]
    
    # Mix 40% short, 40% medium, 20% long
    diverse = (
        random.sample(short, int(len(balanced) * 0.4)) +
        random.sample(medium, int(len(balanced) * 0.4)) +
        random.sample(long, int(len(balanced) * 0.2))
    )
    
    # 3. Shuffle
    random.shuffle(diverse)
    
    return diverse
```

---

### Phase 2: Training Infrastructure (6 weeks)

#### Week 5-6: DPO Trainer Implementation

```python
# dpo_trainer.py
import torch
from torch.nn import functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, List
import wandb

class DPOTrainer:
    """DPO trainer for language models."""
    
    def __init__(
        self,
        model_name: str = "meta-llama/Llama-2-7b-hf",
        beta: float = 0.1,
        learning_rate: float = 5e-7,
        max_length: int = 2048
    ):
        self.beta = beta
        self.lr = learning_rate
        self.max_length = max_length
        
        # Load model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Reference model (frozen)
        self.ref_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.ref_model.eval()
        
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=learning_rate
        )
    
    def compute_log_probs(
        self, 
        model: torch.nn.Module,
        input_ids: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """Compute log probabilities for tokens."""
        
        with torch.no_grad() if model == self.ref_model else torch.enable_grad():
            outputs = model(input_ids, labels=labels)
            logits = outputs.logits
            
            # Shift logits and labels for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Compute log probabilities
            log_probs = F.log_softmax(shift_logits, dim=-1)
            
            # Gather log probs for actual tokens
            token_log_probs = torch.gather(
                log_probs,
                dim=-1,
                index=shift_labels.unsqueeze(-1)
            ).squeeze(-1)
            
            # Mask padding tokens
            mask = (shift_labels != self.tokenizer.pad_token_id).float()
            
            # Sum log probs for sequence
            return (token_log_probs * mask).sum(-1)
    
    def dpo_loss(
        self,
        prompt: str,
        chosen: str,
        rejected: str
    ) -> torch.Tensor:
        """Compute DPO loss for a preference pair."""
        
        # Tokenize
        chosen_input = self.tokenizer(
            prompt + chosen,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding="max_length"
        ).to(self.model.device)
        
        rejected_input = self.tokenizer(
            prompt + rejected,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding="max_length"
        ).to(self.model.device)
        
        # Get log probs from policy model
        logp_chosen = self.compute_log_probs(
            self.model,
            chosen_input.input_ids,
            chosen_input.input_ids
        )
        
        logp_rejected = self.compute_log_probs(
            self.model,
            rejected_input.input_ids,
            rejected_input.input_ids
        )
        
        # Get log probs from reference model
        logp_ref_chosen = self.compute_log_probs(
            self.ref_model,
            chosen_input.input_ids,
            chosen_input.input_ids
        )
        
        logp_ref_rejected = self.compute_log_probs(
            self.ref_model,
            rejected_input.input_ids,
            rejected_input.input_ids
        )
        
        # Compute DPO loss
        pi_logratios = logp_chosen - logp_rejected
        ref_logratios = logp_ref_chosen - logp_ref_rejected
        
        loss = -F.logsigmoid(self.beta * (pi_logratios - ref_logratios))
        
        return loss.mean()
    
    def train_step(self, batch: Dict[str, List[str]]) -> float:
        """Single training step."""
        
        self.model.train()
        self.optimizer.zero_grad()
        
        # Compute loss for batch
        losses = []
        for prompt, chosen, rejected in zip(
            batch['prompts'],
            batch['chosen'],
            batch['rejected']
        ):
            loss = self.dpo_loss(prompt, chosen, rejected)
            losses.append(loss)
        
        # Average loss
        total_loss = torch.stack(losses).mean()
        
        # Backprop
        total_loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        
        # Update
        self.optimizer.step()
        
        return total_loss.item()
    
    def train(
        self,
        dataset: List[Dict],
        num_epochs: int = 3,
        batch_size: int = 4,
        eval_steps: int = 100,
        save_steps: int = 500
    ):
        """Full training loop."""
        
        # Initialize wandb
        wandb.init(project="obsidian-dpo-training")
        
        # Training loop
        global_step = 0
        
        for epoch in range(num_epochs):
            print(f"Epoch {epoch + 1}/{num_epochs}")
            
            # Shuffle dataset
            random.shuffle(dataset)
            
            # Batch training
            for i in range(0, len(dataset), batch_size):
                batch_data = dataset[i:i + batch_size]
                
                batch = {
                    'prompts': [d['prompt'] for d in batch_data],
                    'chosen': [d['chosen'] for d in batch_data],
                    'rejected': [d['rejected'] for d in batch_data]
                }
                
                # Train step
                loss = self.train_step(batch)
                
                # Log
                wandb.log({
                    'loss': loss,
                    'epoch': epoch,
                    'step': global_step
                })
                
                # Evaluate
                if global_step % eval_steps == 0:
                    self.evaluate()
                
                # Save checkpoint
                if global_step % save_steps == 0:
                    self.save_checkpoint(f"checkpoint-{global_step}")
                
                global_step += 1
        
        # Final save
        self.save_model("final_model")
    
    def evaluate(self):
        """Evaluate model on held-out set."""
        # TODO: Implement evaluation
        pass
    
    def save_checkpoint(self, path: str):
        """Save model checkpoint."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
```

#### Week 7-8: LoRA/QLoRA Integration

**Efficient Fine-tuning with LoRA**:
```python
from peft import LoraConfig, get_peft_model, TaskType

class EfficientDPOTrainer(DPOTrainer):
    """DPO trainer with LoRA for efficient training."""
    
    def __init__(self, *args, use_lora: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        
        if use_lora:
            # Configure LoRA
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=16,  # LoRA rank
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
                bias="none"
            )
            
            # Apply LoRA to model
            self.model = get_peft_model(self.model, lora_config)
            
            print(f"Trainable params: {self.model.print_trainable_parameters()}")
            # Expected: ~0.5% of parameters (e.g., 35M/7B for Llama-2-7b)
```

**QLoRA for 4-bit Training**:
```python
from transformers import BitsAndBytesConfig

def load_model_qlora(model_name: str):
    """Load model with QLoRA (4-bit quantization)."""
    
    # 4-bit config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True
    )
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto"
    )
    
    return model

# Memory usage:
# - Standard: ~28GB for 7B model
# - LoRA: ~28GB (same VRAM, fewer trained params)
# - QLoRA: ~6GB (VRAM savings!)
```

#### Week 9-10: Training Pipeline

```python
# train_dpo.py - Main training script
import argparse
from pathlib import Path
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--model", type=str, default="meta-llama/Llama-2-7b-hf")
    parser.add_argument("--output", type=str, default="./dpo_model")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--use-lora", action="store_true")
    parser.add_argument("--use-qlora", action="store_true")
    args = parser.parse_args()
    
    # Load preference dataset
    with open(args.data) as f:
        dataset = json.load(f)['preferences']
    
    print(f"Loaded {len(dataset)} preference pairs")
    
    # Split train/eval
    split_idx = int(len(dataset) * 0.9)
    train_data = dataset[:split_idx]
    eval_data = dataset[split_idx:]
    
    # Initialize trainer
    if args.use_qlora:
        model = load_model_qlora(args.model)
        trainer = EfficientDPOTrainer(
            model=model,
            use_lora=True
        )
    elif args.use_lora:
        trainer = EfficientDPOTrainer(
            model_name=args.model,
            use_lora=True
        )
    else:
        trainer = DPOTrainer(model_name=args.model)
    
    # Train
    trainer.train(
        dataset=train_data,
        num_epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    # Save
    trainer.save_model(args.output)
    print(f"Model saved to {args.output}")

if __name__ == "__main__":
    main()
```

---

### Phase 3: Integration (2 weeks)

#### Week 11: Model Serving

```python
# serve_dpo_model.py
from fastapi import FastAPI
from pydantic import BaseModel
import torch

app = FastAPI()

class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 512
    temperature: float = 0.7

class DPOModelServer:
    def __init__(self, model_path: str):
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model.eval()
    
    def generate(self, prompt: str, **kwargs) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=kwargs.get('max_length', 512),
                temperature=kwargs.get('temperature', 0.7),
                do_sample=True,
                top_p=0.9
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

# Global model instance
server = DPOModelServer("./dpo_model")

@app.post("/generate")
async def generate(request: GenerationRequest):
    response = server.generate(
        request.prompt,
        max_length=request.max_length,
        temperature=request.temperature
    )
    return {"response": response}
```

#### Week 12: A/B Testing

```python
class ABTestManager:
    """Manage A/B testing between base and DPO models."""
    
    def __init__(self):
        self.base_model = load_model("llama-2-7b")
        self.dpo_model = load_model("./dpo_model")
        self.results = []
    
    async def get_response(self, user_id: str, prompt: str) -> str:
        # Route 50% to DPO model
        use_dpo = hash(user_id) % 2 == 0
        
        if use_dpo:
            response = self.dpo_model.generate(prompt)
            model_version = "dpo"
        else:
            response = self.base_model.generate(prompt)
            model_version = "base"
        
        # Log for analysis
        self.results.append({
            'user_id': user_id,
            'model': model_version,
            'prompt': prompt,
            'response': response,
            'timestamp': datetime.now()
        })
        
        return response
    
    def analyze_results(self) -> Dict:
        """Analyze A/B test results."""
        dpo_feedback = [r for r in self.results if r['model'] == 'dpo']
        base_feedback = [r for r in self.results if r['model'] == 'base']
        
        return {
            'dpo_satisfaction': calculate_satisfaction(dpo_feedback),
            'base_satisfaction': calculate_satisfaction(base_feedback),
            'sample_size': len(self.results)
        }
```

---

## Hardware Requirements

### Training Requirements

| Model Size | Method | VRAM | Training Time | Cost (Cloud) |
|------------|--------|------|---------------|--------------|
| **7B** | Full | 28GB | 12h | $50-100 |
| **7B** | LoRA | 28GB | 6h | $25-50 |
| **7B** | QLoRA | 6GB | 8h | $15-30 |
| **13B** | QLoRA | 10GB | 16h | $40-80 |
| **70B** | QLoRA | 40GB | 48h | $200-400 |

### Recommended Setup

**For 7B Models** (Recommended):
```
GPU: NVIDIA RTX 4090 (24GB) or A100 (40GB)
RAM: 32GB+ system RAM
Storage: 100GB SSD for checkpoints
Method: QLoRA (most efficient)
```

**Cloud Alternatives**:
- Lambda Labs: $0.50-1.10/hr (A100)
- RunPod: $0.40-0.80/hr (A100)
- Vast.ai: $0.30-0.60/hr (A100, spot pricing)

---

## Dataset Requirements

### Minimum Viable Dataset
- **Size**: 500-1000 preference pairs
- **Quality**: High-quality, diverse examples
- **Coverage**: Multiple use cases
- **Balance**: Equal chosen/rejected distribution

### Recommended Dataset
- **Size**: 5000-10000 preference pairs
- **Sources**:
  - 30% explicit user feedback
  - 40% synthetic from vault
  - 30% curated examples

### Quality Metrics
```python
def validate_dataset(preferences: List[Dict]) -> Dict:
    """Validate preference dataset quality."""
    
    issues = []
    
    # Check diversity
    unique_prompts = len(set(p['prompt'] for p in preferences))
    diversity_ratio = unique_prompts / len(preferences)
    
    if diversity_ratio < 0.7:
        issues.append("Low prompt diversity")
    
    # Check length distribution
    lengths = [len(p['chosen']) for p in preferences]
    if max(lengths) / min(lengths) > 100:
        issues.append("Extreme length variance")
    
    # Check for duplicates
    duplicates = find_duplicates(preferences)
    if len(duplicates) > len(preferences) * 0.1:
        issues.append("Too many duplicates")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'diversity': diversity_ratio,
        'size': len(preferences)
    }
```

---

## Evaluation Metrics

### Automatic Metrics

```python
def evaluate_dpo_model(model, eval_dataset):
    """Evaluate DPO model performance."""
    
    metrics = {
        'preference_accuracy': 0.0,
        'perplexity': 0.0,
        'diversity': 0.0
    }
    
    # Preference accuracy: does model prefer chosen over rejected?
    correct = 0
    for example in eval_dataset:
        score_chosen = model.score(example['prompt'] + example['chosen'])
        score_rejected = model.score(example['prompt'] + example['rejected'])
        
        if score_chosen > score_rejected:
            correct += 1
    
    metrics['preference_accuracy'] = correct / len(eval_dataset)
    
    # Perplexity on chosen responses
    perplexities = []
    for example in eval_dataset:
        ppl = model.perplexity(example['prompt'] + example['chosen'])
        perplexities.append(ppl)
    
    metrics['perplexity'] = sum(perplexities) / len(perplexities)
    
    # Response diversity (distinct-n)
    responses = [model.generate(ex['prompt']) for ex in eval_dataset[:100]]
    metrics['diversity'] = calculate_distinct_n(responses, n=2)
    
    return metrics
```

### Human Evaluation

```python
def run_human_eval(base_model, dpo_model, test_prompts):
    """Side-by-side human evaluation."""
    
    results = []
    
    for prompt in test_prompts:
        base_response = base_model.generate(prompt)
        dpo_response = dpo_model.generate(prompt)
        
        # Randomize order
        if random.random() < 0.5:
            response_a, response_b = base_response, dpo_response
            label_a, label_b = 'base', 'dpo'
        else:
            response_a, response_b = dpo_response, base_response
            label_a, label_b = 'dpo', 'base'
        
        # Show to human evaluator
        print(f"\nPrompt: {prompt}\n")
        print(f"Response A:\n{response_a}\n")
        print(f"Response B:\n{response_b}\n")
        
        preference = input("Which is better? (A/B/Tie): ").upper()
        
        if preference == 'A':
            winner = label_a
        elif preference == 'B':
            winner = label_b
        else:
            winner = 'tie'
        
        results.append({
            'prompt': prompt,
            'winner': winner
        })
    
    # Calculate win rate
    dpo_wins = sum(1 for r in results if r['winner'] == 'dpo')
    win_rate = dpo_wins / len(results)
    
    print(f"\nDPO Model Win Rate: {win_rate:.1%}")
    
    return results
```

---

## Risks & Challenges

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Overfitting | High | Regular evaluation, early stopping |
| Mode collapse | Medium | Diverse dataset, entropy regularization |
| Catastrophic forgetting | Medium | Freeze layers, conservative LR |
| OOM errors | Medium | Gradient checkpointing, QLoRA |

### Data Quality Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Biased preferences | High | Diverse examples, bias detection |
| Low-quality synthetic data | Medium | Human validation, filtering |
| Insufficient data | High | Active learning, data augmentation |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| High compute cost | Medium | QLoRA, cloud spot instances |
| Long training time | Low | Smaller model, better data |
| Model versioning | Low | MLflow, DVC for tracking |

---

## Cost Estimate

### One-Time Costs

**Initial Development** (12 weeks):
- Research & design: 2 weeks
- Data collection UI: 2 weeks
- Training infrastructure: 6 weeks
- Integration & testing: 2 weeks

**Total Engineering**: ~$0 (self-implementation)

### Recurring Costs

**Data Collection**:
- User feedback: Free (built-in)
- Synthetic generation: $0
- Dataset curation: 2 hours/week

**Training** (monthly):
- Cloud GPU (QLoRA): $30-50
- Storage: $5
- Monitoring (W&B): Free tier

**Inference**:
- Self-hosted: $0
- Cloud API: $0.50-2.00/1M tokens

**Total Monthly**: ~$35-55

---

## Success Criteria

### Phase 1 Success (Data Collection)
- [ ] Collect 1000+ preference pairs
- [ ] 80%+ user feedback quality
- [ ] Balanced chosen/rejected distribution
- [ ] Pass dataset validation checks

### Phase 2 Success (Training)
- [ ] 70%+ preference accuracy on eval set
- [ ] <10% perplexity increase vs base model
- [ ] Training completes in <24 hours
- [ ] Model size <5GB (with QLoRA)

### Phase 3 Success (Deployment)
- [ ] 60%+ win rate in human eval
- [ ] <200ms inference latency
- [ ] User satisfaction >80%
- [ ] No major regressions

---

## Next Steps

1. **Community RFC** (2 weeks)
   - Gather feedback on DPO approach
   - Validate use cases
   - Prioritize features

2. **Prototype** (4 weeks)
   - Build preference collector UI
   - Generate 500 synthetic pairs
   - Train proof-of-concept on small model

3. **Alpha Testing** (4 weeks)
   - Deploy to 10 beta users
   - Collect real preferences
   - Measure improvements

4. **Full Implementation** (12 weeks)
   - Follow plan above
   - Train production model
   - Integrate into main app

5. **Beta Release** (v2.5-beta)
   - Limited rollout
   - Collect metrics
   - Iterate on feedback

---

## References

- **Paper**: [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- **Code**: [DPO Trainer (Hugging Face)](https://github.com/huggingface/trl)
- **Guide**: [Fine-tuning with QLoRA](https://huggingface.co/blog/4bit-transformers-bitsandbytes)
- **Datasets**: [OpenAssistant Conversations](https://huggingface.co/datasets/OpenAssistant/oasst1)

---

**Status**: 🔬 Research Complete  
**Next Action**: Community RFC & Prototype  
**Estimated Timeline**: 16-20 weeks to v2.5 beta  
**GitHub Issue**: [#107](https://github.com/B0LK13/obsidian-agent/issues/107)
