#!/usr/bin/env python3
"""
Master Agent Orchestrator
Brings together all AI enhancements:
- Advanced RAG with multi-hop retrieval
- Agent tools and function calling
- Reasoning and planning
- Advanced memory
- Context management
- Evaluation and feedback
- Prompt engineering

Provides a unified interface for the intelligent agent.
"""

import json
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time

# Import all our enhancement modules
from ai_stack.advanced_rag import AdvancedRAG, RetrievedDocument
from ai_stack.agent_tools import ToolRegistry, ToolUsingAgent, create_obsidian_tools
from ai_stack.reasoning_engine import ReasoningOrchestrator, ReasoningStrategy
from ai_stack.advanced_memory import AdvancedMemorySystem
from ai_stack.context_manager import SmartContextBuilder
from ai_stack.evaluation_harness import ResponseEvaluator, FeedbackLoop
from ai_stack.prompt_engineering import PromptLibrary, DynamicPromptBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('agent_orchestrator')


@dataclass
class AgentConfig:
    """Configuration for the AI Agent"""
    # Model settings
    model_name: str = "local-llm"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    # RAG settings
    use_advanced_rag: bool = True
    use_multi_hop: bool = True
    retrieval_top_k: int = 5
    
    # Reasoning settings
    reasoning_strategy: str = "auto"  # auto, cot, react, tot, direct
    max_reasoning_steps: int = 10
    
    # Memory settings
    use_advanced_memory: bool = True
    max_working_memory: int = 10
    
    # Context settings
    max_context_tokens: int = 6000
    
    # Evaluation settings
    enable_evaluation: bool = True
    enable_hallucination_detection: bool = True
    
    # Tool settings
    enable_tools: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'model_name': self.model_name,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'use_advanced_rag': self.use_advanced_rag,
            'use_multi_hop': self.use_multi_hop,
            'retrieval_top_k': self.retrieval_top_k,
            'reasoning_strategy': self.reasoning_strategy,
            'max_reasoning_steps': self.max_reasoning_steps,
            'use_advanced_memory': self.use_advanced_memory,
            'max_working_memory': self.max_working_memory,
            'max_context_tokens': self.max_context_tokens,
            'enable_evaluation': self.enable_evaluation,
            'enable_hallucination_detection': self.enable_hallucination_detection,
            'enable_tools': self.enable_tools
        }


