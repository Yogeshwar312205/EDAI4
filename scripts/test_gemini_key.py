#!/usr/bin/env python3
"""
Test Gemini API key
"""
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("="*60)
print("Gemini API Key Test")
print("="*60)

# Check if key exists
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ No API key found in environment")
    print("\nChecked variables:")
    print("  - GOOGLE_API_KEY")
    print("  - GEMINI_API_KEY")
    print("\nPlease add to .env file:")
    print("  GOOGLE_API_KEY=your_key_here")
    exit(1)

print(f"✅ API key found: {api_key[:10]}...{api_key[-5:]}")
print(f"   Length: {len(api_key)} characters")
print()

# Check key format
if api_key.startswith("AIza"):
    print("✅ Key format looks correct (starts with 'AIza')")
elif api_key.startswith("AQ."):
    print("⚠️  WARNING: This looks like a different Google API key")
    print("   Gemini API keys typically start with 'AIza'")
    print()
    print("   This might be:")
    print("   - A Google Cloud API key (not for Gemini)")
    print("   - An OAuth token")
    print("   - A different service key")
    print()
    print("   To get a Gemini API key:")
    print("   1. Go to: https://makersuite.google.com/app/apikey")
    print("   2. Click 'Create API Key'")
    print("   3. Copy the key (should start with 'AIza')")
else:
    print(f"⚠️  Unusual key format (starts with '{api_key[:4]}')")
    print("   Gemini API keys typically start with 'AIza'")

print()
print("="*60)
print("Testing API Connection")
print("="*60)

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("Sending test request...")
    response = model.generate_content("Say 'Hello, I am working!' in exactly 5 words.")
    
    print("✅ SUCCESS! Gemini API is working!")
    print(f"\nResponse: {response.text}")
    print()
    print("Your API key is valid and working! 🎉")
    
except ImportError:
    print("❌ google-generativeai package not installed")
    print("\nInstall with:")
    print("  pip install google-generativeai")
    
except Exception as e:
    print(f"❌ API Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Invalid API key")
    print("  2. API key not activated")
    print("  3. Network connection issue")
    print("  4. Rate limit exceeded")
    print()
    print("Solutions:")
    print("  1. Get new key: https://makersuite.google.com/app/apikey")
    print("  2. Check key starts with 'AIza'")
    print("  3. Verify internet connection")
    print("  4. Wait a minute and try again")

print("="*60)
