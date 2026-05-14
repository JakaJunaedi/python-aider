from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import init_db, get_db, AsyncSessionLocal, Session, Message
import httpx
import json
import os
import uuid
import base64
import PyPDF2
import io

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Coding Assistant")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

OPENROUTER_API_KEY = os.getenv("API_KEY_OPENROUTER")
OPENROUTER_API_URL = os.getenv("API_URL_OPENROUTER", "https://openrouter.ai/api/v1/chat/completions")
MODEL = "meta-llama/llama-3.3-70b-instruct"

# Extensions yang didukung
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
TEXT_EXTS    = {".py", ".js", ".ts", ".html", ".css", ".md", ".txt",
                ".json", ".yaml", ".yml", ".xml", ".sh", ".bash",
                ".sql", ".php", ".go", ".rs", ".java", ".cpp", ".c",
                ".cs", ".rb", ".swift", ".kt", ".vue", ".jsx", ".tsx",
                ".env", ".toml", ".ini", ".dockerfile", ".gitignore"}
PDF_EXTS     = {".pdf"}
MAX_FILE_MB  = 10

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

@app.on_event("startup")
async def startup():
    await init_db()

class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/session/new")
async def new_session(db: AsyncSession = Depends(get_db)):
    session = Session(id=str(uuid.uuid4()), title="New Chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"session_id": session.id, "title": session.title}

@app.get("/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.updated_at.desc()))
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "updated_at": str(s.updated_at)} for s in sessions]

@app.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]

@app.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(Message.__table__.delete().where(Message.session_id == session_id))
    await db.execute(Session.__table__.delete().where(Session.id == session_id))
    await db.commit()
    return {"status": "deleted"}

# ── UPLOAD FILE ──────────────────────────────────────
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    content = await file.read()

    # Cek ukuran file
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        return {"error": f"File terlalu besar. Maksimal {MAX_FILE_MB}MB."}

    # Gambar → base64
    if ext in IMAGE_EXTS:
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext[1:]}"
        b64  = base64.b64encode(content).decode()
        return {
            "type": "image",
            "filename": file.filename,
            "mime": mime,
            "data": b64,
            "preview": f"data:{mime};base64,{b64}"
        }

    # PDF → extract teks
    if ext in PDF_EXTS:
        try:
            reader   = PyPDF2.PdfReader(io.BytesIO(content))
            text     = "\n".join(page.extract_text() or "" for page in reader.pages)
            preview  = text[:500] + ("..." if len(text) > 500 else "")
            return {
                "type": "pdf",
                "filename": file.filename,
                "content": text,
                "preview": preview,
                "pages": len(reader.pages)
            }
        except Exception as e:
            return {"error": f"Gagal membaca PDF: {str(e)}"}

    # File teks / kode
    if ext in TEXT_EXTS or ext == "":
        try:
            text    = content.decode("utf-8", errors="replace")
            preview = text[:300] + ("..." if len(text) > 300 else "")
            return {
                "type": "text",
                "filename": file.filename,
                "ext": ext,
                "content": text,
                "preview": preview,
                "lines": len(text.splitlines())
            }
        except Exception as e:
            return {"error": f"Gagal membaca file: {str(e)}"}

    return {"error": f"Format file '{ext}' tidak didukung."}

# ── CHAT ─────────────────────────────────────────────
@app.post("/chat")
async def chat(body: ChatMessage, db: AsyncSession = Depends(get_db)):
    session_id = body.session_id

    if not session_id:
        session = Session(id=str(uuid.uuid4()), title="New Chat")
        db.add(session)
        await db.commit()
        session_id = session.id

    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    history = result.scalars().all()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    user_msg = Message(session_id=session_id, role="user", content=body.message)
    db.add(user_msg)

    if not history:
        # Buat judul dari pesan pertama (strip tag file jika ada)
        clean = body.message.split("\n")[0].replace("[FILE:", "").strip()
        title = clean[:40] + ("..." if len(clean) > 40 else "")
        await db.execute(update(Session).where(Session.id == session_id).values(title=title))

    await db.commit()

    async def generate():
        full_response = ""
        try:
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

                if "choices" in data:
                    full_response = data["choices"][0]["message"]["content"]
                    for chunk in full_response.split(" "):
                        yield f"data: {json.dumps({'text': chunk + ' ', 'session_id': session_id})}\n\n"
                else:
                    error = data.get("error", {}).get("message", "Unknown error")
                    yield f"data: {json.dumps({'error': error})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        if full_response:
            async with AsyncSessionLocal() as save_db:
                ai_msg = Message(session_id=session_id, role="assistant", content=full_response)
                save_db.add(ai_msg)
                await save_db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)