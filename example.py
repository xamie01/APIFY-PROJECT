import os
from dotenv import load_dotenv
from google import genai

# load .env if present
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("GOOGLE_API_KEY not set in environment")

# create client (openai >=1.0)
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Write a poem about AI helping humans."
)

print(response.text)