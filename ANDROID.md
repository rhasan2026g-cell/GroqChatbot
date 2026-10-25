# Groq Chat — Android app

An installable Android build of the same bilingual (English / বাংলা) chat app,
packaged with Capacitor 6.

| | |
|---|---|
| Package | `com.rbk.groqchat` |
| Version | 1.0 (versionCode 1) |
| Size | ~2.9 MB |
| Min Android | 5.1 (API 22) |
| Target | Android 14 (API 34) |
| Signing | release keystore, self-signed (v1 + v2 schemes) |

## Files

| File | Purpose |
|---|---|
| `GroqChat-v1.0.apk` | **Install this one.** Signed release build. |
| `GroqChat-v1.0-debug.apk` | Debug build, only needed for troubleshooting. |

## Install on the phone

1. Copy `GroqChat-v1.0.apk` to the phone (USB cable, Google Drive, Telegram to
   yourself — anything).
2. Tap the file. Android will say the app is from an unknown source — allow
   "Install unknown apps" for whichever app opened it (Files, Chrome, …).
3. Open **Groq Chat** from the app drawer.

Because the APK is self-signed rather than distributed through the Play Store,
Play Protect may show a "scan for harmful apps" prompt. Tap **Install anyway**
(or "More details → Install anyway"). That warning appears for every sideloaded
APK, not because anything is wrong with this one.

## First run

The API key is **not** baked into the APK. On first launch a guided setup sheet
opens automatically (you can reopen it any time with **⚙** or the **Connect Groq
key** button on the welcome screen):

1. The sheet walks through getting a free key at
   <https://console.groq.com/keys> — tap **Get a free key ↗** to open it.
2. Paste the key. It accepts a bare key, `GROQ_API_KEY=…`, `export …` or a quoted
   value, so copying a whole `.env` line works too. **Show** / **Hide** reveals
   what you pasted.
3. Tap **Save & test** — the key is checked against Groq before it is stored. A
   rejected key stays in the sheet with an explanation; if the phone is offline,
   the key is kept and verified on the first message instead.

The sheet also shows a masked preview (`gsk_…m6B5`), lets you replace the key,
and has a **Remove** button. The key lives in the app's private `localStorage` on
the device and is only ever sent to `api.groq.com`. The **⚙** button shows an
amber dot while no key is connected.

## What the app does

- **English / বাংলা** toggle in the header — switches every label, the placeholder,
  the suggestion chips and the model tags instantly. The choice and the
  conversation survive closing the app.
- **Streaming replies** with a live caret, a **stop** button that keeps the
  partial answer.
- **Three models**: GPT-OSS 20B (fast), GPT-OSS 120B (smart), Qwen 3.8 27B.
- **Code blocks, bold, inline code and links** rendered from Markdown.
- **Copy** button on every message.
- **＋** starts a new chat; the previous one is discarded.
- Replies follow the language you write in — write Bengali, get Bengali.

## Rebuilding after a change

Everything lives in `android-app/`. The UI is plain HTML/CSS/JS in
`android-app/www/`; there is no framework to install.

```powershell
$env:JAVA_HOME    = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
$env:ANDROID_HOME = "C:\Android\sdk"
$env:PATH         = "$env:JAVA_HOME\bin;$env:PATH"

cd "C:\Users\rbkha\Desktop\Chatbot VS AI agnet\ChatBot\android-app"
npx cap sync android          # copies www/ into the native project
cd android
.\gradlew.bat assembleRelease # → app\build\outputs\apk\release\app-release.apk
```

Swap `assembleRelease` for `assembleDebug` to get a debug APK instead.

To install straight onto a USB-connected phone:

```powershell
adb install -r "C:\Users\rbkha\Desktop\Chatbot VS AI agnet\ChatBot\GroqChat-v1.0.apk"
```

### Signing key

`android-app/android/groqchat-release.jks` with the passwords in
`android-app/android/keystore.properties` (store & key password `groqchat2026`,
alias `groqchat`).

**Keep both files.** Android only accepts an update if it is signed with the
same key, so if you lose this keystore you can never update an already-installed
copy — you would have to uninstall first.

### Play Store (optional)

The Play Store wants an `.aab`, not an `.apk`:

```powershell
.\gradlew.bat bundleRelease   # → app\build\outputs\bundle\release\app-release.aab
```

## Project layout

```
android-app/
├── capacitor.config.json     appId, app name, webDir
├── package.json              @capacitor/* 6.2.0
├── www/                      the entire UI (edit here, then `npx cap sync`)
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── android/                  native project (generated, safe to leave alone)
    ├── keystore.properties
    ├── groqchat-release.jks
    └── app/src/main/
        ├── AndroidManifest.xml
        ├── java/com/rbk/groqchat/MainActivity.java
        └── res/               icons, splash screens, theme
```

## Notes

- Icons and splash screens were generated in the app's own palette (blue `G`
  tile on `#0F131A`); regenerate them with the script described in the chat if
  you change the branding.
- Capacitor 6 is pinned deliberately: Capacitor 7 requires JDK 21 and SDK 35.
- The app talks to Groq directly from the WebView. Groq's API sends
  `access-control-allow-origin: *`, which is what makes that possible without a
  backend proxy.
