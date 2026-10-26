# GroqChatbot 1.1.0

A full interface release. The desktop app gains a live dashboard, real system
dialogs, a database browser, a tool bench and a creation studio. The Android app
is redesigned to match, and both platforms ship as fresh signed builds.

## Download

| Platform | File | Notes |
|---|---|---|
| Windows 10/11 | **GroqChatbot-v1.1.exe** | One file, no Python needed. Unsigned — SmartScreen → *More info → Run anyway*. |
| Android 5.1+ | **GroqChatbot-v1.1.apk** | 3.5 MB, signed. Allow "install unknown apps" when prompted. |

Neither build contains an API key. On first launch a guided dialog walks you
through creating a free [Groq key](https://console.groq.com/keys) and tests it
before saving. The desktop app writes it to `.env`; Android keeps it in the app's
private storage.

## Highlights

### Desktop

- **Dashboard sidebar** — messages, facts, documents and tokens in four cards; a
  7-day activity chart; six quick actions; live badges for memory mode, search
  mode, provider count and the data folder.
- **Settings & system** — five tabs covering model, language, theme, accent
  colour, compact spacing, temperature, token budget, retained turns, custom
  system prompt, keys, memory and RAG diagnostics, studio and about.
- **Database browser** (`Ctrl+D`) — inspect conversations, facts, the vector
  index, documents and RAG chunks; filter, refresh, export JSON, open the folder,
  delete rows.
- **Tool workbench** — every tool with its JSON schema, a runnable editor, live
  results and explicit permissions for file writes, Python and network access.
- **Creation studio** — image, illustration, music and video with model choice,
  negative prompt, size/duration controls, a "Surprise me" prompt and a recent
  outputs gallery.
- **Chat polish** — regenerate, Markdown export, per-message copy, keyboard
  shortcuts, Unicode maths and token accounting.
- **Splash screen** and a new gradient app icon.

### Android

- Redesigned UI with a splash screen, dashboard drawer, bottom-sheet settings,
  SVG icons and matching dark/light themes.
- Full English / বাংলা switch across every label, including new settings copy.
- Conversation and preferences persist across restarts.
- Version 1.1.0 (versionCode 2), 3.5 MB signed APK.

### Under the hood

- Agent tools: web search, page reader, calculator, current time, read/write
  files, list files, isolated Python, weather and random numbers.
- RAG ingestion for PDF, DOCX and XLSX, plus 30+ text and source formats (txt, md,
  csv, json, yaml, html, py, js, java, c, go, rs, sh, tex, …), with cited passages
  in the prompt. Files up to 30 MB.
- Optional `sqlite-vec` + `sentence-transformers` semantic memory, with an FTS5
  keyword fallback and a visible badge showing which mode is active.
- Provider-aware generation with automatic fallback: HuggingFace, Replicate,
  fal.ai, Stability AI and Together AI for images; HuggingFace and Replicate for
  music; Replicate and fal.ai for video. OpenRouter is a stored key slot only.
- Every provider error is surfaced in the studio — no silent failures.

## Honest limitations

- Android is chat-only; memory, RAG, tools and the studio are desktop features.
- Semantic recall needs the optional dependencies. Without them the app uses
  keyword/FTS5 search — good, not magic.
- Video generation is experimental and depends on provider queues.
- OpenRouter is stored as a key only; no generator uses it yet.
- Both builds are unsigned/self-signed, so OS warnings are expected.

## Verify the downloads

| File | Size | SHA-256 |
| --- | --- | --- |
| `GroqChatbot-v1.1.exe` | 90,660,151 bytes (86.5 MB) | `68ab398e3560dbeb9a08b59c9968b39df1f515bab4baabecf470c12126ad44f0` |
| `GroqChatbot-v1.1.apk` | 3,684,960 bytes (3.5 MB) | `a265e2790e9e5b1ce81bc2dd72d52af85d7d466b30ac107d9619d9b7f9e4e4f0` |

```powershell
Get-FileHash .\GroqChatbot-v1.1.exe -Algorithm SHA256
Get-FileHash .\GroqChatbot-v1.1.apk -Algorithm SHA256
```

```bash
# Android signature
apksigner verify --print-certs GroqChatbot-v1.1.apk
```

Full details: [README](https://github.com/rhasan2026g-cell/GroqChatbot#readme) ·
[CHANGELOG](https://github.com/rhasan2026g-cell/GroqChatbot/blob/main/CHANGELOG.md).
