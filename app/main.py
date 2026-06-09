from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent


class ChatRequest(BaseModel):
    message: str
    site: str


def load_prompt(site):
    prompt_file = BASE_DIR / "prompts" / f"{site}.txt"

    if prompt_file.exists():
        return prompt_file.read_text()

    return "You are a helpful website assistant. Answer simply and shortly."


def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["response"]


@app.post("/chat")
def chat(data: ChatRequest):
    system_prompt = load_prompt(data.site)

    prompt = f"""
{system_prompt}

User message:
{data.message}
"""

    reply = ask_ollama(prompt)

    return {"reply": reply}