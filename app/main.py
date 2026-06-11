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
    file = BASE_DIR / "prompts" / f"{site}.txt"
    if file.exists():
        return file.read_text()
    return "You are a helpful website assistant."


def load_knowledge(site):
    folder = BASE_DIR / "knowledge" / site
    if not folder.exists():
        return ""

    text = ""
    for file in folder.glob("*.txt"):
        text += file.read_text() + "\n\n"

    return text


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

def clean_product_query(message):
    text = message.lower()

    remove_words = [
        "show", "me", "find", "search", "product", "products",
        "do", "you", "have", "any", "please"
    ]

    words = text.split()
    clean_words = [word for word in words if word not in remove_words]

    if clean_words:
        return " ".join(clean_words)

    return message


def search_electromart_products(message):
    query = clean_product_query(message)

    response = requests.get(
        "http://127.0.0.1:8000/ai/products/search/",
        params={"q": query},
        timeout=10,
    )

    if response.status_code != 200:
        return []

    return response.json().get("products", [])


def is_product_search(message):
    text = message.lower()

    keywords = [
        "show",
        "find",
        "search",
        "product",
        "phone",
        "laptop",
        "camera",
        "tablet",
        "computer",
        "mobile",
    ]

    return any(word in text for word in keywords)


def format_products(products):
    if not products:
        return "I could not find matching products."

    reply = "Here are matching products:\n\n"

    for product in products:
        reply += f"- {product['title']}\n"

        if product.get("category"):
            reply += f"  Category: {product['category']}\n"

        if product.get("shop"):
            reply += f"  Shop: {product['shop']}\n"

        if product.get("description"):
            reply += f"  {product['description']}\n"

        if product.get("url"):
            reply += f"  View: {product['url']}\n"

        reply += "\n"

    return reply


@app.post("/chat")
def chat(data: ChatRequest):
    # Real product search, no AI hallucination
    if data.site == "electromart" and is_product_search(data.message):
        products = search_electromart_products(data.message)

        if products:
            return {
                "type": "products",
                "reply": "Here are matching products:",
                "products": products,
            }

        return {
            "type": "text",
            "reply": "I could not find matching products.",
        }

    # Normal AI answer
    system_prompt = load_prompt(data.site)
    knowledge = load_knowledge(data.site)

    prompt = f"""
{system_prompt}

Website knowledge:
{knowledge}

User message:
{data.message}

Answer simply and shortly.
"""

    reply = ask_ollama(prompt)

    return {"reply": reply}