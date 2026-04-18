# Smart OCR Tag Explainer - Implementation Guide

## Overview

The Smart OCR Tag Explainer uses Google's Gemini AI to automatically analyze and explain P&ID instrument tags. When you click on an instrument node in the graph viewer, it provides an AI-powered definition of what that instrument does.

## Features

✅ **AI-Powered Analysis** - Uses Google Gemini 1.5 Flash for fast, accurate explanations
✅ **Image Support** - Can analyze cropped instrument bubble images (future enhancement)
✅ **Text Fallback** - Works with tag text when no image is available
✅ **Simulated Mode** - Provides basic ISA tag definitions when Gemini API is not configured
✅ **Real-time UI** - Shows loading state and displays results in a clean panel

## Setup

### 1. Install Dependencies

```bash
pip install google-generativeai
```

Or add to `requirements.txt`:
```
google-generativeai>=0.3.0
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure Environment

Add to your `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

### 4. Restart Backend

```bash
python -m uvicorn src.api.main:app --reload
```

## Usage

### Frontend (User Perspective)

1. **Process a P&ID image** to load the graph
2. **Navigate to Graph view**
3. **Click on any instrument node** (blue circles)
4. **See AI analysis** appear in the right panel:
   - Tag name (e.g., "FIC-101")
   - Engineering definition
   - Powered by Gemini AI badge

### Backend API

#### Endpoint: `POST /api/analyze-tag`

**With Image (Future):**
```bash
curl -X POST http://localhost:8000/api/analyze-tag \
  -F "file=@instrument_bubble.jpg"
```

**With Text (Current):**
```bash
curl -X POST http://localhost:8000/api/analyze-tag \
  -F "tag_text=FIC-101"
```

**Response:**
```json
{
  "tag": "FIC-101",
  "definition": "Flow Indicator Controller - Measures flow rate and provides automatic control to maintain desired flow setpoint in the process line."
}
```

## How It Works

### Backend Flow

1. **Request received** at `/api/analyze-tag`
2. **Check for image** - If provided, send to Gemini Vision API
3. **Fallback to text** - If no image, analyze tag text
4. **Gemini processing** - AI reads tag and generates definition
5. **Parse response** - Extract TAG and DEFINITION from AI output
6. **Return JSON** - Send structured response to frontend

### Frontend Flow

1. **User clicks node** - `onNodeClick` handler triggered
2. **Check node type** - Only analyze if `type.includes('instrument')`
3. **Show loading** - Display spinner in AI panel
4. **API call** - POST to `/api/analyze-tag` with tag text
5. **Display result** - Show tag name and definition
6. **Error handling** - Show error message if API fails

### Simulated Mode (No API Key)

If `GEMINI_API_KEY` is not set, the system uses a built-in ISA tag dictionary:

```python
definitions = {
    "FIC": "Flow Indicator Controller - Measures flow rate and provides automatic control",
    "PT": "Pressure Transmitter - Measures and transmits pressure signal",
    "TIC": "Temperature Indicator Controller - Measures temperature and provides automatic control",
    # ... 30+ common tags
}
```

## Architecture

### Files Created/Modified

**Backend:**
- `src/api/gemini_analyzer.py` - Gemini AI integration class
- `src/api/main.py` - Added `/api/analyze-tag` endpoint

**Frontend:**
- `frontend/src/components/GraphViewer.tsx` - Added AI panel and analysis logic

### Key Components

#### GeminiTagAnalyzer Class

```python
class GeminiTagAnalyzer:
    def __init__(self):
        """Initialize Gemini API with API key"""
        
    async def analyze_tag_from_image(self, image_file):
        """Analyze tag from uploaded image"""
        
    def analyze_tag_from_text(self, tag_text):
        """Analyze tag from text (fallback)"""
        
    def _parse_gemini_response(self, response_text):
        """Parse AI response into structured format"""
        
    def _get_simulated_response(self, tag_text):
        """Generate simulated response when API unavailable"""
```

#### Frontend State

```typescript
const [tagAnalysis, setTagAnalysis] = useState<{
  tag: string;
  definition: string;
} | null>(null);
const [isAnalyzing, setIsAnalyzing] = useState(false);
const [analysisError, setAnalysisError] = useState<string | null>(null);
```

