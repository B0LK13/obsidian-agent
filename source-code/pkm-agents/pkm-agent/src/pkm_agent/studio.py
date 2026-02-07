"""Advanced TUI interface for PKM Agent."""

import asyncio
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Markdown,
    Static,
    Tab,
    Tabs,
)

from pkm_agent.app import PKMAgentApp
from pkm_agent.data.models import Note


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
        elif self.role == "system":
            self.add_class("system-message")
        else:
            self.add_class("assistant-message")


class NoteListItem(ListItem):
    """List item for a note."""

    def __init__(self, note: Note):
        super().__init__(
            Vertical(
                Label(note.title or "Untitled", classes="note-title"),
                Label(str(note.path), classes="note-path"),
            )
        )
        self.note = note


class SearchResultItem(ListItem):
    """List item for a search result."""

    def __init__(self, result: dict[str, Any]):
        snippet = (result.get("snippet") or "").strip().replace("\n", " ")
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."

        rows = [
            Label(result.get("title", "Untitled"), classes="note-title"),
            Label(result.get("path", ""), classes="note-path"),
        ]
        if snippet:
            rows.append(Label(snippet, classes="note-snippet"))
        rows.append(Label(f"Score: {result.get('score', 0):.2f}", classes="note-score"))

        super().__init__(Vertical(*rows))
        self.result = result


HELP_TEXT = """# PKM Studio

## Shortcuts
- q / Ctrl+C: quit
- F1 or ?: help
- Tab / Shift+Tab: next/previous focus
- Typing anywhere restores chat input focus
- Ctrl+1: focus Library
- Ctrl+2: focus Chat
- Ctrl+3: focus Inspector
- Ctrl+L: focus Library filter
- Ctrl+F: focus Search tab
- Ctrl+E: focus Chat input
- Ctrl+R: refresh panels
- Ctrl+I: reindex notes
- Ctrl+O: open selected note in Obsidian
- Ctrl+Shift+O: reveal selected note in Explorer

## Slash commands
- /help
- /index
- /refresh
- /search <query>
- /open <relative path>
- /reveal [path]
- /obsidian [path]
- /settings
- /stats
- /audit
- /clear
"""


