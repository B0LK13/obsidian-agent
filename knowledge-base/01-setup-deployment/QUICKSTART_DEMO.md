# 🚀 PKM-Agent Demo Quickstart Guide

This guide will help you set up and run the PKM-Agent Proof of Concept (PoC) demo locally.

## Prerequisites

- **Python 3.12+** installed and added to PATH.
- **PowerShell** or **Git Bash** (Terminal).

## 📂 Directory Setup

Ensure you are in the project root directory:
```powershell
cd C:\Users\Admin\Documents\B0LK13v2
```

## ⚡ Option 1: Quick Run (No Install Required)

You can run the demo directly by setting the `PYTHONPATH` environment variable. This is the fastest way to verify the current codebase.

### 1. Run the Demo

**PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONPATH="$PWD\B0LK13v2\pkm-agent\src"
python B0LK13v2\demo_poc.py
```

**Git Bash:**
```bash
export PYTHONIOENCODING=utf-8
export PYTHONPATH="$PWD/B0LK13v2/pkm-agent/src"
python B0LK13v2/demo_poc.py
```

### 2. Run the Test Suite

**PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONPATH="$PWD\B0LK13v2\pkm-agent\src"
python B0LK13v2\test_comprehensive.py
```

**Git Bash:**
```bash
export PYTHONIOENCODING=utf-8
export PYTHONPATH="$PWD/B0LK13v2/pkm-agent/src"
python B0LK13v2/test_comprehensive.py
```

## 📦 Option 2: Standard Installation (Recommended for Development)

If you plan to modify the code, it's best to install the package in editable mode.

1.  **Create a Virtual Environment:**
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate
    ```

2.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    pip install -e B0LK13v2/pkm-agent
    ```

3.  **Run Demo:**
    ```powershell
    python B0LK13v2/demo_poc.py
    ```

## 🔍 Troubleshooting

-   **ModuleNotFoundError: No module named 'pkm_agent'**: This means Python cannot find the source code. Ensure `$env:PYTHONPATH` correctly points to the `src` directory inside `pkm-agent`.
-   **UnicodeEncodeError**: Ensure you set `$env:PYTHONIOENCODING="utf-8"` before running the scripts to handle emojis and special characters correctly in the terminal.
