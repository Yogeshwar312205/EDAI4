"""
Test Script for Interactive Flow Simulator
==========================================
Quick test to verify the flow simulation endpoint works correctly.
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/simulate-flow"

# Test Case 1: Simple linear flow (all valves open)
test_case_1 = {
    "topology": {
        "nodes": [
            {"id": "Tank-101", "type": "equipment.tank", "label": "Feed Tank", "x": 0, "y": 0},
            {"id": "V-101", "type": "valve.gate", "label": "Isolation Valve", "x": 100, "y": 0},
            {"id": "Pump-201", "type": "equipment.pump", "label": "Transfer Pump", "x": 200, "y": 0},
            {"id": "V-102", "type": "valve.ball", "label": "Discharge Valve", "x": 300, "y": 0},
            {"id": "Tank-501", "type": "equipment.tank", "label": "Storage Tank", "x": 400, "y": 0}
        ],
        "edges": [
            {"source": "Tank-101", "target": "V-101"},
            {"source": "V-101", "target": "Pump-201"},
            {"source": "Pump-201", "target": "V-102"},
            {"source": "V-102", "target": "Tank-501"}
        ]
    },
    "start_node_id": "Tank-101",
    "closed_valve_ids": []
}

# Test Case 2: Flow blocked by closed valve
test_case_2 = {
    **test_case_1,
    "closed_valve_ids": ["V-102"]
}

# Test Case 3: Multiple closed valves
test_case_3 = {
    **test_case_1,
    "closed_valve_ids": ["V-101", "V-102"]
}


def run_test(test_name, test_data):
    """Run a single test case."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_URL, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"\nResults:")
            print(f"  Active Nodes: {len(result['active_node_ids'])}")
            print(f"  Active Edges: {len(result['active_edge_ids'])}")
            print(f"  Blocked Nodes: {len(result['blocked_nodes'])}")
            print(f"  Total Distance: {result['total_distance']:.1f}px")
            print(f"\nMessage:")
            print(f"  {result['message']}")
            print(f"\nFlow Path:")
            for i, node in enumerate(result['flow_path'], 1):
                blocked = " 🔴 BLOCKED" if node in result['blocked_nodes'] else ""
                print(f"  {i}. {node}{blocked}")
            return True
        else:
            print(f"❌ FAILED")
            print(f"  Status Code: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR")
        print(f"  Could not connect to {API_URL}")
        print(f"  Make sure the backend is running:")
        print(f"    uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Interactive Flow Simulator - Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(run_test(
        "Test 1: All Valves Open",
        test_case_1
    ))
    
    results.append(run_test(
        "Test 2: One Valve Closed (V-102)",
        test_case_2
    ))
    
    results.append(run_test(
        "Test 3: Multiple Valves Closed (V-101, V-102)",
        test_case_3
    ))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
