# Obsidian Agent Python Backend - Installation & Usage Guide

## Overview

The Python backend provides powerful CLI tools for indexing and searching your Obsidian vault using full-text search with the Whoosh library.

## Features

- **Fast Indexing**: Index all markdown files in your vault with metadata extraction
- **Full-Text Search**: Search across titles, content, and tags with relevance scoring
- **Vault Statistics**: View comprehensive statistics about your knowledge base
- **Automated Indexing**: Set up systemd service for periodic reindexing
- **Metadata Support**: Extract and index frontmatter metadata (title, tags, etc.)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment support (included in Python 3.3+)

### Quick Start

1. Clone or download the repository:
   ```bash
   git clone https://github.com/B0LK13/obsidian-agent.git
   cd obsidian-agent
   ```

2. Run the automated setup script:
   ```bash
   ./setup.sh
   ```

   This script will:
   - Create a Python virtual environment in `venv/`
   - Install all required dependencies
   - Make the CLI wrapper executable

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Verify installation:
   ```bash
   obsidian-agent --version
   ```

## Usage

### Indexing Your Vault

Index all markdown files in your vault:

```bash
obsidian-agent index /path/to/your/vault
```

Options:
- `--index-dir, -i <path>`: Specify custom index directory (default: `<vault>/.obsidian/agent-index`)
- `--force, -f`: Force reindex all documents

Example:
```bash
obsidian-agent index ~/Documents/MyVault --force
```

### Searching

Search your indexed vault:

```bash
obsidian-agent search "your search query" --vault-path /path/to/your/vault
```

Options:
- `--vault-path, -v <path>`: Path to your vault (default: current directory)
- `--limit, -l <number>`: Maximum results to return (default: 10)
- `--fields, -f <field>`: Fields to search (can specify multiple: title, content, tags)

Examples:
```bash
# Search in current directory
obsidian-agent search "machine learning"

# Search with limit
obsidian-agent search "python programming" --vault-path ~/MyVault --limit 5

# Search only in titles and tags
obsidian-agent search "tutorial" -v ~/MyVault -f title -f tags
```

### Vault Statistics

View statistics about your vault:

```bash
obsidian-agent stats /path/to/your/vault
```

This displays:
- Total indexed documents
- Total vault markdown files
- Vault path
- Index location

### Using the Wrapper Script

If you don't want to activate the virtual environment each time, use the wrapper script:

```bash
./bin/obsidian-agent index ~/MyVault
./bin/obsidian-agent search "query" --vault-path ~/MyVault
./bin/obsidian-agent stats ~/MyVault
```

## Systemd Service (Linux)

Set up automated indexing to run periodically:

### Installation

1. Edit `obsidian-agent.service` and update the vault path:
   ```ini
   ExecStart=/usr/local/bin/obsidian-agent index /your/vault/path
   ```

2. Copy service files to systemd directory:
   ```bash
   sudo cp obsidian-agent.service /etc/systemd/system/
   sudo cp obsidian-agent.timer /etc/systemd/system/
   ```

3. Copy the CLI to system bin:
   ```bash
   sudo cp bin/obsidian-agent /usr/local/bin/
   ```

4. Enable and start the timer:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable obsidian-agent.timer
   sudo systemctl start obsidian-agent.timer
   ```

### Verify Service

Check timer status:
```bash
sudo systemctl status obsidian-agent.timer
```

View service logs:
```bash
sudo journalctl -u obsidian-agent.service
```

### Configuration

The timer runs indexing:
- 5 minutes after boot
- Every hour thereafter

To change the schedule, edit `obsidian-agent.timer` and reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart obsidian-agent.timer
```

## Dependencies

The backend uses the following Python packages:

- **click** (>=8.1.0): CLI framework
- **whoosh** (>=2.7.4): Full-text search engine
- **pydantic** (>=2.0.0): Data validation
- **watchdog** (>=3.0.0): File system monitoring
- **python-frontmatter** (>=1.0.0): Frontmatter parsing
- **rich** (>=13.0.0): Terminal formatting

All dependencies are automatically installed by `setup.sh`.

## Troubleshooting

### Virtual Environment Not Found

If you see "Virtual environment not found":
```bash
cd /path/to/obsidian-agent
./setup.sh
```

### Index Not Found

If searching fails with "No index found":
```bash
obsidian-agent index /path/to/your/vault
```

### Permission Denied

If wrapper script is not executable:
```bash
chmod +x bin/obsidian-agent
```

### Python Version Issues

Check Python version:
```bash
python3 --version
```

Requires Python 3.8 or higher. Update Python if needed.

## Development

### Installing in Development Mode

The package is installed in editable mode by default, so changes to the source code are immediately reflected.

### Running Tests

Create a test vault:
```bash
mkdir -p /tmp/test-vault
echo -e "---\ntitle: Test Note\n---\n\n# Hello World" > /tmp/test-vault/test.md
```

Test indexing:
```bash
obsidian-agent index /tmp/test-vault
```

Test search:
```bash
obsidian-agent search "hello" --vault-path /tmp/test-vault
```

## Support

For issues, questions, or contributions:
- Open an issue on [GitHub](https://github.com/B0LK13/obsidian-agent/issues)
- Check existing documentation in README.md

## License

MIT License - see LICENSE file for details
