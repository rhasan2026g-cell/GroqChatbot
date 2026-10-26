# Security Policy

GroqChatbot runs entirely on your machine: there is no backend, no account and no
telemetry. That keeps the attack surface small, but it also means the security of
your API keys, memory database and generated files depends on your device.

## Supported versions

| Version | Supported | Notes |
| --- | --- | --- |
| 1.1.x | ✅ | Current release (desktop 1.1.0, Android 1.1.0 / versionCode 2) |
| 1.0.x | ❌ | Superseded — please upgrade |

Security fixes ship in the newest release only. Upgrade before reporting a
problem that may already be fixed.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private reporting flow:
[Report a vulnerability](https://github.com/rhasan2026g-cell/GroqChatbot/security/advisories/new)
(Security tab → *Report a vulnerability*). If that is unavailable, contact the
maintainer through the profile at
<https://github.com/rhasan2026g-cell>.

Include:

- what you found, and the affected version (**Settings → About** shows it);
- steps to reproduce, or a proof of concept;
- the impact you believe it has;
- your platform (Windows build, Android version, phone model);
- an optional suggested fix.

### What to expect

| Stage | Target |
| --- | --- |
| Acknowledgement | within 48 hours |
| Initial assessment and severity | within 7 days |
| Fix or mitigation plan | as soon as practical, coordinated with you |
| Public disclosure | after a fix ships, with credit if you want it |

Please give us a reasonable window before publishing details.

## Security model

### What stays local

| Data | Where it lives | Protection |
| --- | --- | --- |
| API keys (desktop) | `.env` next to the script (source) or next to the EXE (packaged) | File permissions of your user account. Git-ignored. |
| API keys (Android) | App-private `localStorage` (`gc_key`) | Android app sandbox — other apps cannot read it. |
| Conversations and facts | `memory.db` (SQLite) | Your user account only. Not encrypted at rest. |
| Uploaded documents and chunks | `documents/` + `rag_chunks` table | Same as above. |
| Generated media | `data/generated/` | Same as above. |
| Settings | `QSettings` (desktop) | Your user profile. |

### Network traffic

- **Desktop:** `api.groq.com` for chat, plus only the generation providers whose
  keys you configured (HuggingFace, Replicate, Stability AI, fal.ai, Together AI).
  The `web_search`, `fetch_url` and `get_weather` tools contact their public
  endpoints when the model chooses to use them.
- **Android:** `api.groq.com` only, directly from the WebView. Groq's API allows
  cross-origin requests, which is why no proxy is needed.
- No analytics, crash reporting, update pings or advertising SDKs.

### Tool permissions

Agent tools that can change your machine are **off by default** and gated in the
Tool workbench:

- `write_file` — create or overwrite files;
- `execute_python` — run a short snippet in a separate process;
- network tools — `web_search`, `fetch_url`, `get_weather`.

`execute_python` is a *separate process*, not a hardened sandbox. Treat it the way
you would treat running a script a stranger wrote: only enable it when you
understand the prompt that triggered it.

## Known considerations

- **Keys are plain text at rest.** `.env` (desktop) and `localStorage` (Android)
  are not encrypted. Anyone who can read your user profile can read the key. Use
  a dedicated key and revoke it at
  [console.groq.com/keys](https://console.groq.com/keys) if it leaks.
- **The memory database is not encrypted.** It contains everything you typed,
  including anything the app extracted as a "fact". Keep disk encryption on.
- **Prompt injection is possible.** Documents you upload and pages the tools fetch
  are untrusted text. A malicious document could try to instruct the model to call
  a tool. Keep write/Python permissions off unless you need them.
- **Builds are unsigned or self-signed.** SmartScreen and Play Protect warnings are
  expected. Verify the SHA-256 checksums published in the release notes.
- **Third-party providers see your prompts.** If you generate an image through
  Replicate or fal.ai, that prompt is sent to them under their terms.
- **The Android release keystore is not in the repository.** `keystore.properties`
  and `*.jks` are git-ignored; only `keystore.properties.example` (placeholders) is
  committed.

## Repository safeguards

- `.env`, `*Api Key*.md`, keystores, databases, build output and scratch files are
  git-ignored.
- CI runs a secret scan on every push and pull request: it fails if a keystore is
  tracked or a `gsk_…` token appears in the source.
- No release artifact contains a baked-in key. The EXE and APK ship without
  credentials and ask for one on first launch.

## Hardening checklist for users

1. Create a key specifically for this app and keep it out of screenshots.
2. Turn on full-disk encryption (BitLocker, FileVault, Android encryption).
3. Leave `write_file`, `execute_python` and network tools disabled unless needed.
4. Review facts in **Database browser → Facts** and delete anything you would not
   want stored.
5. Keep the app and its dependencies updated.
6. On Android, install only APKs you downloaded from this repository's Releases.

## Disclaimer

GroqChatbot is provided "as is", without warranty of any kind. You are responsible
for the prompts you send, the documents you upload, the tools you enable and the
keys you store. See [LICENSE](LICENSE).
