# Gemini P&ID Scripts - Complete Guide

## Overview

Two powerful scripts for P&ID analysis using Gemini AI:

1. **`yolo_gemini_tag_reader_updated.py`** - Detect and read instrument tags
2. **`gemini_pid_assistant.py`** - Interactive multimodal P&ID assistant

## Prerequisites

### Install Dependencies

```bash
pip install google-generativeai pillow opencv-python ultralytics
```

### Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set environment variable:

```bash
# Windows
set GOOGLE_API_KEY=your_api_key_here

# Linux/Mac
export GOOGLE_API_KEY=your_api_key_here
```

Or create a `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

## Script 1: YOLO + Gemini Tag Reader

### Purpose
Automatically detect instrument tags in P&IDs and read their text using Gemini Vision.

### Features
- ✅ Detects instrument tags using YOLO
- ✅ Crops each tag region
- ✅ Reads text with Gemini Vision AI
- ✅ Handles both 11-class and 32-class models
- ✅ Saves cropped images
- ✅ Exports results to JSON
- ✅ Error handling for blurry/unreadable tags

### Usage

#### Basic Usage

```python
from scripts.yolo_gemini_tag_reader_updated import InstrumentTagReader

# Initialize reader
reader = InstrumentTagReader(
    yolo_model_path='models/yolov8/best.pt',
    confidence_threshold=0.25,
    use_32_class_model=True  # True for 32-class, False for 11-class
)

# Process image
results = reader.process_image(
    image_path='data/input/pid_image.jpg',
    save_crops=True,
    output_dir='output/tag_crops'
)

# Print results
reader.print_results_table(results)
```

#### Command Line

```bash
# Edit the script to set your paths, then run:
python scripts/yolo_gemini_tag_reader_updated.py
```

### Configuration

Update these variables in the script:

```python
MODEL_PATH = "models/yolov8/best.pt"  # Your YOLO model
IMAGE_PATH = "data/input/pid_image.jpg"  # Your P&ID image
```

### Model Compatibility

**32-Class Model (Current):**
```python
reader = InstrumentTagReader(
    yolo_model_path='models/yolov8/best.pt',
    use_32_class_model=True  # Detects classes 26, 27, 28, 29, 31
)
```

**11-Class Model (Old):**
```python
reader = InstrumentTagReader(
    yolo_model_path='models/yolov8/best.pt',
    use_32_class_model=False  # Detects class 7
)
```

### Output

**Console Output:**
```
[Tag 1/5]
  Bounding Box: [245.3, 156.7, 298.1, 178.4]
  Confidence: 87.5%
  Class: Instrument_Field
  🔤 Reading text... 'FT-101'

[Tag 2/5]
  Bounding Box: [512.8, 234.2, 567.3, 256.9]
  Confidence: 92.3%
  Class: Instrument_Panel
  🔤 Reading text... 'PIC-202'
```

**JSON Output (`output/tag_reading_results.json`):**
```json
[
  {
    "tag_id": 1,
    "bbox": [245.3, 156.7, 298.1, 178.4],
    "confidence": 0.875,
    "class_id": 26,
    "class_name": "Instrument_Field",
    "text": "FT-101",
    "readable": true
  },
  {
    "tag_id": 2,
    "bbox": [512.8, 234.2, 567.3, 256.9],
    "confidence": 0.923,
    "class_id": 28,
    "class_name": "Instrument_Panel",
    "text": "PIC-202",
    "readable": true
  }
]
```

**Saved Crops:**
- `output/tag_crops/tag_001.png`
- `output/tag_crops/tag_002.png`
- etc.

### Error Handling

The script handles:
- **Blurry tags**: Returns "UNREADABLE"
- **Gemini API errors**: Retries 2 times, then returns "ERROR: ..."
- **No detections**: Returns empty list with warning
- **Missing files**: Clear error messages

## Script 2: Gemini P&ID Assistant

### Purpose
Interactive AI assistant that answers questions about P&IDs using both visual and topological data.

### Features
- ✅ Multimodal analysis (image + JSON topology)
- ✅ Interactive Q&A session
- ✅ Expert chemical engineering knowledge
- ✅ Flow path tracing
- ✅ Failure analysis
- ✅ Equipment identification
- ✅ Conversation history
- ✅ Session saving

### Usage

#### Basic Usage

```python
from scripts.gemini_pid_assistant import PIDAssistant

