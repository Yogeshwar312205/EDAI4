#!/usr/bin/env python3
"""
Diagnostic script to check coordinate generation from a processed P&ID
"""
import sys
import json
import requests
from pathlib import Path

def check_graph_coordinates():
    """Fetch and analyze graph coordinates from API"""
    
    try:
        # Fetch graph data from API
        response = requests.get("http://localhost:8000/graph")
        response.raise_for_status()
        
        data = response.json()
        
        if "message" in data:
            print(f"❌ Error: {data['message']}")
            print("\nPlease:")
            print("1. Start the backend: python -m uvicorn src.api.main:app --reload")
            print("2. Upload and process a P&ID image")
            print("3. Run this script again")
            return
        
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        if not nodes:
            print("❌ No nodes found in graph")
            return
        
        # Analyze coordinates
        x_coords = [n["x"] for n in nodes]
        y_coords = [n["y"] for n in nodes]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        span_x = max_x - min_x
        span_y = max_y - min_y
        
        print("="*70)
        print("COORDINATE ANALYSIS")
        print("="*70)
        print(f"Total nodes: {len(nodes)}")
        print(f"Total edges: {len(edges)}")
        print()
        print(f"X coordinates:")
        print(f"  Min: {min_x:.1f}")
        print(f"  Max: {max_x:.1f}")
        print(f"  Span: {span_x:.1f} pixels")
        print()
        print(f"Y coordinates:")
        print(f"  Min: {min_y:.1f}")
        print(f"  Max: {max_y:.1f}")
        print(f"  Span: {span_y:.1f} pixels")
        print()
        
        # Diagnosis
        print("="*70)
        print("DIAGNOSIS")
        print("="*70)
        
        if span_x < 200 or span_y < 200:
            print("❌ PROBLEM DETECTED: Coordinates are CLUSTERED")
            print(f"   X span: {span_x:.1f}px (expected >1000px)")
            print(f"   Y span: {span_y:.1f}px (expected >1000px)")
            print()
            print("This explains why the minimap shows dots clustered together!")
            print()
            print("Possible causes:")
            print("1. SAHI is only detecting objects in one region of the image")
            print("2. Image preprocessing is cropping the P&ID")
            print("3. Detection confidence threshold is too high")
            print("4. YOLO model is not detecting objects across full image")
            print()
            print("Recommended actions:")
            print("- Check backend logs for image dimensions")
            print("- Verify SAHI slice_size and overlap_ratio")
            print("- Lower confidence threshold")
            print("- Visualize raw detections on image")
        elif span_x > 1000 and span_y > 1000:
            print("✅ GOOD: Coordinates are properly distributed")
            print(f"   X span: {span_x:.1f}px")
            print(f"   Y span: {span_y:.1f}px")
            print()
            print("If minimap still shows clustering, the issue is in frontend transformation.")
        else:
            print("⚠️  WARNING: Coordinates have limited distribution")
            print(f"   X span: {span_x:.1f}px")
            print(f"   Y span: {span_y:.1f}px")
            print("   Expected: >1000px for good distribution")
        
        print()
        print("="*70)
        print("SAMPLE NODES (first 10)")
        print("="*70)
        for i, node in enumerate(nodes[:10]):
            print(f"{i+1:2d}. {node['id']:15s} ({node['x']:7.1f}, {node['y']:7.1f}) - {node.get('tag', 'N/A')}")
        
        if len(nodes) > 10:
            print(f"... and {len(nodes)-10} more nodes")
        
        # Save to file for inspection
        output_file = Path("data/coordinate_analysis.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        analysis = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "x_range": {"min": min_x, "max": max_x, "span": span_x},
            "y_range": {"min": min_y, "max": max_y, "span": span_y},
            "is_clustered": span_x < 200 or span_y < 200,
            "nodes": nodes,
            "edges": edges
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print()
        print(f"📄 Full analysis saved to: {output_file}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        print("\nPlease start the backend:")
        print("  python -m uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_graph_coordinates()
