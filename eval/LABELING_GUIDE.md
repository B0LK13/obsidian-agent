# Golden Dataset Labeling Guide v1.0

## Overview
This guide defines the labeling standards for the Obsidian AI Agent golden dataset. Consistent, high-quality labels are essential for meaningful evaluation metrics and agent improvement.

---

## Label Fields

### 1. **id** (required)
- **Format**: `[type_prefix][number]`  
- **Type prefixes**: `t` (technical), `p` (project), `r` (research), `m` (maintenance)
- **Example**: `t001`, `p042`, `r015`, `m003`
- **Rules**:
  - Sequential numbering within each type
  - Zero-padded to 3 digits
  - No duplicates across dataset

### 2. **query** (required)
- **Format**: Natural language question or command
- **Length**: 5-150 characters recommended
- **Rules**:
  - Use realistic user phrasing (not technical jargon unless appropriate)
  - Include context where necessary
  - Avoid ambiguous pronouns without referents
- **Good examples**:
  - ✅ "How do I implement authentication in my React app?"
  - ✅ "Find notes with broken links"
  - ✅ "What are the key decisions from Q1 planning meeting?"
- **Bad examples**:
  - ❌ "auth stuff?" (too vague)
  - ❌ "Implement the thing we discussed" (unclear reference)
  - ❌ "Give me some info about that topic" (no specifics)

### 3. **type** (required)
- **Values**: `technical | project | research | maintenance`
- **Definitions**:
  - **technical**: Programming, debugging, technical how-to questions
  - **project**: Project management, status, planning, team coordination
  - **research**: Learning, exploration, concept understanding, knowledge synthesis
  - **maintenance**: Vault organization, cleanup, health checks, structure optimization
- **Edge cases**:
  - If query spans multiple types, use **primary intent**
  - Example: "Create a project plan for learning React" → `project` (planning is primary action)

### 4. **difficulty** (required)
- **Values**: `easy | medium | hard`
- **Criteria**:

#### Easy
- Answer available in 1-2 notes
- No disambiguation needed
- Clear, direct path to response
- Examples: "What is REST API?", "Find orphan notes"

#### Medium
- Requires 2-5 notes
- Some synthesis or inference needed
- May need basic disambiguation
- Examples**: "Best practices for API error handling", "Track progress on API migration"

#### Hard
- Requires 5+ notes or complex reasoning
- Significant synthesis, analysis, or disambiguation
- May involve conflicting information
- No existing answer (research/creation needed)
- Examples**: "Analyze evolution of my thinking on AI", "Debug memory leak in React app"

### 5. **expected_notes** (required)
- **Format**: Array of note names or topics
- **Purpose**: Ground truth for retrieval evaluation
- **Rules**:
  - List actual note titles if known, or likely topics
  - Empty array `[]` for maintenance queries (no specific notes)
  - Include 1-5 most relevant notes
- **Examples**:
  - `["React", "Authentication"]` for auth question
  - `["Mobile App", "Redesign"]` for project status
  - `[]` for "Find broken links" (no specific notes)

### 6. **expected_confidence** (required)
- **Values**: `high | medium | low`
- **Criteria**:
  - **high**: Answer definitively available in vault, clear evidence
  - **medium**: Partial information available, some inference needed
  - **low**: Little/no information in vault, requires creation or external knowledge
- **Not the same as difficulty**: A hard query can have high confidence if evidence exists

### 7. **expected_next_step** (required)
- **Format**: Single sentence describing the immediate action
- **Purpose**: Ground truth for forward motion evaluation
- **Rules**:
  - Must be specific and actionable
  - Should indicate action, owner (implied user or agent), and outcome
  - Use imperative or infinitive form
- **Good examples**:
  - ✅ "Search vault for auth patterns or create guide"
  - ✅ "Find retro notes and summarize"
  - ✅ "Request code snippet or create checklist"
- **Bad examples**:
  - ❌ "Do something" (not specific)
  - ❌ "Look into it" (no clear outcome)
  - ❌ "It depends on the context" (no action)

### 8. **expected_answer_outline** (optional)
- **Format**: Brief bullet points of expected answer structure
- **Purpose**: Faithfulness evaluation (does answer match expected content?)
- **Example**:
  ```
  - Explain JWT token structure
  - Describe login/refresh flow
  - Mention security best practices
  ```
- **When to include**: For queries with well-defined expected answers

