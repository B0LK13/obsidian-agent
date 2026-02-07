Using pip (recommended)
cd pkm-agent
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ollama]"
- .[dev,ollama] installs core + dev tools (pytest, ruff, mypy) and Ollama extras.
- If you don’t need Ollama, use .[dev].
If python points to Python 2 on your system, use:
cd pkm-agent
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev,ollama]"
Optional: only core runtime (no dev tools, no ollama)
cd pkm-agent
python -m pip install -e .