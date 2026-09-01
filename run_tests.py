#!/usr/bin/env python3
"""
Phase 1 Test Execution Report Generator
Runs all tests and displays complete PASS/FAIL output
"""

import sys
import unittest
import io
from pathlib import Path

# Ensure proper path resolution
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def main():
    print("\n" + "=" * 100)
    print("JANGIRA AUTOPRINT - PHASE 1 TEST EXECUTION REPORT")
    print("=" * 100)
    print()
    
    # Import test module
    try:
        from tests import test_phase1
        print(f"✅ Test module loaded successfully")
        print()
    except ImportError as e:
        print(f"❌ Failed to load test module: {e}")
        return 1
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        test_phase1.TestLogger,
        test_phase1.TestDatabase,
        test_phase1.TestPrinterManager,
        test_phase1.TestPDFValidator,
        test_phase1.TestPDFManager,
        test_phase1.TestPDFProcessor,
        test_phase1.TestJobExecutor,
        test_phase1.TestJobQueue,
        test_phase1.TestConfiguration,
        test_phase1.TestIntegration
    ]
    
    print(f"Loading {len(test_classes)} test classes...")
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
        print(f"  ✓ {test_class.__name__}")
    
    total_tests = suite.countTestCases()
    print(f"\nTotal tests to run: {total_tests}")
    print()
    print("-" * 100)
    print("TEST EXECUTION OUTPUT:")
    print("-" * 100)
    print()
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print()
    print("-" * 100)
    print("TEST SUMMARY")
    print("-" * 100)
    print()
    
    print(f"Tests Run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print()
    
    if result.failures:
        print("FAILED TESTS:")
        for test, traceback in result.failures:
            print(f"\n  ❌ {test}")
            print(f"  {traceback}")
    
    if result.errors:
        print("ERROR TESTS:")
        for test, traceback in result.errors:
            print(f"\n  ❌ {test}")
            print(f"  {traceback}")
    
    print()
    print("=" * 100)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        print("=" * 100)
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("=" * 100)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
