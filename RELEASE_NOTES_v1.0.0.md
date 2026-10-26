# GroqChatbot v1.0.0 — Release Notes

> **Historical.** v1.0.0 was the first public build and has been superseded by
> **[v1.1.0](RELEASE_NOTES_v1.1.0.md)**, which redesigned both interfaces and
> added the dashboard, database browser, tool workbench and creation studio.
> The v1.0 APKs are no longer distributed — download the current release from
> <https://github.com/rhasan2026g-cell/GroqChatbot/releases/latest>.

**Release date:** October 25, 2026

## What shipped

### Chat

- **Bilingual UI** — every label switches between English and বাংলা; replies follow
  the language you write in.
- **Streaming replies** over SSE, with a live caret, stop button and Markdown
  rendering including fenced code blocks.
- **Three Groq models**: GPT-OSS 20B (fast), GPT-OSS 120B (smart) and Qwen 3.8 27B.
- **Guided key setup** with `gsk_` validation, live test, show/hide and a masked
  preview. Keys were never baked into the builds.

### Platforms

- **Windows desktop** — PySide6 single-file EXE, no Python required.
- **Android** — Capacitor 6 WebView client, signed APK, tested at 390×844.

### Groundwork for 1.1

The 1.0 tree already contained the memory, RAG, tool and generation modules, but
they were not yet exposed in the interface. v1.1 finished that work.

## Downloads at the time

| Platform | File |
| --- | --- |
| Windows | desktop build run from source — no EXE was attached to the 1.0 release |
| Android | `GroqChatbot-v1.0.apk` (2.9 MB, debug APK also built) |

Both files were removed from the repository when v1.1.0 shipped. Use the latest
release instead.

## Requirements

- Python 3.10+ when running from source (the EXE bundles its own runtime)
- A free Groq API key from <https://console.groq.com/keys>
- Optional: HuggingFace or Replicate key for image generation

## Getting started

```bash
git clone https://github.com/rhasan2026g-cell/GroqChatbot.git
cd GroqChatbot
pip install -r requirements.txt
cp .env.example .env
# add GROQ_API_KEY=... to .env
python "My Chatbot.py"
```

## Full changelog

See [CHANGELOG.md](CHANGELOG.md).

## Acknowledgements

Thanks to Groq for the fast inference API and to the maintainers of PySide6,
SQLite, sqlite-vec, sentence-transformers and Capacitor.

**Full changelog:** <https://github.com/rhasan2026g-cell/GroqChatbot/commit/4c3ac3d72f663e06f4b614594bd5e5be5774491a>