class HelpScreen(ModalScreen):
    """Help overlay for PKM Studio."""

    CSS = """
    HelpScreen {
        align: center middle;
        background: #0b0f14;
    }

    #help-dialog {
        width: 80%;
        max-width: 96;
        height: 80%;
        border: solid #263241;
        background: #10161f;
        padding: 1 2;
    }

    #help-title {
        background: #1b2a36;
        color: #c5d0d8;
        padding: 0 1;
    }

    #help-body {
        height: 1fr;
    }

    #help-close {
        margin-top: 1;
        width: 12;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("PKM Studio Help", id="help-title"),
            VerticalScroll(Markdown(HELP_TEXT), id="help-body"),
            Button("Close", id="help-close"),
            id="help-dialog",
        )

    def action_dismiss(self) -> None:
        self.dismiss()
        self.app.restore_chat_focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help-close":
            self.action_dismiss()


class LibraryPanel(Vertical):
    """Panel showing recent notes."""

    def __init__(self, app: PKMAgentApp, on_open: Callable[[Note], Any], **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app
        self.on_open = on_open
        self.notes: list[Note] = []
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Label("Library", classes="panel-title")
        self.filter_input = Input(placeholder="Filter notes...", id="library-filter")
        self.refresh_button = Button("Refresh", variant="primary", id="library-refresh")
        self.index_button = Button("Reindex", id="library-index")
        yield self.filter_input
        yield Horizontal(self.refresh_button, self.index_button, id="library-controls")
        self.list_view = ListView(id="library-list")
        yield self.list_view

    async def on_mount(self) -> None:
        await self.load_notes()

    async def load_notes(self) -> None:
        self.notes = self.pkm_app.db.get_all_notes(limit=200)
        await self._render_notes(self.notes)

    async def _render_notes(self, notes: list[Note]) -> None:
        self.list_view.clear()
        if not notes:
            await self.list_view.append(
                ListItem(Label("No notes found.", classes="empty-state"))
            )
            return
        for note in notes:
            await self.list_view.append(NoteListItem(note))

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.filter_input.disabled = busy
        self.refresh_button.disabled = busy
        self.index_button.disabled = busy

    def focus_filter(self) -> None:
        self.filter_input.focus()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, NoteListItem):
            await self.on_open(item.note)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if isinstance(item, NoteListItem):
            await self.on_open(item.note)

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input != self.filter_input:
            return
        query = self.filter_input.value.strip().lower()
        if not query:
            await self._render_notes(self.notes)
            return
        filtered = [
            note for note in self.notes
            if query in (note.title or "").lower() or query in str(note.path).lower()
        ]
        await self._render_notes(filtered)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.refresh_button:
            await self.app.refresh_panels()
            self.app.set_status("Panels refreshed.", tone="info")
        elif event.button == self.index_button:
            await self.app.reindex_notes()


class PreviewPanel(Vertical):
    """Preview of the selected note."""

    def compose(self) -> ComposeResult:
        yield Label("Preview", classes="panel-title")
        self.meta = Static("", id="preview-meta")
        self.content_markdown = Markdown("", id="preview-markdown")
        self.content_scroll = VerticalScroll(self.content_markdown, id="preview-content")
        yield self.meta
        yield self.content_scroll

    def show_note(self, note: Note | None) -> None:
        if not note:
            self.meta.update("No note selected.")
            self.content_markdown.update("")
            return

        tags = ", ".join(note.metadata.tags) if note.metadata.tags else "none"
        meta = [
            f"[b]Title:[/b] {note.title}",
            f"[b]Path:[/b] {note.path}",
            f"[b]Tags:[/b] {tags}",
            f"[b]Modified:[/b] {note.modified_at.strftime('%Y-%m-%d %H:%M')}",
        ]
        self.meta.update("\n".join(meta))

        content = note.content.strip()
        if len(content) > 4000:
            content = content[:4000] + "\n\n...[truncated]..."
        self.content_markdown.update(content or "_(empty note)_")
        self.content_scroll.scroll_home(animate=False)


class SearchPanel(Vertical):
    """Panel for searching the knowledge base."""

    def __init__(self, app: PKMAgentApp, on_open: Callable[[str], Any], **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app
        self.on_open = on_open

    def compose(self) -> ComposeResult:
        yield Label("Search", classes="panel-title")
        self.search_input = Input(placeholder="Search query...", id="search-input")
        self.search_button = Button("Search", variant="primary", id="search-button")
        yield Horizontal(self.search_input, self.search_button, id="search-row")
        self.results = ListView(id="search-results")
        yield self.results

    async def perform_search(self, query: str) -> None:
        query = query.strip()
        if not query:
            return
        self.app.set_status(f"Searching for: {query}", tone="info")
        self.app.set_busy(True)
        try:
            results = await self.pkm_app.search(query, limit=20)
        except Exception as exc:
            self.app.set_status(f"Search failed: {exc}", tone="error")
            return
        finally:
            self.app.set_busy(False)

        self.results.clear()
        if not results:
            await self.results.append(
                ListItem(Label("No results found.", classes="empty-state"))
            )
            return

        for result in results:
            await self.results.append(SearchResultItem(result))
        self.app.set_status(f"Found {len(results)} results.", tone="info")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input == self.search_input:
            await self.perform_search(self.search_input.value)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.search_button:
            await self.perform_search(self.search_input.value)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, SearchResultItem):
            path = item.result.get("path")
            if path:
                await self.on_open(path)

    def focus_input(self) -> None:
        self.search_input.focus()


class StatsPanel(Vertical):
    """Panel to display statistics."""

    def __init__(self, app: PKMAgentApp, **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app

    def compose(self) -> ComposeResult:
        yield Label("Stats", classes="panel-title")
        self.stats_content = Static("", id="stats-content")
        yield self.stats_content

    async def on_mount(self) -> None:
        await self.update_stats()

    async def update_stats(self) -> None:
        stats = await self.pkm_app.get_stats()
        content = [
            f"[b]PKM Root:[/b] {stats['pkm_root']}",
            "",
            f"[b]Notes:[/b] {stats['notes']:,}",
            f"[b]Tags:[/b] {stats['tags']:,}",
            f"[b]Links:[/b] {stats['links']:,}",
            f"[b]Total Words:[/b] {stats['total_words']:,}",
            "",
            "[b]Vector Store:[/b]",
            f"  Chunks: {stats['vector_store']['total_chunks']:,}",
            f"  Collection: {stats['vector_store']['collection_name']}",
            "",
            "[b]LLM:[/b]",
            f"  Provider: {stats['llm']['provider']}",
            f"  Model: {stats['llm']['model']}",
        ]
        self.stats_content.update("\n".join(content))


class AuditPanel(Vertical):
    """Panel showing recent audit log entries."""

    def __init__(self, app: PKMAgentApp, **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app

    def compose(self) -> ComposeResult:
        yield Label("Audit", classes="panel-title")
        self.refresh_button = Button("Refresh", id="audit-refresh")
        yield self.refresh_button
        self.audit_content = Static("", id="audit-content")
        yield self.audit_content

    async def on_mount(self) -> None:
        await self.refresh_logs()

    async def refresh_logs(self) -> None:
        logs = self.pkm_app.db.get_audit_logs(limit=50)
        lines = []
        for entry in logs:
            timestamp = entry["created_at"].replace("T", " ")
            lines.append(f"[dim]{timestamp}[/dim] {entry['category']}::{entry['action']}")
        self.audit_content.update("\n".join(lines) if lines else "No audit entries yet.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.refresh_button:
            await self.refresh_logs()


class SettingsPanel(Vertical):
    """Panel for editing runtime settings (proof-of-concept)."""

    def __init__(self, app: PKMAgentApp, **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app
        self._last_chunk_settings = (
            app.config.rag.chunk_size,
            app.config.rag.chunk_overlap,
        )

    def compose(self) -> ComposeResult:
        yield Label("Settings", classes="panel-title")
        with VerticalScroll(id="settings-body"):
            yield Label("LLM", classes="settings-section")
            yield Label("Provider", classes="field-label")
            self.llm_provider = Input(placeholder="ollama/openai", id="settings-llm-provider")
            yield self.llm_provider
            yield Label("Model", classes="field-label")
            self.llm_model = Input(placeholder="llama3.1", id="settings-llm-model")
            yield self.llm_model
            yield Label("Base URL", classes="field-label")
            self.llm_base_url = Input(placeholder="http://localhost:11434", id="settings-llm-base-url")
            yield self.llm_base_url
            yield Label("Temperature", classes="field-label")
            self.llm_temperature = Input(placeholder="0.7", id="settings-llm-temperature")
            yield self.llm_temperature
            yield Label("Max Tokens", classes="field-label")
            self.llm_max_tokens = Input(placeholder="2048", id="settings-llm-max-tokens")
            yield self.llm_max_tokens

            yield Label("Retrieval", classes="settings-section")
            yield Label("Top K", classes="field-label")
            self.retriever_top_k = Input(placeholder="5", id="settings-top-k")
            yield self.retriever_top_k
            yield Label("Chunk Size", classes="field-label")
            self.chunk_size = Input(placeholder="512", id="settings-chunk-size")
            yield self.chunk_size
            yield Label("Chunk Overlap", classes="field-label")
            self.chunk_overlap = Input(placeholder="64", id="settings-chunk-overlap")
            yield self.chunk_overlap

            yield Label("TUI", classes="settings-section")
            yield Label("Theme", classes="field-label")
            self.tui_theme = Input(placeholder="tokyo-night", id="settings-theme")
            yield self.tui_theme

        self.notice = Static("", id="settings-notice")
        yield self.notice
        self.apply_button = Button("Apply", variant="primary", id="settings-apply")
        self.reset_button = Button("Reset", id="settings-reset")
        yield Horizontal(self.apply_button, self.reset_button, id="settings-actions")

    async def on_mount(self) -> None:
        self.load_from_config()

    def load_from_config(self) -> None:
        cfg = self.pkm_app.config
        self.llm_provider.value = cfg.llm.provider
        self.llm_model.value = cfg.llm.model
        self.llm_base_url.value = cfg.llm.base_url or ""
        self.llm_temperature.value = str(cfg.llm.temperature)
        self.llm_max_tokens.value = str(cfg.llm.max_tokens)
        self.retriever_top_k.value = str(self.pkm_app.retriever.config.top_k)
        self.chunk_size.value = str(cfg.rag.chunk_size)
        self.chunk_overlap.value = str(cfg.rag.chunk_overlap)
        self.tui_theme.value = cfg.tui.theme
        self.notice.update("")
        self._last_chunk_settings = (cfg.rag.chunk_size, cfg.rag.chunk_overlap)

    def focus_first(self) -> None:
        self.llm_provider.focus()

    def _parse_int(self, value: str, label: str, minimum: int = 1) -> int:
        try:
            parsed = int(value)
        except ValueError:
            raise ValueError(f"{label} must be an integer.")
        if parsed < minimum:
            raise ValueError(f"{label} must be >= {minimum}.")
        return parsed

    def _parse_float(self, value: str, label: str, minimum: float = 0.0, maximum: float = 2.0) -> float:
        try:
            parsed = float(value)
        except ValueError:
            raise ValueError(f"{label} must be a number.")
        if parsed < minimum or parsed > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return parsed

    async def apply_settings(self) -> None:
        provider = self.llm_provider.value.strip().lower()
        allowed = {"openai", "ollama"}
        if provider not in allowed:
            self.notice.update(f"Provider must be one of: {', '.join(sorted(allowed))}.")
            self.app.set_status("Invalid provider.", tone="error")
            return

        try:
            temperature = self._parse_float(self.llm_temperature.value.strip(), "Temperature")
            max_tokens = self._parse_int(self.llm_max_tokens.value.strip(), "Max Tokens", minimum=64)
            top_k = self._parse_int(self.retriever_top_k.value.strip(), "Top K", minimum=1)
            chunk_size = self._parse_int(self.chunk_size.value.strip(), "Chunk Size", minimum=128)
            chunk_overlap = self._parse_int(self.chunk_overlap.value.strip(), "Chunk Overlap", minimum=0)
        except ValueError as exc:
            self.notice.update(str(exc))
            self.app.set_status("Invalid settings.", tone="error")
            return

        if chunk_overlap >= chunk_size:
            self.notice.update("Chunk Overlap must be smaller than Chunk Size.")
            self.app.set_status("Invalid chunk settings.", tone="error")
            return

        cfg = self.pkm_app.config
        cfg.llm.provider = provider
        cfg.llm.model = self.llm_model.value.strip() or cfg.llm.model
        cfg.llm.base_url = self.llm_base_url.value.strip() or None
        cfg.llm.temperature = temperature
        cfg.llm.max_tokens = max_tokens

        cfg.rag.chunk_size = chunk_size
        cfg.rag.chunk_overlap = chunk_overlap
        cfg.rag.top_k = top_k

        cfg.tui.theme = self.tui_theme.value.strip() or cfg.tui.theme

        self.pkm_app.llm = None
        self.pkm_app.retriever.config.top_k = top_k
        self.pkm_app.chunker.config.chunk_size = chunk_size
        self.pkm_app.chunker.config.chunk_overlap = chunk_overlap

        if self._last_chunk_settings != (chunk_size, chunk_overlap):
            self.notice.update("Chunk settings changed. Reindex recommended.")
        else:
            self.notice.update("Settings applied.")

        await self.app.refresh_status()
        self.app.set_status("Settings applied.", tone="success")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.apply_button:
            await self.apply_settings()
        elif event.button == self.reset_button:
            self.load_from_config()
            self.app.set_status("Settings reset.", tone="info")


class InspectorPanel(Vertical):
    """Right-side inspector with tabs."""

    def __init__(self, app: PKMAgentApp, on_open: Callable[[str], Any], **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app
        self.on_open = on_open
        self.preview_panel = PreviewPanel(id="preview")
        self.search_panel = SearchPanel(app, on_open, id="search")
        self.stats_panel = StatsPanel(app, id="stats")
        self.audit_panel = AuditPanel(app, id="audit")
        self.settings_panel = SettingsPanel(app, id="settings")

    def compose(self) -> ComposeResult:
        yield Label("Inspector", classes="panel-title")
        self.tabs = Tabs(
            Tab("Preview", id="preview"),
            Tab("Search", id="search"),
            Tab("Stats", id="stats"),
            Tab("Audit", id="audit"),
            Tab("Settings", id="settings"),
            id="inspector-tabs",
        )
        yield self.tabs
        self.switcher = ContentSwitcher(
            self.preview_panel,
            self.search_panel,
            self.stats_panel,
            self.audit_panel,
            self.settings_panel,
            id="inspector-switcher",
        )
        yield self.switcher

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        self.switcher.current = event.tab.id

    def show_note(self, note: Note | None) -> None:
        self.preview_panel.show_note(note)
        self.switcher.current = "preview"
        self.tabs.active = "preview"

    async def search(self, query: str) -> None:
        await self.search_panel.perform_search(query)
        self.switcher.current = "search"
        self.tabs.active = "search"

    async def refresh_stats(self) -> None:
        await self.stats_panel.update_stats()

    async def refresh_audit(self) -> None:
        await self.audit_panel.refresh_logs()

    def focus_search(self) -> None:
        self.switcher.current = "search"
        self.tabs.active = "search"
        self.search_panel.focus_input()

    def show_settings(self) -> None:
        self.switcher.current = "settings"
        self.tabs.active = "settings"
        self.settings_panel.focus_first()


class StudioChatPanel(Vertical):
    """Chat panel with command support."""

    def __init__(self, app: PKMAgentApp, on_command: Callable[[str], Any], **kwargs: Any):
        super().__init__(**kwargs)
        self.pkm_app = app
        self.on_command = on_command
        self.messages: list[ChatMessage] = []
        self.streaming = False

    def compose(self) -> ComposeResult:
        yield Label("Conversation", classes="panel-title")
        self.messages_container = VerticalScroll(id="chat-messages")
        yield self.messages_container
        yield Label(
            "Commands: /help, /index, /refresh, /search <query>, /open <path>, /reveal, /obsidian, /settings, /stats, /audit, /clear",
            classes="hint",
        )
        self.chat_input = Input(placeholder="Ask a question or run a /command", id="chat-input")
        self.send_button = Button("Send", variant="primary", id="chat-send")
        yield Horizontal(self.chat_input, self.send_button, id="chat-controls")

    def _set_streaming(self, streaming: bool) -> None:
        self.streaming = streaming
        self.chat_input.disabled = streaming
        self.send_button.disabled = streaming

    async def send_message(self, text: str) -> None:
        """Send a message or run a command."""
        if not text.strip() or self.streaming:
            return

        if text.strip().startswith("/"):
            response = await self.on_command(text.strip())
            if response:
                self._add_message("system", response)
            return
        if self.app.is_busy():
            self._add_message("system", "System is busy. Please wait for background tasks to finish.")
            return

        self._add_message("user", text)
        assistant_msg = self._add_message("assistant", "...")
        self._set_streaming(True)
        self.app.set_busy(True)

        try:
            full_response = ""
            async for chunk in self.pkm_app.ask_with_context(text):
                full_response += chunk
                assistant_msg.query_one(Markdown).update(full_response)
                assistant_msg.query_one(Markdown).scroll_end()
        except Exception as exc:
            assistant_msg.query_one(Markdown).update(f"Error: {exc}")
        finally:
            self.app.set_busy(False)
            self._set_streaming(False)

    def _add_message(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role, content)
        self.messages.append(msg)
        self.messages_container.mount(msg)
        self.messages_container.scroll_end(animate=False)
        return msg

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input != self.chat_input:
            return
        text = self.chat_input.value
        self.chat_input.value = ""
        await self.send_message(text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button != self.send_button:
            return
        text = self.chat_input.value
        self.chat_input.value = ""
        await self.send_message(text)

    def clear_messages(self) -> None:
        self.messages.clear()
        self.messages_container.remove_children()
        self.messages_container.scroll_home(animate=False)

    def focus_input(self) -> None:
        self.chat_input.focus()


class PKMStudio(App):
    """Advanced PKM Agent TUI."""

    CSS = """
    Screen {
        background: #0f1216;
        color: #e6edf3;
    }

    #status-bar {
        background: #16202b;
        color: #9aa7b2;
        padding: 0 1;
        height: 1;
    }

    #status-loading {
        width: 2;
        height: 1;
    }

    #status-text {
        width: 1fr;
    }

    #workspace {
        height: 1fr;
    }

    LibraryPanel, StudioChatPanel, InspectorPanel {
        border: solid #263241;
        background: #121923;
    }

    LibraryPanel {
        width: 30;
        min-width: 28;
    }

    StudioChatPanel {
        width: 1fr;
        background: #10161f;
    }

    InspectorPanel {
        width: 40;
        min-width: 36;
    }

    .panel-title {
        background: #1b2a36;
        color: #c5d0d8;
        padding: 0 1;
    }

    .hint {
        color: #7f8b99;
        padding: 0 1;
    }

    #library-filter {
        margin: 1 1 0 1;
    }

    #library-controls {
        padding: 0 1 1 1;
    }

    #library-list {
        height: 1fr;
        overflow-y: auto;
    }

    #chat-messages {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    .user-message {
        background: #1d2b3a;
        padding: 1;
        margin-bottom: 1;
        border-left: tall #5fb3a3;
    }

    .assistant-message {
        background: #1a1f2b;
        padding: 1;
        margin-bottom: 1;
        border-left: tall #7aa2f7;
    }

    .system-message {
        background: #1a2430;
        padding: 1;
        margin-bottom: 1;
        border-left: tall #f0b36a;
    }

    #chat-controls {
        padding: 1;
        height: 3;
    }

    #chat-input {
        width: 1fr;
    }

    #preview-content {
        height: 1fr;
        padding: 1;
        background: #10161f;
    }

    #preview-markdown {
        width: 1fr;
    }

    #preview-meta {
        padding: 1;
        background: #141c26;
    }

    #search-row {
        padding: 0 1 1 1;
    }

    #search-input {
        width: 1fr;
    }

    #search-results {
        height: 1fr;
        overflow-y: auto;
    }

    #stats-content, #audit-content {
        padding: 1;
        background: #10161f;
        height: 1fr;
        overflow-y: auto;
    }

    #settings-body {
        height: 1fr;
        padding: 1;
        background: #10161f;
    }

    #settings-actions {
        padding: 0 1 1 1;
    }

    #settings-notice {
        color: #9aa7b2;
        padding: 0 1;
        height: 1;
    }

    .settings-section {
        margin-top: 1;
        padding: 0 1;
        color: #c5d0d8;
        background: #141c26;
    }

    .field-label {
        padding: 0 1;
        color: #7f8b99;
    }

    ListView > ListItem {
        padding: 0 1;
    }

    ListView > ListItem.--highlight {
        background: #233041;
    }

    .note-score {
        color: #7f8b99;
    }

    .note-snippet {
        color: #9aa7b2;
    }

    .empty-state {
        color: #7f8b99;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("f1", "show_help", "Help"),
        ("?", "show_help", "Help"),
        ("tab", "focus_next", "Next"),
        ("shift+tab", "focus_previous", "Previous"),
        ("ctrl+1", "focus_library", "Library"),
        ("ctrl+2", "focus_chat", "Chat"),
        ("ctrl+3", "focus_inspector", "Inspector"),
        ("ctrl+l", "focus_filter", "Filter"),
        ("ctrl+f", "focus_search", "Search"),
        ("ctrl+e", "focus_chat_input", "Chat Input"),
        ("ctrl+r", "refresh_panels", "Refresh"),
        ("ctrl+i", "reindex_notes", "Reindex"),
        ("ctrl+o", "open_obsidian", "Open in Obsidian"),
        ("ctrl+shift+o", "reveal_note", "Reveal in Explorer"),
    ]

    def __init__(
        self,
        app: PKMAgentApp,
        initial_prompt: str | None = None,
    ):
        super().__init__()
        self.pkm_app = app
        self.initial_prompt = initial_prompt
        self._status_default = ""
        self._status_reset_timer = None
        self._busy_count = 0
        self._indexing = False
        self.current_note: Note | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.status_loading = LoadingIndicator(id="status-loading")
        self.status_loading.display = False
        self.status_text = Static("", id="status-text")
        self.status_bar = Horizontal(self.status_loading, self.status_text, id="status-bar")
        yield self.status_bar
        yield Horizontal(
            LibraryPanel(self.pkm_app, self.open_note, id="library"),
            StudioChatPanel(self.pkm_app, self.run_command, id="studio-chat"),
            InspectorPanel(self.pkm_app, self.open_note_by_path, id="inspector"),
            id="workspace",
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_status()
        chat = self.query_one(StudioChatPanel)
        chat.focus_input()
        if self.initial_prompt:
            await asyncio.sleep(0.3)
            await chat.send_message(self.initial_prompt)

    def set_busy(self, busy: bool) -> None:
        if busy:
            self._busy_count += 1
        else:
            self._busy_count = max(0, self._busy_count - 1)
        self.status_loading.display = self._busy_count > 0

    def is_busy(self) -> bool:
        return self._busy_count > 0

    def restore_chat_focus(self) -> None:
        chat = self.query_one(StudioChatPanel)
        if chat.chat_input.disabled:
            return
        focused = self.focused
        if isinstance(focused, Input):
            return
        chat.focus_input()

    def on_screen_resume(self, event: events.ScreenResume) -> None:
        self.restore_chat_focus()

    def on_key(self, event: events.Key) -> None:
        if isinstance(self.focused, Input):
            return
        if not event.character or not event.character.isprintable():
            return
        chat = self.query_one(StudioChatPanel)
        if chat.chat_input.disabled:
            return
        chat.focus_input()
        chat.chat_input.insert_text_at_cursor(event.character)
        event.stop()

    def _restore_status(self, _timer: object = None) -> None:
        if self._status_default:
            self.status_text.update(self._status_default)

    def set_status(
        self,
        message: str,
        tone: str = "info",
        persist: bool = False,
        reset_in: float = 3.0,
    ) -> None:
        tone_map = {
            "info": "[dim]",
            "warning": "[bold yellow]",
            "success": "[bold green]",
            "error": "[bold red]",
        }
        prefix = tone_map.get(tone, "")
        suffix = "[/]" if prefix else ""
        formatted = f"{prefix}{message}{suffix}"
        self.status_text.update(formatted)

        if persist:
            self._status_default = formatted
            return

        if self._status_reset_timer:
            self._status_reset_timer.stop()
        self._status_reset_timer = self.set_timer(reset_in, self._restore_status)

    async def refresh_status(self) -> None:
        stats = await self.pkm_app.get_stats()
        status = (
            f"Notes: {stats['notes']:,} | Chunks: {stats['vector_store']['total_chunks']:,} | "
            f"LLM: {stats['llm']['provider']}:{stats['llm']['model']}"
        )
        self.set_status(status, tone="info", persist=True)

    async def refresh_panels(self) -> None:
        library = self.query_one(LibraryPanel)
        inspector = self.query_one(InspectorPanel)
        await library.load_notes()
        await inspector.refresh_stats()
        await inspector.refresh_audit()
        await self.refresh_status()

    def _run_index_sync(self) -> None:
        asyncio.run(self.pkm_app.index_pkm())

    async def reindex_notes(self) -> str:
        if self._indexing:
            self.set_status("Index already running.", tone="warning")
            return "Index already running."

        library = self.query_one(LibraryPanel)
        self._indexing = True
        self.set_busy(True)
        library.set_busy(True)
        self.set_status("Indexing notes...", tone="warning", persist=True)

        try:
            await asyncio.to_thread(self._run_index_sync)
        except Exception as exc:
            message = f"Index failed: {exc}"
            self.set_status(message, tone="error")
            return message
        finally:
            self.set_busy(False)
            library.set_busy(False)
            self._indexing = False

        await self.refresh_panels()
        self.set_status("Index complete.", tone="success")
        return "Index complete."

    async def run_command(self, raw: str) -> str:
        raw = raw.strip()
        if not raw:
            return ""
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lstrip("/").lower()
        arg = parts[1] if len(parts) > 1 else ""

        inspector = self.query_one(InspectorPanel)
        chat = self.query_one(StudioChatPanel)

        try:
            if cmd in {"help", "?"}:
                self.action_show_help()
                return "Help opened."
            if cmd == "index":
                return await self.reindex_notes()
            if cmd == "refresh":
                await self.refresh_panels()
                return "Panels refreshed."
            if cmd == "search":
                if not arg:
                    return "Usage: /search <query>"
                await inspector.search(arg)
                return f"Search results for: {arg}"
            if cmd == "open":
                if not arg:
                    return "Usage: /open <relative path>"
                await self.open_note_by_path(arg)
                return f"Opened: {arg}"
            if cmd == "reveal":
                note = self._resolve_note(arg)
                if not note:
                    return "No note selected. Open a note or pass a path."
                abs_path = self._abs_note_path(note)
                if not abs_path.exists():
                    return f"File not found: {abs_path}"
                self._reveal_in_explorer(note)
                return f"Revealed: {note.path}"
            if cmd == "obsidian":
                note = self._resolve_note(arg)
                if not note:
                    return "No note selected. Open a note or pass a path."
                self._open_in_obsidian(note)
                return f"Opened in Obsidian: {note.path}"
            if cmd == "settings":
                inspector.show_settings()
                return "Settings opened."
            if cmd == "stats":
                await inspector.refresh_stats()
                inspector.switcher.current = "stats"
                inspector.tabs.active = "stats"
                return "Stats updated."
            if cmd == "audit":
                await inspector.refresh_audit()
                inspector.switcher.current = "audit"
                inspector.tabs.active = "audit"
                return "Audit log updated."
            if cmd == "clear":
                chat.clear_messages()
                return "Chat cleared."
        except Exception as exc:
            message = f"Command failed: {exc}"
            self.set_status(message, tone="error")
            return message

        return f"Unknown command: {cmd}"

    async def open_note(self, note: Note) -> None:
        inspector = self.query_one(InspectorPanel)
        inspector.show_note(note)
        self.current_note = note
        self.set_status(f"Previewing: {note.title}", tone="info")

    def _resolve_note(self, raw_path: str) -> Note | None:
        raw_path = raw_path.strip()
        if raw_path:
            note = self.pkm_app.db.get_note_by_path(raw_path)
            if note:
                return note

            candidate = Path(raw_path)
            if candidate.is_absolute():
                try:
                    rel_path = candidate.relative_to(self.pkm_app.config.pkm_root)
                    return self.pkm_app.db.get_note_by_path(str(rel_path))
                except ValueError:
                    return None
            return None

        return self.current_note

    def _abs_note_path(self, note: Note) -> Path:
        return self.pkm_app.config.pkm_root / note.path

    def _open_uri(self, uri: str) -> None:
        if sys.platform.startswith("win"):
            os.startfile(uri)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", uri])
        else:
            subprocess.Popen(["xdg-open", uri])

    def _reveal_in_explorer(self, note: Note) -> None:
        abs_path = self._abs_note_path(note)
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", str(abs_path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(abs_path)])
        else:
            subprocess.Popen(["xdg-open", str(abs_path.parent)])

    def _open_in_obsidian(self, note: Note) -> None:
        vault = self.pkm_app.config.pkm_root.name
        file_path = note.path.as_posix()
        uri = f"obsidian://open?vault={quote(vault)}&file={quote(file_path)}"
        self._open_uri(uri)

    async def open_note_by_path(self, path: str) -> None:
        raw_path = path.strip()
        note = self._resolve_note(raw_path)
        if not note:
            self.set_status(f"Note not found: {path}", tone="error")
            return
        await self.open_note(note)

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_focus_library(self) -> None:
        self.query_one(LibraryPanel).list_view.focus()

    def action_focus_chat(self) -> None:
        self.query_one(StudioChatPanel).focus_input()

    def action_focus_chat_input(self) -> None:
        self.query_one(StudioChatPanel).focus_input()

    def action_focus_inspector(self) -> None:
        self.query_one(InspectorPanel).tabs.focus()

    def action_focus_filter(self) -> None:
        self.query_one(LibraryPanel).focus_filter()

    def action_focus_search(self) -> None:
        self.query_one(InspectorPanel).focus_search()

    async def action_refresh_panels(self) -> None:
        await self.refresh_panels()
        self.set_status("Panels refreshed.", tone="info")

    async def action_reindex_notes(self) -> None:
        await self.reindex_notes()

    async def action_reveal_note(self) -> None:
        note = self._resolve_note("")
        if not note:
            self.set_status("No note selected to reveal.", tone="warning")
            return
        abs_path = self._abs_note_path(note)
        if not abs_path.exists():
            self.set_status(f"File not found: {abs_path}", tone="error")
            return
        self._reveal_in_explorer(note)
        self.set_status(f"Revealed: {note.path}", tone="info")

    async def action_open_obsidian(self) -> None:
        note = self._resolve_note("")
        if not note:
            self.set_status("No note selected to open.", tone="warning")
            return
        self._open_in_obsidian(note)
        self.set_status(f"Opened in Obsidian: {note.path}", tone="info")
