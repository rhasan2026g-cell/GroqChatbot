# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Documentation

- **Search and discovery pass.** Repository description rewritten around the
  phrases people actually search for (free, open-source, ChatGPT-style, Windows,
  Android, Bengali/বাংলা), and the twenty topics re-chosen from measured GitHub
  demand — broad ones (`ai`, `llm`, `android`, `windows`, `open-source`) for
  classification, tight ones (`groq`, `pyside6`, `rag`, `tool-calling`) for stack
  searches, and `bengali` / `bilingual` where a young repo can actually rank.
- Added [SEO.md](SEO.md): the keyword map, the demand data behind each topic, the
  rules (no fake stars, no stuffing, no competitor claims) and a monthly
  measurement routine.
- README front-loads the search phrases in the first two paragraphs, gains an
  "At a glance" fact table, keyword-rich section headings, descriptive alt text on
  every screenshot, and FAQ questions phrased the way people type them
  ("Is there a free ChatGPT alternative for Windows?", "Is there an AI chatbot
  that speaks Bengali?").
- Discussions enabled so questions do not pile up in issue threads.

## [1.1.0] — 2026-10-26

A full interface release: the desktop app gains a dashboard, real system
dialogs and a database browser, the Android app is redesigned to match, and both
ship as fresh signed builds.

### Added

- **Desktop dashboard** — messages, facts, documents and tokens in four stat
  cards, a 7-day activity chart with weekday labels and a highlighted today, six
  quick actions (Database, Tools, Studio, Upload, Memories, Data) and live badges
  for memory mode, search mode, provider count and the active data folder.
- **Brand splash screen** — gradient mark, version, and a "starting local
  systems" status while SQLite, memory and RAG warm up.
- **Settings & system dialog** — five tabs (Chat & agent, API keys, Memory & RAG,
  Creation studio, About) with model, language, theme, accent colour, compact
  spacing, temperature, token budget, retained turns, editable system prompt,
  reset, key management and memory/RAG diagnostics.
- **In-app database browser** (`Ctrl+D`) — tabs for conversations, facts, the
  vector index, documents and RAG chunks; filter the current table, refresh,
  export JSON, open the data folder and delete selected rows.
- **Tool workbench** — every tool with its description and JSON schema, a
  runnable argument editor, "Insert example", live result pane and explicit
  permissions for file writes, Python execution and network access.
- **Creation studio** — image, illustration, music and video tabs with model
  choice, negative prompt, width/height, duration, "Surprise me", provider
  detection, a preview pane and recent outputs.
- **Guided key dialog** — three numbered steps, `gsk_` validation, live test
  against Groq, show/hide, masked preview and remove; writes to `.env` on desktop.
- **Agent tools** — web search, page reader, calculator, current time, read/write
  files, list files, isolated Python, weather and random numbers, with
  permission gates.
- **Document Q&A (RAG)** — PDF, DOCX, XLSX, CSV, TXT, Markdown, JSON and HTML
  ingestion, overlapping chunks, and cited passages injected into the prompt.
- **Optional semantic memory** — `sqlite-vec` + `sentence-transformers`
  (`all-MiniLM-L6-v2`, 384-dim) with an automatic FTS5 keyword fallback and a
  visible badge telling you which one is active.
- **Desktop polish** — regenerate, Markdown export, per-message copy, keyboard
  shortcuts, Unicode maths rendering and token accounting.
- **Assets** — new application icon (PNG + ICO), a regenerated EXE, new Android
  launcher icons and native splash screens in the app's palette.

### Changed

- **Desktop UI rewritten** — theme-aware palettes, hand-tuned light and dark
  variants, five accents, 300–360 px sidebar, 2×2 stat cards, auto-sizing
  composer, wider bubbles and cleaner code blocks.
- **Android UI rewritten** — splash, dashboard drawer with stats and system
  status, bottom-sheet settings, dark/light themes, SVG icons, bilingual labels
  and conversation persistence. Version 1.1.0, versionCode 2.
- **README and documentation** — new banner, social preview, screenshots,
  architecture diagrams and honest limitations.
- **APK size** — 3.5 MB signed release (1.0 was 2.9 MB) after the new UI assets.

### Fixed

- Tool calls are now ordered correctly and streamed without `stream_options`
  errors during tool loops.
- LaTeX fragments are converted to readable Unicode instead of leaking into chat.
- Silent failures in memory, RAG and generation paths now surface as visible
  notes or dialog errors.
- PowerShell build scripts no longer emit `NativeCommandError` noise for normal
  stderr output, and mojibake comments were removed from requirements files.

### Security

- No API key is baked into the EXE or APK, and none is committed.
- `.env`, keystores, databases and build outputs are gitignored.
- File writes, Python execution and network tools require explicit permission.
- CI now fails if a keystore is tracked or a `gsk_…` token appears in the source.

### Documentation

- `README.md` rebuilt around the 1.1 interface: banner, badge row with CI status,
  full screenshot gallery, Mermaid architecture and message-flow diagrams, tool
  and provider tables, build instructions, honest limitations, FAQ and topics.
- `SECURITY.md` rewritten: supported versions, private advisory flow, data map,
  network destinations, tool permissions, known considerations and hardening.
- `CONTRIBUTING.md` rewritten: project map, bilingual and no-silent-failure rules,
  CI-equivalent checks, PR process and a maintainer release checklist.
- `ANDROID.md` updated for 1.1.0 with checksums, install troubleshooting and the
  published release link; `GITHUB_ABOUT.md` and `GITHUB_SETUP.md` now describe the
  live repository, the 20 applied topics and a repeatable release runbook.
- Added `RELEASE_NOTES_v1.1.0.md`; `RELEASE_NOTES_v1.0.0.md` marked historical
  with working links.
- Release assets published: `GroqChatbot-v1.1.exe` (86.5 MB) and
  `GroqChatbot-v1.1.apk` (3.5 MB), with SHA-256 checksums documented.

### Published

- Tag `v1.1.0` and GitHub release
  <https://github.com/rhasan2026g-cell/GroqChatbot/releases/tag/v1.1.0>
  (marked Latest).

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

[1.1.0]: https://github.com/rhasan2026g-cell/GroqChatbot/releases/tag/v1.1.0
[1.0.0]: https://github.com/rhasan2026g-cell/GroqChatbot/commit/4c3ac3d72f663e06f4b614594bd5e5be5774491a
