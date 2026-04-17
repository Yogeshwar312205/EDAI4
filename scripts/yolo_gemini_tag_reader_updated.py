"""
YOLO + Gemini Instrument Tag Reader (Updated for Current Model)
================================================================
Detects instrument tags using YOLOv8 and reads text using Gemini Vision.

This version works with your current 32-class model where instruments are at:
- Class 26, 27: Instrument_Field
- Class 28, 31: Instrument_Panel  
- Class 29: Instrument_Aux_Panel

Author: AI Engineering Team
Purpose: Extract and read instrument tags from P&ID diagrams
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import google.generativeai as genai
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import model loader to handle both YOLOv5 and YOLOv8
from src.perception.model_loader import load_model_safe


class InstrumentTagReader:
    """
    Combines YOLO detection with Gemini Vision for reading instrument tags.
    Supports both old (class 7) and new (classes 26-31) instrument models.
    """
    
    # Instrument classes for the 32-class model
    INSTRUMENT_CLASSES_32 = [26, 27, 28, 29, 31]
    
    # Instrument class for old 11-class model
    INSTRUMENT_CLASS_11 = 7
    
    def __init__(
        self,
        yolo_model_path: str,
        gemini_api_key: Optional[str] = None,
        confidence_threshold: float = 0.25,
        use_32_class_model: bool = True
    ):
        """
        Initialize the tag reader.
        
        Args:
            yolo_model_path: Path to YOLO model (best.pt)
            gemini_api_key: Google API key (or set GOOGLE_API_KEY env var)
            confidence_threshold: Minimum confidence for YOLO detections
            use_32_class_model: True for 32-class model, False for 11-class
        """
        print("=" * 70)
        print("Initializing Instrument Tag Reader")
        print("=" * 70)
        
        # Set instrument classes based on model type
        self.instrument_classes = (
            self.INSTRUMENT_CLASSES_32 if use_32_class_model 
            else [self.INSTRUMENT_CLASS_11]
        )
        
        # Load YOLO model using model loader (handles both YOLOv5 and YOLOv8)
        print(f"\n[1/3] Loading YOLO model from: {yolo_model_path}")
        try:
            self.yolo_model = load_model_safe(
                model_path=yolo_model_path,
                model_type=None,  # Auto-detect
                verbose=True
            )
            
            if self.yolo_model is None:
                raise RuntimeError("Failed to load YOLO model")
            
            print(f"✓ Model loaded successfully")
            print(f"  Classes: {self.yolo_model.names}")
            print(f"  Target instrument classes: {self.instrument_classes}")
        except Exception as e:
            print(f"✗ Failed to load YOLO model: {e}")
            raise
        
        self.confidence_threshold = confidence_threshold
        
        # Initialize Gemini
        print(f"\n[2/3] Initializing Gemini AI")
        api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable "
                "or pass gemini_api_key parameter."
            )
        
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print(f"✓ Gemini model initialized: gemini-2.0-flash-exp")
        except Exception as e:
            print(f"✗ Failed to initialize Gemini: {e}")
            raise
        
        # Gemini prompt for tag reading
        self.tag_reading_prompt = (
            "Read the text inside this instrument tag. "
            "Only output the exact text you see, nothing else. "
            "If the text is unclear or unreadable, output 'UNREADABLE'."
        )
        
        print(f"\n[3/3] Configuration complete")
        print(f"  Confidence threshold: {confidence_threshold}")
        print(f"  Target classes: {self.instrument_classes}")
        print("=" * 70)
    
    def detect_instrument_tags(self, image_path: str) -> List[Dict]:
        """
        Detect instrument tags using YOLO.
        
        Args:
            image_path: Path to P&ID image
            
        Returns:
            List of detections with bounding boxes
        """
        print(f"\n🔍 Running YOLO detection on: {image_path}")
        
        try:
            # Run YOLO inference
            results = self.yolo_model(
                image_path,
                conf=self.confidence_threshold,
                verbose=False
            )
            
            # Filter for instrument classes
            instrument_tags = []
            
            for result in results:
                if result.boxes is None:
                    continue
                
                boxes = result.boxes
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    
                    # Only process instrument classes
                    if cls_id in self.instrument_classes:
                        xyxy = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        
                        instrument_tags.append({
                            'bbox': xyxy,  # [x1, y1, x2, y2]
                            'confidence': conf,
                            'class_id': cls_id,
                            'class_name': self.yolo_model.names[cls_id]
                        })
            
            print(f"✓ Found {len(instrument_tags)} instrument tags")
            return instrument_tags
            
        except Exception as e:
            print(f"✗ YOLO detection failed: {e}")
            return []
    
    def crop_tag_region(
        self,
        image: np.ndarray,
        bbox: np.ndarray,
        padding: int = 5
    ) -> Image.Image:
        """
        Crop the tag region from the image with optional padding.
        
        Args:
            image: Original image (BGR format from OpenCV)
            bbox: Bounding box [x1, y1, x2, y2]
            padding: Extra pixels around the box
            
        Returns:
            PIL Image of cropped region
        """
        h, w = image.shape[:2]
        
        # Extract coordinates with padding
        x1 = max(0, int(bbox[0]) - padding)
        y1 = max(0, int(bbox[1]) - padding)
        x2 = min(w, int(bbox[2]) + padding)
        y2 = min(h, int(bbox[3]) + padding)
        
        # Crop the region
        cropped = image[y1:y2, x1:x2]
        
        # Convert BGR to RGB for PIL
        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(cropped_rgb)
        
        return pil_image
    
    def read_tag_with_gemini(
        self,
        cropped_image: Image.Image,
        retry_count: int = 2
    ) -> str:
        """
        Use Gemini Vision to read text from cropped tag image.
        
        Args:
            cropped_image: PIL Image of the tag
            retry_count: Number of retries on failure
            
        Returns:
            Extracted text or error message
        """
        for attempt in range(retry_count + 1):
            try:
                # Generate content with image and prompt
                response = self.gemini_model.generate_content([
                    self.tag_reading_prompt,
                    cropped_image
                ])
                
                # Extract text from response
                text = response.text.strip()
                
                # Clean up the response
                if text and text != "UNREADABLE":
                    return text
                else:
                    return "UNREADABLE"
                    
            except Exception as e:
                if attempt < retry_count:
                    print(f"  ⚠ Gemini attempt {attempt + 1} failed, retrying...")
                    continue
                else:
                    print(f"  ✗ Gemini failed after {retry_count + 1} attempts: {e}")
                    return f"ERROR: {str(e)[:50]}"
        
        return "ERROR: Max retries exceeded"
    
    def process_image(
        self,
        image_path: str,
        save_crops: bool = False,
        output_dir: str = "output/tag_crops"
    ) -> List[Dict]:
        """
        Complete pipeline: detect tags and read text.
        
        Args:
            image_path: Path to P&ID image
            save_crops: Whether to save cropped tag images
            output_dir: Directory to save crops
            
        Returns:
            List of results with bbox and text
        """
        print("\n" + "=" * 70)
        print("PROCESSING P&ID IMAGE")
        print("=" * 70)
        
        # Load image
        print(f"\n📂 Loading image: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            print(f"✗ Failed to load image: {image_path}")
            return []
        
        h, w = image.shape[:2]
        print(f"✓ Image loaded: {w}x{h} pixels")
        
        # Detect instrument tags
        detections = self.detect_instrument_tags(image_path)
        
        if not detections:
            print("\n⚠ No instrument tags detected")
            return []
        
        # Create output directory if saving crops
        if save_crops:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            print(f"\n💾 Saving crops to: {output_dir}")
        
        # Process each detected tag
        results = []
        print(f"\n🤖 Reading tags with Gemini AI...")
        print("-" * 70)
        
        for idx, detection in enumerate(detections, 1):
            bbox = detection['bbox']
            conf = detection['confidence']
            
            print(f"\n[Tag {idx}/{len(detections)}]")
            print(f"  Bounding Box: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
            print(f"  Confidence: {conf:.2%}")
            print(f"  Class: {detection['class_name']}")
            
            # Crop the tag region
            cropped_tag = self.crop_tag_region(image, bbox, padding=5)
            
            # Save crop if requested
            if save_crops:
                crop_path = Path(output_dir) / f"tag_{idx:03d}.png"
                cropped_tag.save(crop_path)
                print(f"  💾 Saved crop: {crop_path}")
            
            # Read text with Gemini
            print(f"  🔤 Reading text...", end=" ")
            text = self.read_tag_with_gemini(cropped_tag)
            print(f"'{text}'")
            
            # Store result
            results.append({
                'tag_id': idx,
                'bbox': bbox.tolist(),
                'confidence': conf,
                'class_id': detection['class_id'],
                'class_name': detection['class_name'],
                'text': text,
                'readable': text not in ['UNREADABLE', 'ERROR'] and not text.startswith('ERROR:')
            })
        
        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        readable_count = sum(1 for r in results if r['readable'])
        print(f"Total tags detected: {len(results)}")
        print(f"Successfully read: {readable_count}")
        print(f"Unreadable/Errors: {len(results) - readable_count}")
        print(f"Success rate: {readable_count/len(results):.1%}")
        
        return results
    
    def print_results_table(self, results: List[Dict]):
        """
        Print results in a formatted table.
        
        Args:
            results: List of result dictionaries
        """
        print("\n" + "=" * 70)
        print("DETAILED RESULTS")
        print("=" * 70)
        print(f"{'ID':<4} {'Bbox (x1, y1, x2, y2)':<30} {'Conf':<6} {'Text':<20}")
        print("-" * 70)
        
        for result in results:
            bbox_str = f"({result['bbox'][0]:.0f}, {result['bbox'][1]:.0f}, " \
                      f"{result['bbox'][2]:.0f}, {result['bbox'][3]:.0f})"
            print(
                f"{result['tag_id']:<4} "
                f"{bbox_str:<30} "
                f"{result['confidence']:<6.2%} "
                f"{result['text']:<20}"
            )


def main():
    """
    Main execution function with example usage.
    """
    # Configuration
    MODEL_PATH = "models/yolov8/best.pt"  # Update with your model path
    IMAGE_PATH = "data/input/pid_image.jpg"  # Update with your image path
    
    # Check if files exist
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found: {MODEL_PATH}")
        print("Please update MODEL_PATH in the script")
        print("\nOr run the quick fix:")
        print("  python quick_fix_model.py")
        return
    
    if not Path(IMAGE_PATH).exists():
        print(f"❌ Image not found: {IMAGE_PATH}")
        print("Please update IMAGE_PATH in the script")
        return
    
    try:
        # Initialize reader (use_32_class_model=True for your current model)
        reader = InstrumentTagReader(
            yolo_model_path=MODEL_PATH,
            confidence_threshold=0.25,
            use_32_class_model=True  # Set to False if using old 11-class model
        )
        
        # Process image
        results = reader.process_image(
            image_path=IMAGE_PATH,
            save_crops=True,  # Save cropped tag images
            output_dir="output/tag_crops"
        )
        
        # Print formatted results
        if results:
            reader.print_results_table(results)
            
            # Save results to JSON
            import json
            output_file = "output/tag_reading_results.json"
            Path("output").mkdir(exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
