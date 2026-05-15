"""
COORDINATE FIX - Backend (FastAPI)
==================================
This file shows the exact changes needed in src/api/main.py

The key change: Convert YOLO bounding boxes to TOP-LEFT PERCENTAGES (0.0 to 1.0)
so React only needs to multiply by 100.
"""

# ============================================================================
# STEP 1: Update the DetectionResult Model
# ============================================================================

from pydantic import BaseModel
from typing import Optional

class DetectionResult(BaseModel):
    """Single detection result with percentage-based coordinates."""
    class_name: str
    confidence: float
    # NEW: Use percentage coordinates (0.0 to 1.0)
    pct_x: float  # Top-left X as percentage
    pct_y: float  # Top-left Y as percentage
    pct_width: float  # Width as percentage
    pct_height: float  # Height as percentage
    tag: Optional[str] = None


# ============================================================================
# STEP 2: Helper Function to Convert YOLO to Percentages
# ============================================================================

def yolo_to_percentages(box, orig_width: int, orig_height: int) -> dict:
    """
    Convert YOLO bounding box to top-left percentages.
    
    Args:
        box: YOLO box object with xywh attribute
        orig_width: Original image width
        orig_height: Original image height
    
    Returns:
        Dictionary with pct_x, pct_y, pct_width, pct_height (0.0 to 1.0)
    """
    # Get YOLO format: center_x, center_y, width, height (in pixels)
    x_c, y_c, w, h = box.xywh[0].cpu().numpy()
    
    # Convert center to top-left corner
    top_left_x = x_c - (w / 2)
    top_left_y = y_c - (h / 2)
    
    # Convert to percentages (0.0 to 1.0)
    pct_x = float(top_left_x / orig_width)
    pct_y = float(top_left_y / orig_height)
    pct_width = float(w / orig_width)
    pct_height = float(h / orig_height)
    
    # Clamp to valid range [0.0, 1.0]
    pct_x = max(0.0, min(1.0, pct_x))
    pct_y = max(0.0, min(1.0, pct_y))
    pct_width = max(0.0, min(1.0 - pct_x, pct_width))
    pct_height = max(0.0, min(1.0 - pct_y, pct_height))
    
    return {
        "pct_x": pct_x,
        "pct_y": pct_y,
        "pct_width": pct_width,
        "pct_height": pct_height,
    }


# ============================================================================
# STEP 3: Update the /process Endpoint
# ============================================================================

@app.post("/process", response_model=ProcessingResult)
async def process_image(file: UploadFile = File(...)):
    """
    Process a P&ID image through all layers.
    Returns detections with percentage-based coordinates.
    """
    import time
    import cv2
    import numpy as np
    from ultralytics import YOLO
    
    start_time = time.time()
    
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Get original dimensions
    orig_height, orig_width = image.shape[:2]
    print(f"Original image size: {orig_width}x{orig_height}")
    
    detections = []
    
    # Load YOLO model
    model = YOLO('models/yolov8/best.pt')
    
    # Run detection
    results = model.predict(
        image,
        conf=0.2,
        iou=0.45,
        imgsz=1280,
        augment=True,
        verbose=False
    )
    
    # Process results
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        # CRITICAL: Get original image dimensions from result
        orig_shape = result.orig_shape  # (height, width)
        orig_h, orig_w = orig_shape
        
        for i in range(len(boxes)):
            box = boxes[i]
            
            # Convert to percentages using helper function
            coords = yolo_to_percentages(box, orig_w, orig_h)
            
            # Get class info
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = model.names[cls_id]
            confidence = float(box.conf[0].cpu().numpy())
            
            # Create detection with percentage coordinates
            detections.append(DetectionResult(
                class_name=class_name,
                confidence=confidence,
                pct_x=coords["pct_x"],
                pct_y=coords["pct_y"],
                pct_width=coords["pct_width"],
                pct_height=coords["pct_height"],
                tag=None,  # Add tag extraction logic if needed
            ))
    
    processing_time_ms = (time.time() - start_time) * 1000
    
    return ProcessingResult(
        image_name=file.filename,
        processing_time_ms=processing_time_ms,
        layer1_detections=len(detections),
        layer2_instruments=0,  # Update with actual count
        layer3_nodes=0,  # Update with actual count
        layer3_edges=0,  # Update with actual count
        detections=detections,
        graph_summary={},
    )


