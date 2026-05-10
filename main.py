from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import httpx
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
print("=== API KEY ===", os.getenv("API_KEY_OPENROUTER"))

app = FastAPI(title="Coding Assistant")
templates = Jinja2Templates(directory="templates")

OPENROUTER_API_KEY = os.getenv("API_KEY_OPENROUTER")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct"

SYSTEM_PROMPT = """Anda adalah agen AI coding yang ahli (tingkat insinyur perangkat lunak senior).

Tujuan utama:
- Bantu pengguna membangun, memperbaiki, dan memahami kode dengan efisien dan benar.

Bahasa:
- Jawab dalam Bahasa Indonesia, kecuali istilah teknis atau kode.

Perilaku:
- Fokus pada solusi, bukan penjelasan panjang
- Berikan jawaban singkat dan langsung

Gaya coding:
- Tulis kode yang siap produksi
- Gunakan best practice modern

Aturan debugging:
- Identifikasi akar masalah
- Berikan perbaikan langsung

Gaya interaksi:
- Seperti pair programmer senior
- Langsung membantu"""

class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/chat")
async def chat(body: ChatMessage):
    # Bangun messages format OpenAI-compatible
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Tambah riwayat chat
    for msg in body.history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Tambah pesan user sekarang
    messages.append({"role": "user", "content": body.message})

    async def generate():
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Jack AI Assistant"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                }
            )
            data = response.json()
            print("=== API RESPONSE ===", data)

            if "choices" in data:
                text = data["choices"][0]["message"]["content"]
                for chunk in text.split(" "):
                    yield f"data: {json.dumps({'text': chunk + ' '})}\n\n"
            else:
                error = data.get("error", {}).get("message", "Unknown error")
                yield f"data: {json.dumps({'error': error})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)