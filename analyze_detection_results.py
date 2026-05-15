"""
Analyze Detection Results
Compare your detection results with expected P&ID components
"""

import json

# Your detection results
detection_results = {
    "image_name": "Screenshot 2026-04-23 112939.png",
    "processing_time_ms": 115569.24343109131,
    "layer1_detections": 47,
    "layer2_instruments": 35,
    "layer3_nodes": 50,
    "layer3_edges": 88,
    "detections": [
        {"class_name": "valve.control", "confidence": 0.8990731835365295, "bbox": {"x1": 895.7428588867188, "y1": 293.51515197753906, "x2": 956.0084838867188, "y2": 390.0522766113281}, "tag": None},
        {"class_name": "valve.control", "confidence": 0.8032587766647339, "bbox": {"x1": 1127.44873046875, "y1": 307.4864196777344, "x2": 1181.416748046875, "y2": 352.9651794433594}, "tag": None},
        {"class_name": "valve.control", "confidence": 0.6853046417236328, "bbox": {"x1": 1092.2005920410156, "y1": 521.3792724609375, "x2": 1150.5558471679688, "y2": 567.4720458984375}, "tag": None},
        {"class_name": "equipment.pump", "confidence": 0.6845385432243347, "bbox": {"x1": 436.08770751953125, "y1": 715.8857421875, "x2": 529.2684936523438, "y2": 805.0175170898438}, "tag": "00-8"},
        {"class_name": "valve.control", "confidence": 0.5279504656791687, "bbox": {"x1": 353.5870666503906, "y1": 728.1568603515625, "x2": 409.3777770996094, "y2": 772.2255859375}, "tag": "4"},
        {"class_name": "valve.control", "confidence": 0.5004816651344299, "bbox": {"x1": 665.8997802734375, "y1": 475.6836853027344, "x2": 725.1263885498047, "y2": 541.42529296875}, "tag": "AA  FWN N="},
        {"class_name": "valve.control", "confidence": 0.4874928891658783, "bbox": {"x1": 895.141357421875, "y1": 627.4375610351562, "x2": 923.1913452148438, "y2": 649.4840087890625}, "tag": None},
        {"class_name": "valve.control", "confidence": 0.46425774693489075, "bbox": {"x1": 1250.807861328125, "y1": 210.54129028320312, "x2": 1295.2269287109375, "y2": 262.4457092285156}, "tag": None},
        {"class_name": "valve.control", "confidence": 0.43017950654029846, "bbox": {"x1": 427.7281188964844, "y1": 494.52874755859375, "x2": 477.783203125, "y2": 541.6771240234375}, "tag": "C0L"},
        {"class_name": "valve.general", "confidence": 0.3738698959350586, "bbox": {"x1": 1011.2316284179688, "y1": 204.18328857421875, "x2": 1042.7786865234375, "y2": 249.0636749267578}, "tag": None},
        {"class_name": "valve.general", "confidence": 0.3496783673763275, "bbox": {"x1": 363.6606750488281, "y1": 471.44647216796875, "x2": 382.6217956542969, "y2": 484.59552001953125}, "tag": "X"},
        {"class_name": "valve.control", "confidence": 0.31206566095352173, "bbox": {"x1": 1004.3635864257812, "y1": 202.46456909179688, "x2": 1039.8990478515625, "y2": 249.1510772705078}, "tag": None},
        {"class_name": "valve.general", "confidence": 0.25882813334465027, "bbox": {"x1": 668.855224609375, "y1": 508.20965576171875, "x2": 721.9532470703125, "y2": 542.6072998046875}, "tag": None},
        {"class_name": "valve.general", "confidence": 0.226030170917511, "bbox": {"x1": 1252.5523376464844, "y1": 215.09914541244507, "x2": 1284.1609497070312, "y2": 262.7943344116211}, "tag": None},
        {"class_name": "instrument.bubble", "confidence": 0.85, "bbox": {"x1": 366.0, "y1": 323.0, "x2": 410.0, "y2": 367.0}, "tag": "Z00-WESSS"},
        {"class_name": "instrument.bubble", "confidence": 0.85, "bbox": {"x1": 549.0, "y1": 732.0, "x2": 599.0, "y2": 782.0}, "tag": "HEET-L0-T"},
        {"class_name": "instrument.bubble", "confidence": 0.85, "bbox": {"x1": 797.0, "y1": 491.0, "x2": 865.0, "y2": 559.0}, "tag": "I11L"},
        {"class_name": "instrument.bubble", "confidence": 0.85, "bbox": {"x1": 252.0, "y1": 548.0, "x2": 314.0, "y2": 610.0}, "tag": "0"},
        {"class_name": "instrument.bubble", "confidence": 0.8, "bbox": {"x1": 958.0, "y1": 638.0, "x2": 1024.0, "y2": 704.0}, "tag": None},
        {"class_name": "instrument.bubble", "confidence": 0.8, "bbox": {"x1": 1294.0, "y1": 772.0, "x2": 1360.0, "y2": 838.0}, "tag": None},
    ]
}

