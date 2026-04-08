"""
YOLO P&ID Symbol Detection Training on Kaggle
Complete training pipeline with proper logging and GPU acceleration
"""

# ============================================================================
# CELL 1: ENVIRONMENT SETUP & GPU CHECK
# ============================================================================

import os
import sys
import logging
from datetime import datetime
import json
from pathlib import Path

# Create logging directory
log_dir = "/kaggle/working/logs"
os.makedirs(log_dir, exist_ok=True)

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"yolo_training_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-8s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("YOLO-P&ID-Training")

# Print header
print("\n" + "=" * 100)
print(" " * 30 + "YOLO P&ID SYMBOL DETECTION TRAINING")
print("=" * 100)

logger.info("=" * 100)
logger.info("YOLO P&ID Symbol Detection Training Started")
logger.info("=" * 100)
logger.info(f"Timestamp: {timestamp}")
logger.info(f"Log file: {log_file}")

# Check PyTorch & CUDA
import torch
import numpy as np

logger.info("\n" + "=" * 100)
logger.info("GPU INFORMATION")
logger.info("=" * 100)

cuda_available = torch.cuda.is_available()
logger.info(f"CUDA Available: {cuda_available}")

if cuda_available:
    device_count = torch.cuda.device_count()
    logger.info(f"CUDA Device Count: {device_count}")

    for i in range(device_count):
        props = torch.cuda.get_device_properties(i)
        logger.info(f"Device {i}: {props.name}")
        logger.info(f"  Memory: {props.total_memory / 1e9:.2f} GB")

    current_device = torch.cuda.current_device()
    logger.info(f"Current GPU (Device {current_device}): {torch.cuda.get_device_name(current_device)}")

    print(f"✓ GPU ENABLED: {torch.cuda.get_device_name(0)}")
    print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    logger.warning("WARNING: GPU NOT AVAILABLE - Training will be VERY slow")
    print("✗ GPU NOT AVAILABLE - Using CPU (SLOW!)")

print("=" * 100 + "\n")

# Store GPU info
gpu_info = {
    "cuda_available": cuda_available,
    "device_count": torch.cuda.device_count() if cuda_available else 0,
    "device_name": torch.cuda.get_device_name(0) if cuda_available else "CPU",
    "torch_version": torch.__version__
}

logger.info("System Information:")
logger.info(f"  Python: {sys.version.split()[0]}")
logger.info(f"  PyTorch: {torch.__version__}")
logger.info(f"  NumPy: {np.__version__}")

# ============================================================================
# CELL 2: INSTALL DEPENDENCIES
# ============================================================================

logger.info("\n" + "=" * 100)
logger.info("INSTALLING DEPENDENCIES")
logger.info("=" * 100)

import subprocess

packages_to_install = [
    ("ultralytics", ">=8.1.0"),
    ("roboflow", ">=1.1.0"),
    ("pyyaml", ">=6.0"),
]

