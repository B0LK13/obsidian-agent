#!/usr/bin/env python3
"""
Prompt Engineering Suite
Advanced prompt techniques:
- Chain-of-Thought prompting
- Few-shot prompting
- System prompt optimization
- Prompt templates and chaining
- Dynamic prompt construction
- Output format specification
"""

import json
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from string import Template
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('prompt_engineering')


class PromptStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    SELF_CONSISTENCY = "self_consistency"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT = "react"


@dataclass
class Example:
    """A few-shot example"""
    input: str
    output: str
    reasoning: str = ""  # For CoT examples
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """A reusable prompt template"""
    name: str
    template: str
    strategy: PromptStrategy
    examples: List[Example] = field(default_factory=list)
    output_format: Optional[str] = None
    system_context: str = ""
    
    def render(self, **kwargs) -> str:
        """Render the template with variables"""
        t = Template(self.template)
        return t.safe_substitute(**kwargs)
    
    def build_few_shot(self, n_examples: int = 3) -> str:
        """Build few-shot prompt with examples"""
        prompt_parts = []
        
        if self.system_context:
            prompt_parts.append(self.system_context)
        
        # Add examples
        for ex in self.examples[:n_examples]:
            if self.strategy == PromptStrategy.CHAIN_OF_THOUGHT and ex.reasoning:
                prompt_parts.append(f"Q: {ex.input}\nA: {ex.reasoning}\nTherefore: {ex.output}")
            else:
                prompt_parts.append(f"Q: {ex.input}\nA: {ex.output}")
        
        # Add template
        prompt_parts.append(self.template)
        
        # Add output format
        if self.output_format:
            prompt_parts.append(f"\nOutput format: {self.output_format}")
        
        return "\n\n".join(prompt_parts)


class PromptLibrary:
    """Library of pre-built prompt templates"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default prompt templates"""
        
        # 1. Question Answering with CoT
        self.register(PromptTemplate(
            name="qa_cot",
            template="Question: $question\nAnswer:",
            strategy=PromptStrategy.CHAIN_OF_THOUGHT,
            system_context="Answer the question step by step, showing your reasoning.",
            output_format="Step-by-step reasoning followed by the final answer.",
            examples=[
                Example(
                    input="What is 15 + 27?",
                    output="42",
                    reasoning="First, add 15 + 20 = 35. Then add 35 + 7 = 42."
                ),
                Example(
                    input="If a train travels 60 km/h for 2.5 hours, how far does it go?",
                    output="150 km",
                    reasoning="Distance = Speed × Time. So 60 km/h × 2.5 h = 150 km."
                )
            ]
        ))
        
        # 2. Summarization
        self.register(PromptTemplate(
            name="summarize",
            template="Summarize the following text in $max_words words:\n\n$text\n\nSummary:",
            strategy=PromptStrategy.ZERO_SHOT,
            system_context="You are a skilled summarizer. Create concise, accurate summaries.",
            output_format="A concise summary capturing the main points."
        ))
        
        # 3. Code Generation
        self.register(PromptTemplate(
            name="code_generate",
            template="Write $language code to $task:\n\n```$language\n",
            strategy=PromptStrategy.FEW_SHOT,
            system_context="You are an expert programmer. Write clean, efficient, well-documented code.",
            output_format="Code block with comments explaining the solution.",
            examples=[
                Example(
                    input="write Python code to reverse a list",
                    output="def reverse_list(lst):\n    return lst[::-1]"
                )
            ]
        ))
        
        # 4. Entity Extraction
        self.register(PromptTemplate(
            name="extract_entities",
            template="Extract all named entities from the following text:\n\n$text\n\nEntities (in JSON format):",
            strategy=PromptStrategy.ZERO_SHOT,
            system_context="Extract named entities (people, organizations, locations) from text.",
            output_format='{"entities": [{"text": "...", "type": "...", "start": 0, "end": 10}]}'
        ))
        
        # 5. Classification
        self.register(PromptTemplate(
            name="classify",
            template="Classify the following text into one of these categories: $categories\n\nText: $text\n\nCategory:",
            strategy=PromptStrategy.FEW_SHOT,
            system_context="Classify text accurately into the given categories.",
            output_format="The category name only.",
            examples=[
                Example(
                    input="The stock market crashed today.",
                    output="Finance"
                ),
                Example(
                    input="New vaccine shows promising results.",
                    output="Health"
                )
            ]
        ))
        
        # 6. ReAct Prompt
        self.register(PromptTemplate(
            name="react",
            template="$question",
            strategy=PromptStrategy.REACT,
            system_context="""Solve problems by alternating between Thought and Action.
Thought: Reason about what to do next
Action: Take an action using available tools
Observation: Observe the result
... (repeat as needed)
Final Answer: Provide the final answer""",
            output_format="Thought/Action/Observation pattern followed by Final Answer."
        ))
        
        # 7. Note Analysis
        self.register(PromptTemplate(
            name="analyze_note",
            template="Analyze the following note and provide insights:\n\nTitle: $title\nContent:\n$content\n\nAnalysis:",
            strategy=PromptStrategy.CHAIN_OF_THOUGHT,
            system_context="""You are a knowledge management expert. Analyze notes to extract:
- Key concepts
- Connections to other ideas
- Action items
- Questions raised""",
            output_format="Structured analysis with sections for concepts, connections, actions, and questions."
        ))
        
        # 8. Knowledge Graph Extraction
        self.register(PromptTemplate(
            name="extract_knowledge",
            template="Extract entities and relationships from:\n\n$text\n\nOutput as JSON:",
            strategy=PromptStrategy.ZERO_SHOT,
            system_context="Extract entities and their relationships from text.",
            output_format='{"entities": [{"name": "...", "type": "..."}], "relationships": [{"source": "...", "relation": "...", "target": "..."}]}'
        ))
    
    def register(self, template: PromptTemplate):
        """Register a new template"""
        self.templates[template.name] = template
        logger.info(f"Registered prompt template: {template.name}")
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.templates.keys())


