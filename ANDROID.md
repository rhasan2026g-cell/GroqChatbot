# GroqChatbot — Android app

An installable Android build of the bilingual (English / বাংলা) chat client,
packaged with Capacitor 6.

| | |
|---|---|
| Package | `com.rbk.groqchat` |
| Version | 1.1.0 (versionCode 2) |
| Size | ~3.5 MB (3,684,960 bytes) |
| Min Android | 5.1 (API 22) |
| Target | Android 14 (API 34) |
| Signing | local release keystore, self-signed (v1 + v2 schemes) |

## What the app does

The phone app is a focused chat client — memory, RAG, tools and the creation
studio are desktop features.

- **English / বাংলা** everywhere: header, drawer, settings, placeholders,
  suggestions and model tags switch instantly. Replies follow your language.
- **Streaming replies** with a live caret, a stop button that keeps the partial
  answer, and per-message copy.
- **Three Groq models**: GPT-OSS 20B (fast), GPT-OSS 120B (smart) and
  Qwen 3.8 27B (fastest).
- **Splash screen** with the GroqChatbot mark.
- **Dashboard drawer** — message count, model, language, theme, quick actions
  (new chat, theme, language, clear history, settings) and system status.
- **Settings sheet** — guided key setup, model picker, dark/light toggle and
  language switch.
- **Local history** — the conversation and preferences survive closing the app.
- **Markdown rendering** — headings, lists, quotes, links, inline code and fenced
  code blocks.

| | |
|---|---|
| ![Dark](docs/screenshots/android-dark.png) | ![Light](docs/screenshots/android-light.png) |
| ![Bengali](docs/screenshots/android-bengali.png) | ![Drawer](docs/screenshots/android-drawer.png) |

## Install on the phone

1. Download **`GroqChatbot-v1.1.apk`** from
   [Releases](https://github.com/rhasan2026g-cell/GroqChatbot/releases).
2. Copy it to the phone (USB, Drive, Telegram to yourself — anything).
3. Tap the file. Android will warn that the app is from an unknown source — allow
   "Install unknown apps" for whichever app opened it (Files, Chrome, …).
4. Open **GroqChatbot** from the app drawer.

The APK is also committed at the repository root, so you can download it without
opening the Releases page.

Verify the build if you like:

```bash
sha256sum GroqChatbot-v1.1.apk
# a265e2790e9e5b1ce81bc2dd72d52af85d7d466b30ac107d9619d9b7f9e4e4f0
apksigner verify --print-certs GroqChatbot-v1.1.apk
```

Because the APK is self-signed rather than distributed through the Play Store,
Play Protect may show a "scan for harmful apps" prompt. Tap **Install anyway**
(or "More details → Install anyway"). That warning appears for every sideloaded
APK, not because anything is wrong with this one.

## First run

The API key is **not** baked into the APK. On first launch a guided sheet opens
automatically (reopen it any time with **⚙**, the menu button → settings, or the
**Connect Groq key** button on the welcome screen):

1. The sheet walks through getting a free key at
   <https://console.groq.com/keys> — tap **Get a free key ↗** to open it.
2. Paste the key. It accepts a bare key, `GROQ_API_KEY=…`, `export …` or a quoted
   value, so copying a whole `.env` line works too. **Show** / **Hide** reveals
   what you pasted.
3. Tap **Save & test** — the key is checked against Groq before it is stored. A
   rejected key stays in the sheet with an explanation; if the phone is offline,
   the key is kept and verified on the first message instead.

The sheet shows a masked preview (`gsk_…m6B5`), lets you replace the key, and has
a **Remove** button. The key lives in the app's private `localStorage` and is only
ever sent to `api.groq.com`. The **⚙** button shows an amber dot while no key is
connected.

## Rebuilding after a change

Everything lives in `android-app/`. The UI is plain HTML/CSS/JS in
`android-app/www/`; there is no framework to install.

```powershell
$env:JAVA_HOME    = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:ANDROID_HOME = "C:\Android\sdk"

cd android-app
npx cap sync android          # copies www/ into the native project
cd android
.\gradlew.bat assembleRelease # → app\build\outputs\apk\release\app-release.apk
```

Swap `assembleRelease` for `assembleDebug` to get a debug APK instead.

To install straight onto a USB-connected phone:

```powershell
adb install -r "path\to\GroqChatbot-v1.1.apk"
```

### Signing key

The release build reads `android-app/android/keystore.properties` and
`android-app/android/groqchat-release.jks`. Both are **git-ignored** and stay on
the build machine — never commit them.

**Keep both files.** Android only accepts an update if it is signed with the same
key, so if you lose this keystore you can never update an already-installed copy —
you would have to uninstall first.

### Play Store (optional)

The Play Store wants an `.aab`, not an `.apk`:

```powershell
.\gradlew.bat bundleRelease   # → app\build\outputs\bundle\release\app-release.aab
```

## Project layout

```text
android-app/
├── capacitor.config.json     appId, app name, webDir, background colour
├── package.json              @capacitor/* 6.2.0
├── www/                      the entire UI (edit here, then `npx cap sync`)
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── android/                  native project (generated, safe to leave alone)
    ├── keystore.properties   (git-ignored)
    ├── groqchat-release.jks  (git-ignored)
    └── app/src/main/
        ├── AndroidManifest.xml
        ├── java/com/rbk/groqchat/MainActivity.java
        └── res/               icons, splash screens, theme
```

## Troubleshooting

**"App not installed"** — an older copy signed with a different key is already on
the phone, or the download was truncated. Uninstall the old app, re-download, and
check the SHA-256 above.

**Play Protect blocks the install** — tap *More details → Install anyway*. This is
the standard warning for any APK outside the Play Store.

**"Invalid API key"** — the key was revoked or copied with extra characters. Open
**⚙ → Groq API key**, paste it again (a whole `GROQ_API_KEY=…` line is accepted),
and tap **Save & test**.

**Replies stop mid-sentence** — that is usually the network. The partial answer is
kept; tap send again or use the stop button before retrying.

**Gradle fails with "Unsupported class file major version"** — you are on the
wrong JDK. Capacitor 6 needs **JDK 17** (`JAVA_HOME` must point at it), not 21.

## Notes

- Launcher icons and native splash screens use the app palette (gradient tile on
  `#0B0F16`). Regenerate them if you change the branding.
- Capacitor 6 is pinned deliberately: Capacitor 7 requires JDK 21 and SDK 35.
- The app talks to Groq directly from the WebView. Groq's API sends
  `access-control-allow-origin: *`, which is what makes that possible without a
  backend proxy.
- The Android UI is verified in a headless Chromium session at 390×844: all
  screens render with zero JavaScript errors.
- Release 1.1.0 is published at
  <https://github.com/rhasan2026g-cell/GroqChatbot/releases/tag/v1.1.0>.
