#!/usr/bin/env python3
"""
Test script for Engineering Q&A Assistant
Tests the /api/ask-pid endpoint with sample topology
"""

import requests
import json
from datetime import datetime

# Sample topology data
sample_topology = {
    "nodes": [
        {"id": "node_1", "type": "instrument", "tag": "FE", "label": "FE", "x": 100, "y": 200},
        {"id": "node_2", "type": "instrument", "tag": "FT-101", "label": "FT-101", "x": 200, "y": 200},
        {"id": "node_3", "type": "instrument", "tag": "FIC-101", "label": "FIC-101", "x": 300, "y": 200},
        {"id": "node_4", "type": "valve", "tag": "CV-101", "label": "CV-101", "x": 400, "y": 200},
        {"id": "node_5", "type": "equipment", "tag": "P-101", "label": "Pump P-101", "x": 150, "y": 300},
    ],
    "edges": [
        {"source": "node_1", "target": "node_2", "type": "signal"},
        {"source": "node_2", "target": "node_3", "type": "signal"},
        {"source": "node_3", "target": "node_4", "type": "control"},
        {"source": "node_5", "target": "node_1", "type": "flow"},
    ]
}

# Test questions
test_questions = [
    "What instruments are measuring flow in this P&ID?",
    "Trace the flow path from the pump to the control valve",
    "What control loops are present in this system?",
    "List all the nodes and their connections",
]

def test_endpoint(base_url="http://localhost:8000"):
    """Test the /api/api/ask-pid endpoint"""
    
    print("=" * 70)
    print("ENGINEERING Q&A ASSISTANT - TEST SCRIPT")
    print("=" * 70)
    print()
    
    endpoint = f"{base_url}/api/api/ask-pid"
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(test_questions)}")
        print(f"{'='*70}")
        print(f"\n📝 Question: {question}")
        print(f"\n⏳ Sending request to {endpoint}...")
        
        try:
            # Prepare request
            payload = {
                "question": question,
                "topology": sample_topology
            }
            
            # Send request
            start_time = datetime.now()
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Success! (took {duration:.2f}s)")
                print(f"\n🤖 AI Answer:")
                print("-" * 70)
                print(data["answer"])
                print("-" * 70)
                print(f"\n⏰ Timestamp: {data['timestamp']}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Connection Error: Could not connect to {base_url}")
            print("   Make sure the backend is running:")
            print("   python -m uvicorn src.api.main:app --reload --port 8000")
            break
        except requests.exceptions.Timeout:
            print(f"\n❌ Timeout: Request took longer than 30 seconds")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}\n")


def test_health(base_url="http://localhost:8000"):
    """Test if backend is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            data = response.json()
            print(f"   Version: {data['version']}")
            print(f"   Status: {data['status']}")
            return True
        else:
            print(f"⚠️  Backend returned status {response.status_code}")
            return False
    except:
        print("❌ Backend is not running")
        print("   Start it with: python -m uvicorn src.api.main:app --reload --port 8000")
        return False


if __name__ == "__main__":
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("\n🔍 Checking backend health...")
    if test_health(base_url):
        print("\n🚀 Starting tests...\n")
        test_endpoint(base_url)
    else:
        print("\n⚠️  Cannot run tests - backend is not available\n")
        sys.exit(1)
