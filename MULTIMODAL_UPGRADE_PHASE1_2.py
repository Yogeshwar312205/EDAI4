# =============================================================================
# EDAI4 MULTIMODAL UPGRADE - PHASE 1 & 2
# SAHI + Florence-2 VLM Integration
# =============================================================================
# 
# This script implements:
# 1. SAHI (Slicing Aided Hyper Inference) for small object detection
# 2. Equipment cluster cropping with buffer zones
# 3. Florence-2 VLM for intelligent text extraction
# 4. Structured output with ISA S5.1 tag parsing
#
# Target Environment: Kaggle T4 GPU (16GB VRAM)
# Author: EDAI4 Upgrade Module
# =============================================================================

# =============================================================================
# SECTION 0: DEPENDENCY INSTALLATION
# =============================================================================
# Run these in a Kaggle cell FIRST:
"""
!pip install -q ultralytics sahi
!pip install -q transformers accelerate
!pip install -q timm einops  # Florence-2 dependencies
!pip install -q paddlepaddle paddleocr  # OCR fallback
"""

import os
import sys
import gc
import re
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from collections import defaultdict

import cv2
import numpy as np
import torch

warnings.filterwarnings('ignore')

# =============================================================================
# SECTION 1: CONFIGURATION
# =============================================================================

@dataclass
class UpgradeConfig:
    """Configuration for the multimodal upgrade pipeline."""
    
    # Model Paths
    yolo_model_path: str = "/kaggle/input/edai4-golden-model/best.pt"
    
    # SAHI Parameters
    sahi_slice_height: int = 640      # Slice height for tiled inference
    sahi_slice_width: int = 640       # Slice width for tiled inference
    sahi_overlap_ratio: float = 0.2   # Overlap between slices (20%)
    sahi_confidence: float = 0.25     # Lower confidence for better recall
    
    # Cluster Cropping
    cluster_buffer_px: int = 300      # Buffer around equipment for cropping
    min_cluster_size: int = 2         # Minimum detections to form a cluster
    
    # Florence-2 VLM
    florence_model: str = "microsoft/Florence-2-base"  # Use base for T4 GPU
    florence_max_tokens: int = 512
    
    # Processing
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_image_size: int = 4096        # Maximum dimension before downscaling
    
    # ISA Pattern Matching
    isa_pattern: str = r'[FPTLACIS][IRTCASVH][-_]?\d{2,4}[A-Z]?'


# =============================================================================
# SECTION 2: SAHI INTEGRATION (Layer 1 Enhancement)
# =============================================================================

