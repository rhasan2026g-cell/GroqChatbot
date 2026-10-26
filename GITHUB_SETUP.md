# GitHub setup and release runbook

The repository is live at <https://github.com/rhasan2026g-cell/GroqChatbot> and
**v1.1.0** is published. This file keeps the repeatable steps: how the repo was
created, how settings are configured, and how to ship the next version.

## Repository facts

| Field | Value |
| --- | --- |
| Owner / name | `rhasan2026g-cell` / `GroqChatbot` |
| URL | <https://github.com/rhasan2026g-cell/GroqChatbot> |
| Default branch | `main` |
| License | MIT |
| Latest release | `v1.1.0` (desktop 1.1.0 · Android 1.1.0 / versionCode 2) |
| CI | `.github/workflows/ci.yml` — Python, JavaScript and secret scan |

## First-time setup (fork or re-create)

```bash
git init
git add .
git commit -m "Initial commit: GroqChatbot - Bilingual AI Agent with memory and tools"
git branch -M main
git remote add origin https://github.com/rhasan2026g-cell/GroqChatbot.git
git push -u origin main
```

Or push an existing clone:

```bash
git remote add origin https://github.com/rhasan2026g-cell/GroqChatbot.git
git branch -M main
git push -u origin main
```

## Repository settings

**About** — description, website and 20 topics are listed in
[GITHUB_ABOUT.md](GITHUB_ABOUT.md).

**General**

- Default branch: `main`
- Social preview: upload `docs/social-preview.png`
- Features: keep Issues on; Wiki and Projects off is fine

**Actions** — enabled; the workflow has `contents: read` only.

**Secrets** — none are needed. The app never uses server-side keys; users bring
their own Groq key.

## Version bump map

Change these together before a release:

| File | Field | 1.1.0 value |
| --- | --- | --- |
| `ui_theme.py` | `APP_VERSION` | `1.1.0` |
| `android-app/package.json` | `version` | `1.1.0` |
| `android-app/android/app/build.gradle` | `versionName` | `1.1.0` |
| `android-app/android/app/build.gradle` | `versionCode` | `2` (always increments) |
| `README.md`, `CHANGELOG.md` | badges, download names | `v1.1` |

## Build both binaries

```powershell
# Desktop EXE (about 3 minutes)
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name GroqChatbot-v1.1 --icon assets\app_icon.ico `
  --hidden-import groq --collect-all groq "My Chatbot.py"
# → dist\GroqChatbot-v1.1.exe

# Android APK (about 9 minutes)
$env:JAVA_HOME    = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:ANDROID_HOME = "C:\Android\sdk"
cd android-app
npx cap sync android
cd android
.\gradlew.bat assembleRelease
# → app\build\outputs\apk\release\app-release.apk
```

Copy the APK to the repository root as `GroqChatbot-v1.1.apk` (it is committed on
purpose so the repo has a one-click download). The EXE stays in `dist/`, which is
git-ignored, and is uploaded to the GitHub release instead.

Smoke-test before publishing: launch the EXE, open the APK on a phone (or check
`aapt dump badging`), and confirm both ask for a key instead of shipping one.

## Publish a release

### In the browser

1. **Releases → Draft a new release**
2. Tag: `v1.1.0` (create it on `main`)
3. Title: `GroqChatbot 1.1.0 — dashboard, database browser, tool bench, new Android UI`
4. Body: paste `RELEASE_NOTES_v1.1.0.md`
5. Attach `GroqChatbot-v1.1.exe` and `GroqChatbot-v1.1.apk`
6. Tick **Set as the latest release**, then publish

### From the command line (no `gh` needed)

```powershell
git tag -a v1.1.0 -m "GroqChatbot 1.1.0"
git push origin v1.1.0
```

Then create the release through the REST API with a token that has `repo` scope;
upload assets to `https://uploads.github.com/repos/<owner>/<repo>/releases/<id>/assets?name=<file>`.
`GITHUB_ABOUT.md` shows the API call shape for the About panel.

## Pre-push checklist

- [ ] `.env`, `*Api Key*.md`, keystores and databases are git-ignored
- [ ] No `gsk_…` token in any tracked file
- [ ] `python -m py_compile` passes for every module
- [ ] `node --check android-app/www/app.js` passes
- [ ] README image paths exist and render
- [ ] `CHANGELOG.md` and release notes match the version
- [ ] EXE and APK launch, and neither contains a key

## Troubleshooting

**Authentication** — HTTPS pushes need a Personal Access Token (or the Git
Credential Manager). Generate one at *Settings → Developer settings → Personal
access tokens*.

**`NativeCommandError` on push/build** — PowerShell treats stderr as an error
record. If the last line says `main -> main` (or `Build complete!`), the command
succeeded; check `$LASTEXITCODE` instead of the noise.

**Large files** — GitHub accepts files up to 100 MB. The EXE is ~87 MB, so it is
uploaded as a release asset rather than committed; the ~3.5 MB APK is committed.

**`LF will be replaced by CRLF`** — harmless on Windows. The repository keeps LF;
add `core.autocrlf=input` if the warnings bother you.

**Remote already exists** — `git remote remove origin` then add it again.
