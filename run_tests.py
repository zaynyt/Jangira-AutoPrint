"""Phase 1 Tests Execution Report"""

import subprocess
import sys
from pathlib import Path

def run_phase1_tests():
    """Run Phase 1 tests and display results"""
    
    print("=" * 80)
    print("JANGIRA AUTOPRINT - PHASE 1 TEST EXECUTION")
    print("=" * 80)
    print()
    
    # Change to repo root
    repo_root = Path(__file__).parent
    
    print(f"Repository Root: {repo_root}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Run tests
    print("Running Phase 1 Tests...")
    print("-" * 80)
    
    cmd = [sys.executable, "-m", "unittest", "tests.test_phase1", "-v"]
    
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    print("-" * 80)
    
    # Summary
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_phase1_tests()
    sys.exit(exit_code)
