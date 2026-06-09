from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    site: str

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
        },
    )
    return response.json()["response"]

@app.post("/chat")
def chat(data: ChatRequest):
    if data.site == "electromart":
        system = "You are ElectroMart AI assistant. Help users find products, shops, orders, and seller information.You only sell electronic items."
    elif data.site == "elitefreelancer":
        system = "You are Elite Freelancer AI assistant. Help users find services, freelancers, projects, and payments."
    else:
        system = "You are a helpful website assistant."

    prompt = f"""
{system}

User message:
{data.message}

Answer simply and shortly.
"""

    reply = ask_ollama(prompt)

    return {"reply": reply}
