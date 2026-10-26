# GitHub Repository — About and release metadata

Everything on this page is **already applied** to
<https://github.com/rhasan2026g-cell/GroqChatbot> except the social preview,
which GitHub only exposes in the web UI.

## About panel

**Description** (currently live):

```
Bilingual (English/বাংলা) AI agent for Windows and Android. Groq LPU streaming, long-term SQLite memory, document Q&A, ten tools, and an image/music/video studio. Built with PySide6 + Capacitor.
```

**Website:** `https://github.com/rhasan2026g-cell/GroqChatbot`

**Topics** (20 — GitHub's maximum, currently live):

```
ai-agent
groq
chatbot
bilingual
bengali
pyside6
desktop-app
android
capacitor
python
llm
rag
long-term-memory
sqlite-vec
tool-calling
image-generation
music-generation
local-first
privacy
streaming
```

The README body also carries phrasing that is not a topic but helps search
engines and GitHub code search: “retrieval-augmented generation”, “function
calling”, “vector search”, “semantic memory”, the model names (FLUX, GPT-OSS,
Qwen, MusicGen, Hunyuan) and বাংলা.

## Social preview

GitHub has no API for this one — set it manually:

**Settings → General → Social preview → Edit →** upload `docs/social-preview.png`
(2000×1000, already in the repository).

## Current release

| Field | Value |
| --- | --- |
| Tag | `v1.1.0` |
| Title | GroqChatbot 1.1.0 — dashboard, database browser, tool bench, new Android UI |
| URL | <https://github.com/rhasan2026g-cell/GroqChatbot/releases/tag/v1.1.0> |
| Marked as | Latest |
| Body | `RELEASE_NOTES_v1.1.0.md` |

**Release assets** (exactly these two are attached):

| File | Size | SHA-256 |
| --- | --- | --- |
| `GroqChatbot-v1.1.exe` | 90,660,151 bytes (86.5 MB) | `68ab398e3560dbeb9a08b59c9968b39df1f515bab4baabecf470c12126ad44f0` |
| `GroqChatbot-v1.1.apk` | 3,684,960 bytes (3.5 MB) | `a265e2790e9e5b1ce81bc2dd72d52af85d7d466b30ac107d9619d9b7f9e4e4f0` |

`docs/banner.png` and `docs/social-preview.png` live in the repository (README and
repository settings), not as release assets.

## Updating the About panel by API

With a token that has `admin:repo` (or `public_repo`) scope:

```powershell
$headers = @{ Authorization = "Bearer $env:GITHUB_TOKEN"; "User-Agent" = "GroqChatbot" }

Invoke-RestMethod -Method Patch -Uri "https://api.github.com/repos/rhasan2026g-cell/GroqChatbot" `
  -Headers $headers -ContentType "application/json" `
  -Body (@{ description = "Bilingual (English/বাংলা) AI agent for Windows and Android." } | ConvertTo-Json)

Invoke-RestMethod -Method Put -Uri "https://api.github.com/repos/rhasan2026g-cell/GroqChatbot/topics" `
  -Headers $headers -ContentType "application/json" `
  -Body (@{ names = @("ai-agent","groq","chatbot") } | ConvertTo-Json)
```

`names` must always be the **full** list you want — the endpoint replaces topics,
it does not merge them. Keep it at 20 or fewer.
