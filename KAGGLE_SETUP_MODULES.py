"""
EDAI4 - Kaggle Quick Setup Script
Run this FIRST in a Kaggle cell to create the module structure.

After running this, you can import from src.* in subsequent cells.
"""

import os

# Create directory structure
dirs = [
    '/kaggle/working/src',
    '/kaggle/working/src/perception',
    '/kaggle/working/src/topology',
    '/kaggle/working/src/utils',
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✓ Created: {d}")

# Create __init__ files
init_files = {
    '/kaggle/working/src/__init__.py': '"""EDAI4 Source Package"""',
    
    '/kaggle/working/src/utils/__init__.py': '''"""EDAI4 Utils"""
from src.utils.logger import setup_logger, get_logger
__all__ = ["setup_logger", "get_logger"]
''',

    '/kaggle/working/src/utils/logger.py': '''"""Simple logger for Kaggle (no loguru dependency)"""
import logging
import sys

def setup_logger(name: str = "edai4", level: str = "INFO"):
    """Setup basic logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str = "edai4"):
    """Get or create logger."""
    return setup_logger(name)
''',
}

for filepath, content in init_files.items():
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Created: {filepath}")

print("\n" + "=" * 60)
print("✅ Module structure created!")
print("=" * 60)
print("\n⚠️ NEXT STEPS:")
print("1. Upload your EDAI4 source files to these directories:")
print("   - src/perception/*.py")
print("   - src/topology/*.py")
print("")
print("2. OR run the next cell to copy from a zip/tar upload")
print("")
print("3. Then run the main pipeline test")