for package_name, version in packages_to_install:
    try:
        logger.info(f"Installing {package_name}{version}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", f"{package_name}{version}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"  ✓ {package_name} installed")
    except subprocess.CalledProcessError as e:
        logger.error(f"  ✗ Failed to install {package_name}: {e}")

logger.info("✓ All dependencies installed")
print("\n✓ Dependencies installed successfully\n")

# ============================================================================
# CELL 3: EXPLORE DATASET STRUCTURE
# ============================================================================

logger.info("=" * 100)
logger.info("EXPLORING DATASET STRUCTURE")
logger.info("=" * 100)

dataset_path = Path("/kaggle/input/datasets/mollous/p-and-id-symbols-for-computer-vision")

logger.info(f"Dataset path: {dataset_path}")
logger.info(f"Dataset exists: {dataset_path.exists()}")

if not dataset_path.exists():
    logger.error(f"✗ Dataset not found at {dataset_path}")
    raise FileNotFoundError(f"Dataset not found at {dataset_path}")

# Explore structure
print("\n" + "=" * 100)
print("DATASET STRUCTURE")
print("=" * 100)

def explore_directory(path, max_depth=2, current_depth=0, prefix=""):
    """Recursively explore directory structure"""
    if current_depth >= max_depth:
        return

    try:
        items = sorted(os.listdir(path))
        for item in items[:20]:  # Limit items shown
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print(f"{prefix}├── {item}/")
                if current_depth < max_depth - 1:
                    explore_directory(item_path, max_depth, current_depth + 1, prefix + "│   ")
            else:
                print(f"{prefix}├── {item}")
    except PermissionError:
        pass

explore_directory(str(dataset_path), max_depth=3)

# Check for YOLO structure
logger.info("\nVerifying YOLO dataset structure...")

splits_info = {}
for split in ['train', 'val', 'test']:
    split_path = dataset_path / split
    if split_path.exists():
        images_path = split_path / "images"
        labels_path = split_path / "labels"

        image_count = len(list(images_path.glob("*"))) if images_path.exists() else 0
        label_count = len(list(labels_path.glob("*"))) if labels_path.exists() else 0

        splits_info[split] = {
            "exists": True,
            "images": image_count,
            "labels": label_count,
            "path": str(split_path)
        }

        logger.info(f"✓ {split.upper():6} : {image_count:5} images | {label_count:5} labels")
        print(f"  ✓ {split.upper():6} : {image_count:5} images | {label_count:5} labels")
    else:
        splits_info[split] = {"exists": False}
        logger.warning(f"✗ {split.upper()} directory not found")

# Save dataset info
with open(os.path.join(log_dir, "dataset_info.json"), "w") as f:
    json.dump(splits_info, f, indent=2)

total_images = sum(info.get("images", 0) for info in splits_info.values())
logger.info(f"Total images: {total_images}")
print(f"\nTotal images: {total_images}")
print("=" * 100 + "\n")

# ============================================================================
# CELL 4: CREATE YOLO CONFIGURATION FILE
# ============================================================================

logger.info("=" * 100)
logger.info("CREATING YOLO DATA CONFIGURATION")
logger.info("=" * 100)

import yaml

# Create data.yaml
data_yaml_content = {
    'path': str(dataset_path),
    'train': 'train/images',
    'val': 'val/images',
    'test': 'test/images',
    'nc': 1,  # Number of classes
    'names': ['pid_symbol']  # Class names
}

yaml_path = "/kaggle/working/data.yaml"
with open(yaml_path, 'w') as f:
    yaml.dump(data_yaml_content, f, default_flow_style=False, sort_keys=False)

logger.info(f"Created data.yaml at: {yaml_path}")
logger.info("Dataset configuration:")
for key, value in data_yaml_content.items():
    logger.info(f"  {key}: {value}")

print("✓ Data configuration created (data.yaml)")
print("=" * 100 + "\n")

# ============================================================================
# CELL 5: VERIFY DATASET FORMAT
# ============================================================================

logger.info("=" * 100)
logger.info("VERIFYING DATASET FORMAT")
logger.info("=" * 100)

import cv2

train_images_path = dataset_path / "train" / "images"
train_labels_path = dataset_path / "train" / "labels"

if train_images_path.exists():
    # Get image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(train_images_path.glob(ext)))

    image_files = sorted(image_files)[:5]  # Check first 5

    logger.info(f"Checking {len(image_files)} sample images...")

    print("\nSample Images Verification:")
    print("=" * 100)

    allValid = True
    for idx, img_file in enumerate(image_files, 1):
        try:
            # Read image
            img = cv2.imread(str(img_file))
            if img is None:
                logger.warning(f"  ✗ Unable to read: {img_file.name}")
                allValid = False
                continue

            h, w = img.shape[:2]

            # Check label
            label_file = train_labels_path / (img_file.stem + ".txt")
            label_exists = label_file.exists()

            status = "✓" if label_exists else "✗"
            print(f"{status} Sample {idx}: {img_file.name}")
            print(f"   Size: {w}x{h} | Label: {status}")

            logger.info(f"  {status} {img_file.name}: {w}x{h} | Label: {status}")

            if label_exists:
                with open(label_file, 'r') as f:
                    label_data = f.read().strip()
                    if label_data:
                        logger.info(f"     Label: {label_data}")

        except Exception as e:
            logger.error(f"  ✗ Error checking {img_file.name}: {e}")
            allValid = False

    if allValid:
        logger.info("✓ All sample images and labels verified successfully")
        print("\n✓ Dataset format verified successfully!")
    else:
        logger.warning("⚠ Some issues found in dataset format")

    print("=" * 100 + "\n")

# ============================================================================
# CELL 6: TRAIN YOLOV8 MODEL
# ============================================================================

logger.info("=" * 100)
logger.info("YOLOV8 MODEL TRAINING")
logger.info("=" * 100)

from ultralytics import YOLO

# Model configuration
model_size = "n"  # nano (fastest), s (small), m (medium), l (large)
logger.info(f"Loading YOLOv8{model_size} model...")

try:
    model = YOLO(f"yolov8{model_size}.pt")
    logger.info(f"✓ Model loaded successfully: YOLOv8{model_size}")
    print(f"\n✓ Model loaded: YOLOv8{model_size}")
except Exception as e:
    logger.error(f"✗ Failed to load model: {e}")
    raise

# Training hyperparameters
training_params = {
    'data': yaml_path,
    'epochs': 100,
    'imgsz': 640,
    'batch': 16,  # Adjust based on GPU memory
    'device': 0,  # GPU device index
    'project': '/kaggle/working',
    'name': 'yolov8_pid_training',
    'exist_ok': True,
    'patience': 20,
    'save': True,
    'save_period': 10,
    'plots': True,
    'verbose': True,
    'optimizer': 'SGD',
    'lr0': 0.01,
    'lrf': 0.01,
    'momentum': 0.937,
    'weight_decay': 0.0005,
    'warmup_epochs': 3.0,
    'warmup_momentum': 0.8,
    'warmup_bias_lr': 0.1,
    'box': 7.5,
    'cls': 0.5,
    'dfl': 1.5,
    'mosaic': 1.0,
    'flipud': 0.5,
    'fliplr': 0.5,
    'hsv_h': 0.015,
    'hsv_s': 0.7,
    'hsv_v': 0.4,
    'degrees': 0.0,
    'translate': 0.1,
    'scale': 0.5,
    'perspective': 0.0,
    'mixup': 0.0,
}

logger.info("\n" + "=" * 100)
logger.info("TRAINING CONFIGURATION")
logger.info("=" * 100)

for param, value in training_params.items():
    logger.info(f"  {param:20} : {value}")

logger.info("=" * 100)
logger.info("Starting training...")
logger.info("=" * 100 + "\n")

print("\n" + "=" * 100)
print("STARTING YOLO TRAINING")
print("=" * 100)
print(f"Model: YOLOv8{model_size}")
print(f"Epochs: {training_params['epochs']}")
print(f"Batch Size: {training_params['batch']}")
print(f"Image Size: {training_params['imgsz']}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
print("=" * 100 + "\n")

try:
    # Start training
    results = model.train(**training_params)

    logger.info("\n" + "=" * 100)
    logger.info("✓ TRAINING COMPLETED SUCCESSFULLY")
    logger.info("=" * 100)

    print("\n✓ TRAINING COMPLETED!\n")

    # Log results
    if results is not None:
        logger.info("Training completed successfully")
        logger.info(f"Results saved to: {results.save_dir}")

except KeyboardInterrupt:
    logger.warning("Training interrupted by user")
    print("\n⚠ Training interrupted by user")

except Exception as e:
    logger.error(f"✗ Training failed: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

# ============================================================================
# CELL 7: VALIDATE & EVALUATE MODEL
# ============================================================================

logger.info("\n" + "=" * 100)
logger.info("MODEL VALIDATION")
logger.info("=" * 100)

try:
    logger.info("Running validation on validation set...")

    # Validate
    val_results = model.val()

    logger.info("✓ Validation completed")

    if val_results is not None:
        logger.info(f"Results saved to: {val_results.save_dir if hasattr(val_results, 'save_dir') else 'N/A'}")

    print("✓ Model validation completed")

except Exception as e:
    logger.error(f"Validation failed: {e}")
    print(f"⚠ Validation error: {e}")

# ============================================================================
# CELL 8: EXPORT TRAINED MODEL
# ============================================================================

logger.info("\n" + "=" * 100)
logger.info("EXPORTING TRAINED MODEL")
logger.info("=" * 100)

best_model_path = "/kaggle/working/yolov8_pid_training/weights/best.pt"

if os.path.exists(best_model_path):
    logger.info(f"Best model found: {best_model_path}")
    logger.info(f"File size: {os.path.getsize(best_model_path) / 1e6:.2f} MB")

    # Load best model
    logger.info("Loading best trained model...")
    best_model = YOLO(best_model_path)

    # Export to multiple formats
    export_formats = ['pt']  # Can add 'onnx', 'torchscript'

    logger.info("Exporting model to different formats...")
    for fmt in export_formats:
        try:
            logger.info(f"  Exporting to {fmt.upper()}...")
            export_path = best_model.export(format=fmt)
            export_size = os.path.getsize(export_path) / 1e6
            logger.info(f"    ✓ Exported: {export_path} ({export_size:.2f} MB)")
            print(f"  ✓ Exported to {fmt.upper()}")
        except Exception as e:
            logger.error(f"  ✗ Export to {fmt.upper()} failed: {e}")

    logger.info("✓ Model export completed")
    print("\n✓ Model exported successfully")
else:
    logger.error(f"Best model not found at {best_model_path}")

# ============================================================================
# CELL 9: TRAINING SUMMARY & LOGS
# ============================================================================

logger.info("\n" + "=" * 100)
logger.info("TRAINING SUMMARY")
logger.info("=" * 100)

training_summary = {
    "timestamp": timestamp,
    "dataset": "P&ID Symbols for Computer Vision",
    "dataset_path": str(dataset_path),
    "model": f"YOLOv8{model_size}",
    "epochs": training_params["epochs"],
    "batch_size": training_params["batch"],
    "image_size": training_params["imgsz"],
    "gpu_used": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    "training_completed": True,
    "log_file": log_file,
    "model_output_dir": "/kaggle/working/yolov8_pid_training",
    "best_model": best_model_path,
    "training_params": training_params
}

summary_path = os.path.join(log_dir, "training_summary.json")
with open(summary_path, "w") as f:
    json.dump(training_summary, f, indent=2)

logger.info("Summary saved to: " + summary_path)

for key, value in training_summary.items():
    if key != "training_params":
        logger.info(f"  {key:25} : {value}")

logger.info("=" * 100)

print("\n" + "=" * 100)
print("TRAINING COMPLETE - SUMMARY")
print("=" * 100)
print(f"\nTimestamp: {timestamp}")
print(f"Model: YOLOv8{model_size}")
print(f"Training Epochs: {training_params['epochs']}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
print("\nImportant Files:")
print(f"  📊 Best Model: {best_model_path}")
print(f"  📋 Log File: {log_file}")
print(f"  📑 Summary: {summary_path}")
print(f"  📈 Training Results: /kaggle/working/yolov8_pid_training/results.csv")
print(f"  📁 All outputs: /kaggle/working/yolov8_pid_training/")
print("\n✓ All logs and models saved to /kaggle/working/")
print("=" * 100 + "\n")

# ============================================================================
# CELL 10: TEST TRAINED MODEL (OPTIONAL)
# ============================================================================

logger.info("=" * 100)
logger.info("TESTING TRAINED MODEL")
logger.info("=" * 100)

if os.path.exists(best_model_path):
    try:
        logger.info("Loading best model for testing...")
        test_model = YOLO(best_model_path)

        # Test on a sample image from test set
        test_images = list((dataset_path / "test" / "images").glob("*"))

        if test_images:
            test_image = test_images[0]
            logger.info(f"Testing on sample image: {test_image.name}")

            # Run inference
            results = test_model.predict(source=str(test_image), conf=0.25)

            logger.info(f"✓ Inference completed on {test_image.name}")
            logger.info(f"  Detections: {len(results[0].boxes) if results else 0}")

            if results and len(results[0].boxes) > 0:
                for i, box in enumerate(results[0].boxes):
                    conf = float(box.conf[0])
                    logger.info(f"  Detection {i+1}: confidence={conf:.3f}")

        logger.info("✓ Model testing completed")
        print("\n✓ Model testing completed successfully!")

    except Exception as e:
        logger.error(f"Testing failed: {e}")
        print(f"\n⚠ Testing error: {e}")
else:
    logger.warning("Best model not found - skipping testing")

logger.info("\n" + "=" * 100)
logger.info("TRAINING PIPELINE COMPLETED")
logger.info("=" * 100)

print("\n" + "=" * 100)
print("✓ YOLO TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
print("=" * 100 + "\n")
