#!/usr/bin/env python3
"""
List available Gemini models
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ No API key found in .env")
        exit(1)
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    genai.configure(api_key=api_key)
    
    print("📋 Available Gemini Models:")
    print("=" * 70)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"\n✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Supported: {', '.join(model.supported_generation_methods)}")
    
    print("\n" + "=" * 70)
    print("\n💡 Use one of these model names in your code!")
    
except ImportError:
    print("❌ google-generativeai not installed")
    print("   Run: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {e}")
