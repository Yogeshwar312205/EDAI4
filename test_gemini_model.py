"""
Test Gemini API with different models
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...{api_key[-4:]}")
print()

try:
    import google.generativeai as genai
    print("✓ google-generativeai package installed")
except ImportError:
    print("❌ google-generativeai not installed")
    print("   Run: pip install google-generativeai")
    exit(1)

# Configure API
genai.configure(api_key=api_key)
print("✓ API configured")
print()

# Test different models
models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro", 
    "gemini-2.0-flash",
    "gemini-1.0-pro",
]

print("=" * 70)
print("TESTING MODELS")
print("=" * 70)

for model_name in models_to_test:
    print(f"\nTesting: {model_name}")
    print("-" * 70)
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello in 5 words")
        
        print(f"✅ SUCCESS!")
        print(f"   Response: {response.text}")
        
    except Exception as e:
        error_str = str(e)
        
        if "429" in error_str or "quota" in error_str.lower():
            print(f"❌ QUOTA ERROR - Model not available in free tier")
            print(f"   Error: {error_str[:100]}...")
        elif "404" in error_str or "not found" in error_str.lower():
            print(f"❌ MODEL NOT FOUND")
        else:
            print(f"❌ ERROR: {error_str[:100]}...")

print()
print("=" * 70)
print("RECOMMENDATION")
print("=" * 70)

# Try to find a working model
working_model = None
for model_name in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("test")
        working_model = model_name
        break
    except:
        continue

if working_model:
    print(f"\n✅ USE THIS MODEL: {working_model}")
    print(f"\nUpdate your code to use:")
    print(f"   model = genai.GenerativeModel('{working_model}')")
else:
    print("\n❌ NO WORKING MODEL FOUND")
    print("\nPossible issues:")
    print("1. API key is invalid")
    print("2. Gemini API not enabled for your project")
    print("3. All models require payment")
    print("\nVisit: https://makersuite.google.com/app/apikey")