# Expected components from visual inspection of P&ID
expected_components = {
    "Storage Tank": {
        "type": "equipment.tank",
        "approximate_location": "Left side (x: 100-400, y: 300-600)",
        "detected": False,
        "reason": "Class 'equipment.tank' not in model"
    },
    "Vessel V-102": {
        "type": "equipment.vessel",
        "approximate_location": "Right side (x: 700-900, y: 150-450)",
        "detected": False,
        "reason": "Class 'equipment.vessel' not in model"
    },
    "Heat Exchanger": {
        "type": "equipment.heat_exchanger",
        "approximate_location": "Center (x: 500-650, y: 350-450)",
        "detected": False,
        "reason": "Class 'equipment.heat_exchanger' not in model"
    },
    "Compressor C-101": {
        "type": "equipment.compressor",
        "approximate_location": "Right side (x: 900-1100, y: 150-300)",
        "detected": False,
        "reason": "Detected as 'equipment.compressor_blower' but low confidence or missed"
    },
    "Centrifugal Pump": {
        "type": "equipment.pump",
        "approximate_location": "Bottom center (x: 400-550, y: 700-800)",
        "detected": True,
        "confidence": 0.68,
        "reason": "✓ Detected correctly"
    },
    "Motor M-101": {
        "type": "equipment.motor",
        "approximate_location": "Bottom (x: 350-450, y: 500-600)",
        "detected": False,
        "reason": "Class 'equipment.motor' not in model"
    },
    "Reducer": {
        "type": "fitting.reducer",
        "approximate_location": "Multiple locations",
        "detected": False,
        "reason": "Low confidence or missed"
    }
}

