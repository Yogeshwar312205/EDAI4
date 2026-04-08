# ============================================================================
# KAGGLE NOTEBOOK - YOLO P&ID TRAINING
# Copy this entire code into ONE cell in your Kaggle notebook
# ============================================================================

# Before running: Enable GPU in Settings → Accelerator

import os, sys, logging, json, subprocess
from datetime import datetime
from pathlib import Path
import torch
import numpy as np
import yaml
import cv2

# ===== SETUP LOGGING =====
log_dir = "/kaggle/working/logs"
os.makedirs(log_dir, exist_ok=True)
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
logger = logging.getLogger("YOLO-P&ID")

# ===== CHECK GPU =====
print("\n" + "=" * 100)
print("GPU STATUS")
print("=" * 100)

logger.info("Starting YOLO P&ID Training")
logger.info(f"GPU Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print(f"✓ GPU ENABLED: {torch.cuda.get_device_name(0)}")
else:
    logger.warning("GPU NOT AVAILABLE!")
    print("✗ GPU NOT AVAILABLE - Using CPU (VERY SLOW)")

print("=" * 100 + "\n")

# ===== INSTALL PACKAGES =====
print("Installing packages...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics", "roboflow"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("✓ Packages installed\n")

# ===== EXPLORE DATASET =====
dataset_path = Path("/kaggle/input/datasets/mollous/p-and-id-symbols-for-computer-vision")

print("=" * 100)
print("DATASET INFORMATION")
print("=" * 100)

for split in ['train', 'val', 'test']:
    split_path = dataset_path / split
    if split_path.exists():
        images = len(list((split_path / "images").glob("*")))
        labels = len(list((split_path / "labels").glob("*")))
        logger.info(f"{split.upper():6} : {images:5} images | {labels:5} labels")
        print(f"✓ {split.upper():6} : {images:5} images | {labels:5} labels")

print("=" * 100 + "\n")

# ===== CREATE DATA.YAML =====
data_yaml = {
    'path': str(dataset_path),
    'train': 'train/images',
    'val': 'val/images',
    'test': 'test/images',
    'nc': 1,
    'names': ['pid_symbol']
}

yaml_path = "/kaggle/working/data.yaml"
with open(yaml_path, 'w') as f:
    yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

logger.info(f"Created data.yaml")
print("✓ Data configuration created\n")

# ===== VERIFY DATASET =====
print("Verifying dataset format...")
images_path = dataset_path / "train" / "images"
sample_images = list(images_path.glob("*.jpg"))[:3] + list(images_path.glob("*.png"))[:3]

for img_file in sample_images[:3]:
    img = cv2.imread(str(img_file))
    if img is not None:
        h, w = img.shape[:2]
        logger.info(f"✓ {img_file.name}: {w}x{h}")
        print(f"  ✓ {img_file.name}: {w}x{h}")

print("✓ Dataset verified\n")

# ===== TRAIN YOLOV8 =====
print("=" * 100)
print("STARTING YOLOV8 TRAINING")
print("=" * 100)

from ultralytics import YOLO

logger.info("Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")
logger.info("Model loaded")

# Training parameters
training_config = {
    'data': yaml_path,
    'epochs': 100,
    'imgsz': 640,
    'batch': 16,
    'device': 0,
    'project': '/kaggle/working',
    'name': 'yolov8_pid_training',
    'exist_ok': True,
    'patience': 20,
    'save': True,
    'plots': True,
    'verbose': True,
    'optimizer': 'SGD',
    'lr0': 0.01,
    'momentum': 0.937,
}

logger.info("Training Configuration:")
for key, val in training_config.items():
    logger.info(f"  {key}: {val}")

print("\nTraining in progress...")
print(f"Model: YOLOv8n | Epochs: 100 | Batch: 16 | GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}\n")

try:
    results = model.train(**training_config)
    logger.info("✓ TRAINING COMPLETED")
    print("\n✓ TRAINING COMPLETED!\n")

    # Validate
    logger.info("Running validation...")
    val_results = model.val()
    logger.info("✓ Validation completed")
    print("✓ Validation completed\n")

except Exception as e:
    logger.error(f"Training failed: {e}")
    raise

# ===== EXPORT MODEL =====
best_model_path = "/kaggle/working/yolov8_pid_training/weights/best.pt"

if os.path.exists(best_model_path):
    logger.info(f"Best model: {best_model_path}")
    logger.info(f"File size: {os.path.getsize(best_model_path) / 1e6:.2f} MB")
    print(f"✓ Best model saved: best.pt ({os.path.getsize(best_model_path) / 1e6:.2f} MB)")

# ===== SUMMARY =====
summary = {
    "timestamp": timestamp,
    "model": "YOLOv8n",
    "epochs": 100,
    "dataset": "P&ID Symbols",
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    "best_model": best_model_path,
    "log_file": log_file
}

with open(log_dir + "/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Best Model: {best_model_path}")
print(f"Log File: {log_file}")
print(f"Results: /kaggle/working/yolov8_pid_training/results.csv")
print(f"Weights: /kaggle/working/yolov8_pid_training/weights/")
print("=" * 100)
print("\n✓ TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
print("\nDownload these files from /kaggle/working/:")
print("  1. yolov8_pid_training/weights/best.pt (trained model)")
print("  2. yolov8_pid_training/results.csv (metrics)")
print("  3. logs/ (complete logs)\n")
