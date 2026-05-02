"""
Test with NEW google.genai package (not deprecated google.generativeai)
"""
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print(f"✓ API Key: {api_key[:20]}...{api_key[-4:]}")
print()

# Try NEW package first
print("=" * 70)
print("TESTING NEW PACKAGE: google.genai")
print("=" * 70)

try:
    from google import genai
    from google.genai import types
    print("✓ NEW google.genai package installed")
    
    # Configure client
    client = genai.Client(api_key=api_key)
    print("✓ Client configured")
    print()
    
    # Test models
    models_to_test = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
    ]
    
    for model_name in models_to_test:
        print(f"\nTesting: {model_name}")
        print("-" * 70)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello in 5 words"
            )
            print(f"✅ SUCCESS!")
            print(f"   Response: {response.text}")
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(f"❌ QUOTA ERROR")
            elif "404" in error_str or "not found" in error_str.lower():
                print(f"❌ MODEL NOT FOUND")
            else:
                print(f"❌ ERROR: {error_str[:150]}")
    
except ImportError:
    print("❌ NEW google.genai package NOT installed")
    print("\nInstall it with:")
    print("   pip install google-genai")
    print()

# Try OLD package
print()
print("=" * 70)
print("TESTING OLD PACKAGE: google.generativeai (DEPRECATED)")
print("=" * 70)

try:
    import google.generativeai as genai_old
    print("⚠️  OLD google.generativeai package installed (deprecated)")
    
    genai_old.configure(api_key=api_key)
    print("✓ Configured")
    print()
    
    # List available models
    print("Available models:")
    try:
        for m in genai_old.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
    except Exception as e:
        print(f"  Error listing models: {e}")
    
except ImportError:
    print("✓ OLD package not installed (good!)")

print()
print("=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print()
print("You need to:")
print("1. Install NEW package: pip install google-genai")
print("2. Uninstall OLD package: pip uninstall google-generativeai")
print("3. Update code to use new API")
