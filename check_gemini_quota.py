"""
Check Gemini API Quota Status
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ No API key found in .env file")
    exit(1)

print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"✓ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configure Gemini
genai.configure(api_key=api_key)

# Try a simple request
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Hello'")
    print("✅ API is working!")
    print(f"Response: {response.text}")
    print()
    print("Your quota has NOT been exceeded.")
    print("You can use Gemini features now.")
except Exception as e:
    error_msg = str(e)
    print("❌ API Error:")
    print(error_msg)
    print()
    
    if "429" in error_msg or "quota" in error_msg.lower():
        print("🚫 QUOTA EXCEEDED")
        print()
        print("Your daily quota has been used up.")
        print()
        print("Solutions:")
        print("1. Wait until midnight Pacific Time for reset")
        print("2. Use a different Google account API key")
        print("3. Upgrade to paid plan at https://ai.google.dev/pricing")
        print()
        
        # Try to extract retry time
        if "retry in" in error_msg.lower():
            import re
            match = re.search(r'retry in (\d+)', error_msg)
            if match:
                seconds = int(match.group(1))
                minutes = seconds // 60
                print(f"⏰ Retry in: {minutes} minutes {seconds % 60} seconds")
    else:
        print("Unknown error. Check your API key and internet connection.")
