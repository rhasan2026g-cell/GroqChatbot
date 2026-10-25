# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-10-24

First public release.

### Added

- **Desktop app** (`My Chatbot.py`) built with PySide6: streaming replies, stop
  button, per-message copy, Markdown export, model picker and keyboard shortcuts.
- **Android app** (`android-app/`) built with Capacitor 6: the same chat
  experience in a 2.9 MB signed APK, installable without the Play Store.
- **Full bilingual UI** — every label, placeholder, suggestion and model tag
  switches instantly between English and বাংলা. Replies follow the language you
  write in.
- **Guided API-key setup** on both platforms: a three-step sheet, `gsk_` format
  validation, live test against Groq, show/hide, masked preview and remove.
  The desktop app writes to `.env`; Android keeps the key on-device.
- **Three Groq models**: GPT-OSS 20B (fast), GPT-OSS 120B (smart) and
  Qwen 3.8 27B (fastest).
- **Streaming over SSE** with a live caret and Markdown rendering, including
  fenced code blocks.
- Conversation persistence on Android (`localStorage`) and preference
  persistence on desktop (`QSettings`).
- Documentation: README with architecture diagrams, `ANDROID.md` build guide,
  `GITHUB_SETUP.md` launch kit, security policy and contributing guide.
- Offline unit tests and a GitHub Actions workflow.

### Security

- No API key is baked into the APK or committed to the repository.
- `.env`, keystore files and local build outputs are gitignored.

[1.0.0]: https://github.com/your-handle/groq-chat/releases/tag/v1.0.0
