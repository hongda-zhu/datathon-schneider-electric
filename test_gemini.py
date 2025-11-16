from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

gemini_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key loaded: {gemini_key[:20]}..." if gemini_key else "NO KEY")

genai.configure(api_key=gemini_key)

# Test which models are available
print("\nAvailable models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"  - {m.name}")

# Try gemini-pro
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say hello in JSON format with key 'message'")
    print("\n✅ Gemini-pro works!")
    print(response.text)
except Exception as e:
    print(f"\n❌ Error: {e}")
