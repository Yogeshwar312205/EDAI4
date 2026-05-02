"""
Quick OCR Performance Test
===========================
Tests PaddleOCR performance with and without optimizations.
"""

import time
import cv2
import numpy as np
from pathlib import Path

def test_ocr_performance():
    """Test OCR performance on a sample image."""
    
    print("=" * 70)
    print("PaddleOCR Performance Test")
    print("=" * 70)
    
    # Find a sample P&ID image
    sample_paths = [
        "data/samples/sample_pid.jpg",
        "data/samples/sample_pid.png",
        "data/input/test.jpg",
        "data/input/test.png",
    ]
    
    image_path = None
    for path in sample_paths:
        if Path(path).exists():
            image_path = path
            break
    
    if not image_path:
        print("❌ No sample image found!")
        print("   Please place a P&ID image in one of these locations:")
        for path in sample_paths:
            print(f"   - {path}")
        return
    
    print(f"✓ Found sample image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return
    
    h, w = image.shape[:2]
    print(f"✓ Image size: {w}x{h} pixels")
    print()
    
    # Test with optimizations
    print("Testing with OPTIMIZATIONS...")
    print("-" * 70)
    
    try:
        from src.perception.sahi_detector import PaddleOCREngine
        
        # Initialize OCR
        print("Initializing PaddleOCR...")
        ocr_engine = PaddleOCREngine(use_gpu=False)
        
        # Run OCR
        print("Running OCR...")
        start = time.time()
        results = ocr_engine.extract_text(image)
        elapsed = (time.time() - start) * 1000
        
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"✓ OCR Time: {elapsed:.0f}ms ({elapsed/1000:.2f}s)")
        print(f"✓ Text Blocks Found: {len(results)}")
        print()
        
        # Show sample results
        if results:
            print("Sample Text Blocks:")
            for i, block in enumerate(results[:10]):
                text = block.get('text', 'N/A')
                conf = block.get('confidence', 0)
                print(f"  {i+1}. '{text}' (confidence: {conf:.2f})")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")
        
        print()
        print("=" * 70)
        print("PERFORMANCE ASSESSMENT")
        print("=" * 70)
        
        if elapsed < 3000:
            print("✅ EXCELLENT - OCR is very fast!")
        elif elapsed < 5000:
            print("✅ GOOD - OCR is reasonably fast")
        elif elapsed < 10000:
            print("⚠️  ACCEPTABLE - OCR is a bit slow but usable")
        else:
            print("❌ SLOW - OCR needs further optimization")
            print()
            print("Suggestions:")
            print("1. Verify backend was restarted after code changes")
            print("2. Check if image resizing is working (look for resize logs)")
            print("3. Try more aggressive resizing (max_dimension=1280)")
            print("4. Consider caching OCR results")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you're running from the project root:")
        print("   python test_ocr_performance.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_performance()