# ============================================================================
# EXAMPLE: Converting Existing Pixel Coordinates to Percentages
# ============================================================================

def convert_existing_detections(detections_list, orig_width: int, orig_height: int):
    """
    If you have existing detections with pixel coordinates (x1, y1, x2, y2),
    convert them to percentage format.
    """
    converted = []
    
    for det in detections_list:
        # Assuming det has bbox with x1, y1, x2, y2 in pixels
        x1 = det.bbox["x1"]
        y1 = det.bbox["y1"]
        x2 = det.bbox["x2"]
        y2 = det.bbox["y2"]
        
        # Calculate width and height
        width = x2 - x1
        height = y2 - y1
        
        # Convert to percentages
        pct_x = x1 / orig_width
        pct_y = y1 / orig_height
        pct_width = width / orig_width
        pct_height = height / orig_height
        
        # Clamp to valid range
        pct_x = max(0.0, min(1.0, pct_x))
        pct_y = max(0.0, min(1.0, pct_y))
        pct_width = max(0.0, min(1.0 - pct_x, pct_width))
        pct_height = max(0.0, min(1.0 - pct_y, pct_height))
        
        converted.append({
            "class_name": det.class_name,
            "confidence": det.confidence,
            "pct_x": pct_x,
            "pct_y": pct_y,
            "pct_width": pct_width,
            "pct_height": pct_height,
            "tag": det.tag,
        })
    
    return converted


# ============================================================================
# TESTING: Verify Conversion
# ============================================================================

def test_conversion():
    """Test the conversion with sample data."""
    
    # Sample YOLO box (center format)
    class MockBox:
        def __init__(self, x_c, y_c, w, h):
            import numpy as np
            self.xywh = [np.array([x_c, y_c, w, h])]
    
    # Image dimensions
    orig_width = 1400
    orig_height = 900
    
    # Test case: Box at center of image
    box = MockBox(x_c=700, y_c=450, w=100, h=80)
    result = yolo_to_percentages(box, orig_width, orig_height)
    
    print("Test Case: Center Box")
    print(f"  Input: center=(700, 450), size=(100, 80)")
    print(f"  Output: {result}")
    print(f"  Expected: pct_x≈0.464, pct_y≈0.456, pct_width≈0.071, pct_height≈0.089")
    
    # Verify in React (multiply by 100)
    print(f"\n  React CSS:")
    print(f"    left: {result['pct_x'] * 100:.1f}%")
    print(f"    top: {result['pct_y'] * 100:.1f}%")
    print(f"    width: {result['pct_width'] * 100:.1f}%")
    print(f"    height: {result['pct_height'] * 100:.1f}%")


if __name__ == "__main__":
    test_conversion()


# ============================================================================
# SUMMARY OF CHANGES
# ============================================================================

"""
WHAT CHANGED:

1. DetectionResult Model:
   - Removed: bbox: Dict[str, float]
   - Added: pct_x, pct_y, pct_width, pct_height (all 0.0 to 1.0)

2. Detection Processing:
   - Get orig_shape from YOLO result
   - Extract xywh from box
   - Convert center to top-left
   - Divide by image dimensions to get percentages
   - Clamp to [0.0, 1.0] range

3. Benefits:
   - React doesn't need to know image dimensions
   - No scaling math in frontend
   - Immune to resize bugs
   - Percentages are resolution-independent

BEFORE (Pixel Coordinates):
{
    "class_name": "valve.control",
    "confidence": 0.88,
    "bbox": {"x1": 895, "y1": 291, "x2": 954, "y2": 390}
}

AFTER (Percentage Coordinates):
{
    "class_name": "valve.control",
    "confidence": 0.88,
    "pct_x": 0.639,
    "pct_y": 0.324,
    "pct_width": 0.042,
    "pct_height": 0.110
}

React just does: left: ${pct_x * 100}%
"""
