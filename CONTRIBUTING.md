# Contributing to GroqChatbot

Thanks for wanting to help. GroqChatbot is a bilingual desktop + Android AI client,
and contributions of every size are welcome: bug reports, translations, provider
adapters, documentation fixes and UI polish.

By participating you agree to keep the project respectful and to license your
contribution under the MIT License.

## Ways to contribute

- **Report a bug** — [open an issue](https://github.com/rhasan2026g-cell/GroqChatbot/issues/new)
  with your OS, app version (Settings → About), what you expected and what happened.
- **Request a feature** — describe the problem first, then the idea.
- **Send a pull request** — small, focused changes merge fastest.
- **Improve translations** — every user-facing string must exist in English *and*
  বাংলা; awkward Bengali is a bug.
- **Add a provider** — see `generation.py`; keep failures visible, never silent.

Security issues go through [SECURITY.md](SECURITY.md), not the public tracker.

## Setting up

```bash
git clone https://github.com/rhasan2026g-cell/GroqChatbot.git
cd GroqChatbot

python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
copy .env.example .env            # then add your GROQ_API_KEY
python "My Chatbot.py"
```

Optional extras (semantic memory, better document extraction):

```bash
pip install -r requirements-optional.txt
```

The Android client lives in `android-app/www/` (plain HTML/CSS/JS). It needs
Node 18+ and, to build an APK, JDK 17 plus Android SDK 34 — see
[ANDROID.md](ANDROID.md).

## Project map

| Path | What it owns |
| --- | --- |
| `My Chatbot.py` | Desktop window, chat flow, agent loop wiring |
| `ui_theme.py` | Palettes, stylesheet, logo, splash, icons |
| `ui_widgets.py` | Stat cards, badges, activity chart |
| `ui_dialogs.py` | Settings, database, tools, studio, key and about dialogs |
| `memory_system.py` | SQLite memory, fact extraction, optional sqlite-vec |
| `rag_system.py` | Document extraction, chunking, retrieval |
| `agent_tools.py` | Tool registry, schemas, permissions |
| `generation.py` | Image, illustration, music and video providers |
| `app_paths.py` | Dev vs frozen data directories |
| `android-app/www/` | The entire Android UI |
| `docs/` | Banner, social preview, screenshots |
| `SEO.md` | Keyword map, topic choices and discovery rules |

## House rules

- **Everything is bilingual.** Desktop: add a key to `STRINGS["en"]` and
  `STRINGS["bn"]` in `My Chatbot.py` and read it with `tr(lang, key)`; inside
  dialogs use `L(host, "English", "বাংলা")`. Android: add the key to both tables in
  `app.js` and read it with `t(key)`. A string with only one language is incomplete.
- **No silent failures.** Surface the error to the user — a dialog, an inline note,
  a footer badge — and log enough detail to debug it.
- **Never commit secrets.** `.env`, `*.jks`, `keystore.properties`, `*Api Key*.md`
  and databases are git-ignored for a reason.
- **Keep it local-first.** No telemetry, no hidden network calls, no accounts.
- **Match the existing style.** PySide6 widgets are built in code with the shared
  stylesheet; don't inline colours that belong in `ui_theme.py`.
- **Treat metadata as part of the product.** The About description, the twenty
  topics and the README headings are what make the project findable. If you change
  what the app does, update all three — the rules and the data behind them are in
  [SEO.md](SEO.md). No fake stars, no keyword stuffing, no claims the code cannot
  back up.
- **One concern per PR.** Unrelated refactors make review slow.

## Checks before opening a PR

There is no pytest suite yet. Run these before opening a pull request; CI
enforces the Python and JavaScript syntax checks on every push.

```bash
# Python syntax for every module
python -m py_compile "My Chatbot.py" app.py app_paths.py memory_system.py \
  rag_system.py agent_tools.py generation.py ui_theme.py ui_widgets.py ui_dialogs.py

# Optional smoke script (memory + tools, no network)
python test_agent.py

# JavaScript syntax for the Android UI
node --check android-app/www/app.js

# Manual pass: chat, a tool call, memory recall, upload a document, open each dialog
python "My Chatbot.py"
```

If you touch the Android UI, also run `npx cap sync android` and confirm the app
still renders at 390×844 in a phone-sized viewport.

## Pull request process

1. Branch from `main` and name it for the change (`fix/memory-duplicates`,
   `feature/openrouter-images`).
2. Describe **what** changed and **how you verified it** — screenshots are welcome
   for UI work.
3. Update `README.md` when behaviour or setup changes, and add an entry to
   `CHANGELOG.md`.
4. Keep the diff reviewable; split unrelated work into separate PRs.
5. A maintainer reviews, may ask for changes, then merges.

## Release checklist (maintainers)

1. Bump `APP_VERSION` in `ui_theme.py`, `version` in `android-app/package.json`,
   and `versionCode` / `versionName` in `android-app/android/app/build.gradle`.
2. Rebuild the EXE and APK (commands in [README.md](README.md) and
   [ANDROID.md](ANDROID.md)); test that each launches.
3. Update `CHANGELOG.md`, add `RELEASE_NOTES_vX.Y.Z.md`, refresh screenshots.
4. Commit, tag `vX.Y.Z`, push, then publish a GitHub release with both binaries
   and their SHA-256 checksums.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE) that covers this project.
