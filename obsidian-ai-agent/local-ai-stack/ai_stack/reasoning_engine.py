#!/usr/bin/env python3
"""
Reasoning and Planning Engine
Implements advanced reasoning capabilities:
- Chain-of-Thought (CoT) reasoning
- ReAct (Reasoning + Acting) pattern
- Tree of Thoughts (ToT)
- Multi-step planning
- Self-reflection and correction
"""

import json
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('reasoning_engine')


class ReasoningStrategy(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    DIRECT = "direct"


@dataclass
class Thought:
    """A single thought in the reasoning process"""
    content: str
    thought_type: str  # reasoning, action, observation, conclusion
    step_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Plan:
    """A plan consisting of multiple steps"""
    goal: str
    steps: List[Dict[str, Any]]
    current_step: int = 0
    completed: bool = False
    
    def get_current_step(self) -> Optional[Dict]:
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def advance(self):
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.completed = True
    
    def to_dict(self) -> Dict:
        return {
            'goal': self.goal,
            'steps': self.steps,
            'current_step': self.current_step,
            'progress': f"{self.current_step}/{len(self.steps)}",
            'completed': self.completed
        }


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning process"""
    query: str
    strategy: ReasoningStrategy
    thoughts: List[Thought]
    final_answer: str = ""
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'query': self.query,
            'strategy': self.strategy.value,
            'thoughts': [
                {
                    'step': t.step_number,
                    'type': t.thought_type,
                    'content': t.content,
                    'timestamp': t.timestamp
                }
                for t in self.thoughts
            ],
            'final_answer': self.final_answer,
            'execution_time_ms': self.execution_time_ms
        }


class ChainOfThoughtReasoner:
    """
    Chain-of-Thought reasoning: Let the model think step by step
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def reason(self, query: str, context: str = "", max_steps: int = 10) -> ReasoningTrace:
        """
        Perform step-by-step reasoning
        """
        import time
        start_time = time.time()
        
        thoughts = []
        
        # Initial prompt for CoT
        system_prompt = """You are a helpful assistant that thinks step by step.
When answering questions, break down your thinking into clear steps.
Format your response as:
Step 1: [your reasoning]
Step 2: [your reasoning]
...
Final Answer: [your conclusion]
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]
        
        # Get reasoning from LLM
        response = self.llm.chat(messages)
        
        # Parse the response into steps
        steps = self._parse_steps(response)
        
        for i, (step_type, content) in enumerate(steps):
            thoughts.append(Thought(
                content=content,
                thought_type=step_type,
                step_number=i + 1
            ))
        
        # Extract final answer
        final_answer = self._extract_final_answer(response)
        
        execution_time = (time.time() - start_time) * 1000
        
        return ReasoningTrace(
            query=query,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            thoughts=thoughts,
            final_answer=final_answer,
            execution_time_ms=execution_time
        )
    
    def _parse_steps(self, text: str) -> List[tuple]:
        """Parse step-by-step reasoning from text"""
        steps = []
        
        # Pattern: "Step N: content" or "N. content"
        step_pattern = r'(?:Step\s*)?(\d+)[:.)]\s*(.+?)(?=\n(?:Step\s*)?\d+[:.)]|Final Answer:|$)'
        matches = list(re.finditer(step_pattern, text, re.DOTALL | re.IGNORECASE))
        
        for match in matches:
            content = match.group(2).strip()
            steps.append(("reasoning", content))
        
        return steps if steps else [("reasoning", text)]
    
    def _extract_final_answer(self, text: str) -> str:
        """Extract the final answer from the response"""
        patterns = [
            r'Final Answer[:\s]+(.+?)(?=\n\n|$)',
            r'Conclusion[:\s]+(.+?)(?=\n\n|$)',
            r'Answer[:\s]+(.+?)(?=\n\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Return last paragraph if no explicit answer
        paragraphs = text.split('\n\n')
        return paragraphs[-1].strip() if paragraphs else text


class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent
    Alternates between thinking and taking actions
    """
    
    def __init__(self, llm_client, tool_executor):
        self.llm = llm_client
        self.tools = tool_executor
        self.max_iterations = 10
    
    def run(self, query: str) -> ReasoningTrace:
        """
        Run ReAct loop: Thought -> Action -> Observation -> ...
        """
        import time
        start_time = time.time()
        
        thoughts = []
        iteration = 0
        
        system_prompt = """You are an AI assistant that can use tools to solve problems.
Follow this format:
Thought: [your reasoning about what to do]
Action: [tool_name]([param]=[value])
Observation: [result of the action]
...
Final Answer: [your answer]

Available tools will be provided in the context."""
        
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        while iteration < self.max_iterations:
            # Get next thought/action from LLM
            response = self.llm.chat(conversation)
            
            # Parse thought and action
            thought, action, action_input = self._parse_react_response(response)
            
            if thought:
                thoughts.append(Thought(
                    content=thought,
                    thought_type="reasoning",
                    step_number=iteration + 1
                ))
            
            # Check if we have a final answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                
                execution_time = (time.time() - start_time) * 1000
                return ReasoningTrace(
                    query=query,
                    strategy=ReasoningStrategy.REACT,
                    thoughts=thoughts,
                    final_answer=final_answer,
                    execution_time_ms=execution_time
                )
            
            # Execute action if present
            if action and action_input is not None:
                thoughts.append(Thought(
                    content=f"Action: {action}({action_input})",
                    thought_type="action",
                    step_number=iteration + 1
                ))
                
                # Execute tool
                try:
                    result = self.tools.execute(action, action_input)
                    observation = str(result) if result else "No result"
                except Exception as e:
                    observation = f"Error: {str(e)}"
                
                thoughts.append(Thought(
                    content=f"Observation: {observation}",
                    thought_type="observation",
                    step_number=iteration + 1
                ))
                
                # Add to conversation
                conversation.append({"role": "assistant", "content": response})
                conversation.append({"role": "system", "content": f"Observation: {observation}"})
            else:
                # No action, just add response
                conversation.append({"role": "assistant", "content": response})
            
            iteration += 1
        
        # Max iterations reached
        execution_time = (time.time() - start_time) * 1000
        return ReasoningTrace(
            query=query,
            strategy=ReasoningStrategy.REACT,
            thoughts=thoughts,
            final_answer="Maximum iterations reached without finding an answer.",
            execution_time_ms=execution_time
        )
    
    def _parse_react_response(self, text: str) -> tuple:
        """Parse Thought and Action from ReAct response"""
        thought = None
        action = None
        action_input = None
        
        # Extract thought
        thought_match = re.search(r'Thought[:\s]+(.+?)(?=Action:|Final Answer:|$)', 
                                   text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        
        # Extract action
        action_match = re.search(r'Action[:\s]+(\w+)\(([^)]*)\)', 
                                  text, re.DOTALL | re.IGNORECASE)
        if action_match:
            action = action_match.group(1)
            action_input = action_match.group(2)
        
        return thought, action, action_input


class TreeOfThoughts:
    """
    Tree of Thoughts: Explore multiple reasoning paths
    """
    
    def __init__(self, llm_client, branching_factor: int = 3, max_depth: int = 3):
        self.llm = llm_client
        self.branching_factor = branching_factor
        self.max_depth = max_depth
    
    @dataclass
    class Node:
        thought: str
        parent: Optional['TreeOfThoughts.Node']
        children: List['TreeOfThoughts.Node'] = field(default_factory=list)
        score: float = 0.0
        depth: int = 0
        is_terminal: bool = False
    
    def solve(self, problem: str) -> ReasoningTrace:
        """
        Explore multiple reasoning paths and select the best
        """
        import time
        start_time = time.time()
        
        thoughts = []
        
        # Generate initial thoughts (root nodes)
        root_thoughts = self._generate_thoughts(problem, None, self.branching_factor)
        
        # Build tree using BFS
        current_level = [self.Node(t, None, [], 0.5, 0) for t in root_thoughts]
        all_nodes = current_level.copy()
        
        for depth in range(self.max_depth):
            next_level = []
            
            for node in current_level:
                # Generate children
                child_thoughts = self._generate_thoughts(problem, node.thought, self.branching_factor)
                
                for ct in child_thoughts:
                    child = self.Node(ct, node, [], 0.0, depth + 1)
                    node.children.append(child)
                    next_level.append(child)
                    all_nodes.append(child)
            
            current_level = next_level
            if not current_level:
                break
        
        # Evaluate all paths
        self._evaluate_nodes(all_nodes, problem)
        
        # Find best path
        best_leaf = max([n for n in all_nodes if not n.children], 
                        key=lambda x: x.score)
        
        # Trace back path
        path = []
        node = best_leaf
        while node:
            path.append(node)
            node = node.parent
        
        path.reverse()
        
        # Build reasoning trace
        for i, node in enumerate(path):
            thoughts.append(Thought(
                content=node.thought,
                thought_type="reasoning",
                step_number=i + 1,
                metadata={'score': node.score}
            ))
        
        execution_time = (time.time() - start_time) * 1000
        
        return ReasoningTrace(
            query=problem,
            strategy=ReasoningStrategy.TREE_OF_THOUGHTS,
            thoughts=thoughts,
            final_answer=best_leaf.thought,
            execution_time_ms=execution_time
        )
    
    def _generate_thoughts(self, problem: str, current_thought: Optional[str], 
                           n: int) -> List[str]:
        """Generate n possible next thoughts"""
        prompt = f"Problem: {problem}\n"
        if current_thought:
            prompt += f"Current thought: {current_thought}\n"
        prompt += f"Generate {n} different possible next steps or approaches:\n"
        
        response = self.llm.chat([{"role": "user", "content": prompt}])
        
        # Parse numbered list
        thoughts = []
        for line in response.split('\n'):
            match = re.match(r'^\d+[.\)]\s*(.+)', line.strip())
            if match:
                thoughts.append(match.group(1))
        
        return thoughts if thoughts else [response]
    
    def _evaluate_nodes(self, nodes: List['Node'], problem: str):
        """Score each node for quality"""
        for node in nodes:
            if not node.children:  # Leaf nodes
                prompt = f"Problem: {problem}\nProposed solution: {node.thought}\nRate the quality of this solution (1-10):"
                
                try:
                    response = self.llm.chat([{"role": "user", "content": prompt}])
                    # Extract number
                    match = re.search(r'(\d+)', response)
                    if match:
                        node.score = float(match.group(1)) / 10.0
                except:
                    node.score = 0.5


class Planner:
    """
    Multi-step planning for complex tasks
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def create_plan(self, goal: str, available_tools: List[str]) -> Plan:
        """
        Create a step-by-step plan to achieve a goal
        """
        prompt = f"""Create a step-by-step plan to achieve the following goal:
Goal: {goal}

Available tools: {', '.join(available_tools)}

Break this down into clear, actionable steps. Format as:
Step 1: [action]
Step 2: [action]
..."""
        
        response = self.llm.chat([{"role": "user", "content": prompt}])
        
        # Parse steps
        steps = []
        for line in response.split('\n'):
            match = re.match(r'(?:Step\s*)?(\d+)[:.\)]\s*(.+)', line.strip())
            if match:
                steps.append({
                    'number': int(match.group(1)),
                    'description': match.group(2),
                    'status': 'pending'
                })
        
        return Plan(goal=goal, steps=steps)
    
    def execute_plan(self, plan: Plan, executor: Callable) -> Dict:
        """
        Execute a plan step by step
        """
        results = []
        
        while not plan.completed:
            step = plan.get_current_step()
            if not step:
                break
            
            # Execute step
            try:
                result = executor(step['description'])
                step['status'] = 'completed'
                step['result'] = result
            except Exception as e:
                step['status'] = 'failed'
                step['error'] = str(e)
            
            results.append(step.copy())
            plan.advance()
        
        return {
            'plan': plan.to_dict(),
            'results': results,
            'success': all(r.get('status') == 'completed' for r in results)
        }


class SelfReflectiveAgent:
    """
    Agent that can reflect on and correct its own reasoning
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def solve_with_reflection(self, problem: str, max_reflections: int = 3) -> Dict:
        """
        Solve a problem with iterative self-reflection and correction
        """
        attempts = []
        
        for attempt in range(max_reflections):
            # Generate initial solution
            if attempt == 0:
                solution = self._generate_solution(problem)
            else:
                # Incorporate critique from previous attempt
                critique = attempts[-1]['critique']
                solution = self._revise_solution(problem, attempts[-1]['solution'], critique)
            
            # Self-critique
            critique = self._critique_solution(problem, solution)
            
            attempt_data = {
                'attempt': attempt + 1,
                'solution': solution,
                'critique': critique,
                'confidence': self._assess_confidence(critique)
            }
            attempts.append(attempt_data)
            
            # Check if solution is good enough
            if attempt_data['confidence'] > 0.8:
                break
        
        # Select best solution
        best = max(attempts, key=lambda x: x['confidence'])
        
        return {
            'final_solution': best['solution'],
            'final_confidence': best['confidence'],
            'attempts': attempts,
            'num_reflections': len(attempts) - 1
        }
    
    def _generate_solution(self, problem: str) -> str:
        """Generate initial solution"""
        prompt = f"Solve this problem: {problem}\nProvide your solution:"
        return self.llm.chat([{"role": "user", "content": prompt}])
    
    def _critique_solution(self, problem: str, solution: str) -> str:
        """Critique the solution"""
        prompt = f"""Problem: {problem}
Proposed solution: {solution}

Critique this solution. What are its strengths and weaknesses? 
Are there any errors or areas for improvement?"""
        
        return self.llm.chat([{"role": "user", "content": prompt}])
    
    def _revise_solution(self, problem: str, previous_solution: str, critique: str) -> str:
        """Revise solution based on critique"""
        prompt = f"""Problem: {problem}
Previous solution: {previous_solution}
Critique: {critique}

Based on this critique, provide an improved solution:"""
        
        return self.llm.chat([{"role": "user", "content": prompt}])
    
    def _assess_confidence(self, critique: str) -> float:
        """Assess confidence based on critique"""
        # Simple heuristic: fewer negative words = higher confidence
        negative_indicators = ['error', 'wrong', 'incorrect', 'problem', 'issue', 'weakness', 'missing']
        positive_indicators = ['correct', 'good', 'strong', 'comprehensive', 'accurate']
        
        critique_lower = critique.lower()
        negative_count = sum(1 for w in negative_indicators if w in critique_lower)
        positive_count = sum(1 for w in positive_indicators if w in critique_lower)
        
        # Base confidence
        confidence = 0.5 + (positive_count - negative_count) * 0.1
        return max(0.0, min(1.0, confidence))


class ReasoningOrchestrator:
    """
    Orchestrates different reasoning strategies based on problem type
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.cot_reasoner = ChainOfThoughtReasoner(llm_client)
        self.tot_reasoner = TreeOfThoughts(llm_client)
        self.planner = Planner(llm_client)
        self.reflector = SelfReflectiveAgent(llm_client)
    
    def solve(self, problem: str, complexity_hint: Optional[str] = None) -> Dict:
        """
        Automatically select and apply best reasoning strategy
        """
        # Analyze problem to select strategy
        if not complexity_hint:
            complexity_hint = self._analyze_complexity(problem)
        
        logger.info(f"Solving problem with complexity: {complexity_hint}")
        
        if complexity_hint == "simple":
            # Direct or CoT
            trace = self.cot_reasoner.reason(problem)
            return {
                'strategy': 'chain_of_thought',
                'result': trace.final_answer,
                'reasoning_trace': trace.to_dict()
            }
        
        elif complexity_hint == "exploratory":
            # Tree of Thoughts
            trace = self.tot_reasoner.solve(problem)
            return {
                'strategy': 'tree_of_thoughts',
                'result': trace.final_answer,
                'reasoning_trace': trace.to_dict()
            }
        
        elif complexity_hint == "multi_step":
            # Planning-based
            # First create plan
            tools = ["search", "calculate", "retrieve"]
            plan = self.planner.create_plan(problem, tools)
            
            return {
                'strategy': 'planning',
                'plan': plan.to_dict(),
                'result': f"Plan created with {len(plan.steps)} steps"
            }
        
        else:  # complex or uncertain
            # Self-reflective solving
            result = self.reflector.solve_with_reflection(problem)
            return {
                'strategy': 'self_reflective',
                'result': result['final_solution'],
                'confidence': result['final_confidence'],
                'attempts': result['num_reflections']
            }
    
    def _analyze_complexity(self, problem: str) -> str:
        """Analyze problem complexity to select strategy"""
        # Simple heuristics
        word_count = len(problem.split())
        
        # Check for multi-step indicators
        multi_step_words = ['plan', 'steps', 'process', 'workflow', 'implement']
        exploratory_words = ['compare', 'best', 'options', 'alternatives', 'choose']
        
        problem_lower = problem.lower()
        
        if word_count < 10 and not any(w in problem_lower for w in multi_step_words + exploratory_words):
            return "simple"
        elif any(w in problem_lower for w in exploratory_words):
            return "exploratory"
        elif any(w in problem_lower for w in multi_step_words):
            return "multi_step"
        else:
            return "complex"


# Example usage
if __name__ == '__main__':
    # Mock LLM for testing
    class MockLLM:
        def chat(self, messages, tools=None):
            return "Step 1: Analyze the problem\nStep 2: Formulate a solution\nFinal Answer: The solution is 42."
    
    llm = MockLLM()
    
    # Test Chain of Thought
    cot = ChainOfThoughtReasoner(llm)
    result = cot.reason("What is the meaning of life?")
    print("Chain of Thought Result:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # Test Orchestrator
    orchestrator = ReasoningOrchestrator(llm)
    result = orchestrator.solve("How do I deploy a web application?")
    print("\nOrchestrator Result:")
    print(json.dumps(result, indent=2))
