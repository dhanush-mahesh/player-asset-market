"""
Test Gemini API connection
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key found: {api_key[:20]}..." if api_key else "No API key found")

try:
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    # List available models
    print("\nAvailable models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    # Try to create and use model
    print("\nTesting gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    response = model.generate_content("Say hello in one sentence")
    print(f"Response: {response.text}")
    print("\n✅ Success!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