# Initialize assistant
assistant = PIDAssistant()

# Load data
assistant.load_pid_image('data/input/pid_image.jpg')
assistant.load_topology('output/topology.json')

# Ask questions
answer = assistant.ask_question(
    "If the valve on the primary cooling line fails, what happens?"
)
print(answer)

# Or start interactive session
assistant.interactive_session()
```

#### Command Line

```bash
# Edit the script to set your paths, then run:
python scripts/gemini_pid_assistant.py
```

### Configuration

Update these variables in the script:

```python
PID_IMAGE = "data/input/pid_image.jpg"  # Your P&ID image
TOPOLOGY_JSON = "output/topology.json"  # Your topology data
```

### Topology JSON Format

The script expects a JSON file with this structure:

```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "valve",
      "tag": "FV-101",
      "position": {"x": 245, "y": 156}
    },
    {
      "id": "node_2",
      "type": "instrument",
      "tag": "PT-202",
      "position": {"x": 512, "y": 234}
    }
  ],
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "type": "pipe"
    }
  ]
}
```

### Interactive Session

**Starting the session:**
```bash
python scripts/gemini_pid_assistant.py
```

**Example interaction:**
```
💬 Your question: What equipment is connected to valve FV-101?

======================================================================
🤖 Assistant:
======================================================================
Based on the P&ID image and topology data, valve FV-101 is connected to:

1. Upstream: Feed line from tank TK-100
2. Downstream: Heat exchanger HX-200 via 2" pipe

The valve appears to be a control valve (based on the symbol) located
at position (245, 156) on the diagram. It controls the flow rate into
the heat exchanger.

From the topology data, the connections are:
- node_0 (TK-100) → node_1 (FV-101) → node_2 (HX-200)

This valve is critical for controlling the feed rate to the process.
======================================================================
```

**Commands:**
- `quit` or `exit` - End session
- `history` - Show conversation history
- `clear` - Clear conversation history

### Example Questions

**Equipment Identification:**
- "What type of valve is FV-101?"
- "List all instruments in the system"
- "Where is the pressure transmitter PT-202 located?"

**Flow Tracing:**
- "Trace the flow path from the inlet to the reactor"
- "What is the flow direction through valve FV-101?"
- "Show me all equipment in the cooling water loop"

**Failure Analysis:**
- "If valve FV-101 fails closed, what happens?"
- "What is the impact of losing pump P-100?"
- "Identify backup systems for the primary cooling line"

**Safety:**
- "What safety valves protect the reactor?"
- "Where are the emergency shutdown valves?"
- "What happens if pressure exceeds the design limit?"

**Operational:**
- "How do I isolate the heat exchanger for maintenance?"
- "What instruments monitor the reactor temperature?"
- "Explain the startup sequence for this system"

### Output

**Session History (`output/pid_assistant_session.json`):**
```json
{
  "chat_history": [
    {
      "question": "What equipment is connected to valve FV-101?",
      "answer": "Based on the P&ID image and topology data..."
    }
  ],
  "topology_summary": {
    "nodes": 15,
    "edges": 18
  }
}
```

## Generating Topology JSON

If you don't have a topology JSON file, generate it using your API:

### Option 1: Via API Endpoint

```bash
curl -X POST "http://localhost:8000/process" \
  -F "file=@data/input/pid_image.jpg" \
  > output/topology.json
```

### Option 2: Via Python

```python
from src.api.main import process_image
import cv2