### 9. **required_evidence_count** (optional, default: 1)
- **Format**: Integer (0-5)
- **Purpose**: Minimum number of vault sources that should be cited
- **Rules**:
  - `0`: Maintenance/procedural queries (no citations needed)
  - `1`: Simple lookups
  - `2-3`: Standard synthesis
  - `4-5`: Deep research/analysis
- **Example**: "Explain SOLID principles" → `2` (expect 2+ source notes cited)

### 10. **allowed_source_scope** (optional, default: vault)
- **Values**: `project | vault | global`
- **Purpose**: Define acceptable evidence scope
- **Definitions**:
  - **project**: Only current project notes
  - **vault**: Entire user vault
  - **global**: Vault + external knowledge
- **Example**: "Debug TypeError in validation function" → `project` (context-specific)

---

## Query Type Distribution

### Target Balance (per 50 queries)
- **Easy**: 15-20 queries (30-40%)
- **Medium**: 20-25 queries (40-50%)
- **Hard**: 10-15 queries (20-30%)

### Special Query Categories (include at least):
- **No-answer queries**: 20 total (5 per type) — queries where vault has no relevant information
  - Label with `expected_confidence: low`, `expected_notes: []`
  - Example: "I want to learn about quantum computing" (no quantum notes in vault)

- **Conflicting-evidence queries**: 20 total (5 per type) — queries where notes contradict
  - Label with `expected_confidence: medium`, note conflict in expected_answer_outline
  - Example: "What is the best state management for React?" (notes have differing opinions)

---

## Quality Assurance Checklist

Before finalizing a query label, verify:

- [ ] **id** follows naming convention and is unique
- [ ] **query** is realistic, clear, and grammatically correct
- [ ] **type** matches primary intent
- [ ] **difficulty** aligns with criteria (retrieval + synthesis complexity)
- [ ] **expected_notes** lists actual/likely notes (or [] for maintenance)
- [ ] **expected_confidence** reflects vault evidence availability
- [ ] **expected_next_step** is specific and actionable
- [ ] **required_evidence_count** makes sense for query type
- [ ] **allowed_source_scope** is appropriate for context
- [ ] Label is consistent with similar queries in the dataset

---

## Versioning & Changelog

### v1.0 (2026-02-07)
- Initial labeling guide
- Defined all required and optional fields
- Established quality criteria
- Set distribution targets

### Future Versions
- Track schema changes
- Document relabeling rationale
- Maintain backward compatibility notes

---

## Examples (Fully Labeled)

### Example 1: Technical (Easy)
```json
{
  "id": "t004",
  "query": "Explain Map vs WeakMap in JavaScript",
  "type": "technical",
  "difficulty": "easy",
  "expected_notes": ["JavaScript"],
  "expected_confidence": "medium",
  "expected_next_step": "Search vault or create comparison",
  "expected_answer_outline": "- Map stores any key types\n- WeakMap only allows objects as keys\n- WeakMap allows garbage collection\n- Use cases for each",
  "required_evidence_count": 1,
  "allowed_source_scope": "vault"
}
```

### Example 2: Project (Hard)
```json
{
  "id": "p015",
  "query": "Review quarterly OKRs progress",
  "type": "project",
  "difficulty": "hard",
  "expected_notes": ["OKRs", "Progress"],
  "expected_confidence": "medium",
  "expected_next_step": "Find OKR docs and analyze progress",
  "required_evidence_count": 3,
  "allowed_source_scope": "project"
}
```

### Example 3: Maintenance (Easy)
```json
{
  "id": "m001",
  "query": "Find notes with broken links",
  "type": "maintenance",
  "difficulty": "easy",
  "expected_notes": [],
  "expected_confidence": "high",
  "expected_next_step": "Scan for broken [[links]]",
  "required_evidence_count": 0,
  "allowed_source_scope": "vault"
}
```

### Example 4: Research (Hard, No-Answer)
```json
{
  "id": "r001",
  "query": "I want to learn about quantum computing",
  "type": "research",
  "difficulty": "medium",
  "expected_notes": ["Quantum"],
  "expected_confidence": "low",
  "expected_next_step": "Create learning path or search notes",
  "expected_answer_outline": "- Acknowledge no existing notes\n- Offer to create structure\n- Suggest starting resources",
  "required_evidence_count": 1,
  "allowed_source_scope": "global"
}
```

---

## Contact & Updates

- **Maintainer**: Obsidian AI Agent Eval Team
- **Last Updated**: 2026-02-07
- **Next Review**: After 200-query milestone

For questions or proposed changes, refer to project documentation.
