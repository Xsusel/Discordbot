import os
import google.generativeai as genai
from dotenv import load_dotenv
import traceback

print("--- Starting Gemini Model Check ---")

# 1. Load environment variables from bot.env
try:
    load_dotenv('bot.env')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("ERROR: GEMINI_API_KEY not found or is set to the default placeholder in bot.env")
        exit()
    print("Successfully loaded GEMINI_API_KEY.")
except Exception as e:
    print(f"ERROR: Failed to load .env file or read API key: {e}")
    traceback.print_exc()
    exit()

# 2. Configure the Gemini client
try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Successfully configured Gemini API.")
except Exception as e:
    print(f"ERROR: Failed during genai.configure(): {e}")
    traceback.print_exc()
    exit()

# 3. List available models
try:
    print("\nAttempting to list available models...")
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

    if not models:
        print("\n--- RESULT ---")
        print("Could not find any models that support 'generateContent'.")
        print("This is highly unusual and suggests an issue with your Google Cloud project's permissions or configuration.")
        print("Please check the following in your Google Cloud Console:")
        print("1. Ensure the 'Generative Language API' or 'Vertex AI API' is enabled.")
        print("2. Make sure your API key is valid and has not been restricted.")
    else:
        print("\n--- AVAILABLE MODELS ---")
        for model in models:
            print(f"- {model.name}")
        print("\n--- END OF SCRIPT ---")

except Exception as e:
    print(f"\nERROR: An exception occurred while trying to list models: {e}")
    print("\n--- TRACEBACK ---")
    traceback.print_exc()
    print("\n--- END OF SCRIPT ---")
    print("\nThis error usually indicates a problem with API key authentication or project configuration.")