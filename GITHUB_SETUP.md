# GitHub Repository Setup Guide

Follow these steps to create and push this repository to GitHub.

## Repository Details
- **Repository Name:** GroqChatbot
- **Owner:** rhasan2026g-cell
- **URL:** https://github.com/rhasan2026g-cell/GroqChatbot.git
- **Description:** A bilingual (English/বাংলা) AI agent for Windows and Android — Groq streaming, SQLite memory, document Q&A, tools and a creation studio. PySide6 + Capacitor.

## Quick Setup Commands

### Option 1: Create new repository from scratch
```bash
# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: GroqChatbot - Bilingual AI Agent with memory and tools"

# Set main branch
git branch -M main

# Add remote origin
git remote add origin https://github.com/rhasan2026g-cell/GroqChatbot.git

# Push to GitHub
git push -u origin main
```

### Option 2: Push existing repository
```bash
git remote add origin https://github.com/rhasan2026g-cell/GroqChatbot.git
git branch -M main
git push -u origin main
```

## GitHub Repository Settings

After pushing, configure your repository:

### About Section
- **Description:** `Bilingual (English/বাংলা) AI agent for Windows and Android. Groq LPU streaming, long-term SQLite memory, document Q&A, ten tools, and an image/music/video studio. Built with PySide6 + Capacitor.`
- **Website:** `https://github.com/rhasan2026g-cell/GroqChatbot`
- **Topics:** Add these tags for discoverability (GitHub allows 20)

### Recommended Topics/Tags
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

### Release Setup
1. Go to Releases > Create a new release
2. Tag version: `v1.1.0`
3. Release title: `GroqChatbot 1.1.0 — dashboard, database browser, tool bench, new Android UI`
4. Upload `GroqChatbot-v1.1.exe` and `GroqChatbot-v1.1.apk` as release assets
5. Paste `RELEASE_NOTES_v1.1.0.md` as the release body
6. Upload `docs/social-preview.png` in Settings > General > Social preview

## Pre-Push Checklist

- [ ] All sensitive files are gitignored (.env, keystores, etc.)
- [ ] README.md is properly formatted
- [ ] LICENSE file is present
- [ ] No API keys in code
- [ ] Dependencies listed in requirements.txt
- [ ] Smoke checks pass locally
- [ ] .gitignore is comprehensive

## Troubleshooting

### Authentication Issues
If you're using HTTPS, GitHub may require a Personal Access Token (PAT) instead of password.
Generate one at: Settings > Developer settings > Personal access tokens > Tokens (classic)

### Large Files
The APK files are included. If you hit size limits, consider using Git LFS, but GitHub allows files up to 100MB.

### Remote Already Exists
```bash
git remote remove origin
git remote add origin https://github.com/rhasan2026g-cell/GroqChatbot.git
```
