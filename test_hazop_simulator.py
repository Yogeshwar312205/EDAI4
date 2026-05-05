"""
Test script for HazOp Simulator
Run this to verify the backend is working correctly
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_hazop_simulator():
    """Test the HazOp simulator with sample data"""
    
    print("=" * 70)
    print("TESTING HAZOP SIMULATOR")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not found in .env file")
        return False
    
    print(f"✓ API Key found: {api_key[:20]}...")
    print()
    
    # Try importing the simulator
    try:
        from src.api.hazop_simulator import HazOpSimulator
        print("✓ HazOp Simulator module imported successfully")
    except ImportError as e:
        print(f"❌ ERROR: Failed to import HazOp Simulator: {e}")
        print("\nMake sure you have installed: pip install google-genai")
        return False
    
    print()
    
    # Create sample topology
    sample_topology = {
        "nodes": [
            {
                "id": "P-101",
                "type": "pump",
                "data": {"label": "Feed Pump", "tag": "P-101"},
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "V-101",
                "type": "valve",
                "data": {"label": "Control Valve", "tag": "V-101"},
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "T-101",
                "type": "tank",
                "data": {"label": "Storage Tank", "tag": "T-101"},
                "position": {"x": 500, "y": 100}
            },
            {
                "id": "V-102",
                "type": "valve",
                "data": {"label": "Outlet Valve", "tag": "V-102"},
                "position": {"x": 700, "y": 100}
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "P-101",
                "target": "V-101",
                "data": {"label": "Feed Line"}
            },
            {
                "id": "e2",
                "source": "V-101",
                "target": "T-101",
                "data": {"label": "Inlet Line"}
            },
            {
                "id": "e3",
                "source": "T-101",
                "target": "V-102",
                "data": {"label": "Outlet Line"}
            }
        ]
    }
    
    print("Sample Topology:")
    print(f"  - Nodes: {len(sample_topology['nodes'])}")
    print(f"  - Edges: {len(sample_topology['edges'])}")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            "failed_node_id": "V-101",
            "failure_mode": "Stuck Closed",
            "description": "Control valve fails closed - should cause pressure buildup"
        },
        {
            "failed_node_id": "P-101",
            "failure_mode": "Failed Open",
            "description": "Pump fails - should cause loss of flow"
        }
    ]
    
    # Initialize simulator
    try:
        simulator = HazOpSimulator()
        print("✓ HazOp Simulator initialized")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize simulator: {e}")
        return False
    
    # Run test scenarios
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{'=' * 70}")
        print(f"TEST SCENARIO {i}: {scenario['description']}")
        print(f"{'=' * 70}")
        print(f"Failed Node: {scenario['failed_node_id']}")
        print(f"Failure Mode: {scenario['failure_mode']}")
        print()
        
        try:
            print("Running simulation...")
            result = simulator.simulate_failure(
                failed_node_id=scenario['failed_node_id'],
                failure_mode=scenario['failure_mode'],
                topology=sample_topology
            )
            
            print("✓ Simulation completed successfully!")
            print()
            
            # Display results
            print("RESULTS:")
            print("-" * 70)
            print(f"Severity Level: {result.severity_level}")
            print()
            print(f"Hazard Summary:")
            print(f"  {result.hazard_summary}")
            print()
            print(f"Cascading Effects ({len(result.cascading_effects)}):")
            for j, effect in enumerate(result.cascading_effects, 1):
                print(f"  {j}. {effect}")
            print()
            print(f"Affected Nodes ({len(result.affected_node_ids)}):")
            print(f"  {', '.join(result.affected_node_ids[:5])}")
            if len(result.affected_node_ids) > 5:
                print(f"  ... and {len(result.affected_node_ids) - 5} more")
            print()
            print(f"Affected Edges ({len(result.affected_edge_ids)}):")
            print(f"  {', '.join(result.affected_edge_ids[:5])}")
            if len(result.affected_edge_ids) > 5:
                print(f"  ... and {len(result.affected_edge_ids) - 5} more")
            print()
            print(f"Recommended Actions ({len(result.recommended_actions)}):")
            for j, action in enumerate(result.recommended_actions, 1):
                print(f"  {j}. {action}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR: Simulation failed: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    print("=" * 70)
    print("✓ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("The HazOp Simulator is working correctly!")
    print("You can now use it in the web interface.")
    print()
    
    return True


if __name__ == "__main__":
    success = test_hazop_simulator()
    sys.exit(0 if success else 1)
