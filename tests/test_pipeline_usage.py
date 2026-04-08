"""
EDAI4 - Perception Pipeline Usage Example
Demonstrates how to use the complete Layer 2 pipeline
"""

# See full example at:
# https://github.com/edai4/examples/perception_pipeline_example.py

from src.perception import PerceptionPipeline

# Initialize
pipeline = PerceptionPipeline(
    model_path="./models/yolov8/best.pt",
    ocr_engine="easyocr",
    confidence_threshold=0.5,
    association_search_radius=150,
)

# Process image
import cv2
image = cv2.imread("./data/sample_pid.png")
result = pipeline.process_image(image)

# Review results
print(result.summary())

for inst in result.instruments:
    print(f"Tag: {inst.tag_number}, Class: {inst.symbol_class}")

# Export to dict/JSON
data = pipeline.export_to_dict(result)

# Visualize
annotated = pipeline.visualize(image, result)
cv2.imwrite("output.png", annotated)
