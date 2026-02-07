import pytest

from pkm_agent.tui import (
    AgentModeSelector,
    QuickSettingsPanel,
    RelatedContextPanel,
    PerformancePanel,
)


def test_agent_mode_selector_changes_active_mode() -> None:
    selector = AgentModeSelector()
    selector.set_active("voice")

    assert selector.active_mode == "voice"


def test_quick_settings_panel_initial_values() -> None:
    quick = QuickSettingsPanel()

    assert quick.temperature == 0.7
    assert quick.context_window == "8K tokens"


def test_related_context_panel_has_default_items() -> None:
    panel = RelatedContextPanel()

    assert len(panel.context_items) == 3
    assert panel.context_items[0][0] == "Quantum Gates.md"


class DummyStatsApp:
    async def get_stats(self) -> dict[str, dict[str, str]]:
        return {
            "vector_store": {"total_chunks": 100, "collection_name": "vault"},
            "llm": {"provider": "ollama", "model": "llama-3.2-7b"},
        }


@pytest.mark.asyncio
async def test_performance_panel_renders_stats() -> None:
    panel = PerformancePanel(DummyStatsApp())

    await panel.update_stats()

    assert "Query Time" in panel.latest_stats


def test_ascii_art_header_reflects_branding() -> None:
    from pkm_agent.tui import ChatPanel

    art = ChatPanel._ascii_art()
    assert "OBSIDIAN" in art.replace(" ", "")
    assert "LOCAL-FIRST" in art
