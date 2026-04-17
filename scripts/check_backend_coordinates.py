#!/usr/bin/env python3
"""
Quick script to check if backend is sending clustered coordinates
Run this AFTER processing a P&ID image
"""
import requests
import json

try:
    response = requests.get("http://localhost:8000/graph")
    data = response.json()
    
    if "nodes" not in data:
        print("❌ No graph loaded. Process a P&ID image first.")
        exit(1)
    
    nodes = data["nodes"]
    
    if not nodes:
        print("❌ No nodes in graph")
        exit(1)
    
    # Get coordinate ranges
    x_coords = [n["x"] for n in nodes]
    y_coords = [n["y"] for n in nodes]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    span_x = max_x - min_x
    span_y = max_y - min_y
    
    print("="*60)
    print("BACKEND COORDINATE CHECK")
    print("="*60)
    print(f"Total nodes: {len(nodes)}")
    print(f"\nX coordinates:")
    print(f"  Range: {min_x:.1f} to {max_x:.1f}")
    print(f"  Span: {span_x:.1f} pixels")
    print(f"\nY coordinates:")
    print(f"  Range: {min_y:.1f} to {max_y:.1f}")
    print(f"  Span: {span_y:.1f} pixels")
    print()
    
    # Diagnosis
    if span_x < 200 and span_y < 200:
        print("❌ PROBLEM: Coordinates are SEVERELY CLUSTERED!")
        print(f"   All {len(nodes)} nodes are within a {span_x:.0f}x{span_y:.0f} pixel area")
        print()
        print("This is why:")
        print("  • Minimap shows dots clustered in one spot")
        print("  • Clicking minimap shows nodes gathered together")
        print("  • Initial view looks spread out (due to extreme zoom)")
        print()
        print("ROOT CAUSE: Backend detection issue")
        print("  • SAHI/YOLO only detecting in small region")
        print("  • Or coordinate transformation error")
        print()
        print("SOLUTION: Fix backend detection parameters")
    elif span_x < 500 or span_y < 500:
        print("⚠️  WARNING: Coordinates are somewhat clustered")
        print(f"   Nodes span only {span_x:.0f}x{span_y:.0f} pixels")
        print("   Expected: >1000 pixels for good distribution")
    else:
        print("✅ GOOD: Coordinates are well distributed")
        print(f"   Nodes span {span_x:.0f}x{span_y:.0f} pixels")
        print("   If minimap still shows clustering, it's a frontend issue")
    
    print()
    print("First 5 node coordinates:")
    for i, node in enumerate(nodes[:5]):
        print(f"  {node['id']}: ({node['x']:.1f}, {node['y']:.1f})")
    
    print("="*60)
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend. Is it running?")
    print("   Start with: python -m uvicorn src.api.main:app --reload")
except Exception as e:
    print(f"❌ Error: {e}")
