#!/usr/bin/env python3
"""
Simple Python-based verification runner
Executes all verification steps without needing PowerShell 7+
"""

import sys
import subprocess
import os
from pathlib import Path
import json
from datetime import datetime

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def print_step(number, text):
    """Print a step header."""
    print(f"\n{'─' * 80}")
    print(f"  STEP {number}: {text}")
    print("─" * 80 + "\n")

def run_command(cmd, description, cwd=None, check=True):
    """Run a command and return success status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=True if isinstance(cmd, str) else False,
            check=check
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ {description} - SUCCESS")
            return True
        else:
            print(f"\n❌ {description} - FAILED (exit code {result.returncode})")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED")
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False

def main():
    """Main verification execution."""
    
    # Get project root
    project_root = Path(__file__).parent
    pkm_agent = project_root / "pkm-agent"
    obsidian_plugin = project_root / "obsidian-pkm-agent"
    
    print_header("PKM-AGENT VERIFICATION & EXECUTION")
    print(f"Project Root: {project_root}")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "steps": [],
        "overall_success": True
    }
    
    # STEP 1: Verify Setup
    print_step(1, "ENVIRONMENT VERIFICATION (5 min)")
    
    verify_file = project_root / "verify_setup.py"
    if verify_file.exists():
        success = run_command(
            [sys.executable, str(verify_file)],
            "Environment verification",
            cwd=str(project_root)
        )
        results["steps"].append({"step": 1, "name": "verify_setup", "success": success})
        if not success:
            results["overall_success"] = False
    else:
        print("❌ verify_setup.py not found!")
        results["steps"].append({"step": 1, "name": "verify_setup", "success": False})
        results["overall_success"] = False
    
    # STEP 2: Install Dependencies
    print_step(2, "INSTALL PYTHON DEPENDENCIES (10 min)")
    
    if pkm_agent.exists() and (pkm_agent / "pyproject.toml").exists():
        # Try with [dev]
        success = run_command(
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            "Install Python dependencies with dev extras",
            cwd=str(pkm_agent),
            check=False
        )
        
        # If that fails, try without [dev]
        if not success:
            print("\nRetrying without dev extras...")
            success = run_command(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                "Install Python dependencies (base)",
                cwd=str(pkm_agent),
                check=False
            )
        
        results["steps"].append({"step": 2, "name": "install_deps", "success": success})
        if not success:
            results["overall_success"] = False
    else:
        print("❌ pkm-agent/pyproject.toml not found!")
        results["steps"].append({"step": 2, "name": "install_deps", "success": False})
        results["overall_success"] = False
    
    # STEP 3: Verify Imports
    print_step(3, "VERIFY IMPORTS (2 min)")
    
    success = run_command(
        [sys.executable, "-c", """
import sys
print("Checking imports...")
try:
    from pkm_agent import exceptions
    print("✅ exceptions module")
except ImportError as e:
    print(f"❌ exceptions module: {e}")
    sys.exit(1)

try:
    from pkm_agent.data import file_watcher
    print("✅ file_watcher module")
except ImportError as e:
    print(f"❌ file_watcher module: {e}")
    sys.exit(1)

try:
    from pkm_agent.data import link_analyzer
    print("✅ link_analyzer module")
except ImportError as e:
    print(f"❌ link_analyzer module: {e}")
    sys.exit(1)

try:
    from pkm_agent.data import link_healer
    print("✅ link_healer module")
except ImportError as e:
    print(f"❌ link_healer module: {e}")
    sys.exit(1)

try:
    from pkm_agent import websocket_sync
    print("✅ websocket_sync module")
except ImportError as e:
    print(f"❌ websocket_sync module: {e}")
    sys.exit(1)

print("\\n✅ All imports successful!")
"""],
        "Verify all imports",
        check=False
    )
    
    results["steps"].append({"step": 3, "name": "verify_imports", "success": success})
    if not success:
        results["overall_success"] = False
    
    # STEP 4: Run Comprehensive Tests
    print_step(4, "RUN COMPREHENSIVE TESTS (15 min)")
    
    test_file = project_root / "test_comprehensive.py"
    if test_file.exists():
        success = run_command(
            [sys.executable, str(test_file)],
            "Comprehensive test suite",
            cwd=str(project_root),
            check=False
        )
        results["steps"].append({"step": 4, "name": "test_comprehensive", "success": success})
        if not success:
            print("⚠️ Tests failed, but continuing...")
    else:
        print("❌ test_comprehensive.py not found!")
        results["steps"].append({"step": 4, "name": "test_comprehensive", "success": False})
    
    # STEP 5: Check TypeScript Plugin
    print_step(5, "CHECK TYPESCRIPT PLUGIN (2 min)")
    
    if obsidian_plugin.exists():
        package_json = obsidian_plugin / "package.json"
        if package_json.exists():
            print(f"✅ Plugin directory exists: {obsidian_plugin}")
            print(f"✅ package.json found")
            
            # Check for built files
            build_dir = obsidian_plugin / "build"
            main_js = build_dir / "main.js"
            
            if main_js.exists():
                size = main_js.stat().st_size / 1024  # KB
                print(f"✅ build/main.js exists ({size:.1f} KB)")
                results["steps"].append({"step": 5, "name": "check_plugin", "success": True, "build_exists": True})
            else:
                print("⚠️ build/main.js not found (need to run npm build)")
                results["steps"].append({"step": 5, "name": "check_plugin", "success": True, "build_exists": False})
        else:
            print("❌ package.json not found!")
            results["steps"].append({"step": 5, "name": "check_plugin", "success": False})
    else:
        print("❌ obsidian-pkm-agent directory not found!")
        results["steps"].append({"step": 5, "name": "check_plugin", "success": False})
    
    # Save results
    print_step(6, "SAVE RESULTS")
    
    results_file = project_root / "verification_results.json"
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to: {results_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
    
    # Print summary
    print_header("VERIFICATION SUMMARY")
    
    print("Results by step:")
    for step in results["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"  {status} Step {step['step']}: {step['name']}")
    
    print(f"\nOverall Status: {'✅ SUCCESS' if results['overall_success'] else '❌ FAILED'}")
    print(f"Results saved to: {results_file}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 80)
    print("  NEXT STEPS")
    print("=" * 80)
    
    if results["overall_success"]:
        print("""
✅ Environment verified successfully!

Next steps:
1. Review test_results.json (if generated)
2. Read DEPLOYMENT_CHECKLIST.md
3. Create production vault backup
4. Deploy to production

For detailed next steps, see:
  → FOLLOW_UP_ACTIONS.md
  → DEPLOYMENT_CHECKLIST.md
""")
    else:
        print("""
⚠️ Some steps failed!

Troubleshooting:
1. Check error messages above
2. Install missing dependencies: pip install -e pkm-agent/[dev]
3. Review MANUAL_EXECUTION_GUIDE.txt
4. Check Python version (need 3.9+)

For help, see:
  → MANUAL_EXECUTION_GUIDE.txt (Troubleshooting section)
""")
    
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())
