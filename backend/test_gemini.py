from google import genai
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print('Key:', key[:15])
client = genai.Client(api_key=key)
r = client.models.generate_content(model='gemini-2.0-flash', contents='Say hello')
print('Response:', r.text)
