"""
FIXED YOLO P&ID TRAINING FOR KAGGLE
Handles pip installation errors properly with detailed logging
"""

import os, sys, logging, json, subprocess, time
from datetime import datetime
from pathlib import Path
import torch
import numpy as np

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

# ===== INSTALL PACKAGES (FIXED) =====
print("Installing required packages...")
print("=" * 100)

logger.info("Installing packages with detailed output...")

packages_to_install = [
    "pyyaml",
    "opencv-python",
    "numpy",
    "torch",
]

# First upgrade pip
print("Upgrading pip...")
logger.info("Upgrading pip...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
        text=True,
        timeout=300
    )
    if result.returncode != 0:
        logger.warning(f"pip upgrade had issues: {result.stderr}")
    else:
        print("✓ pip upgraded")
except Exception as e:
    logger.warning(f"pip upgrade failed: {e}")

# Install ultralytics (critical package)
print("\nInstalling ultralytics...")
logger.info("Installing ultralytics...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "ultralytics", "-v"],
        capture_output=True,
        text=True,
        timeout=600
    )
    if result.returncode == 0:
        print("✓ ultralytics installed")
        logger.info("✓ ultralytics installed successfully")
    else:
        print(f"⚠ ultralytics installation had issues:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        logger.error(f"ultralytics installation stderr: {result.stderr}")
        logger.warning("Continuing anyway, trying to import...")

except Exception as e:
    logger.error(f"ultralytics installation failed: {e}")
    print(f"Error: {e}")

# Try importing ultralytics to verify
print("\nVerifying ultralytics installation...")
logger.info("Verifying ultralytics installation...")
try:
    from ultralytics import YOLO
    print("✓ ultralytics imported successfully")
    logger.info("✓ ultralytics verified")
except ImportError as e:
    print(f"✗ Failed to import ultralytics: {e}")
    logger.error(f"✗ Failed to import ultralytics: {e}")
    print("\nTrying alternative installation...")
    logger.info("Attempting alternative ultralytics installation...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "ultralytics==8.0.221"],
            capture_output=True,
            timeout=600
        )
        from ultralytics import YOLO
        print("✓ ultralytics installed (alternative version)")
        logger.info("✓ ultralytics installed (alternative version)")
    except Exception as e2:
        logger.error(f"Alternative installation also failed: {e2}")
        raise

print("=" * 100 + "\n")

# ===== EXPLORE DATASET =====
dataset_path = Path("/kaggle/input/datasets/mollous/p-and-id-symbols-for-computer-vision")

print("=" * 100)
print("DATASET INFORMATION")
print("=" * 100)

logger.info(f"Checking dataset at: {dataset_path}")

if not dataset_path.exists():
    logger.error(f"Dataset not found at {dataset_path}")
    print(f"✗ Dataset not found at {dataset_path}")
    print("\nAvailable inputs:")
    input_dir = Path("/kaggle/input")
    for item in input_dir.iterdir():
        print(f"  - {item.name}")
    raise FileNotFoundError(f"Dataset not found")

for split in ['train', 'val', 'test']:
    split_path = dataset_path / split
    if split_path.exists():
        images = len(list((split_path / "images").glob("*")))
        labels = len(list((split_path / "labels").glob("*")))
        logger.info(f"{split.upper():6} : {images:5} images | {labels:5} labels")
        print(f"✓ {split.upper():6} : {images:5} images | {labels:5} labels")
    else:
        logger.warning(f"{split.upper()} directory not found")
        print(f"✗ {split.upper():6} not found")

print("=" * 100 + "\n")

# ===== CREATE DATA.YAML =====
print("Creating YOLO configuration...")

import yaml

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

logger.info(f"Created data.yaml at {yaml_path}")
print("✓ Data configuration created (data.yaml)\n")

# ===== VERIFY DATASET =====
print("Verifying dataset format...")
import cv2

images_path = dataset_path / "train" / "images"
sample_images = list(images_path.glob("*.jpg"))[:3]
if not sample_images:
    sample_images = list(images_path.glob("*.png"))[:3]

logger.info(f"Testing {len(sample_images)} sample images...")
for img_file in sample_images:
    try:
        img = cv2.imread(str(img_file))
        if img is not None:
            h, w = img.shape[:2]
            logger.info(f"✓ {img_file.name}: {w}x{h}")
            print(f"  ✓ {img_file.name}: {w}x{h}")
        else:
            logger.warning(f"Could not read {img_file.name}")
    except Exception as e:
        logger.error(f"Error reading {img_file.name}: {e}")

print("✓ Dataset verified\n")

# ===== TRAIN YOLOV8 =====
print("=" * 100)
print("STARTING YOLOV8 TRAINING")
print("=" * 100)

logger.info("Loading YOLOv8n model...")
print("\nLoading YOLOv8n model...")

try:
    model = YOLO("yolov8n.pt")
    logger.info("✓ Model loaded successfully")
    print("✓ YOLOv8n model loaded\n")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    print(f"✗ Failed to load model: {e}")
    raise

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

print("Training Configuration:")
for key, val in training_config.items():
    if key != 'data':
        print(f"  {key}: {val}")

print("\nTraining Progress:")
print("=" * 100)

try:
    # Start training
    results = model.train(**training_config)

    logger.info("✓ TRAINING COMPLETED")
    print("\n" + "=" * 100)
    print("✓ TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 100)

except Exception as e:
    logger.error(f"Training failed: {type(e).__name__}: {e}")
    print(f"\n✗ Training failed: {e}")
    import traceback
    logger.error(traceback.format_exc())
    raise

# ===== VALIDATION =====
print("\nRunning validation...")
logger.info("Running validation...")

try:
    val_results = model.val()
    logger.info("✓ Validation completed")
    print("✓ Validation completed\n")
except Exception as e:
    logger.error(f"Validation failed: {e}")
    print(f"⚠ Validation error: {e}\n")

# ===== CHECK OUTPUT =====
best_model_path = "/kaggle/working/yolov8_pid_training/weights/best.pt"

if os.path.exists(best_model_path):
    size_mb = os.path.getsize(best_model_path) / 1e6
    logger.info(f"✓ Best model saved: {best_model_path} ({size_mb:.2f} MB)")
    print(f"✓ Best model saved: best.pt ({size_mb:.2f} MB)")
else:
    logger.warning(f"Best model not found at expected location")
    print(f"⚠ Best model not found at: {best_model_path}")

# ===== SUMMARY =====
summary = {
    "timestamp": timestamp,
    "model": "YOLOv8n",
    "epochs": 100,
    "dataset": "P&ID Symbols",
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    "best_model": best_model_path,
    "log_file": log_file,
    "training_completed": True
}

with open(log_dir + "/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

logger.info("\n" + "=" * 100)
logger.info("TRAINING PIPELINE COMPLETED")
logger.info("=" * 100)

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Model: YOLOv8n")
print(f"Epochs: 100")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
print(f"\nOutput Files:")
print(f"  📊 Best Model: {best_model_path}")
print(f"  📈 Results: /kaggle/working/yolov8_pid_training/results.csv")
print(f"  📋 Logs: {log_file}")
print(f"  📁 Weights: /kaggle/working/yolov8_pid_training/weights/")
print("=" * 100)
print("\n✓ YOLO TRAINING COMPLETED!")
print("\nDownload these files:")
print("  1. yolov8_pid_training/weights/best.pt")
print("  2. yolov8_pid_training/results.csv")
print("  3. logs/yolo_training_*.log")
print("\n" + "=" * 100)
