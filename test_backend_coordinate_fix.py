"""
Test script to verify the backend coordinate fix is working correctly.
This script sends a test image to the /process endpoint and checks the response.
"""

import requests
import json
from pathlib import Path

# Backend URL
BACKEND_URL = "http://localhost:8000"

def test_process_endpoint():
    """Test the /process endpoint with a sample image."""
    print("=" * 70)
    print("TESTING BACKEND COORDINATE FIX")
    print("=" * 70)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"\n✅ Backend is running: {response.status_code}")
        print(f"Health check response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend is not running!")
        print("Please start the backend with: uvicorn src.api.main:app --reload")
        return
    except Exception as e:
        print(f"\n❌ Error checking backend health: {e}")
        return
    
    # Find a test image
    test_images = [
        "test_images/sample.jpg",
        "test_images/sample.png",
        "uploads/test.jpg",
        "uploads/test.png",
    ]
    
    test_image = None
    for img_path in test_images:
        if Path(img_path).exists():
            test_image = img_path
            break
    
    if not test_image:
        print("\n⚠️  No test image found. Creating a dummy request...")
        print("Please upload an image through the frontend to test properly.")
        return
    
    print(f"\n📤 Uploading test image: {test_image}")
    
    # Send image to /process endpoint
    try:
        with open(test_image, 'rb') as f:
            files = {'file': (Path(test_image).name, f, 'image/jpeg')}
            response = requests.post(
                f"{BACKEND_URL}/process",
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            print(f"\n✅ Processing successful!")
            result = response.json()
            
            print(f"\n📊 Processing Result:")
            print(f"  - Image: {result['image_name']}")
            print(f"  - Processing time: {result['processing_time_ms']:.0f}ms")
            print(f"  - Detections: {result['layer1_detections']}")
            print(f"  - Instruments: {result['layer2_instruments']}")
            print(f"  - Nodes: {result['layer3_nodes']}")
            print(f"  - Edges: {result['layer3_edges']}")
            
            # Check coordinate format
            if result['detections']:
                print(f"\n🔍 Checking coordinate format (first 3 detections):")
                for i, det in enumerate(result['detections'][:3]):
                    print(f"\n  Detection {i+1}:")
                    print(f"    Class: {det['class_name']}")
                    print(f"    Confidence: {det['confidence']:.2f}")
                    print(f"    pct_x: {det['pct_x']:.4f} (should be 0.0-1.0)")
                    print(f"    pct_y: {det['pct_y']:.4f} (should be 0.0-1.0)")
                    print(f"    pct_width: {det['pct_width']:.4f} (should be 0.0-1.0)")
                    print(f"    pct_height: {det['pct_height']:.4f} (should be 0.0-1.0)")
                    
                    # Validate range
                    if not (0.0 <= det['pct_x'] <= 1.0):
                        print(f"    ❌ ERROR: pct_x out of range!")
                    if not (0.0 <= det['pct_y'] <= 1.0):
                        print(f"    ❌ ERROR: pct_y out of range!")
                    if not (0.0 <= det['pct_width'] <= 1.0):
                        print(f"    ❌ ERROR: pct_width out of range!")
                    if not (0.0 <= det['pct_height'] <= 1.0):
                        print(f"    ❌ ERROR: pct_height out of range!")
                
                print(f"\n✅ Coordinate format is correct! Backend is sending percentages (0.0-1.0)")
            else:
                print(f"\n⚠️  No detections found in the image")
            
        else:
            print(f"\n❌ Processing failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (>60s)")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_process_endpoint()
