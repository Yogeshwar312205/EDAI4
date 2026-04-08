"""
EDAI4 - Layer 2 Test Runner
Runs all unit and integration tests for the perception layer
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all Layer 2 tests."""
    
    print("\n" + "="*70)
    print("  EDAI4 - Layer 2 Test Suite")
    print("  Perception Layer (OCR & Text-Symbol Association)")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'tests.test_text_normalizer_unit',
        'tests.test_text_symbol_associator_unit',
        'tests.test_perception_pipeline_integration',
    ]
    
    for module_name in test_modules:
        try:
            tests = loader.loadTestsFromName(module_name)
            suite.addTests(tests)
            print(f"✓ Loaded: {module_name}")
        except Exception as e:
            print(f"✗ Failed to load {module_name}: {e}")
    
    print(f"\nTotal test cases: {suite.countTestCases()}")
    print("-"*70)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test module or test case."""
    
    print(f"\nRunning: {test_name}\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def list_all_tests():
    """List all available tests."""
    
    print("\n" + "="*70)
    print("  AVAILABLE TESTS")
    print("="*70 + "\n")
    
    test_modules = [
        ('tests.test_text_normalizer_unit', 'TextNormalizer unit tests'),
        ('tests.test_text_symbol_associator_unit', 'TextSymbolAssociator unit tests'),
        ('tests.test_perception_pipeline_integration', 'PerceptionPipeline integration tests'),
    ]
    
    for module, description in test_modules:
        print(f"{module}")
        print(f"  {description}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run EDAI4 Layer 2 tests')
    parser.add_argument(
        'test',
        nargs='?',
        help='Specific test to run (e.g., tests.test_text_normalizer_unit.TestInstrumentTagParsing)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tests'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_all_tests()
    elif args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
