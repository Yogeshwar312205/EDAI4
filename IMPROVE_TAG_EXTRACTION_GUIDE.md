# Guide: Improve Backend Tag Extraction

## Problem Statement

Many instrument nodes show `"instrument.bubble"` as their label instead of actual ISA tags like `"FIC-101"`, `"PT-205"`, etc.

**Root Cause**: The hybrid pipeline detects instrument bubbles (circles) but doesn't always extract the text inside them.

## Current Pipeline Flow

```
P&ID Image
    ↓
1. YOLO Detection (finds instrument symbols)
    ↓
2. Circle Detection (finds circular bubbles)
    ↓
3. OCR (extracts all text from image)
    ↓
4. Text Association (tries to match text to symbols)
    ↓
5. Graph Building (creates nodes with labels)
```

**Issue**: Step 4 (Text Association) often fails to match OCR text with detected circles.

## Solution Approaches

### Approach 1: Targeted OCR Inside Detected Circles (Recommended)

**Concept**: After detecting instrument circles, crop each circle and run OCR specifically on that region.

**Implementation**:

```python
# In src/perception/hybrid_pipeline.py

def extract_text_from_circles(self, image, circles):
    """Extract text from inside detected circles using targeted OCR"""
    tagged_circles = []
    
    for circle in circles:
        cx, cy, radius = circle['center'][0], circle['center'][1], circle['radius']
        
        # Crop region around circle (with padding)
        padding = int(radius * 0.2)  # 20% padding
        x1 = max(0, int(cx - radius - padding))
        y1 = max(0, int(cy - radius - padding))
        x2 = min(image.shape[1], int(cx + radius + padding))
        y2 = min(image.shape[0], int(cy + radius + padding))
        
        # Extract crop
        crop = image[y1:y2, x1:x2]
        
        # Preprocess for better OCR
        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        crop_thresh = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Run OCR on crop
        ocr_result = self.ocr_engine.extract_text(crop_thresh)
        
        # Find ISA tag in OCR results
        tag = self._find_isa_tag_in_text(ocr_result)
        
        if tag:
            circle['tag'] = tag
            tagged_circles.append(circle)
        else:
            circle['tag'] = 'UNTAGGED'
            tagged_circles.append(circle)
    
    return tagged_circles

def _find_isa_tag_in_text(self, ocr_result):
    """Find ISA tag pattern in OCR text"""
    import re
    
    # ISA tag pattern: [Letter][Letter]-[Number]
    # Examples: FIC-101, PT-205, TT-301
    pattern = r'\b([FPTLAICSZWVH][ITCVSEYAR][-_]?\d{1,4}[A-Z]?)\b'
    
    for text_block in ocr_result.text_blocks:
        match = re.search(pattern, text_block.text.upper())
        if match:
            return match.group(1)
    
    return None
```

**Where to add**: In `src/perception/hybrid_pipeline.py`, after circle detection and before merging results.

**Pros**:
- ✅ Highly accurate (focused on specific region)
- ✅ Reduces false positives from background text
- ✅ Works even with cluttered P&IDs

**Cons**:
- ⚠️ Slower (OCR runs multiple times)
- ⚠️ Requires good image quality

### Approach 2: Improve Text-to-Circle Association

**Concept**: Enhance the existing text association logic to better match OCR text with detected circles.

**Implementation**:

```python
# In src/perception/text_symbol_associator.py

def associate_text_with_circles(self, text_blocks, circles, max_distance=50):
    """
    Associate OCR text with detected circles
    
    Args:
        text_blocks: List of OCR text blocks with positions
        circles: List of detected circles with centers
        max_distance: Maximum distance (pixels) to consider association
    """
    associations = []
    
    for circle in circles:
        cx, cy = circle['center']
        best_match = None
        best_distance = float('inf')
        
        for text_block in text_blocks:
            tx, ty = text_block.center
            
            # Calculate distance from text to circle center
            distance = ((tx - cx)**2 + (ty - cy)**2)**0.5
            
            # Check if text is inside or very close to circle
            if distance < circle['radius'] * 1.2:  # Within 120% of radius
                # Check if text looks like ISA tag
                if self._is_isa_tag(text_block.text):
                    if distance < best_distance:
                        best_distance = distance
                        best_match = text_block.text
        
        if best_match:
            circle['tag'] = best_match
        else:
            circle['tag'] = 'UNTAGGED'
        
        associations.append(circle)
    
    return associations

def _is_isa_tag(self, text):
    """Check if text matches ISA tag pattern"""
    import re
    pattern = r'^[FPTLAICSZWVH][ITCVSEYAR][-_]?\d{1,4}[A-Z]?$'
    return bool(re.match(pattern, text.upper().strip()))
```

**Pros**:
- ✅ Fast (uses existing OCR results)
- ✅ No additional OCR calls
- ✅ Easy to implement

**Cons**:
- ⚠️ May miss tags if OCR didn't detect them initially
- ⚠️ Sensitive to distance threshold tuning

### Approach 3: Hybrid Approach (Best Results)

