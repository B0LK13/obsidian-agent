"""
Quick Verification - Check if all implementations are ready
Run this first to verify the environment is set up correctly
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python {version.major}.{version.minor} - Need 3.11+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    packages = {
        'watchdog': 'File system monitoring',
        'websockets': 'WebSocket sync server',
        'rapidfuzz': 'Fuzzy string matching',
        'textual': 'TUI framework',
        'chromadb': 'Vector database',
        'openai': 'LLM integration',
    }
    
    missing = []
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✅ {package:15s} - {description}")
        except ImportError:
            print(f"❌ {package:15s} - {description} (MISSING)")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_files():
    """Check if all implementation files exist."""
    base_path = Path(__file__).parent / "pkm-agent" / "src" / "pkm_agent"
    
    files = {
        "exceptions.py": "Exception hierarchy",
        "data/file_watcher.py": "File system watcher",
        "data/link_analyzer.py": "Link analyzer",
        "data/link_healer.py": "Link healer",
        "websocket_sync.py": "WebSocket sync server",
    }
    
    missing = []
    for file, description in files.items():
        file_path = base_path / file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"✅ {file:30s} - {description} ({size_kb:.1f} KB)")
        else:
            print(f"❌ {file:30s} - {description} (MISSING)")
            missing.append(file)
    
    return len(missing) == 0, missing

def check_typescript():
    """Check TypeScript plugin."""
    plugin_path = Path(__file__).parent / "obsidian-pkm-agent"
    
    files = {
        "src/SyncClient.ts": "TypeScript sync client",
        "main.tsx": "Plugin main file",
        "package.json": "NPM configuration",
    }
    
    missing = []
    for file, description in files.items():
        file_path = plugin_path / file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"✅ {file:30s} - {description} ({size_kb:.1f} KB)")
        else:
            print(f"❌ {file:30s} - {description} (MISSING)")
            missing.append(file)
    
    return len(missing) == 0, missing

def main():
    """Run all checks."""
    print("="*60)
    print(" PKM-Agent Environment Verification")
    print("="*60)
    print()
    
    all_ok = True
    
    # Check Python
    print("[1/4] Python Version")
    if not check_python_version():
        all_ok = False
    print()
    
    # Check dependencies
    print("[2/4] Python Dependencies")
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        all_ok = False
        print()
        print(f"Missing {len(missing_deps)} packages. Install with:")
        print(f"  pip install -e \".[dev]\"")
    print()
    
    # Check Python files
    print("[3/4] Python Implementation Files")
    files_ok, missing_files = check_files()
    if not files_ok:
        all_ok = False
        print()
        print(f"Missing {len(missing_files)} implementation files!")
    print()
    
    # Check TypeScript files
    print("[4/4] TypeScript Plugin Files")
    ts_ok, missing_ts = check_typescript()
    if not ts_ok:
        all_ok = False
        print()
        print(f"Missing {len(missing_ts)} TypeScript files!")
    print()
    
    # Summary
    print("="*60)
    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready to test!")
        print()
        print("Next steps:")
        print("  1. Run: python test_comprehensive.py")
        print("  2. Run: python demo_poc.py")
        print("  3. Build plugin: cd obsidian-pkm-agent && npm run build")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before testing")
        print()
        if not deps_ok:
            print("Install dependencies:")
            print("  cd pkm-agent")
            print("  pip install -e \".[dev]\"")
        return 1

if __name__ == "__main__":
    sys.exit(main())