class EnhancedLLMClient:
    """
    Enhanced LLM client with all capabilities
    """
    
    def __init__(self, base_client, config: AgentConfig):
        self.base = base_client
        self.config = config
        
        # Initialize components
        self.rag = AdvancedRAG() if config.use_advanced_rag else None
        self.memory = AdvancedMemorySystem(llm_client=base_client) if config.use_advanced_memory else None
        self.reasoning = ReasoningOrchestrator(base_client)
        self.context_builder = SmartContextBuilder(base_client, config.max_context_tokens)
        self.tools = None
        self.tool_agent = None
        self.evaluator = ResponseEvaluator(base_client) if config.enable_evaluation else None
        self.feedback = FeedbackLoop()
        self.prompts = DynamicPromptBuilder(base_client)
        
        logger.info("Enhanced LLM Client initialized")
    
    def setup_tools(self, vault_interface):
        """Setup tools for the agent"""
        if self.config.enable_tools and vault_interface:
            self.tools = create_obsidian_tools(vault_interface)
            self.tool_agent = ToolUsingAgent(self.base, self.tools)
            logger.info(f"Setup {len(self.tools.list_tools())} tools")
    
    def chat(self, query: str, conversation_history: List[Dict] = None,
             context_documents: List[Dict] = None, 
             use_reasoning: bool = True,
             use_tools: bool = True) -> Dict:
        """
        Enhanced chat with all capabilities
        
        Returns:
            {
                'response': str,
                'reasoning_trace': Dict (optional),
                'retrieved_documents': List,
                'tool_calls': List,
                'evaluation': Dict (optional),
                'metadata': Dict
            }
        """
        start_time = time.time()
        result = {
            'query': query,
            'response': '',
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'config': self.config.to_dict()
            }
        }
        
        try:
            # Step 1: Store query in memory
            if self.memory:
                self.memory.store(query, memory_type="working", importance=0.8,
                                 metadata={'type': 'user_query'})
            
            # Step 2: Retrieve relevant context
            retrieved_docs = []
            if self.rag and self.config.use_advanced_rag:
                rag_result = self.rag.retrieve(
                    query, 
                    use_multi_hop=self.config.use_multi_hop,
                    top_k=self.config.retrieval_top_k
                )
                retrieved_docs = rag_result.get('documents', [])
                result['retrieved_documents'] = [d.to_dict() for d in retrieved_docs]
                result['metadata']['retrieval_time_ms'] = rag_result.get('retrieval_time_ms', 0)
            
            # Step 3: Build context
            self._build_context(query, conversation_history, retrieved_docs)
            
            # Step 4: Determine reasoning strategy and generate response
            if use_reasoning and self.config.reasoning_strategy != "direct":
                response_data = self._generate_with_reasoning(query, retrieved_docs)
            else:
                response_data = self._generate_direct(query, retrieved_docs)
            
            result['response'] = response_data['response']
            if 'reasoning_trace' in response_data:
                result['reasoning_trace'] = response_data['reasoning_trace']
            
            # Step 5: Use tools if needed
            if use_tools and self.tool_agent:
                tool_result = self._execute_tools_if_needed(query, result['response'])
                if tool_result:
                    result['tool_calls'] = tool_result.get('tool_calls', [])
                    if tool_result.get('response'):
                        result['response'] = tool_result['response']
            
            # Step 6: Evaluate response
            if self.evaluator and self.config.enable_evaluation:
                evaluation = self.evaluator.evaluate(
                    query, 
                    result['response'],
                    [d.content for d in retrieved_docs]
                )
                result['evaluation'] = evaluation.to_dict()
                
                # Add warning if hallucination detected
                if evaluation.metrics.get('hallucination_risk', 0) > 0.5:
                    result['metadata']['hallucination_warning'] = True
            
            # Step 7: Store response in memory
            if self.memory:
                self.memory.store(
                    result['response'],
                    memory_type="working",
                    importance=0.7,
                    metadata={'type': 'assistant_response', 'query': query}
                )
            
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            result['response'] = f"I encountered an error while processing your request: {str(e)}"
            result['error'] = str(e)
        
        result['metadata']['execution_time_ms'] = (time.time() - start_time) * 1000
        return result
    
    def _build_context(self, query: str, conversation_history: List[Dict],
                       retrieved_docs: List[RetrievedDocument]):
        """Build context for the LLM"""
        # Set system prompt
        system_prompt = self._get_system_prompt()
        self.context_builder.set_system_prompt(system_prompt)
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    self.context_builder.add_user_message(content)
        
        # Add retrieved documents
        if retrieved_docs:
            doc_dicts = [{'id': d.id, 'content': d.content, 'source': d.retrieval_method}
                        for d in retrieved_docs[:self.config.retrieval_top_k]]
            self.context_builder.add_retrieved_context(doc_dicts)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt"""
        base_prompt = """You are an intelligent AI assistant integrated with Obsidian.
You have access to the user's notes and can help with:
- Answering questions based on their knowledge base
- Creating and organizing notes
- Finding connections between ideas
- Summarizing content
- And much more

Guidelines:
- Be concise but thorough
- Cite sources when using retrieved information
- If you don't know something, say so
- Use tools when appropriate"""
        
        return base_prompt
    
    def _generate_with_reasoning(self, query: str, 
                                  retrieved_docs: List[RetrievedDocument]) -> Dict:
        """Generate response with reasoning"""
        # Determine complexity
        complexity = self._assess_complexity(query)
        
        # Use reasoning orchestrator
        reasoning_result = self.reasoning.solve(query, complexity)
        
        # Get final response from reasoning
        if 'reasoning_trace' in reasoning_result:
            # Build prompt with reasoning trace
            context = self._format_retrieved_context(retrieved_docs)
            
            messages = self.context_builder.build_context(query)
            
            # Add reasoning context
            reasoning_context = f"""Reasoning process:
{json.dumps(reasoning_result.get('reasoning_trace', {}), indent=2)}

