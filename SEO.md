# Search & discovery playbook

How this repository is made findable — on GitHub search, on Google, and when
someone pastes the link into a chat app. Everything here is measured, not guessed,
and every claim in the copy has to be true. A repo that over-promises gets clicks
and loses stars; a repo that answers a real query keeps them.

Maintained alongside [README.md](README.md) and [GITHUB_ABOUT.md](GITHUB_ABOUT.md).

## Where GitHub discovery actually comes from

| Surface | Limit | Weight | Current value |
| --- | --- | --- | --- |
| Repository name | — | High | `GroqChatbot` |
| About description | 350 characters | High | see below |
| Topics | 20 | High | 20 set, listed below |
| README text | — | Medium (repo search `in:readme`, Google) | keyword-front-loaded intro, FAQ phrased as queries |
| Release title + notes | — | Medium (Google indexes release pages) | `v1.1.0` |
| Stars, forks, recent commits | — | Ranking signal | honest growth only |
| Social preview image | 1 | Click-through rate, not ranking | needs a manual upload |

Default repository search matches **name, description, topics and README**, so the
first ~150 words of the README carry the phrases people actually type.

## Live description (269 / 350 characters)

> Free, open-source ChatGPT-style AI app for Windows and Android. Bilingual
> English/Bengali (বাংলা) chat with Groq LPU streaming, offline SQLite long-term
> memory, RAG document Q&A, 10 agent tools and an image/music/video studio. No
> account, no telemetry, keys stay local.

Why this order: `free` and `open-source` are the highest-intent filters, `ChatGPT-style`
captures the comparison search without claiming to *be* ChatGPT, `Windows` and
`Android` name the platforms, `Bengali (বাংলা)` carries the differentiating script
that almost no competitor has in its metadata, and the last sentence answers the
privacy question before it is asked.

## Topics, chosen by demand

Public repository counts per topic, measured with the GitHub search API
(`topic:<name>`, public repos). Broad topics classify the project; narrow ones are
where a young repo can actually reach page one.

| Topic | Public repos | Role |
| --- | ---: | --- |
| `ai` | 191,801 | category |
| `android` | 167,815 | platform |
| `llm` | 164,162 | category |
| `windows` | 93,824 | platform |
| `open-source` | 78,857 | intent |
| `rag` | 58,864 | feature |
| `ai-agent` | 41,380 | category |
| `privacy` | 33,606 | intent |
| `chatbot` | 32,851 | category |
| `local-first` | 29,270 | intent |
| `desktop-app` | 29,124 | platform |
| `generative-ai` | 23,961 | category |
| `groq` | 10,100 | stack |
| `image-generation` | 9,870 | feature |
| `ai-assistant` | 8,578 | category |
| `pyside6` | 5,946 | stack |
| `tool-calling` | 3,803 | feature |
| `capacitor` | 3,249 | stack |
| `bilingual` | 3,009 | differentiator |
| `bengali` | 512 | **zero-competition niche** |

*Counts measured 26 October 2026. They drift monthly — treat them as relative
orders of magnitude, not exact targets.*

Deliberately **not** used: `python` (977k repos — the language badge already shows
it), `chatgpt` (implies an OpenAI integration this app does not have), `self-hosted`
(it is a client, not a server), `machine-learning` (nothing is trained here).

Swapped out in this pass: `sqlite-vec` (277), `long-term-memory` (1,181),
`music-generation` (1,332), `streaming` (13,057) and `python` — replaced by `ai`,
`windows`, `open-source`, `generative-ai` and `ai-assistant`.

## Keyword map

Each cluster is served by a real section of the README, so the phrase is supported
by substance rather than repetition.

| Intent | Phrases the project answers | Where they live |
| --- | --- | --- |
| Free alternative | free ChatGPT alternative for Windows, open-source AI chat app, no subscription | intro, at-a-glance, FAQ |
| Bengali | Bengali AI chatbot, বাংলা chatbot, bangla AI assistant, bilingual UI | subtitle, at-a-glance, feature heading, FAQ |
| Local & private | local-first AI assistant, private AI chat, no telemetry, keys stay local | intro, privacy section, FAQ |
| Memory | AI with long-term memory, offline memory, persistent chat history | memory section, at-a-glance |
| Documents | chat with PDF, DOCX, XLSX, RAG without a backend, document Q&A | RAG section, FAQ |
| Speed | fast AI chat, Groq LPU, streaming replies, GPT-OSS, Qwen | models row, chat section |
| Agents | AI agent tools, function calling, agent with permissions | tools section |
| Media | AI image generator, text to music, text to video | studio section |
| Platform | Windows AI app, Android AI chat APK, PySide6 desktop app, Capacitor | download, build, project tree |

## What we do not do

- **No fake engagement.** No bought stars, no star-exchange, no bot issues. GitHub
  detects it and it destroys the credibility the README is building.
- **No keyword stuffing.** A term appears where it is genuinely the clearest word.
  Repeating "best AI chatbot" twenty times ranks worse and reads like spam.
- **No competitor claims.** No "better than X" table with unverifiable numbers.
  The comparison the README makes is with *your own* alternatives, not rivals' flaws.
- **No misleading topics.** `chatgpt` is avoidable because it suggests an
  integration; `self-hosted` because there is no server component.
- **No keyword-only files.** No `keywords.txt`, no hidden HTML in the README —
  GitHub renders it, readers see it, and it looks desperate.

## Changing metadata safely

```powershell
# Description must stay at or under 350 characters
$description = "…"
$description.Length

# Topics: the endpoint REPLACES the list, it does not merge. Send all 20.
Invoke-RestMethod -Method Put `
  -Uri "https://api.github.com/repos/rhasan2026g-cell/GroqChatbot/topics" `
  -Headers @{ Authorization = "Bearer $env:GITHUB_TOKEN"; "User-Agent" = "GroqChatbot" } `
  -ContentType "application/json" `
  -Body (@{ names = @("ai", "llm", "rag") } | ConvertTo-Json)
```

Then confirm what the public actually sees:

```powershell
Invoke-RestMethod "https://api.github.com/repos/rhasan2026g-cell/GroqChatbot" |
  Select-Object description, topics, has_discussions
```

Keep the lists in this file, [README.md](README.md) (`Topics & search terms`) and
[GITHUB_ABOUT.md](GITHUB_ABOUT.md) identical — three places that disagree is how
metadata rots.

**Not automatable:** the social preview. Upload `docs/social-preview.png` in
*Settings → General → Social preview*; it is what X, Slack, Discord and WhatsApp
show when someone shares the link, and it moves click-through more than any single
keyword.

## Measuring, monthly

1. **Insights → Traffic** — views, clones, referrers, popular content. Referrers
   show which topics or posts actually send people.
2. **Insights → Traffic → Popular content** — if `README.md` leads, the copy is
   doing the work; if a screenshot leads, the images are.
3. **Search impressions** — open an incognito window and search GitHub for
   `bengali ai chatbot`, `free chatgpt alternative windows`, `rag desktop app` and
   `groq gui`; note which page the repo appears on.
4. Adjust one variable at a time (description *or* topics *or* README) so the
   effect is attributable.

Realistic expectation: the `bengali` and `pyside6` topics can rank quickly because
the pools are small; `ai` and `llm` are decided by stars and activity, which only
come from shipping and telling people. Metadata gets the repo in front of the right
people — it cannot substitute for them finding it useful.
