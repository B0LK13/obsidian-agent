"""TUI interface for PKM Agent using Textual."""

import asyncio
from datetime import datetime
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
    Tabs,
)

from pkm_agent.app import PKMAgentApp


class ChatMessage(Static):
    """A chat message display widget."""

    def __init__(self, role: str, content: str, timestamp: datetime | None = None):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.role.upper()}[/bold] [{self.timestamp.strftime('%H:%M')}]")
        yield Markdown(self.content)

    def on_mount(self) -> None:
        """Set styling based on role."""
        if self.role == "user":
            self.add_class("user-message")
        else:
            self.add_class("assistant-message")


class ChatPanel(Vertical):
    """Panel for chat interaction."""

    def __init__(self, app: PKMAgentApp):
        super().__init__()
        self.pkm_app = app
        self.messages: list[ChatMessage] = []
        self.streaming = False

    def compose(self) -> ComposeResult:
        self.messages_container = Container()
        self.chat_input = Input(placeholder="Type your message...")
        self.send_button = Button("Send", variant="primary")
        yield self.messages_container
        yield Horizontal(self.chat_input, self.send_button, id="input-row")

    async def send_message(self, text: str) -> None:
        """Send a message and get response."""
        if not text.strip() or self.streaming:
            return

        # Add user message
        self._add_message("user", text)

        # Add assistant message placeholder
        assistant_msg = self._add_message("assistant", "...")
        self.streaming = True

        try:
            full_response = ""
            async for chunk in self.pkm_app.ask_with_context(text):
                full_response += chunk
                assistant_msg.query_one(Markdown).update(full_response)
                assistant_msg.query_one(Markdown).scroll_end()
        except Exception as e:
            assistant_msg.query_one(Markdown).update(f"Error: {e}")
        finally:
            self.streaming = False

    def _add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the chat."""
        msg = ChatMessage(role, content)
        self.messages.append(msg)

        self.messages_container.mount(msg)
        msg.scroll_visible()

        return msg

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_widget = event.input
        text = input_widget.value
        input_widget.value = ""
        await self.send_message(text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button == self.send_button:
            text = self.chat_input.value
            self.chat_input.value = ""
            await self.send_message(text)


class SearchResults(ListView):
    """Widget to display search results."""

    async def add_results(self, results: list[dict[str, Any]]) -> None:
        """Add search results to the list."""
        self.clear()

        for r in results:
            item = ListItem(
                Vertical(
                    Label(f"[bold]{r['title']}[/bold]"),
                    Label(f"[dim]{r['path']}[/dim]"),
                    Label(f"Score: {r['score']:.2f}"),
                    Label(f"[dim]{r['snippet'][:100]}...[/dim]"),
                )
            )
            await self.append(item)


class SearchPanel(Vertical):
    """Panel for searching the knowledge base."""

    def __init__(self, app: PKMAgentApp):
        super().__init__()
        self.pkm_app = app

    def compose(self) -> ComposeResult:
        yield Label("[bold]Search Your Knowledge Base[/bold]")
        self.search_input = Input(placeholder="Search query...")
        self.search_button = Button("Search", variant="primary")
        self.results = SearchResults()
        yield Horizontal(self.search_input, self.search_button, id="search-row")
        yield self.results

    async def perform_search(self, query: str) -> None:
        """Perform a search."""
        if not query.strip():
            return

        results = await self.pkm_app.search(query, limit=20)
        await self.results.add_results(results)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_widget = event.input
        await self.perform_search(input_widget.value)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button == self.search_button:
            await self.perform_search(self.search_input.value)


class StatsPanel(Vertical):
    """Panel to display statistics."""

    def __init__(self, app: PKMAgentApp):
        super().__init__()
        self.pkm_app = app

    def compose(self) -> ComposeResult:
        yield Label("[bold]PKM Statistics[/bold]")
        self.stats_content = Static("")
        yield self.stats_content

    async def on_mount(self) -> None:
        """Load stats when mounted."""
        await self.update_stats()

    async def update_stats(self) -> None:
        """Update statistics display."""
        stats = await self.pkm_app.get_stats()

        content = f"""
[b]PKM Root:[/b] {stats['pkm_root']}

[b]Notes:[/b] {stats['notes']:,}
[b]Tags:[/b] {stats['tags']:,}
[b]Links:[/b] {stats['links']:,}
[b]Total Words:[/b] {stats['total_words']:,}

[b]Vector Store:[/b]
  Chunks: {stats['vector_store']['total_chunks']:,}
  Collection: {stats['vector_store']['collection_name']}

[b]LLM:[/b]
  Provider: {stats['llm']['provider']}
  Model: {stats['llm']['model']}
"""
        self.stats_content.update(content)


class PKMTUI(App):
    """Main TUI application for PKM Agent."""

    CSS = """
    Screen {
        background: $background;
    }

    ChatPanel {
        height: 1fr;
    }

    #messages-container {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    .user-message {
        background: $primary;
        padding: 1;
        margin-bottom: 1;
    }

    .assistant-message {
        background: $surface;
        padding: 1;
        margin-bottom: 1;
    }

    #input-row {
        dock: bottom;
        padding: 1;
        height: 3;
    }

    #chat-input {
        width: 1fr;
    }

    SearchPanel {
        padding: 1;
    }

    #search-row {
        margin-bottom: 1;
    }

    #search-input {
        width: 1fr;
    }

    #search-results {
        height: 1fr;
    }

    StatsPanel {
        padding: 2;
    }

    #stats-content {
        background: $surface;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("tab", "focus_next", "Next"),
        ("shift+tab", "focus_previous", "Previous"),
    ]

    def __init__(
        self,
        app: PKMAgentApp,
        initial_prompt: str | None = None,
    ):
        super().__init__()
        self.pkm_app = app
        self.initial_prompt = initial_prompt

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tabs("Chat", "Search", "Stats")
        yield ContentSwitcher(
            ChatPanel(self.pkm_app),
            SearchPanel(self.pkm_app),
            StatsPanel(self.pkm_app),
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Handle async mount operations."""
        # Set subtitle if initial prompt
        if self.initial_prompt:
            self.sub_title = f"Prompt: {self.initial_prompt[:50]}..."
            # Send initial prompt
            chat_panel = self.query_one(ChatPanel)
            _ = await asyncio.sleep(0.5)  # Wait for UI to settle
            await chat_panel.send_message(self.initial_prompt)