class SAHIDetector:
    """
    SAHI-wrapped YOLOv8 detector for small object detection on large images.
    
    SAHI (Slicing Aided Hyper Inference) works by:
    1. Slicing the image into overlapping tiles
    2. Running detection on each tile
    3. Merging results with NMS to remove duplicates
    
    This solves the "tiny symbol" problem on massive P&ID blueprints.
    """
    
    def __init__(self, config: UpgradeConfig):
        """
        Initialize SAHI detector with YOLOv8 model.
        
        Args:
            config: UpgradeConfig with model paths and parameters
        """
        self.config = config
        self.model = None
        self.detection_model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model and wrap with SAHI."""
        try:
            from sahi import AutoDetectionModel
            from sahi.predict import get_sliced_prediction
            
            print(f"🔄 Loading YOLO model from: {self.config.yolo_model_path}")
            
            # SAHI's AutoDetectionModel wraps YOLOv8
            self.detection_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=self.config.yolo_model_path,
                confidence_threshold=self.config.sahi_confidence,
                device=self.config.device,
            )
            
            print(f"✅ SAHI + YOLOv8 loaded on {self.config.device}")
            
        except ImportError:
            print("⚠️ SAHI not installed. Falling back to standard YOLO inference.")
            self._load_standard_yolo()
        except Exception as e:
            print(f"❌ Failed to load SAHI model: {e}")
            self._load_standard_yolo()
    
    def _load_standard_yolo(self):
        """Fallback: Load standard YOLOv8 without SAHI."""
        from ultralytics import YOLO
        self.model = YOLO(self.config.yolo_model_path)
        print("✅ Standard YOLOv8 loaded (no SAHI)")
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Run SAHI-enhanced detection on image.
        
        Args:
            image: BGR numpy array (OpenCV format)
            
        Returns:
            List of detection dictionaries with:
            - class_name: str
            - confidence: float
            - bbox: Dict[str, float] (x1, y1, x2, y2)
            - center: Tuple[float, float]
        """
        detections = []
        
        if self.detection_model is not None:
            # SAHI sliced prediction
            detections = self._detect_sahi(image)
        elif self.model is not None:
            # Fallback to standard YOLO
            detections = self._detect_standard(image)
        
        print(f"📊 SAHI detected {len(detections)} objects")
        return detections
    
    def _detect_sahi(self, image: np.ndarray) -> List[Dict]:
        """Run SAHI sliced prediction."""
        from sahi.predict import get_sliced_prediction
        
        # Convert BGR to RGB for SAHI
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Run sliced prediction
        result = get_sliced_prediction(
            image=image_rgb,
            detection_model=self.detection_model,
            slice_height=self.config.sahi_slice_height,
            slice_width=self.config.sahi_slice_width,
            overlap_height_ratio=self.config.sahi_overlap_ratio,
            overlap_width_ratio=self.config.sahi_overlap_ratio,
            postprocess_type="NMS",           # Use NMS for duplicate removal
            postprocess_match_threshold=0.5,  # IoU threshold for NMS
            verbose=0,
        )
        
        # Convert SAHI results to our format
        detections = []
        for pred in result.object_prediction_list:
            bbox = pred.bbox
            detections.append({
                "class_name": pred.category.name,
                "confidence": pred.score.value,
                "bbox": {
                    "x1": bbox.minx,
                    "y1": bbox.miny,
                    "x2": bbox.maxx,
                    "y2": bbox.maxy,
                },
                "center": ((bbox.minx + bbox.maxx) / 2, (bbox.miny + bbox.maxy) / 2),
            })
        
        return detections
    
    def _detect_standard(self, image: np.ndarray) -> List[Dict]:
        """Fallback: Standard YOLO detection."""
        results = self.model(image, conf=self.config.sahi_confidence, verbose=False)
        
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append({
                    "class_name": self.model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                })
        
        return detections


# =============================================================================
# SECTION 3: EQUIPMENT CLUSTER DETECTION & CROPPING
# =============================================================================

@dataclass
class EquipmentCluster:
    """Represents an equipment cluster with associated instruments."""
    equipment_id: str
    equipment_type: str
    center: Tuple[float, float]
    bbox: Dict[str, float]
    associated_detections: List[Dict] = field(default_factory=list)
    crop_bbox: Dict[str, float] = field(default_factory=dict)


