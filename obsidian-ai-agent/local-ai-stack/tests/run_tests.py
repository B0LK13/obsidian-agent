#!/usr/bin/env python3
"""
Test runner for Obsidian AI Agent
Runs all unit tests with coverage reporting
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests():
    """Discover and run all tests"""
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


def run_with_coverage():
    """Run tests with coverage reporting"""
    try:
        import coverage
        
        # Start coverage
        cov = coverage.Coverage(
            source=['ai_stack'],
            omit=['*/tests/*', '*/venv/*']
        )
        cov.start()
        
        # Run tests
        exit_code = run_tests()
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        # Report
        print("\n" + "="*70)
        print("COVERAGE REPORT")
        print("="*70)
        cov.report()
        
        # Generate HTML report
        html_dir = Path(__file__).parent / "coverage_html"
        cov.html_report(directory=str(html_dir))
        print(f"\nHTML coverage report saved to: {html_dir}")
        
        return exit_code
        
    except ImportError:
        print("coverage package not installed. Running tests without coverage.")
        print("Install with: pip install coverage")
        return run_tests()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Obsidian AI Agent tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--module', help='Run specific test module (e.g., test_memory_rag)')
    
    args = parser.parse_args()
    
    if args.module:
        # Run specific module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(args.module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    elif args.coverage:
        sys.exit(run_with_coverage())
    else:
        sys.exit(run_tests())