# Load image
image = cv2.imread('data/input/pid_image.jpg')

# Process
result = process_image(image)

# Save topology
import json
with open('output/topology.json', 'w') as f:
    json.dump(result['graph'], f, indent=2)
```

## Troubleshooting

### Issue 1: "Google API key not found"

**Solution:**
```bash
# Set environment variable
export GOOGLE_API_KEY=your_key_here

# Or add to .env file
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Issue 2: "Model not found"

**Solution:**
```bash
# Run the quick fix to download a working model
python quick_fix_model.py

# Or update the path in the script
MODEL_PATH = "path/to/your/model.pt"
```

### Issue 3: "No instrument tags detected"

**Possible causes:**
- Wrong model (11-class vs 32-class)
- Confidence threshold too high
- Image quality issues

**Solution:**
```python
# Try lower confidence threshold
reader = InstrumentTagReader(
    yolo_model_path='models/yolov8/best.pt',
    confidence_threshold=0.15,  # Lower threshold
    use_32_class_model=True
)

# Or check which model you have
print(reader.yolo_model.names)  # See all classes
```

### Issue 4: "Topology file not found"

**Solution:**
```bash
# Generate topology first by processing an image
python -m uvicorn src.api.main:app --reload

# Then upload an image through the API
# The topology will be in the response
```

### Issue 5: Gemini returns "UNREADABLE"

**Possible causes:**
- Tag is blurry or low resolution
- Poor lighting in the image
- Tag is partially occluded

**Solution:**
- Use higher resolution images
- Increase padding around crops
- Pre-process image (enhance contrast, denoise)

## Best Practices

### For Tag Reading

1. **Use high-resolution images** (at least 1920x1080)
2. **Good lighting** - avoid shadows on tags
3. **Clean scans** - no wrinkles or distortions
4. **Save crops** for manual verification
5. **Review JSON output** for accuracy

### For P&ID Assistant

1. **Provide complete topology** - include all nodes and edges
2. **Use descriptive tags** - helps Gemini identify equipment
3. **Ask specific questions** - better than vague queries
4. **Reference tag numbers** - more accurate than descriptions
5. **Save sessions** - for documentation and review

## Performance

### Tag Reading Speed

- **YOLO detection**: ~0.5-2 seconds per image
- **Gemini per tag**: ~1-3 seconds
- **Total for 10 tags**: ~15-35 seconds

### Assistant Response Time

- **Simple questions**: 2-5 seconds
- **Complex analysis**: 5-15 seconds
- **Depends on**: Image size, topology complexity, question detail

## Cost Estimation

### Gemini API Pricing (as of 2024)

**Gemini 2.0 Flash:**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Images: ~258 tokens per image

**Estimated costs:**
- Tag reading (10 tags): ~$0.01
- Assistant session (10 questions): ~$0.05-0.10

Very affordable for production use!

## Integration with Your Pipeline

### Add to API

```python
# In src/api/main.py
from scripts.yolo_gemini_tag_reader_updated import InstrumentTagReader

@app.post("/read-tags")
async def read_tags(file: UploadFile):
    # Save uploaded file
    image_path = save_upload(file)
    
    # Read tags
    reader = InstrumentTagReader(
        yolo_model_path='models/yolov8/best.pt',
        use_32_class_model=True
    )
    results = reader.process_image(image_path)
    
    return {"tags": results}
```

### Add to Frontend

```typescript
// In frontend/src/lib/api.ts
export async function readTags(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/read-tags', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
}
```

## Summary

✅ **Tag Reader**: Automatically detect and read instrument tags  
✅ **P&ID Assistant**: Interactive AI for P&ID analysis  
✅ **Multimodal**: Combines vision + topology data  
✅ **Production-ready**: Error handling, logging, JSON export  
✅ **Easy to use**: Simple API, clear documentation  

Both scripts are ready to use with your P&ID pipeline! 🎉