class DynamicPromptBuilder:
    """
    Dynamically builds prompts based on context and requirements
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.library = PromptLibrary()
    
    def build(self, task_type: str, context: Dict[str, Any], 
              constraints: Dict[str, Any] = None) -> str:
        """
        Build an optimal prompt for the given task
        """
        constraints = constraints or {}
        
        # Get base template
        template = self.library.get(task_type)
        if not template:
            # Build generic prompt
            return self._build_generic_prompt(task_type, context, constraints)
        
        # Customize based on constraints
        if constraints.get('max_tokens'):
            context['max_words'] = constraints['max_tokens'] // 5  # Rough estimate
        
        # Render template
        prompt = template.render(**context)
        
        # Add examples if few-shot
        if template.strategy == PromptStrategy.FEW_SHOT:
            prompt = template.build_few_shot(n_examples=constraints.get('n_examples', 3))
        
        return prompt
    
    def _build_generic_prompt(self, task: str, context: Dict, constraints: Dict) -> str:
        """Build a generic prompt when no template exists"""
        parts = []
        
        # Task description
        parts.append(f"Task: {task}")
        
        # Context
        for key, value in context.items():
            parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Constraints
        if constraints:
            parts.append("\nConstraints:")
            for key, value in constraints.items():
                parts.append(f"- {key}: {value}")
        
        return "\n\n".join(parts)
    
    def optimize_prompt(self, original_prompt: str, 
                        performance_history: List[Dict]) -> str:
        """
        Optimize a prompt based on performance history
        """
        if not self.llm or not performance_history:
            return original_prompt
        
        # Analyze what worked and what didn't
        successful = [h for h in performance_history if h.get('success', False)]
        unsuccessful = [h for h in performance_history if not h.get('success', False)]
        
        optimization_prompt = f"""Optimize the following prompt based on performance data:

Original Prompt:
{original_prompt}

Successful examples ({len(successful)}):
{json.dumps(successful[:3], indent=2)}

Unsuccessful examples ({len(unsuccessful)}):
{json.dumps(unsuccessful[:3], indent=2)}

