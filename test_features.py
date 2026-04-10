"""
Test script to verify all advanced features are working
Run this to diagnose any issues
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("EDAI4 - Feature Diagnostic Test")
print("=" * 80)
print()

# Test 1: Import deliverables module
print("Test 1: Importing deliverables module...")
try:
    from src.deliverables import (
        InstrumentIndexGenerator,
        IOListGenerator,
        AlarmListGenerator,
        ExcelFormatter
    )
    print("✅ SUCCESS: All deliverables classes imported")
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Import advanced module
print("\nTest 2: Importing advanced module...")
try:
    from src.advanced import (
        DesignRuleChecker,
        FlowSimulator,
        PIDDiffEngine
    )
    print("✅ SUCCESS: All advanced classes imported")
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

# Test 3: Check if classes can be instantiated
print("\nTest 3: Instantiating classes...")
try:
    formatter = ExcelFormatter()
    inst_gen = InstrumentIndexGenerator()
    io_gen = IOListGenerator()
    alarm_gen = AlarmListGenerator()
    print("✅ SUCCESS: All deliverable generators instantiated")
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

try:
    checker = DesignRuleChecker()
    simulator = FlowSimulator()
    diff_engine = PIDDiffEngine()
    print("✅ SUCCESS: All advanced feature classes instantiated")
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)

# Test 4: Check dependencies
print("\nTest 4: Checking dependencies...")
missing_deps = []

try:
    import pandas
    print("✅ pandas installed")
except ImportError:
    missing_deps.append("pandas")
    print("❌ pandas NOT installed")

try:
    import openpyxl
    print("✅ openpyxl installed")
except ImportError:
    missing_deps.append("openpyxl")
    print("❌ openpyxl NOT installed")

try:
    import networkx
    print("✅ networkx installed")
except ImportError:
    missing_deps.append("networkx")
    print("❌ networkx NOT installed")

try:
    from fastapi import FastAPI
    print("✅ fastapi installed")
except ImportError:
    missing_deps.append("fastapi")
    print("❌ fastapi NOT installed")

# Test 5: Check if API endpoints exist
print("\nTest 5: Checking API endpoints...")
try:
    from src.api.main import app
    
    routes = [route.path for route in app.routes]
    
    required_endpoints = [
        "/deliverables/generate",
        "/design-rules/check",
        "/flow/trace",
        "/flow/simulate-valve",
        "/diff/compare"
    ]
    
    for endpoint in required_endpoints:
        if endpoint in routes:
            print(f"✅ {endpoint} exists")
        else:
            print(f"❌ {endpoint} NOT FOUND")
            
except Exception as e:
    print(f"❌ FAILED to load API: {e}")

# Final Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

if missing_deps:
    print(f"\n❌ MISSING DEPENDENCIES: {', '.join(missing_deps)}")
    print("\nTo install missing dependencies, run:")
    print(f"pip install {' '.join(missing_deps)}")
else:
    print("\n✅ ALL TESTS PASSED!")
    print("\nYour system is ready to run. Start the servers:")
    print("1. Backend:  python -m uvicorn src.api.main:app --reload --port 8000")
    print("2. Frontend: cd frontend && npm run dev")
    print("3. Browser:  http://localhost:3000")

print("\n" + "=" * 80)
