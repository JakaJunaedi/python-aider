"""
Jackode Engineer — AI Testing Agent Dashboard
FastAPI backend + Jinja2 templates + Chat API
"""

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import httpx
import json
import uuid
import os

load_dotenv()

OPENROUTER_KEY = os.getenv("API_KEY_OPENROUTER", "")
OPENROUTER_URL = os.getenv("API_URL_OPENROUTER", "https://openrouter.ai/api/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-2.5-flash-lite")

# In-memory store
sessions_store: dict = {}
messages_store: dict = {}

def _ensure_session(sid: str) -> str:
    if not sid or sid not in sessions_store:
        sid = str(uuid.uuid4())
        sessions_store[sid] = {"id": sid, "title": "New Chat", "created_at": ""}
        messages_store[sid] = []
    return sid

@asynccontextmanager
async def lifespan(app: FastAPI):
    sid = str(uuid.uuid4())
    sessions_store[sid] = {"id": sid, "title": "New Chat", "created_at": ""}
    messages_store[sid] = []
    yield

app = FastAPI(title="Jackode Engineer", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

MOCK_STEPS = [
    {"id": 1,  "text": "Initialize test environment",           "status": "current"},
    {"id": 2,  "text": "Load project configuration",             "status": "pending"},
    {"id": 3,  "text": "Connect to target database",             "status": "pending"},
    {"id": 4,  "text": "Run unit test suite (187 cases)",        "status": "pending"},
    {"id": 5,  "text": "Execute integration tests",              "status": "pending"},
    {"id": 6,  "text": "Run end-to-end scenarios",               "status": "pending"},
    {"id": 7,  "text": "Validate API contract (OpenAPI spec)",   "status": "pending"},
    {"id": 8,  "text": "Performance benchmark (100 rps target)", "status": "pending"},
    {"id": 9,  "text": "Security scan (OWASP top 10)",           "status": "pending"},
    {"id": 10, "text": "Generate test report & coverage summary","status": "pending"},
]

MOCK_STATS = {
    "total_tests": 187, "passed": 152, "failed": 12, "skipped": 23,
    "coverage_pct": 78.4, "duration_sec": 34.2, "agent_status": "idle",
    "last_run": "2026-05-21 08:42:17",
}

# ── Pages ────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "steps": MOCK_STEPS, "stats": MOCK_STATS,
    })

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ── Chat API ─────────────────────────────────────────────
@app.get("/sessions")
async def list_sessions():
    return JSONResponse(list(sessions_store.values()))

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    return JSONResponse(messages_store.get(session_id, []))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    sessions_store.pop(session_id, None)
    messages_store.pop(session_id, None)
    return JSONResponse({"ok": True})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            import base64
            b64 = base64.b64encode(content).decode()
            mime = file.content_type or "image/png"
            return JSONResponse({"type": "image", "filename": filename, "preview": f"data:{mime};base64,{b64}", "mime": mime, "data": b64})
        elif ext == ".pdf":
            try:
                from PyPDF2 import PdfReader; from io import BytesIO
                reader = PdfReader(BytesIO(content))
                text = "\n".join((p.extract_text() or "") for p in reader.pages)
                return JSONResponse({"type": "pdf", "filename": filename, "content": text, "preview": text[:200].replace("\n", " "), "pages": len(reader.pages)})
            except Exception:
                return JSONResponse({"type": "text", "filename": filename, "content": "[PDF extraction failed]", "preview": filename, "ext": ".pdf"})
        else:
            try:
                text = content.decode("utf-8", errors="replace")
            except Exception:
                text = "[Binary file]"
            return JSONResponse({"type": "text", "filename": filename, "content": text, "preview": text[:200].replace("\n", " "), "ext": ext})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/chat")
async def chat_stream(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    session_id = _ensure_session(body.get("session_id", ""))

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    messages_store.setdefault(session_id, []).append({"role": "user", "content": user_message})
    if sessions_store.get(session_id, {}).get("title") == "New Chat":
        sessions_store[session_id]["title"] = user_message[:50].replace("\n", " ")

    history = messages_store.get(session_id, [])
    payload = [{"role": "system", "content": "You are Jackode Engineer, an AI testing agent assistant. Help with code, testing, debugging, and software engineering."}]
    payload += [{"role": m["role"], "content": m["content"]} for m in history]

    async def event_stream():
        full = ""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", OPENROUTER_URL, json={
                    "model": MODEL_NAME, "messages": payload, "stream": True, "temperature": 0.7, "max_tokens": 2048
                }, headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}) as resp:
                    # ── Periksa HTTP status dari OpenRouter ──
                    if resp.status_code != 200:
                        try:
                            body = await resp.aread()
                            err_raw = body.decode("utf-8", errors="replace")
                            try:
                                err_json = json.loads(err_raw)
                                err_msg = err_json.get("error", {}).get("message", "") or str(err_json)
                            except json.JSONDecodeError:
                                err_msg = err_raw
                        except Exception:
                            err_msg = f"HTTP {resp.status_code}"
                        yield f"data: {json.dumps({'error': f'API Error ({resp.status_code}): {err_msg}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "): continue
                        ds = line[6:]
                        if ds == "[DONE]": break
                        try:
                            ch = json.loads(ds)
                            c = ch.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if c: full += c; yield f"data: {json.dumps({'text': c, 'session_id': session_id})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError): pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        if full:
            messages_store.setdefault(session_id, []).append({"role": "assistant", "content": full})
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"X-Session-Id": session_id})

# ── Entrypoint ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
