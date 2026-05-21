# ⚡ Jackode — AI Coding Assistant

Aplikasi web **coding assistant** berbasis **Gemma 4** via Google AI Studio API, dibangun dengan **FastAPI + Python**. Mendukung streaming response, syntax highlighting, dan berbagai quick actions untuk membantu produktivitas coding kamu.

---

## 📋 Daftar Isi

- [Prasyarat](#-prasyarat)
- [Struktur Project](#-struktur-project)
- [Langkah 1 — Dapatkan API Key](#langkah-1--dapatkan-api-key)
- [Langkah 2 — Setup Project](#langkah-2--setup-project)
- [Langkah 3 — Konfigurasi](#langkah-3--konfigurasi)
- [Langkah 4 — Jalankan Aplikasi](#langkah-4--jalankan-aplikasi)
- [Fitur Aplikasi](#-fitur-aplikasi)
- [Troubleshooting](#-troubleshooting)
- [Model yang Tersedia](#-model-yang-tersedia)

---

## ✅ Prasyarat

Pastikan sudah terinstall:

- **Python 3.10+** → [python.org/downloads](https://python.org/downloads)
- **pip** (biasanya sudah include bersama Python)
- **Browser** (Chrome, Firefox, Edge, dll)
- **Koneksi internet** (untuk akses Google AI Studio API)

Cek versi Python:
```bash
python --version
# Output: Python 3.10.x atau lebih baru
```

---

## 📁 Struktur Project

```
coding-assistant/
├── main.py               # Backend FastAPI (server & API handler)
├── requirements.txt      # Daftar Python dependencies
├── .env.example          # Contoh konfigurasi environment
├── README.md             # Dokumentasi ini
└── templates/
    └── index.html        # Frontend UI (chat interface)
```

---

## Langkah 1 — Dapatkan API Key

1. Buka **[aistudio.google.com](https://aistudio.google.com)** dan login dengan akun Google
2. Di sidebar kiri, klik **"Get API key"**
3. Klik **"Create API key"**
4. Pilih project Google Cloud (atau buat baru)
5. **Salin API key** yang dihasilkan — simpan di tempat aman

> ⚠️ **Jangan share API key kamu ke siapapun atau upload ke GitHub!**

---

## Langkah 2 — Setup Project

### Ekstrak Project
```bash
# Ekstrak file zip yang didownload
# Lalu masuk ke folder project
cd coding-assistant
```

### Buat Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Jika berhasil, prompt akan berubah menjadi:
```
(venv) C:\...\coding-assistant>
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

Output yang diharapkan:
```
Successfully installed fastapi uvicorn httpx jinja2 pydantic ...
```

---

## Langkah 3 — Konfigurasi

Buka file `main.py` dengan text editor (Notepad, VS Code, dll), lalu ubah baris berikut:

```python
# Baris 13 — ganti YOUR_API_KEY_HERE dengan API key kamu
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")

# Baris 14 — pastikan nama model sudah benar
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent"
```

**Alternatif** — set via environment variable (lebih aman):

```bash
# Windows (Command Prompt)
set GEMINI_API_KEY=api_key_kamu_disini

# Windows (PowerShell)
$env:GEMINI_API_KEY="api_key_kamu_disini"

# Linux / macOS
export GEMINI_API_KEY=api_key_kamu_disini
```

---

## Langkah 4 — Jalankan Aplikasi

### Cara 1 — via Python langsung
```bash
python main.py
```

### Cara 2 — via Uvicorn (recommended, support reload otomatis)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Output yang diharapkan:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Buka di Browser

Akses aplikasi di: **[http://localhost:8000](http://localhost:8000)**

### Menghentikan Server
```bash
Ctrl + C
```

---

## ✨ Fitur Aplikasi

| Fitur | Keterangan |
|---|---|
| 💬 Chat AI | Tanya jawab seputar coding dengan Gemma 4 |
| ⚡ Streaming Response | Jawaban muncul bertahap seperti ChatGPT |
| 🎨 Syntax Highlighting | Kode otomatis diwarnai sesuai bahasa |
| 📋 Copy Code | Tombol copy di setiap blok kode |
| 🚀 Quick Actions | Shortcut untuk debug, review, explain, dll |
| 💡 Suggestion Chips | Contoh pertanyaan untuk memulai chat |
| 🧠 Riwayat Percakapan | Model mengingat konteks 10 turn terakhir |
| 🔄 New Chat | Reset percakapan kapan saja |

### Quick Actions yang Tersedia
- 🔍 **Explain Code** — Jelaskan cara kerja suatu kode
- 🐛 **Debug Error** — Bantu cari dan perbaiki bug
- ✨ **Code Review** — Review dan saran perbaikan kode
- 📝 **Write Function** — Buat fungsi sesuai kebutuhan
- 🔄 **Convert Code** — Konversi kode ke bahasa lain
- 🧪 **Write Tests** — Buatkan unit test otomatis
- ⚡ **Optimize** — Optimasi performa kode

---

## 🔧 Troubleshooting

### ❌ Error: Model not found
```
models/gemma-3-27b-it is not found for API version v1beta
```
**Solusi:** Pastikan nama model di `main.py` sudah benar:
```python
GEMINI_API_URL = "...models/gemma-4-26b-a4b-it:generateContent"
```

---

### ❌ Error: API Key Invalid
```
API key not valid. Please pass a valid API key.
```
**Solusi:** Cek ulang API key di `main.py` atau environment variable, pastikan tidak ada spasi atau karakter berlebih.

---

### ❌ Error: Connection refused saat buka browser
```
This site can't be reached — localhost refused to connect
```
**Solusi:** Pastikan server sudah berjalan. Jalankan ulang:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### ❌ Warning: reload requires import string
```
WARNING: You must pass the application as an import string to enable 'reload'
```
**Solusi:** Gunakan perintah uvicorn di atas (bukan `python main.py`) atau ubah `main.py`:
```python
# Ubah baris terakhir dari:
uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
# Menjadi:
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

---

### ❌ `python` tidak dikenali di Windows
**Solusi:** Saat install Python, pastikan centang **"Add python.exe to PATH"**. Atau coba gunakan perintah `py` sebagai pengganti `python`.

---

### ❌ PowerShell tidak bisa aktifkan venv
```
cannot be loaded because running scripts is disabled
```
**Solusi:** Jalankan PowerShell sebagai Administrator, lalu:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🤖 Model yang Tersedia

| Model API Name | Ukuran | Keterangan |
|---|---|---|
| `gemma-4-26b-a4b-it` | 26B MoE | ✅ Lebih cepat, efisien, **recommended** |
| `gemma-4-31b-it` | 31B Dense | 🏆 Paling canggih, sedikit lebih lambat |

Untuk mengganti model, ubah variabel `GEMINI_API_URL` di `main.py`.

---

## 🔐 Tips Keamanan

- Jangan hardcode API key langsung di kode jika ingin upload ke GitHub
- Tambahkan `.env` ke file `.gitignore`
- Gunakan environment variable untuk menyimpan API key
- Batasi penggunaan API key di Google AI Studio jika perlu

---

## 📚 Referensi

- [Google AI Studio](https://aistudio.google.com) — Dapatkan API key & coba model
- [Gemma 4 Documentation](https://ai.google.dev/gemma/docs/core) — Dokumentasi resmi Gemma 4
- [FastAPI Documentation](https://fastapi.tiangolo.com) — Dokumentasi FastAPI
- [Gemini API Reference](https://ai.google.dev/api) — Referensi lengkap Gemini API

---

<div align="center">
  Dibuat dengan ⚡ menggunakan FastAPI + Gemma 4
</div>
