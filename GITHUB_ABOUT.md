# GitHub Repository — About and release metadata

Everything on this page is **already applied** to
<https://github.com/rhasan2026g-cell/GroqChatbot> except the social preview,
which GitHub only exposes in the web UI.

## About panel

**Description** (currently live, 269 / 350 characters):

```
Free, open-source ChatGPT-style AI app for Windows and Android. Bilingual English/Bengali (বাংলা) chat with Groq LPU streaming, offline SQLite long-term memory, RAG document Q&A, 10 agent tools and an image/music/video studio. No account, no telemetry, keys stay local.
```

**Website:** `https://github.com/rhasan2026g-cell/GroqChatbot`

**Topics** (20 — GitHub's maximum, currently live):
`ai`, `llm`, `rag`, `ai-agent`, `ai-assistant`, `chatbot`, `generative-ai`,
`android`, `desktop-app`, `windows`, `open-source`, `local-first`, `privacy`,
`groq`, `pyside6`, `capacitor`, `bilingual`, `bengali`, `image-generation`,
`tool-calling`.

These were chosen from measured GitHub demand rather than intuition; the data, the
keyword map and the rules are in [SEO.md](SEO.md). Short version: broad topics
(`ai`, `llm`) classify the project, mid-size ones (`groq`, `pyside6`, `rag`) match
how people browse stacks, and `bengali` / `bilingual` are near-empty pools where a
young repository can actually reach page one.

**Discussions:** enabled, so questions have a home that is not an issue thread.

## Social preview

GitHub has no API for this one — set it manually:

**Settings → General → Social preview → Edit →** upload `docs/social-preview.png`
(2000×1000, already in the repository).

## Current release

| Field | Value |
| --- | --- |
| Tag | `v1.1.0` |
| Title | GroqChatbot 1.1.0 — free bilingual AI app for Windows & Android (Groq, RAG, memory, studio) |
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
  -Body (@{ description = "Free, open-source ChatGPT-style AI app for Windows and Android. Bilingual English/Bengali (বাংলা)." } | ConvertTo-Json)

Invoke-RestMethod -Method Put -Uri "https://api.github.com/repos/rhasan2026g-cell/GroqChatbot/topics" `
  -Headers $headers -ContentType "application/json" `
  -Body (@{ names = @("ai","llm","rag","bengali") } | ConvertTo-Json)
```

`names` must always be the **full** list you want — the endpoint replaces topics,
it does not merge them. Keep it at 20 or fewer and keep [SEO.md](SEO.md) in sync.