def analyze_detections():
    """Analyze detection results"""
    
    print("=" * 80)
    print("P&ID DETECTION ANALYSIS")
    print("=" * 80)
    
    # Summary statistics
    detections = detection_results["detections"]
    
    print(f"\n📊 SUMMARY")
    print("-" * 80)
    print(f"Total detections: {len(detections)}")
    print(f"Processing time: {detection_results['processing_time_ms']/1000:.2f} seconds")
    
    # Count by class
    class_counts = {}
    for det in detections:
        class_name = det['class_name']
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
    
    print(f"\n📦 DETECTIONS BY CLASS")
    print("-" * 80)
    for class_name, count in sorted(class_counts.items()):
        print(f"  {class_name:30s}: {count:3d}")
    
    # Confidence analysis
    confidences = [det['confidence'] for det in detections]
    
    print(f"\n📈 CONFIDENCE DISTRIBUTION")
    print("-" * 80)
    print(f"  Minimum:  {min(confidences):.3f}")
    print(f"  Maximum:  {max(confidences):.3f}")
    print(f"  Average:  {sum(confidences)/len(confidences):.3f}")
    
    # Confidence ranges
    high_conf = sum(1 for c in confidences if c >= 0.7)
    med_conf = sum(1 for c in confidences if 0.5 <= c < 0.7)
    low_conf = sum(1 for c in confidences if 0.3 <= c < 0.5)
    very_low_conf = sum(1 for c in confidences if c < 0.3)
    
    print(f"\n  High (≥0.7):      {high_conf:3d} ({high_conf/len(confidences)*100:5.1f}%)")
    print(f"  Medium (0.5-0.7): {med_conf:3d} ({med_conf/len(confidences)*100:5.1f}%)")
    print(f"  Low (0.3-0.5):    {low_conf:3d} ({low_conf/len(confidences)*100:5.1f}%)")
    print(f"  Very Low (<0.3):  {very_low_conf:3d} ({very_low_conf/len(confidences)*100:5.1f}%)")
    
    # Tag analysis
    tagged = [det for det in detections if det.get('tag')]
    
    print(f"\n🏷️  TAG READING")
    print("-" * 80)
    print(f"  Detections with tags: {len(tagged)}/{len(detections)} ({len(tagged)/len(detections)*100:.1f}%)")
    
    if tagged:
        print(f"\n  Detected tags:")
        for det in tagged:
            tag = det['tag']
            valid = "✓" if is_valid_isa_tag(tag) else "✗"
            print(f"    {valid} {tag:20s} (confidence: {det['confidence']:.3f})")
    
    # Expected components analysis
    print(f"\n🎯 EXPECTED COMPONENTS")
    print("-" * 80)
    
    detected_count = sum(1 for comp in expected_components.values() if comp['detected'])
    total_count = len(expected_components)
    
    print(f"  Detected: {detected_count}/{total_count} ({detected_count/total_count*100:.1f}%)")
    print()
    
    for name, info in expected_components.items():
        status = "✓" if info['detected'] else "✗"
        print(f"  {status} {name:25s}")
        print(f"     Type: {info['type']}")
        print(f"     Location: {info['approximate_location']}")
        print(f"     Status: {info['reason']}")
        print()
    
    # Issues summary
    print(f"\n⚠️  ISSUES IDENTIFIED")
    print("-" * 80)
    
    issues = [
        ("Missing Equipment Classes", [
            "equipment.tank",
            "equipment.vessel", 
            "equipment.heat_exchanger",
            "equipment.motor"
        ]),
        ("Low Confidence Detections", [
            f"{very_low_conf} detections below 0.3 confidence",
            f"{low_conf} detections between 0.3-0.5 confidence"
        ]),
        ("Poor Tag Reading", [
            f"Only {len(tagged)}/{len(detections)} detections have tags",
            "Many tags are garbled (e.g., 'Z00-WESSS', 'HEET-L0-T')",
            "Need better OCR preprocessing"
        ]),
        ("Missing Major Equipment", [
            "Storage tank not detected",
            "Vessel V-102 not detected",
            "Heat exchanger not detected",
            "Motor not detected"
        ])
    ]
    
    for issue_name, details in issues:
        print(f"\n  {issue_name}:")
        for detail in details:
            print(f"    • {detail}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 80)
    
    recommendations = [
        ("Immediate", [
            "Lower confidence threshold to 0.2-0.3",
            "Use larger image size (1280 instead of 640)",
            "Enable Test Time Augmentation (TTA)",
            "Add circle detection for instruments",
            "Implement better OCR preprocessing"
        ]),
        ("Short-term (1 week)", [
            "Collect and annotate 200+ more P&ID images",
            "Add missing equipment classes to training data",
            "Retrain model with data augmentation",
            "Implement PaddleOCR for better text recognition",
            "Add ISA tag validation"
        ]),
        ("Long-term (1 month)", [
            "Expand training dataset to 500-1000 images",
            "Implement SAHI for multi-scale detection",
            "Add hybrid detection (YOLO + traditional CV)",
            "Implement ensemble methods",
            "Set up continuous evaluation pipeline"
        ])
    ]
    
    for timeframe, items in recommendations:
        print(f"\n  {timeframe}:")
        for item in items:
            print(f"    • {item}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Run 'quick_fix_detection.py' for immediate improvements")
    print("  2. Read 'DETECTION_IMPROVEMENT_PLAN.md' for detailed guidance")
    print("  3. Start collecting more training data")
    print("=" * 80)

def is_valid_isa_tag(tag):
    """Check if tag looks like valid ISA format"""
    if not tag:
        return False
    
    import re
    
    patterns = [
        r'^[A-Z]{1,4}[-_]?\d{1,4}[A-Z]?$',
        r'^\d{2,3}[-_][A-Z0-9]+$',
    ]
    
    tag = tag.strip().upper()
    
    for pattern in patterns:
        if re.match(pattern, tag):
            return True
    
    return False

if __name__ == "__main__":
    analyze_detections()
