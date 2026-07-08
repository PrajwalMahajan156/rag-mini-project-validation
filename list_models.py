import google.generativeai as genai
from app.core.config import Config

genai.configure(api_key=Config.GOOGLE_API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
