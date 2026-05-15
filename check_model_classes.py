"""
Check YOLO model classes and configuration
"""
from ultralytics import YOLO
import json

print("=" * 70)
print("YOLO Model Diagnostic")
print("=" * 70)

model_path = 'models/yolov8/best.pt'
print(f"\nLoading model: {model_path}")

try:
    model = YOLO(model_path)
    
    print(f"\n✓ Model loaded successfully")
    print(f"\nModel Classes ({len(model.names)} total):")
    print("-" * 70)
    
    for class_id, class_name in model.names.items():
        print(f"  {class_id:2d}: {class_name}")
    
    print("\n" + "=" * 70)
    print("Model Info:")
    print("=" * 70)
    
    # Get model info
    if hasattr(model, 'info'):
        model.info()
    
    # Export class mapping as JSON
    class_mapping = dict(model.names)
    with open('model_classes.json', 'w') as f:
        json.dump(class_mapping, f, indent=2)
    
    print(f"\n✓ Class mapping saved to: model_classes.json")
    
except Exception as e:
    print(f"\n❌ Error loading model: {e}")
    import traceback
    traceback.print_exc()