class ClusterDetector:
    """
    Identifies equipment clusters and creates buffered crops.
    
    A "cluster" is defined as:
    - An equipment detection (pump, compressor, vessel)
    - Plus all nearby instruments and valves within the buffer zone
    """
    
    EQUIPMENT_CLASSES = {
        "equipment.pump", "equipment.compressor_blower", 
        "equipment", "pump", "compressor", "vessel", "tank"
    }
    
    def __init__(self, config: UpgradeConfig):
        self.config = config
    
    def find_clusters(
        self, 
        detections: List[Dict], 
        image_shape: Tuple[int, int]
    ) -> List[EquipmentCluster]:
        """
        Find equipment clusters from detections.
        
        Args:
            detections: List of detection dicts from SAHIDetector
            image_shape: (height, width) of original image
            
        Returns:
            List of EquipmentCluster objects
        """
        h, w = image_shape
        clusters = []
        
        # Find all equipment detections
        equipment_dets = [
            d for d in detections 
            if any(eq in d["class_name"].lower() for eq in self.EQUIPMENT_CLASSES)
        ]
        
        # For each equipment, find associated instruments
        for i, eq in enumerate(equipment_dets):
            cluster = EquipmentCluster(
                equipment_id=f"EQ-{i:03d}",
                equipment_type=eq["class_name"],
                center=eq["center"],
                bbox=eq["bbox"],
            )
            
            # Calculate buffer zone
            buffer = self.config.cluster_buffer_px
            cx, cy = eq["center"]
            
            crop_x1 = max(0, cx - buffer)
            crop_y1 = max(0, cy - buffer)
            crop_x2 = min(w, cx + buffer)
            crop_y2 = min(h, cy + buffer)
            
            cluster.crop_bbox = {
                "x1": crop_x1, "y1": crop_y1,
                "x2": crop_x2, "y2": crop_y2,
            }
            
            # Find all detections within buffer zone
            for det in detections:
                dx, dy = det["center"]
                if crop_x1 <= dx <= crop_x2 and crop_y1 <= dy <= crop_y2:
                    cluster.associated_detections.append(det)
            
            if len(cluster.associated_detections) >= self.config.min_cluster_size:
                clusters.append(cluster)
        
        # If no equipment found, create clusters around instrument groups
        if not clusters:
            clusters = self._create_instrument_clusters(detections, image_shape)
        
        print(f"📦 Found {len(clusters)} equipment clusters")
        return clusters
    
    def _create_instrument_clusters(
        self, 
        detections: List[Dict],
        image_shape: Tuple[int, int]
    ) -> List[EquipmentCluster]:
        """Create clusters from instrument groupings when no equipment found."""
        h, w = image_shape
        
        # Use grid-based clustering
        grid_size = self.config.cluster_buffer_px * 2
        grid_clusters = defaultdict(list)
        
        for det in detections:
            cx, cy = det["center"]
            grid_x = int(cx // grid_size)
            grid_y = int(cy // grid_size)
            grid_clusters[(grid_x, grid_y)].append(det)
        
        clusters = []
        for (gx, gy), dets in grid_clusters.items():
            if len(dets) >= self.config.min_cluster_size:
                # Calculate centroid
                cx = np.mean([d["center"][0] for d in dets])
                cy = np.mean([d["center"][1] for d in dets])
                
                buffer = self.config.cluster_buffer_px
                cluster = EquipmentCluster(
                    equipment_id=f"CLUSTER-{gx}-{gy}",
                    equipment_type="instrument_group",
                    center=(cx, cy),
                    bbox={"x1": cx-50, "y1": cy-50, "x2": cx+50, "y2": cy+50},
                    associated_detections=dets,
                    crop_bbox={
                        "x1": max(0, cx - buffer),
                        "y1": max(0, cy - buffer),
                        "x2": min(w, cx + buffer),
                        "y2": min(h, cy + buffer),
                    }
                )
                clusters.append(cluster)
        
        return clusters
    
    def crop_cluster(
        self, 
        image: np.ndarray, 
        cluster: EquipmentCluster
    ) -> np.ndarray:
        """
        Crop image to cluster bounding box.
        
        Args:
            image: Full P&ID image (BGR)
            cluster: EquipmentCluster with crop_bbox
            
        Returns:
            Cropped image (BGR)
        """
        bbox = cluster.crop_bbox
        x1, y1 = int(bbox["x1"]), int(bbox["y1"])
        x2, y2 = int(bbox["x2"]), int(bbox["y2"])
        
        crop = image[y1:y2, x1:x2].copy()
        return crop


# =============================================================================
# SECTION 4: FLORENCE-2 VLM INTEGRATION (Layer 2 Enhancement)
# =============================================================================

class FlorenceVLM:
    """
    Florence-2 Vision-Language Model for intelligent text extraction.
    
    Florence-2 is Microsoft's efficient multimodal model that can:
    - Extract text from images (OCR)
    - Answer questions about image content
    - Describe specific regions
    
    We use it to extract ISA S5.1 instrument tags from P&ID crops.
    """
    
    def __init__(self, config: UpgradeConfig):
        """
        Initialize Florence-2 model.
        
        Args:
            config: UpgradeConfig with model settings
        """
        self.config = config
        self.model = None
        self.processor = None
        self.device = config.device
        
        self._load_model()
    
    def _load_model(self):
        """Load Florence-2 model with memory optimization."""
        try:
            from transformers import AutoProcessor, AutoModelForCausalLM
            
            print(f"🔄 Loading Florence-2 from: {self.config.florence_model}")
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.config.florence_model,
                trust_remote_code=True,
            )
            
            # Load model with memory optimization
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.florence_model,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
            )
            
            if self.device == "cuda" and self.model.device.type != "cuda":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            print(f"✅ Florence-2 loaded on {self.device}")
            
        except ImportError as e:
            print(f"❌ Florence-2 dependencies missing: {e}")
            print("   Run: pip install transformers accelerate timm einops")
            self.model = None
        except Exception as e:
            print(f"❌ Failed to load Florence-2: {e}")
            self.model = None
    
    def extract_tags(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract instrument tags from image using Florence-2.
        
        Args:
            image: BGR numpy array (cropped region)
            
        Returns:
            Dict with:
            - tags: List of extracted tag strings
            - raw_text: Full OCR text
            - confidence: Extraction confidence
        """
        if self.model is None:
            return self._fallback_ocr(image)
        
        try:
            from PIL import Image
            
            # Convert BGR to RGB PIL Image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Task prompt for OCR
            prompt = "<OCR>"
            
            # Process input
            inputs = self.processor(
                text=prompt,
                images=pil_image,
                return_tensors="pt",
            )
            
            # Move to device
            if self.device == "cuda":
                inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                         for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs.get("pixel_values"),
                    max_new_tokens=self.config.florence_max_tokens,
                    num_beams=3,
                    do_sample=False,
                )
            
            # Decode
            generated_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            # Extract ISA tags using regex
            isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
            tags = isa_pattern.findall(generated_text.upper())
            
            # Clean and deduplicate tags
            tags = list(set([self._normalize_tag(t) for t in tags]))
            
            return {
                "tags": tags,
                "raw_text": generated_text,
                "confidence": 0.85 if tags else 0.3,
                "source": "florence-2",
            }
            
        except Exception as e:
            print(f"⚠️ Florence-2 extraction failed: {e}")
            return self._fallback_ocr(image)
    
    def extract_with_prompt(
        self, 
        image: np.ndarray, 
        prompt: str = "List all instrument tag numbers visible (e.g., FT-101, PI-202)"
    ) -> Dict[str, Any]:
        """
        Extract information using a custom prompt.
        
        Args:
            image: BGR numpy array
            prompt: Custom extraction prompt
            
        Returns:
            Dict with extracted information
        """
        if self.model is None:
            return {"error": "Model not loaded", "tags": []}
        
        try:
            from PIL import Image
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Use caption task with prompt
            task_prompt = f"<CAPTION>{prompt}"
            
            inputs = self.processor(
                text=task_prompt,
                images=pil_image,
                return_tensors="pt",
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                         for k, v in inputs.items()}
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs.get("pixel_values"),
                    max_new_tokens=self.config.florence_max_tokens,
                    num_beams=3,
                )
            
            response = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            # Extract tags from response
            isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
            tags = list(set(isa_pattern.findall(response.upper())))
            
            return {
                "response": response,
                "tags": [self._normalize_tag(t) for t in tags],
                "confidence": 0.8,
                "source": "florence-2-prompted",
            }
            
        except Exception as e:
            return {"error": str(e), "tags": []}
    
    def _normalize_tag(self, tag: str) -> str:
        """Normalize ISA tag format (e.g., FT101 -> FT-101)."""
        tag = tag.upper().strip()
        # Add hyphen if missing
        match = re.match(r'^([A-Z]{2,3})(\d+)([A-Z]?)$', tag)
        if match:
            return f"{match.group(1)}-{match.group(2)}{match.group(3)}"
        return tag
    
    def _fallback_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """Fallback to EasyOCR/PaddleOCR if Florence fails."""
        tags = []
        raw_text = ""
        
        # Try PaddleOCR first (faster, more accurate)
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            result = ocr.ocr(image, cls=True)
            
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    raw_text += text + " "
                    
                    # Extract ISA tags
                    isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
                    found = isa_pattern.findall(text.upper())
                    tags.extend([self._normalize_tag(t) for t in found])
            
            return {
                "tags": list(set(tags)),
                "raw_text": raw_text.strip(),
                "confidence": 0.7 if tags else 0.3,
                "source": "paddleocr",
            }
            
        except ImportError:
            pass
        
        # Try EasyOCR
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            results = reader.readtext(image)
            
            for bbox, text, conf in results:
                raw_text += text + " "
                isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
                found = isa_pattern.findall(text.upper())
                tags.extend([self._normalize_tag(t) for t in found])
            
            return {
                "tags": list(set(tags)),
                "raw_text": raw_text.strip(),
                "confidence": 0.6 if tags else 0.2,
                "source": "easyocr",
            }
            
        except ImportError:
            return {
                "tags": [],
                "raw_text": "",
                "confidence": 0.0,
                "source": "none",
                "error": "No OCR engine available",
            }
    
    def unload(self):
        """Free GPU memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("🗑️ Florence-2 unloaded from memory")


# =============================================================================
# SECTION 5: UNIFIED MULTIMODAL PIPELINE
# =============================================================================

@dataclass
class ExtractionResult:
    """Complete extraction result for a P&ID image."""
    image_path: str
    detections: List[Dict]
    clusters: List[EquipmentCluster]
    extracted_tags: List[str]
    tag_to_cluster: Dict[str, str]
    processing_time_ms: float
    detection_count: int
    instrument_count: int


class MultimodalPipeline:
    """
    Unified multimodal pipeline for P&ID extraction.
    
    Combines:
    - SAHI for small object detection
    - Cluster detection for equipment grouping
    - Florence-2 VLM for intelligent text extraction
    """
    
    def __init__(self, config: Optional[UpgradeConfig] = None):
        """
        Initialize the multimodal pipeline.
        
        Args:
            config: Optional UpgradeConfig (uses defaults if None)
        """
        self.config = config or UpgradeConfig()
        
        print("=" * 60)
        print("🚀 EDAI4 MULTIMODAL PIPELINE INITIALIZATION")
        print("=" * 60)
        
        # Initialize components
        self.detector = SAHIDetector(self.config)
        self.cluster_detector = ClusterDetector(self.config)
        self.vlm = None  # Lazy load to save memory
        
        print("=" * 60)
        print("✅ Pipeline ready")
        print("=" * 60)
    
    def _ensure_vlm_loaded(self):
        """Lazy load VLM when needed."""
        if self.vlm is None:
            self.vlm = FlorenceVLM(self.config)
    
    def process(
        self, 
        image_path: str,
        use_vlm: bool = True,
        save_crops: bool = False,
        output_dir: str = "./crops"
    ) -> ExtractionResult:
        """
        Process a P&ID image through the full multimodal pipeline.
        
        Args:
            image_path: Path to P&ID image
            use_vlm: Whether to use Florence-2 for text extraction
            save_crops: Whether to save cluster crops to disk
            output_dir: Directory for saved crops
            
        Returns:
            ExtractionResult with all extracted data
        """
        import time
        start_time = time.time()
        
        print(f"\n📄 Processing: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        h, w = image.shape[:2]
        print(f"   Image size: {w}x{h}")
        
        # Resize if too large
        if max(h, w) > self.config.max_image_size:
            scale = self.config.max_image_size / max(h, w)
            image = cv2.resize(image, None, fx=scale, fy=scale)
            h, w = image.shape[:2]
            print(f"   Resized to: {w}x{h}")
        
        # Step 1: SAHI Detection
        print("\n🔍 Step 1: SAHI Object Detection")
        detections = self.detector.detect(image)
        
        # Step 2: Find Equipment Clusters
        print("\n📦 Step 2: Equipment Cluster Detection")
        clusters = self.cluster_detector.find_clusters(detections, (h, w))
        
        # Step 3: Extract Tags from Each Cluster
        print("\n🏷️ Step 3: Tag Extraction")
        all_tags = []
        tag_to_cluster = {}
        
        if use_vlm:
            self._ensure_vlm_loaded()
        
        for i, cluster in enumerate(clusters):
            print(f"   Processing cluster {i+1}/{len(clusters)}: {cluster.equipment_id}")
            
            # Crop the cluster region
            crop = self.cluster_detector.crop_cluster(image, cluster)
            
            # Save crop if requested
            if save_crops:
                os.makedirs(output_dir, exist_ok=True)
                crop_path = os.path.join(output_dir, f"{cluster.equipment_id}.jpg")
                cv2.imwrite(crop_path, crop)
            
            # Extract tags
            if use_vlm and self.vlm is not None and self.vlm.model is not None:
                result = self.vlm.extract_tags(crop)
            else:
                result = self._extract_tags_ocr_only(crop)
            
            tags = result.get("tags", [])
            all_tags.extend(tags)
            
            for tag in tags:
                tag_to_cluster[tag] = cluster.equipment_id
            
            print(f"      Found tags: {tags}")
        
        # Also extract from ISA pattern in detection classes
        for det in detections:
            if "instrument" in det["class_name"].lower():
                # Try to find associated text
                pass  # Already handled in cluster extraction
        
        # Deduplicate tags
        all_tags = list(set(all_tags))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Build result
        result = ExtractionResult(
            image_path=image_path,
            detections=detections,
            clusters=clusters,
            extracted_tags=all_tags,
            tag_to_cluster=tag_to_cluster,
            processing_time_ms=processing_time,
            detection_count=len(detections),
            instrument_count=len([d for d in detections if "instrument" in d["class_name"].lower()]),
        )
        
        print(f"\n✅ Processing complete in {processing_time:.0f}ms")
        print(f"   Detections: {result.detection_count}")
        print(f"   Clusters: {len(clusters)}")
        print(f"   Tags found: {len(all_tags)}")
        
        return result
    
    def _extract_tags_ocr_only(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract tags using OCR only (no VLM)."""
        # Try PaddleOCR
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            result = ocr.ocr(image, cls=True)
            
            tags = []
            if result and result[0]:
                isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
                for line in result[0]:
                    text = line[1][0].upper()
                    found = isa_pattern.findall(text)
                    tags.extend(found)
            
            return {"tags": list(set(tags)), "source": "paddleocr"}
        except:
            pass
        
        # Try EasyOCR
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            results = reader.readtext(image)
            
            tags = []
            isa_pattern = re.compile(self.config.isa_pattern, re.IGNORECASE)
            for bbox, text, conf in results:
                found = isa_pattern.findall(text.upper())
                tags.extend(found)
            
            return {"tags": list(set(tags)), "source": "easyocr"}
        except:
            pass
        
        return {"tags": [], "source": "none"}
    
    def unload_vlm(self):
        """Free VLM memory when not needed."""
        if self.vlm is not None:
            self.vlm.unload()
            self.vlm = None


# =============================================================================
# SECTION 6: OUTPUT FORMATTING
# =============================================================================

def format_as_instrument_index(result: ExtractionResult) -> List[Dict]:
    """
    Format extraction result as Instrument Index entries.
    
    Args:
        result: ExtractionResult from pipeline
        
    Returns:
        List of instrument index entries
    """
    entries = []
    
    for tag in result.extracted_tags:
        # Parse ISA tag
        match = re.match(r'^([A-Z]+)-?(\d+)([A-Z]?)$', tag)
        if match:
            letters = match.group(1)
            loop_num = match.group(2)
            suffix = match.group(3)
            
            # Decode ISA first letter
            first_letter_meanings = {
                'F': 'Flow', 'L': 'Level', 'P': 'Pressure', 'T': 'Temperature',
                'A': 'Analysis', 'C': 'Conductivity', 'I': 'Current',
                'S': 'Speed/Safety', 'V': 'Vibration', 'W': 'Weight',
            }
            
            # Decode succeeding letters
            succeeding_meanings = {
                'I': 'Indicator', 'T': 'Transmitter', 'C': 'Controller',
                'V': 'Valve', 'S': 'Switch', 'A': 'Alarm', 'R': 'Recorder',
                'H': 'High', 'L': 'Low', 'E': 'Element',
            }
            
            measured_var = first_letter_meanings.get(letters[0], 'Unknown')
            functions = [succeeding_meanings.get(l, l) for l in letters[1:]]
            
            entry = {
                "Tag Number": tag,
                "Measured Variable": measured_var,
                "Functions": ", ".join(functions),
                "Loop Number": loop_num,
                "Suffix": suffix or "-",
                "Equipment Association": result.tag_to_cluster.get(tag, "Unassigned"),
                "Source P&ID": Path(result.image_path).name,
            }
            entries.append(entry)
    
    return entries


def print_summary(result: ExtractionResult):
    """Print a formatted summary of extraction results."""
    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    
    print(f"\n📄 Source: {result.image_path}")
    print(f"⏱️ Processing Time: {result.processing_time_ms:.0f}ms")
    
    print(f"\n🔍 Detections:")
    print(f"   Total objects: {result.detection_count}")
    print(f"   Instruments: {result.instrument_count}")
    print(f"   Clusters: {len(result.clusters)}")
    
    print(f"\n🏷️ Extracted Tags ({len(result.extracted_tags)}):")
    for tag in sorted(result.extracted_tags):
        cluster = result.tag_to_cluster.get(tag, "N/A")
        print(f"   • {tag} (Cluster: {cluster})")
    
    # Format as instrument index
    print("\n📋 Instrument Index Preview:")
    entries = format_as_instrument_index(result)
    for entry in entries[:10]:  # Show first 10
        print(f"   {entry['Tag Number']:10} | {entry['Measured Variable']:12} | {entry['Functions']}")
    
    if len(entries) > 10:
        print(f"   ... and {len(entries) - 10} more entries")
    
    print("\n" + "=" * 60)


# =============================================================================
# SECTION 7: MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution function for Kaggle notebook.
    
    Usage:
        1. Upload your P&ID image to Kaggle
        2. Update IMAGE_PATH below
        3. Run this cell
    """
    
    # Configuration
    IMAGE_PATH = "/kaggle/input/your-pid-image/pid_drawing.jpg"  # UPDATE THIS
    MODEL_PATH = "/kaggle/input/edai4-golden-model/best.pt"
    USE_VLM = True  # Set False to use OCR only (faster, less accurate)
    SAVE_CROPS = True
    
    # Check if paths exist
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️ Model not found at {MODEL_PATH}")
        print("   Please upload your YOLO model to Kaggle Input")
        return
    
    # Find test images if path doesn't exist
    if not os.path.exists(IMAGE_PATH):
        # Try to find any image
        search_paths = [
            "/kaggle/input/**/images/**/*.jpg",
            "/kaggle/input/**/*.png",
            "/kaggle/working/*.jpg",
        ]
        import glob
        for pattern in search_paths:
            found = glob.glob(pattern, recursive=True)
            if found:
                IMAGE_PATH = found[0]
                print(f"📄 Using found image: {IMAGE_PATH}")
                break
        else:
            print("⚠️ No test image found. Please upload a P&ID image.")
            return
    
    # Create config
    config = UpgradeConfig(
        yolo_model_path=MODEL_PATH,
        sahi_slice_height=640,
        sahi_slice_width=640,
        sahi_overlap_ratio=0.2,
        sahi_confidence=0.25,
        cluster_buffer_px=300,
        florence_model="microsoft/Florence-2-base" if USE_VLM else None,
    )
    
    # Initialize pipeline
    pipeline = MultimodalPipeline(config)
    
    # Process image
    result = pipeline.process(
        image_path=IMAGE_PATH,
        use_vlm=USE_VLM,
        save_crops=SAVE_CROPS,
        output_dir="/kaggle/working/crops",
    )
    
    # Print results
    print_summary(result)
    
    # Export to JSON
    import json
    output = {
        "source": result.image_path,
        "processing_time_ms": result.processing_time_ms,
        "detection_count": result.detection_count,
        "tags": result.extracted_tags,
        "tag_associations": result.tag_to_cluster,
        "instrument_index": format_as_instrument_index(result),
    }
    
    with open("/kaggle/working/extraction_result.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n💾 Results saved to /kaggle/working/extraction_result.json")
    
    # Cleanup GPU memory
    pipeline.unload_vlm()
    
    return result


# =============================================================================
# SECTION 8: KAGGLE NOTEBOOK QUICK START
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           EDAI4 MULTIMODAL UPGRADE - PHASE 1 & 2             ║
    ║                 SAHI + Florence-2 Pipeline                    ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  This script implements:                                      ║
    ║  ✓ SAHI for small object detection on large P&IDs            ║
    ║  ✓ Equipment cluster detection and cropping                  ║
    ║  ✓ Florence-2 VLM for intelligent tag extraction             ║
    ║  ✓ ISA S5.1 pattern matching and normalization               ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  QUICK START:                                                 ║
    ║  1. pip install ultralytics sahi transformers accelerate     ║
    ║  2. Upload YOLO model (best.pt) to Kaggle Input              ║
    ║  3. Upload P&ID image to Kaggle Input                        ║
    ║  4. Update IMAGE_PATH in main() function                     ║
    ║  5. Run this script                                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Auto-run if in Kaggle environment
    if os.path.exists("/kaggle"):
        main()
    else:
        print("Run main() to start processing")
