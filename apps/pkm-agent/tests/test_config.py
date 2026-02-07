from pathlib import Path
from textwrap import dedent

from pkm_agent.config import Config, load_config


def test_ensure_dirs_creates_required_structure(tmp_path: Path) -> None:
    data_dir = tmp_path / ".pkm-agent-test"
    cfg = Config(data_dir=data_dir)

    cfg.ensure_dirs()

    assert cfg.data_dir.exists()
    assert cfg.chroma_path.exists()
    assert cfg.cache_path.exists()


def test_load_config_respects_toml(tmp_path: Path) -> None:
    vault_dir = tmp_path / "vault"
    data_dir = tmp_path / ".pkm-config"
    config_file = tmp_path / "pkm_config.toml"
    config_file.write_text(
        dedent(
            f"""
            [general]
            pkm_root = "{vault_dir.as_posix()}"
            data_dir = "{data_dir.as_posix()}"

            [llm]
            provider = "ollama"
            model = "llama-3.2-7b"

            [rag]
            chunk_size = 256
            chunk_overlap = 32

            [tui]
            theme = "gruvbox"
            """
        )
    )

    cfg = load_config(config_file)

    assert cfg.pkm_root == vault_dir
    assert cfg.data_dir == data_dir
    assert cfg.llm.provider == "ollama"
    assert cfg.llm.model == "llama-3.2-7b"
    assert cfg.rag.chunk_size == 256
    assert cfg.rag.chunk_overlap == 32
    assert cfg.tui.theme == "gruvbox"