## Prompt Engineering

The Gemini prompt is carefully crafted to ensure consistent output:

```
You are an expert in Process & Instrumentation Diagrams (P&IDs) and industrial instrumentation.

Analyze this instrument tag: FIC-101

Provide a clear, concise engineering definition of what this instrument does based on the ISA standard abbreviations.

Format your response EXACTLY as:
TAG: FIC-101
DEFINITION: [brief engineering explanation in 1-2 sentences]
```

This ensures:
- Consistent format for parsing
- Engineering-focused explanations
- ISA standard compliance
- Concise, actionable information

## Future Enhancements

### 1. Image Upload from Frontend

Currently, the frontend sends tag text. Future enhancement:

```typescript
// Crop node area from canvas
const cropNodeImage = (nodeId: string) => {
  const node = nodes.find(n => n.id === nodeId);
  // Use canvas API to crop image around node
  // Return blob
};

// Send image to API
const formData = new FormData();
formData.append('file', imageBlob, 'node.jpg');
```

### 2. Caching

Add Redis/memory cache to avoid re-analyzing same tags:

```python
@lru_cache(maxsize=1000)
def analyze_tag_cached(tag_text: str):
    return analyzer.analyze_tag_from_text(tag_text)
```

### 3. Batch Analysis

Analyze all instrument tags at once:

```python
@app.post("/api/analyze-all-tags")
async def analyze_all_tags():
    results = []
    for node in state.current_graph.get_instruments():
        result = analyzer.analyze_tag_from_text(node.tag)
        results.append(result)
    return results
```

### 4. Custom Prompts

Allow users to customize the AI prompt:

```python
@app.post("/api/analyze-tag")
async def analyze_tag(
    tag_text: str,
    custom_prompt: Optional[str] = None
):
    prompt = custom_prompt or default_prompt
    # Use custom prompt
```

## Troubleshooting

### Issue: "Gemini API not configured"

**Solution:** Set `GEMINI_API_KEY` in `.env` file

### Issue: API rate limits

**Solution:** Gemini 1.5 Flash has generous free tier:
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

For production, upgrade to paid tier.

### Issue: Slow responses

**Solution:** 
- Use `gemini-1.5-flash` (fastest model)
- Implement caching
- Batch requests

### Issue: Inaccurate definitions

**Solution:**
- Improve prompt with more examples
- Add domain-specific context
- Fine-tune with custom training data

## Cost Estimation

**Gemini 1.5 Flash Pricing (as of 2024):**
- Free tier: 1,500 requests/day
- Paid tier: $0.00025 per request

**Example usage:**
- 100 tags analyzed per day = FREE
- 10,000 tags per day = $2.50/day = $75/month

Very cost-effective for most use cases!

## Security Considerations

1. **API Key Protection**
   - Never commit API key to git
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   - Validate tag text format
   - Limit image file size
   - Sanitize user inputs

3. **Rate Limiting**
   - Implement per-user rate limits
   - Cache responses
   - Monitor API usage

## Testing

### Test with curl

```bash
# Test with tag text
curl -X POST http://localhost:8000/api/analyze-tag \
  -F "tag_text=FIC-101"

# Expected response
{
  "tag": "FIC-101",
  "definition": "Flow Indicator Controller - Measures flow rate and provides automatic control to maintain desired flow setpoint in the process line."
}
```

### Test in Frontend

1. Process a P&ID image
2. Click on instrument node
3. Verify AI panel appears
4. Check definition is relevant
5. Test error handling (disconnect backend)

## Summary

The Smart OCR Tag Explainer adds AI-powered intelligence to your P&ID viewer:

✅ **Easy Setup** - Just add API key
✅ **Fast** - Gemini 1.5 Flash responds in <1 second
✅ **Accurate** - Trained on engineering knowledge
✅ **Fallback** - Works without API key (simulated mode)
✅ **Extensible** - Easy to add image support, caching, etc.

Perfect for:
- Training new engineers
- Quick reference during design reviews
- Documentation generation
- Quality assurance checks

Enjoy your AI-powered P&ID analysis! 🤖
