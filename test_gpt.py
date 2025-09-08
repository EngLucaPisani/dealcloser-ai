from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os

# carica .env con percorso ASSOLUTO
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=False)

print("Key set:", bool(os.getenv("OPENAI_API_KEY")))

client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Ping from DealCloser (2 lines)."}],
    max_tokens=40,
    temperature=0.2,
)
print(resp.choices[0].message.content)