Provide an optimized version of the prompt that addresses the issues:
"""
        
        optimized = self.llm.chat([{"role": "user", "content": optimization_prompt}])
        return optimized


class OutputParser:
    """
    Parse and validate LLM outputs
    """
    
    def __init__(self):
        self.parsers: Dict[str, Callable] = {
            'json': self._parse_json,
            'list': self._parse_list,
            'key_value': self._parse_key_value,
            'code': self._parse_code,
        }
    
    def parse(self, output: str, format_type: str = 'text') -> Dict:
        """Parse output into structured format"""
        parser = self.parsers.get(format_type, self._parse_text)
        
        try:
            return {
                'success': True,
                'data': parser(output),
                'raw': output
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw': output
            }
    
    def _parse_json(self, output: str) -> Any:
        """Extract and parse JSON from output"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find any JSON object
        json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try parsing entire output
        return json.loads(output)
    
    def _parse_list(self, output: str) -> List[str]:
        """Parse numbered or bulleted list"""
        items = []
        
        # Numbered list
        numbered = re.findall(r'^\d+[.\)]\s*(.+)$', output, re.MULTILINE)
        if numbered:
            items = numbered
        else:
            # Bulleted list
            bullets = re.findall(r'^[-*]\s*(.+)$', output, re.MULTILINE)
            items = bullets
        
        return [item.strip() for item in items if item.strip()]
    
    def _parse_key_value(self, output: str) -> Dict[str, str]:
        """Parse key: value format"""
        result = {}
        for line in output.split('\n'):
            match = re.match(r'^([^:]+):\s*(.+)$', line)
            if match:
                key, value = match.groups()
                result[key.strip()] = value.strip()
        return result
    
    def _parse_code(self, output: str) -> Dict:
        """Extract code blocks"""
        code_blocks = re.findall(r'```(\w+)?\s*\n(.*?)\n```', output, re.DOTALL)
        
        if code_blocks:
            return {
                'language': code_blocks[0][0] or 'unknown',
                'code': code_blocks[0][1].strip()
            }
        
        # Try to find indented code
        lines = output.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                code_lines.append(line.strip())
                in_code = True
            elif in_code and line.strip() == '':
                continue
            elif in_code:
                break
        
        return {'language': 'unknown', 'code': '\n'.join(code_lines)}
    
    def _parse_text(self, output: str) -> str:
        """Default text parser"""
        return output.strip()


class PromptChain:
    """
    Chain multiple prompts together for complex tasks
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.steps: List[Dict] = []
    
    def add_step(self, name: str, template: str, 
                 output_key: str, input_mapping: Dict = None):
        """Add a step to the chain"""
        self.steps.append({
            'name': name,
            'template': template,
            'output_key': output_key,
            'input_mapping': input_mapping or {}
        })
    
    def execute(self, initial_input: Dict) -> Dict:
        """Execute the chain"""
        context = initial_input.copy()
        results = {'steps': []}
        
        for step in self.steps:
            # Prepare input
            step_input = {}
            for key, value_key in step['input_mapping'].items():
                step_input[key] = context.get(value_key, value_key)
            
            # Render prompt
            prompt_template = Template(step['template'])
            prompt = prompt_template.safe_substitute(**step_input)
            
            # Execute
            output = self.llm.chat([{'role': 'user', 'content': prompt}])
            
            # Store result
            context[step['output_key']] = output
            results['steps'].append({
                'name': step['name'],
                'input': step_input,
                'output': output
            })
        
        results['final_output'] = context
        return results


# Example usage
if __name__ == '__main__':
    # Create library
    library = PromptLibrary()
    
    print("Available templates:")
    for name in library.list_templates():
        print(f"  - {name}")
    
    # Use a template
    template = library.get("qa_cot")
    prompt = template.render(question="What is the capital of France?")
    print(f"\nGenerated prompt:\n{prompt}")
    
    # Test output parsing
    parser = OutputParser()
    
    test_output = """
    Here are the items:
    1. First item
    2. Second item
    3. Third item
    """
    
    result = parser.parse(test_output, 'list')
    print(f"\nParsed list: {result}")
