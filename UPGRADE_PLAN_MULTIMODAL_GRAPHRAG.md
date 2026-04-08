# EDAI4 Upgrade Plan: Multimodal Graph-Native Architecture

## Executive Summary

**Current State**: 5-layer deterministic pipeline (YOLO + EasyOCR + NetworkX)
**Proposed State**: Multimodal Graph-Native Architecture (SAHI + VLM + GraphRAG)
**Recommendation**: ⚠️ **PARTIAL UPGRADE** - Some components justified, others overkill

---

## 🔍 Critical Review: Is This Upgrade Needed?

### Current Pain Points (Validated)
| Issue | Severity | Root Cause |
|-------|----------|------------|
| 0 instruments detected | HIGH | Model trained on isolated symbols, not full P&IDs |
| OCR returns 0 text | HIGH | EasyOCR not initialized / resolution issues |
| Small symbols missed | MEDIUM | YOLO inference at fixed resolution |
| Complex drawings fail | MEDIUM | No tiled/sliced processing |

### Proposed vs. Actual Need

| Proposed Solution | Actual Need | Verdict |
|-------------------|-------------|---------|
| SAHI for tiled inference | ✅ **YES** | Solves small symbol detection |
| Florence-2 VLM for OCR | ⚠️ **MAYBE** | Overkill - fix EasyOCR first |
| Local LLM (Llama 3.1) | ⚠️ **MAYBE** | Current RAG works, LLM optional |
| GraphRAG architecture | ❌ **NO** | NetworkX + query engine sufficient |

---

## 💰 Cost Analysis

### Compute Requirements

| Component | GPU Memory | Inference Time | Cost (Cloud) |
|-----------|------------|----------------|--------------|
| YOLOv8 + SAHI | 4-6 GB | 5-15s/image | $0.01/image |
| Florence-2-large | 8-10 GB | 3-5s/crop | $0.02/crop |
| Llama 3.1 8B | 16+ GB | 2-5s/query | $0.005/query |
| **Total per P&ID** | **16+ GB** | **30-60s** | **$0.10-0.20** |

### Hardware Requirements

| Setup | Can Run? | Notes |
|-------|----------|-------|
| Kaggle T4 (16GB) | ⚠️ Partial | Can't run all models simultaneously |
| Kaggle P100 (16GB) | ⚠️ Partial | Same limitation |
| Colab A100 (40GB) | ✅ Yes | Expensive ($0.50/hr) |
| Local RTX 3090 (24GB) | ✅ Yes | Best for development |
| Local RTX 4090 (24GB) | ✅ Yes | Optimal |

### Annual Cost Projection (1000 P&IDs/month)

| Approach | Monthly Cost | Annual Cost |
|----------|--------------|-------------|
| Current (YOLO + EasyOCR) | ~$50 | ~$600 |
| Proposed (Full Multimodal) | ~$200-400 | ~$2,400-4,800 |
| **Recommended (Hybrid)** | ~$80-120 | ~$1,000-1,500 |

---

## 🎯 Recommended Hybrid Approach

### What to Upgrade

| Layer | Current | Upgrade To | Priority |
|-------|---------|------------|----------|
| 1 | YOLO fixed resolution | **YOLO + SAHI** | 🔴 HIGH |
| 2 | EasyOCR (broken) | **Fix EasyOCR + PaddleOCR fallback** | 🔴 HIGH |
| 2b | - | **Florence-2 for complex regions** (optional) | 🟡 MEDIUM |
| 3 | NetworkX | Keep NetworkX | ✅ DONE |
| 4-5 | Query Engine + RAG | Keep current + **optional Ollama** | 🟢 LOW |

### What NOT to Upgrade (Yet)

1. **Don't replace entire OCR with VLM** - Fix EasyOCR initialization first
2. **Don't require local LLM** - Current query engine works offline
3. **Don't add KùzuDB** - NetworkX handles current scale fine
4. **Don't add vector embeddings** - TF-IDF fallback working

---

## 🔧 Technology Alternatives Review

### For Small Object Detection

| Technology | Pros | Cons | Recommendation |
|------------|------|------|----------------|
| **SAHI** | Easy integration, proven | Slower inference | ✅ **USE THIS** |
| DINO | State-of-art accuracy | Complex setup, slow | ❌ Overkill |
| Tiled Detection (custom) | Already implemented | Basic NMS issues | ⚠️ Fallback |
| RT-DETR | Fast, accurate | Needs retraining | ❌ Future option |

### For Text Extraction (OCR)