Based on this reasoning, provide a clear answer to the user."""
            
            messages.append({'role': 'system', 'content': reasoning_context})
            messages.append({'role': 'user', 'content': query})
            
            response = self.base.chat(messages)
            
            return {
                'response': response,
                'reasoning_trace': reasoning_result.get('reasoning_trace')
            }
        else:
            return {'response': reasoning_result.get('result', '')}
    
    def _generate_direct(self, query: str, 
                         retrieved_docs: List[RetrievedDocument]) -> Dict:
        """Generate response directly"""
        messages = self.context_builder.build_context(query)
        messages.append({'role': 'user', 'content': query})
        
        response = self.base.chat(messages)
        
        return {'response': response}
    
    def _execute_tools_if_needed(self, query: str, 
                                  draft_response: str) -> Optional[Dict]:
        """Execute tools if the query requires them"""
        if not self.tool_agent:
            return None
        
        # Check if tools are needed
        tool_indicators = ['create', 'search', 'find', 'add', 'delete', 'update', 'generate']
        needs_tools = any(indicator in query.lower() for indicator in tool_indicators)
        
        if needs_tools:
            result = self.tool_agent.run(query)
            return result
        
        return None
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        # Simple heuristics
        word_count = len(query.split())
        
        complex_indicators = ['compare', 'analyze', 'evaluate', 'explain why', 'steps to',
                             'how do I', 'what is the best', 'pros and cons']
        
        if any(ind in query.lower() for ind in complex_indicators):
            return "complex"
        elif word_count > 15:
            return "exploratory"
        else:
            return "simple"
    
    def _format_retrieved_context(self, docs: List[RetrievedDocument]) -> str:
        """Format retrieved documents as context"""
        if not docs:
            return ""
        
        context_parts = ["Relevant information from your notes:"]
        
        for i, doc in enumerate(docs[:5], 1):
            context_parts.append(f"[{i}] {doc.content[:300]}...")
        
        return "\n\n".join(context_parts)
    
    def provide_feedback(self, query: str, response: str, 
                         user_rating: int, user_comment: str = ""):
        """Collect user feedback for improvement"""
        evaluation_data = None
        if self.evaluator:
            evaluation = self.evaluator.evaluate(query, response)
            evaluation_data = evaluation.to_dict()
        
        self.feedback.collect_feedback(
            query, response, user_rating, user_comment, evaluation_data
        )
    
    def get_stats(self) -> Dict:
        """Get comprehensive stats about the agent"""
        stats = {
            'config': self.config.to_dict(),
            'components': {
                'rag_enabled': self.rag is not None,
                'memory_enabled': self.memory is not None,
                'tools_enabled': self.tools is not None,
                'evaluation_enabled': self.evaluator is not None
            }
        }
        
        if self.memory:
            stats['memory'] = self.memory.get_stats()
        
        if self.tools:
            stats['tools'] = {
                'available': len(self.tools.list_tools()),
                'list': [t.name for t in self.tools.list_tools()]
            }
        
        stats['feedback'] = self.feedback.get_insights()
        
        return stats


class AgentSession:
    """
    Manages a conversation session with the agent
    """
    
    def __init__(self, orchestrator: EnhancedLLMClient, session_id: str = None):
        self.orchestrator = orchestrator
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.history: List[Dict] = []
        self.metadata: Dict = {
            'created_at': datetime.now().isoformat(),
            'message_count': 0
        }
    
    def send_message(self, message: str, **kwargs) -> Dict:
        """Send a message and get response"""
        result = self.orchestrator.chat(
            message,
            conversation_history=self.history,
            **kwargs
        )
        
        # Update history
        self.history.append({'role': 'user', 'content': message})
        self.history.append({'role': 'assistant', 'content': result['response']})
        
        self.metadata['message_count'] += 2
        
        return result
    
    def provide_feedback(self, message_index: int, rating: int, comment: str = ""):
        """Provide feedback on a specific message"""
        if message_index < len(self.history):
            msg = self.history[message_index]
            if msg['role'] == 'assistant' and message_index > 0:
                query = self.history[message_index - 1]['content']
                response = msg['content']
                self.orchestrator.provide_feedback(query, response, rating, comment)
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []
        self.metadata['message_count'] = 0


# Factory function
def create_enhanced_agent(base_llm_client, 
                          config: AgentConfig = None,
                          vault_interface = None) -> EnhancedLLMClient:
    """
    Factory function to create an enhanced agent
    
    Usage:
        agent = create_enhanced_agent(
            my_llm_client,
            AgentConfig(use_advanced_rag=True, enable_tools=True),
            vault_interface=my_vault
        )
    """
    config = config or AgentConfig()
    agent = EnhancedLLMClient(base_llm_client, config)
    
    if vault_interface:
        agent.setup_tools(vault_interface)
    
    return agent


# Example usage
if __name__ == '__main__':
    # Mock LLM client for testing
    class MockLLM:
        def chat(self, messages):
            return "This is a test response from the enhanced agent."
    
    # Create enhanced agent
    config = AgentConfig(
        use_advanced_rag=True,
        use_multi_hop=True,
        enable_evaluation=True,
        enable_tools=False  # No vault interface in test
    )
    
    agent = create_enhanced_agent(MockLLM(), config)
    
    # Test chat
    result = agent.chat("What is machine learning?")
    
    print("Agent Response:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\nAgent Stats:")
    print(json.dumps(agent.get_stats(), indent=2, default=str))
