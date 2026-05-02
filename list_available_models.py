"""
List ALL models available for your API key
"""
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print(f"✓ API Key: {api_key[:20]}...{api_key[-4:]}")
print()

print("=" * 70)
print("LISTING ALL AVAILABLE MODELS")
print("=" * 70)
print()

# Try with NEW package
try:
    from google import genai
    
    client = genai.Client(api_key=api_key)
    print("✓ Using NEW google.genai package")
    print()
    
    try:
        # List all models
        models = client.models.list()
        
        print("Available models for your API key:")
        print("-" * 70)
        
        count = 0
        for model in models:
            print(f"  {count+1}. {model.name}")
            count += 1
        
        if count == 0:
            print("  ❌ NO MODELS AVAILABLE!")
            print()
            print("This means:")
            print("  1. Gemini API is not enabled for your project")
            print("  2. Your API key doesn't have access")
            print("  3. You need to enable the API")
            print()
            print("Visit: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
        else:
            print()
            print(f"✅ Found {count} models!")
            print()
            print("Now testing the first available model...")
            print("-" * 70)
            
            # Test first model
            first_model = list(client.models.list())[0]
            print(f"\nTesting: {first_model.name}")
            
            try:
                response = client.models.generate_content(
                    model=first_model.name,
                    contents="Say hello in 5 words"
                )
                print(f"✅ SUCCESS!")
                print(f"   Response: {response.text}")
                print()
                print(f"✅ USE THIS MODEL: {first_model.name}")
            except Exception as e:
                print(f"❌ Error: {str(e)[:200]}")
    
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print()
        print("Possible issues:")
        print("1. API key is invalid")
        print("2. Gemini API not enabled")
        print("3. Network/firewall issue")
        print()
        print("Try:")
        print("1. Create NEW API key: https://makersuite.google.com/app/apikey")
        print("2. Enable Gemini API: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")

except ImportError:
    print("❌ google.genai package not installed")
    print("   Run: pip install google-genai")

print()
print("=" * 70)
print("ALTERNATIVE: Try AI Studio")
print("=" * 70)
print()
print("If no models are available, try:")
print("1. Go to: https://aistudio.google.com/")
print("2. Sign in with your Google account")
print("3. Click 'Get API Key'")
print("4. Create API key in NEW project")
print("5. Use that key in your .env file")
