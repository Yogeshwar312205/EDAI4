#!/usr/bin/env python3
"""
Setup script for Gemini AI integration
"""
import os
from pathlib import Path

def setup_gemini():
    """Setup Gemini API key in .env file"""
    
    print("="*60)
    print("Gemini AI Setup")
    print("="*60)
    print()
    print("This script will help you configure the Gemini API for")
    print("the Smart OCR Tag Explainer feature.")
    print()
    print("Steps:")
    print("1. Get API key from: https://makersuite.google.com/app/apikey")
    print("2. Enter your API key below")
    print("3. Script will add it to your .env file")
    print()
    
    # Check if .env exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env from .env.example...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ Created .env file")
        print()
    
    # Get API key
    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print()
        print("⚠️  No API key provided.")
        print("   The system will work in simulated mode with basic ISA definitions.")
        print()
        print("To add API key later:")
        print("1. Edit .env file")
        print("2. Add line: GEMINI_API_KEY=your_key_here")
        print("3. Restart backend")
        return
    
    # Update .env file
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Check if GEMINI_API_KEY already exists
        found = False
        for i, line in enumerate(lines):
            if line.startswith('GEMINI_API_KEY='):
                lines[i] = f'GEMINI_API_KEY={api_key}\n'
                found = True
                break
        
        if not found:
            lines.append(f'\n# Gemini AI Configuration\nGEMINI_API_KEY={api_key}\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
    else:
        with open(env_file, 'w') as f:
            f.write(f'# Gemini AI Configuration\nGEMINI_API_KEY={api_key}\n')
    
    print()
    print("✅ API key saved to .env file")
    print()
    print("="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Install dependencies:")
    print("   pip install google-generativeai")
    print()
    print("2. Restart backend:")
    print("   python -m uvicorn src.api.main:app --reload")
    print()
    print("3. Test the feature:")
    print("   - Process a P&ID image")
    print("   - Click on an instrument node")
    print("   - See AI-powered definition appear!")
    print()
    print("For more info, see: SMART_OCR_TAG_EXPLAINER.md")
    print("="*60)

if __name__ == "__main__":
    try:
        setup_gemini()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