| Technology | Pros | Cons | Recommendation |
|------------|------|------|----------------|
| **EasyOCR** | Already integrated | GPU init issues | ✅ **FIX THIS** |
| **PaddleOCR** | Fast, accurate | Different API | ✅ **ADD AS FALLBACK** |
| TrOCR | Transformer-based | Slow, heavy | ⚠️ For handwriting |
| Florence-2 | Multimodal, smart | 8GB+ GPU, slow | ⚠️ For complex only |
| Tesseract | Lightweight, free | Less accurate | ⚠️ CPU fallback |

### For Vision-Language Understanding

| Technology | Size | GPU Memory | Speed | Recommendation |
|------------|------|------------|-------|----------------|
| Florence-2-base | 0.2B | 4GB | Fast | ✅ **If needed** |
| Florence-2-large | 0.7B | 8GB | Medium | ⚠️ Heavy |
| Qwen2-VL-2B | 2B | 8GB | Medium | ⚠️ Alternative |
| LLaVA-1.5-7B | 7B | 16GB | Slow | ❌ Too heavy |
| GPT-4V API | - | Cloud | Fast | ❌ Expensive |

### For Local LLM (GraphRAG)

| Technology | Size | GPU Memory | Quality | Recommendation |
|------------|------|------------|---------|----------------|
| **Ollama + Llama3.1-8B** | 8B | 8GB | Good | ✅ **If needed** |
| Ollama + Mistral-7B | 7B | 6GB | Good | ✅ Alternative |
| Ollama + Phi-3-mini | 3.8B | 4GB | OK | ✅ Lightweight |
| LM Studio + Llama | 8B | 8GB | Good | ⚠️ GUI only |
| Gemini API | Cloud | - | Excellent | ✅ Already have |

---

## 📊 Decision Matrix

### Upgrade Priority Scoring

| Component | Impact | Effort | Risk | Priority Score |
|-----------|--------|--------|------|----------------|
| SAHI integration | 9/10 | 3/10 | Low | **27** (HIGH) |
| Fix EasyOCR | 8/10 | 2/10 | Low | **24** (HIGH) |
| Add PaddleOCR | 7/10 | 3/10 | Low | **21** (MEDIUM) |
| Florence-2 VLM | 6/10 | 6/10 | Medium | **12** (LOW) |
| Ollama LLM | 5/10 | 4/10 | Low | **10** (LOW) |
| Full GraphRAG | 4/10 | 8/10 | High | **4** (SKIP) |

---

## 🚀 Recommended Implementation Phases

### Phase 1: Critical Fixes (Week 1) - **DO THIS FIRST**
- [x] Fix EasyOCR initialization (GPU=False for Windows)
- [ ] Add SAHI for tiled YOLO inference
- [ ] Add ISA tag pattern matching from OCR text
- **Expected Result**: 80%+ instrument detection

### Phase 2: OCR Hardening (Week 2)
- [ ] Add PaddleOCR as fallback
- [ ] Implement multi-OCR consensus
- [ ] Improve text-symbol association radius
- **Expected Result**: 90%+ tag extraction

### Phase 3: VLM Enhancement (Week 3-4) - **OPTIONAL**
- [ ] Add Florence-2 for equipment cluster analysis
- [ ] Implement intelligent prompting
- [ ] Add confidence scoring
- **Expected Result**: Handle complex edge cases

### Phase 4: LLM Integration (Month 2) - **OPTIONAL**
- [ ] Set up Ollama with Llama 3.1
- [ ] Integrate with existing query engine
- [ ] Add natural language explanations
- **Expected Result**: Better user experience

---

## ✅ Final Recommendation

### DO NOW (High ROI)
1. **Add SAHI** - Simple pip install, big improvement
2. **Fix EasyOCR** - Change `gpu=True` to `gpu=False` on Windows
3. **Add PaddleOCR** - Better accuracy fallback

### DO LATER (Medium ROI)
4. Florence-2 for complex regions only
5. Ollama for enhanced query responses

### DON'T DO (Low ROI / Overkill)
- Full GraphRAG architecture overhaul
- KùzuDB graph database migration
- Complete VLM-based OCR replacement
- Real-time streaming inference

---

## 📈 Expected Outcomes

| Metric | Current | After Phase 1-2 | After Phase 3-4 |
|--------|---------|-----------------|-----------------|
| Instrument Detection | 0% | 70-80% | 85-95% |
| Tag Extraction | 0% | 60-70% | 80-90% |
| Processing Time | 25s | 35-45s | 60-90s |
| GPU Memory | 6GB | 8GB | 16GB+ |
| Complexity | Low | Medium | High |

---

**Bottom Line**: Start with SAHI + fixed OCR. Only add VLM/LLM if those don't achieve 80%+ accuracy.
