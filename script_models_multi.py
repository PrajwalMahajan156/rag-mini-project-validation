import google.generativeai as genai
from app.core.config import Config

PREFERRED = ["gemini-3-flash-preview", "gemini-1.5-flash", "gemini-1.5-pro"]

if not Config.GOOGLE_API_KEY:
    print('No GOOGLE_API_KEY configured. Aborting.')
    raise SystemExit(1)

genai.configure(api_key=Config.GOOGLE_API_KEY)

results = {}

for pid in PREFERRED:
    tried = []
    success = False
    message = ''
    for candidate in [f"models/{pid}", pid]:
        if candidate in tried:
            continue
        tried.append(candidate)
        try:
            model = genai.GenerativeModel(candidate)
            print(f"Testing {candidate}...", end=' ')
            response = model.generate_content("Please respond with 'ok' in one short word.", stream=True)
            collected = ''
            for chunk in response:
                text = getattr(chunk, 'text', None)
                if text:
                    collected += text
            print('SUCCESS')
            results[pid] = {"tested": tried.copy(), "working_id": candidate, "sample": collected}
            success = True
            break
        except Exception as e:
            print(f'FAIL ({candidate}): {e}')
            message = str(e)
    if not success:
        results[pid] = {"tested": tried.copy(), "working_id": None, "error": message}

print('\nSummary:')
for k, v in results.items():
    if v.get('working_id'):
        print(f"- {k}: WORKING as {v['working_id']}")
    else:
        print(f"- {k}: NOT WORKING (tested: {v['tested']})")
