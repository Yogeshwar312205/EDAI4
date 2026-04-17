#!/usr/bin/env python3
"""
Quick script to update SAHI parameters to fix clustered detection
"""
import re
from pathlib import Path

def update_sahi_parameters():
    """Update SAHI parameters in high_density_pipeline.py"""
    
    file_path = Path("src/perception/high_density_pipeline.py")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_path = file_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_path}")
    
    # Update parameters
    changes_made = []
    
    # Update slice_size
    new_content = re.sub(
        r'slice_size:\s*int\s*=\s*640',
        'slice_size: int = 800',
        content
    )
    if new_content != content:
        changes_made.append("slice_size: 640 → 800")
        content = new_content
    
    # Update overlap_ratio
    new_content = re.sub(
        r'overlap_ratio:\s*float\s*=\s*0\.25',
        'overlap_ratio: float = 0.3',
        content
    )
    if new_content != content:
        changes_made.append("overlap_ratio: 0.25 → 0.3")
        content = new_content
    
    # Update confidence_threshold
    new_content = re.sub(
        r'confidence_threshold:\s*float\s*=\s*0\.20',
        'confidence_threshold: float = 0.15',
        content
    )
    if new_content != content:
        changes_made.append("confidence_threshold: 0.20 → 0.15")
        content = new_content
    
    if not changes_made:
        print("⚠️  No changes needed - parameters already updated or not found")
        return False
    
    # Write updated file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ SAHI parameters updated successfully!")
    print("\nChanges made:")
    for change in changes_made:
        print(f"  • {change}")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Restart the backend:")
    print("   python -m uvicorn src.api.main:app --reload")
    print()
    print("2. Process your P&ID image again")
    print()
    print("3. Check if nodes are now spread out:")
    print("   python scripts/check_backend_coordinates.py")
    print()
    print("4. If still clustered, check:")
    print("   • Image dimensions in backend logs")
    print("   • Debug visualization: data/output/debug_detections.jpg")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("SAHI Parameter Fix Script")
    print("="*60)
    print()
    print("This script will update SAHI detection parameters to:")
    print("  • Increase slice_size: 640 → 800")
    print("  • Increase overlap_ratio: 0.25 → 0.3")
    print("  • Decrease confidence_threshold: 0.20 → 0.15")
    print()
    print("These changes help detect objects across the full P&ID image.")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    success = update_sahi_parameters()
    
    if success:
        print("\n✅ Done! Restart the backend and try again.")
    else:
        print("\n⚠️  Please check the file manually.")