**Concept**: Combine both approaches:
1. First try text association with existing OCR
2. If no tag found, run targeted OCR on the circle

**Implementation**:

```python
def extract_tags_hybrid(self, image, circles, global_ocr_results):
    """
    Hybrid approach: Try association first, then targeted OCR
    """
    tagged_circles = []
    
    for circle in circles:
        # Step 1: Try to find tag in global OCR results
        tag = self._find_nearby_tag(circle, global_ocr_results)
        
        if tag:
            circle['tag'] = tag
            circle['tag_source'] = 'association'
        else:
            # Step 2: Run targeted OCR on this circle
            tag = self._ocr_circle_region(image, circle)
            circle['tag'] = tag if tag else 'UNTAGGED'
            circle['tag_source'] = 'targeted_ocr' if tag else 'none'
        
        tagged_circles.append(circle)
    
    return tagged_circles
```

**Pros**:
- ✅ Best accuracy
- ✅ Falls back to targeted OCR only when needed
- ✅ Balanced speed/accuracy tradeoff

**Cons**:
- ⚠️ More complex code
- ⚠️ Requires careful tuning

## Implementation Steps

### Step 1: Add Targeted OCR Function

**File**: `src/perception/hybrid_pipeline.py`

Add the `extract_text_from_circles()` method shown in Approach 1.

### Step 2: Integrate into Pipeline

**File**: `src/perception/hybrid_pipeline.py`

In the `process()` method, after circle detection:

```python
# After circle detection
circles = self.circle_detector.detect_circles(image)

# NEW: Extract text from circles
circles_with_tags = self.extract_text_from_circles(image, circles)

# Continue with rest of pipeline...
```

### Step 3: Update Node Creation

**File**: `src/perception/hybrid_pipeline.py`

When creating nodes from circles, use the extracted tag:

```python
for circle in circles_with_tags:
    node = DetectedNode(
        class_name='instrument.bubble',
        confidence=circle['confidence'],
        x1=circle['x1'],
        y1=circle['y1'],
        x2=circle['x2'],
        y2=circle['y2'],
        tag=circle['tag'],  # Use extracted tag
        source='circle_detection'
    )
    nodes.append(node)
```

### Step 4: Test and Tune

```python
# Test script
python scripts/test_tag_extraction.py --image data/samples/sample_pid.jpg
```

**Tune these parameters**:
- `padding`: How much extra space around circle to include (default: 20%)
- `max_distance`: Maximum distance for text association (default: 50px)
- `radius_multiplier`: How far outside circle to look for text (default: 1.2x)

## Expected Results

**Before**:
```
Node 1: label="instrument.bubble", tag=None
Node 2: label="instrument.bubble", tag=None
Node 3: label="FE", tag="FE"  (lucky OCR match)
```

**After**:
```
Node 1: label="FIC-101", tag="FIC-101"
Node 2: label="PT-205", tag="PT-205"
Node 3: label="FE", tag="FE"
```

**Improvement**: 90%+ of instrument bubbles should have proper tags.

## Testing Checklist

- [ ] Run on sample P&ID with known tags
- [ ] Verify tags are correctly extracted
- [ ] Check for false positives (wrong tags)
- [ ] Test with rotated text
- [ ] Test with low-quality images
- [ ] Measure processing time impact
- [ ] Compare before/after accuracy

## Performance Considerations

**Current**: ~2-3 seconds per P&ID
**With Targeted OCR**: ~4-6 seconds per P&ID (acceptable)

**Optimization tips**:
- Run OCR in parallel for multiple circles
- Cache OCR results
- Use faster OCR engine (EasyOCR vs PaddleOCR)
- Reduce image resolution for OCR

## Alternative: Quick Fix with Manual Tagging

If you need a quick solution without modifying the backend:

**Add manual tag editing in frontend**:

```typescript
// In GraphViewer.tsx
const [editingTag, setEditingTag] = useState<string | null>(null);

const handleTagEdit = (nodeId: string, newTag: string) => {
  setNodes((nds) =>
    nds.map((node) =>
      node.id === nodeId
        ? { ...node, data: { ...node.data, label: newTag } }
        : node
    )
  );
};

// Add edit button in the AI Tag Explainer panel
<button onClick={() => setEditingTag(selectedNodeId)}>
  Edit Tag
</button>
```

This allows users to manually correct tags that weren't detected properly.

## Summary

**Recommended Solution**: Implement Approach 3 (Hybrid)

**Timeline**:
- Implementation: 2-4 hours
- Testing: 1-2 hours
- Tuning: 1-2 hours
- **Total**: ~1 day of work

**Expected Improvement**:
- Current: ~30% of nodes have proper tags
- After fix: ~90% of nodes have proper tags

**Files to modify**:
1. `src/perception/hybrid_pipeline.py` - Add targeted OCR
2. `src/perception/text_symbol_associator.py` - Improve association
3. `src/perception/ocr_engine.py` - Add crop OCR method

The Smart OCR Tag Explainer will work much better once the backend properly extracts tags!
