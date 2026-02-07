"""ReAct (Reasoning + Acting) agent loop for multi-step workflows.

Implements autonomous reasoning with tool calling for complex PKM tasks.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


class ToolResult:
    """Result from tool execution."""

    def __init__(self, success: bool, data: Any = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error

    def __str__(self) -> str:
        if self.success:
            return f"Success: {self.data}"
        return f"Error: {self.error}"


class Tool(Protocol):
    """Protocol for agent tools."""

    name: str
    description: str

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        ...


@dataclass
class ThoughtStep:
    """Single thought/action/observation in reasoning chain."""

    thought: str
    action: str | None = None
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str | None = None
    step_number: int = 0


class AgentStatus(str, Enum):
    """Agent execution status."""

    THINKING = "thinking"
    ACTING = "acting"
    COMPLETED = "completed"
    ERROR = "error"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class AgentResult:
    """Result from agent execution."""

    status: AgentStatus
    answer: str
    reasoning_chain: list[ThoughtStep]
    metadata: dict[str, Any] = field(default_factory=dict)


class ReActAgent:
    """Reasoning and Acting agent with tool use."""

    def __init__(
        self,
        llm_provider,
        tools: list[Tool],
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        self.llm_provider = llm_provider
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose

    async def execute(self, goal: str, context: str = "") -> AgentResult:
        """Execute the agent loop to achieve the goal."""
        reasoning_chain: list[ThoughtStep] = []
        iteration = 0

        # Build system prompt with tool descriptions
        tool_descriptions = self._format_tools()
        system_prompt = self._build_system_prompt(tool_descriptions)

        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Goal: {goal}\n\nContext: {context}"},
        ]

        while iteration < self.max_iterations:
            iteration += 1

            if self.verbose:
                logger.info(f"Iteration {iteration}: Thinking...")

            # Get next thought/action from LLM
            response = await self.llm_provider.chat(conversation_history)

            # Parse response
            step = self._parse_response(response, iteration)
            reasoning_chain.append(step)

            if self.verbose:
                logger.info(f"Thought: {step.thought}")
                if step.action:
                    logger.info(f"Action: {step.action}({step.action_input})")

            # Check if done
            if not step.action or step.action.lower() == "finish":
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    answer=step.thought,
                    reasoning_chain=reasoning_chain,
                )

            # Execute action
            try:
                tool = self.tools.get(step.action)
                if not tool:
                    step.observation = f"Error: Unknown tool '{step.action}'"
                else:
                    result = await tool.execute(**step.action_input)
                    step.observation = str(result)

                if self.verbose:
                    logger.info(f"Observation: {step.observation}")

            except Exception as e:
                step.observation = f"Error executing {step.action}: {str(e)}"
                logger.error(f"Tool execution error: {e}", exc_info=True)

            # Add observation to conversation
            conversation_history.append({"role": "assistant", "content": response})
            conversation_history.append({"role": "user", "content": f"Observation: {step.observation}"})

        return AgentResult(
            status=AgentStatus.MAX_ITERATIONS,
            answer="Maximum iterations reached without completion",
            reasoning_chain=reasoning_chain,
            metadata={"iterations": iteration},
        )

    def _build_system_prompt(self, tool_descriptions: str) -> str:
        """Build system prompt for ReAct agent."""
        return f"""You are an intelligent agent helping with personal knowledge management tasks.

You have access to the following tools:
{tool_descriptions}

Use the following format for each step:

Thought: Consider what to do next
Action: tool_name
Action Input: {{"param": "value"}}

After receiving an observation, continue with the next thought.

When you have enough information to answer the goal, use:
Thought: I now have enough information to answer
Action: Finish

Be systematic and thorough. Break down complex goals into multiple steps.
"""

    def _format_tools(self) -> str:
        """Format tool descriptions for prompt."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)

    def _parse_response(self, response: str, step_number: int) -> ThoughtStep:
        """Parse LLM response into ThoughtStep."""
        lines = response.strip().split("\n")

        thought = ""
        action = None
        action_input = {}

        current_section = None
        input_buffer = []

        for line in lines:
            line = line.strip()

            if line.startswith("Thought:"):
                current_section = "thought"
                thought = line.replace("Thought:", "").strip()
            elif line.startswith("Action:"):
                current_section = "action"
                action = line.replace("Action:", "").strip()
            elif line.startswith("Action Input:"):
                current_section = "input"
                input_str = line.replace("Action Input:", "").strip()
                input_buffer = [input_str]
            elif current_section == "thought" and line:
                thought += " " + line
            elif current_section == "input" and line:
                input_buffer.append(line)

        # Parse action input JSON
        if input_buffer:
            try:
                input_json = " ".join(input_buffer)
                action_input = json.loads(input_json)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse action input: {input_buffer}")

        return ThoughtStep(
            thought=thought,
            action=action,
            action_input=action_input,
            step_number=step_number,
        )


# Example Tools for PKM Agent

class SearchNotesTool:
    """Tool for searching notes in the vault."""

    name = "search_notes"
    description = "Search for notes by semantic similarity to a query. Returns relevant notes."

    def __init__(self, retriever):
        self.retriever = retriever

    async def execute(self, query: str, top_k: int = 5) -> ToolResult:
        """Search for notes."""
        try:
            results = await self.retriever.search(query, k=top_k)
            return ToolResult(success=True, data=results)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadNoteTool:
    """Tool for reading note content."""

    name = "read_note"
    description = "Read the full content of a specific note by ID or path."

    def __init__(self, note_loader):
        self.note_loader = note_loader

    async def execute(self, note_id: str) -> ToolResult:
        """Read a note."""
        try:
            content = await self.note_loader.load(note_id)
            return ToolResult(success=True, data=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateNoteTool:
    """Tool for creating a new note."""

    name = "create_note"
    description = "Create a new note with given title and content."

    def __init__(self, note_creator):
        self.note_creator = note_creator

    async def execute(self, title: str, content: str, tags: list[str] | None = None) -> ToolResult:
        """Create a note."""
        try:
            note_id = await self.note_creator.create(title, content, tags or [])
            return ToolResult(success=True, data={"note_id": note_id})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SynthesizeTool:
    """Tool for synthesizing information from multiple notes."""

    name = "synthesize"
    description = "Synthesize insights from multiple note contents. Provide list of note IDs."

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    async def execute(self, note_ids: list[str], question: str) -> ToolResult:
        """Synthesize from notes."""
        try:
            # Load all notes (would be implemented with actual note loader)
            # Then use LLM to synthesize
            synthesis = await self.llm_provider.synthesize(note_ids, question)
            return ToolResult(success=True, data=synthesis)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
