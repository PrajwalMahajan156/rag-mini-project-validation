import time
import google.generativeai as genai
from app.core.config import Config

MODEL_ID = 'models/gemini-3-flash-preview'

if not Config.GOOGLE_API_KEY:
    print('No GOOGLE_API_KEY configured in environment (.env).')
    raise SystemExit(1)

genai.configure(api_key=Config.GOOGLE_API_KEY)

try:
    model = genai.GenerativeModel(MODEL_ID)
    print(f'Trying model: {MODEL_ID}')
    response = model.generate_content(f"Please reply in one short sentence: Is this model available and working?", stream=True)
    collected = ''
    for chunk in response:
        # chunk may have .text attribute
        text = getattr(chunk, 'text', None)
        if text:
            print(text, end='', flush=True)
            collected += text
    print('\n--- End of stream ---')
    # Try to show usage metadata if present
    try:
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            print('Usage metadata:', usage)
    except Exception:
        pass
except Exception as e:
    print('Error during generation:', e)
    raise
