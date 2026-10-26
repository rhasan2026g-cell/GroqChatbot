/* GroqChatbot — Android client
   English / বাংলা · streaming chat · local history · themeable UI */

const API_URL = "https://api.groq.com/openai/v1/chat/completions";
const MODELS_URL = "https://api.groq.com/openai/v1/models";
const APP_VERSION = "1.1.0";

const SYSTEM_PROMPT =
  "You are GroqChatbot, a helpful and friendly assistant inside a mobile app. " +
  "Always answer in the same language the user writes in: if they write in Bengali (বাংলা), " +
  "answer in natural Bengali; if they write in English, answer in English. Match their script " +
  "and tone. Keep answers clear and concise, use short paragraphs, bullet points when useful, " +
  "and wrap code in triple backticks with a language tag. Be honest when you are unsure.";

const MODELS = [
  { id: "openai/gpt-oss-20b", name: "GPT-OSS 20B", tag: "fast" },
  { id: "openai/gpt-oss-120b", name: "GPT-OSS 120B", tag: "smart" },
  { id: "qwen/qwen3.8-27b", name: "Qwen 3.8 27B", tag: "fastest" },
];

/* -------------------------------------------------------------------------- */
/* translations                                                               */
/* -------------------------------------------------------------------------- */
const STRINGS = {
  en: {
    appTitle: "GroqChatbot",
    tagline: "Fast Groq AI · English & বাংলা",
    welcomeTitle: "How can I help you today?",
    welcomeSub: "Ask anything — in English or বাংলা. Replies stream in real time.",
    placeholder: "Message GroqChatbot…",
    send: "Send",
    stop: "Stop",
    stopped: "(stopped)",
    you: "You",
    assistant: "GroqChatbot",
    copy: "Copy",
    copied: "Copied",
    newChat: "New chat",
    thinking: "Thinking…",
    streaming: "Streaming…",
    suggestions: [
      "Explain quantum computing",
      "Write a poem in বাংলা",
      "Python loop example",
    ],
    modelFast: "fast",
    modelSmart: "smart",
    modelFastest: "fastest",
    dashboard: "Dashboard",
    atAGlance: "At a glance",
    quickActions: "Quick actions",
    system: "System",
    statMessages: "Messages",
    statModel: "Model",
    statLang: "Language",
    statTheme: "Theme",
    themeDark: "Dark",
    themeLight: "Light",
    switchLight: "Switch to light",
    switchDark: "Switch to dark",
    english: "English",
    bengali: "বাংলা",
    toBengali: "বাংলা",
    toEnglish: "English",
    clearHistory: "Clear history",
    clearAsk: "Delete this conversation from this device?",
    historyCleared: "Chat cleared.",
    settingsAction: "API key & models",
    settingsTitle: "Settings",
    modelLabel: "Model",
    modelHint: "The model applies to your next message.",
    appearance: "Appearance",
    languageLabel: "Language",
    privacy:
      "Your Groq API key is stored only on this phone. Chats are kept locally and " +
      "sent to Groq only to generate a reply.",
    aboutLine: `GroqChatbot ${APP_VERSION} · Groq + Capacitor`,
    sysKeyOn: "Groq key connected",
    sysKeyOff: "Connect your Groq key",
    sysHistory: "Local chat history",
    sysStreaming: "Live streaming replies",
    menu: "Open dashboard",
    keyTitleNew: "Connect to Groq",
    keyTitleExisting: "Groq connection",
    keyBodyNew:
      "Groq is free to use. You just need your own API key — it takes about a minute.",
    keyBodyExisting: "Your key is saved on this device. Replace it or run a quick test.",
    keyStep1: "Open console.groq.com/keys and sign in — it's free.",
    keyStep2: "Tap “Create API Key”, then give it any name.",
    keyStep3: "Copy the key that starts with gsk_ and paste it below.",
    keyGet: "Get a free key ↗",
    keySave: "Save & test",
    keyTesting: "Testing…",
    keyShow: "Show",
    keyHide: "Hide",
    keyRemove: "Remove",
    keyRemoveAsk: "Remove the saved Groq API key from this device?",
    keyEmpty: "Paste your key first.",
    keyBadFormat: "That doesn't look like a Groq key — it should start with gsk_.",
    keyInvalid2: "Groq rejected this key. Copy it again from console.groq.com/keys.",
    keyOk: "Connected — you're ready to chat.",
    keySavedOffline:
      "Key saved. Couldn't verify it right now — it will be checked on your first message.",
    keyRemoved: "API key removed from this device.",
    keyCurrent: "Saved key: {key}",
    keyNotSet: "No API key yet — tap to connect",
    keySet: "Groq key connected",
    keyMissing: "Connect your Groq API key to start chatting.",
    keyInvalid: "Invalid API key. Check it in settings (⚙).",
    close: "Close",
    connectGroq: "Connect Groq key",
    rateLimit: "Rate limit reached. Wait a moment and try again.",
    netError: "Network error. Check your connection and try again.",
  },
  bn: {
    appTitle: "গ্রকচ্যাটবট",
    tagline: "দ্রুত গ্রক এআই · ইংরেজি ও বাংলা",
    welcomeTitle: "আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
    welcomeSub: "ইংরেজি বা বাংলায় যেকোনো কিছু জিজ্ঞাসা করুন। উত্তর সরাসরি আসবে।",
    placeholder: "গ্রকচ্যাটবটকে কিছু লিখুন…",
    send: "পাঠান",
    stop: "থামান",
    stopped: "(থামানো হয়েছে)",
    you: "আপনি",
    assistant: "গ্রকচ্যাটবট",
    copy: "কপি",
    copied: "কপি হয়েছে",
    newChat: "নতুন চ্যাট",
    thinking: "ভাবছি…",
    streaming: "উত্তর আসছে…",
    suggestions: [
      "কোয়ান্টাম কম্পিউটিং কী?",
      "বাংলায় কবিতা লেখো",
      "পাইথন লুপ শেখাও",
    ],
    modelFast: "দ্রুত",
    modelSmart: "স্মার্ট",
    modelFastest: "সবচেয়ে দ্রুত",
    dashboard: "ড্যাশবোর্ড",
    atAGlance: "এক নজরে",
    quickActions: "দ্রুত কাজ",
    system: "সিস্টেম",
    statMessages: "বার্তা",
    statModel: "মডেল",
    statLang: "ভাষা",
    statTheme: "থিম",
    themeDark: "ডার্ক",
    themeLight: "লাইট",
    switchLight: "লাইট মোডে যান",
    switchDark: "ডার্ক মোডে যান",
    english: "English",
    bengali: "বাংলা",
    toBengali: "বাংলা",
    toEnglish: "English",
    clearHistory: "ইতিহাস মুছুন",
    clearAsk: "এই ডিভাইস থেকে এই কথোপকথন মুছে ফেলবেন?",
    historyCleared: "চ্যাট মুছে ফেলা হয়েছে।",
    settingsAction: "এপিআই কী ও মডেল",
    settingsTitle: "সেটিংস",
    modelLabel: "মডেল",
    modelHint: "মডেল পরের বার্তা থেকে কার্যকর হবে।",
    appearance: "অ্যাপিয়ারেন্স",
    languageLabel: "ভাষা",
    privacy:
      "আপনার গ্রক এপিআই কী শুধু এই ফোনে সংরক্ষিত থাকে। চ্যাট ইতিহাস ফোনেই থাকে " +
      "এবং উত্তর তৈরির জন্য শুধু গ্রকে পাঠানো হয়।",
    aboutLine: `গ্রকচ্যাটবট ${APP_VERSION} · গ্রক + ক্যাপাসিটর`,
    sysKeyOn: "গ্রক কী সংযুক্ত",
    sysKeyOff: "গ্রক কী সংযুক্ত করুন",
    sysHistory: "স্থানীয় চ্যাট ইতিহাস",
    sysStreaming: "সরাসরি স্ট্রিমিং উত্তর",
    menu: "ড্যাশবোর্ড খুলুন",
    keyTitleNew: "গ্রকে সংযোগ করুন",
    keyTitleExisting: "গ্রক সংযোগ",
    keyBodyNew:
      "গ্রক ব্যবহার বিনামূল্যে। শুধু আপনার নিজের এপিআই কী দরকার — এক মিনিটের কাজ।",
    keyBodyExisting: "আপনার কী এই ডিভাইসে সংরক্ষিত আছে। বদলাতে পারেন বা পরীক্ষা করতে পারেন।",
    keyStep1: "console.groq.com/keys খুলে বিনামূল্যে সাইন ইন করুন।",
    keyStep2: "“Create API Key” চাপুন, তারপর যেকোনো নাম দিন।",
    keyStep3: "gsk_ দিয়ে শুরু হওয়া কী-টি কপি করে নিচে পেস্ট করুন।",
    keyGet: "বিনামূল্যে কী নিন ↗",
    keySave: "সংরক্ষণ ও পরীক্ষা",
    keyTesting: "পরীক্ষা চলছে…",
    keyShow: "দেখান",
    keyHide: "লুকান",
    keyRemove: "মুছুন",
    keyRemoveAsk: "এই ডিভাইস থেকে সংরক্ষিত গ্রক এপিআই কী মুছে ফেলবেন?",
    keyEmpty: "আগে আপনার কী-টি পেস্ট করুন।",
    keyBadFormat: "এটি গ্রক কী-এর মতো দেখাচ্ছে না — শুরুতে gsk_ থাকা উচিত।",
    keyInvalid2: "গ্রক এই কী গ্রহণ করেনি। console.groq.com/keys থেকে আবার কপি করুন।",
    keyOk: "সংযোগ হয়েছে — এখন চ্যাট করতে পারেন।",
    keySavedOffline:
      "কী সংরক্ষণ হয়েছে। এখন যাচাই করা যায়নি — প্রথম বার্তায় যাচাই হবে।",
    keyRemoved: "এই ডিভাইস থেকে এপিআই কী মুছে ফেলা হয়েছে।",
    keyCurrent: "সংরক্ষিত কী: {key}",
    keyNotSet: "এখনো এপিআই কী নেই — সংযোগ করতে চাপুন",
    keySet: "গ্রক কী সংযুক্ত",
    keyMissing: "চ্যাট শুরু করতে আপনার গ্রক এপিআই কী সংযুক্ত করুন।",
    keyInvalid: "এপিআই কী সঠিক নয়। সেটিংস (⚙)-এ ঠিক করুন।",
    close: "বন্ধ করুন",
    connectGroq: "গ্রক কী সংযুক্ত করুন",
    rateLimit: "অনুরোধের সীমা পূর্ণ। একটু পরে আবার চেষ্টা করুন।",
    netError: "নেটওয়ার্ক সমস্যা। ইন্টারনেট সংযোগ দেখুন।",
  },
};

/* -------------------------------------------------------------------------- */
/* elements + state                                                           */
/* -------------------------------------------------------------------------- */
const $ = (id) => document.getElementById(id);

const ICON_ARROW =
  '<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" ' +
  'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg>';
const ICON_STOP =
  '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2.4"/></svg>';

const store = {
  get(key, fallback = "") {
    try {
      const value = localStorage.getItem(key);
      return value === null ? fallback : value;
    } catch (_) {
      return fallback;
    }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); } catch (_) { /* private mode */ }
  },
  remove(key) {
    try { localStorage.removeItem(key); } catch (_) { /* ignore */ }
  },
};

const state = {
  lang: store.get("gc_lang", "en"),
  theme: store.get("gc_theme", "dark"),
  model: store.get("gc_model", MODELS[0].id),
  messages: [],
  bubbles: [],
  busy: false,
  controller: null,
};

if (!STRINGS[state.lang]) state.lang = "en";
if (!["dark", "light"].includes(state.theme)) state.theme = "dark";
if (!MODELS.some((model) => model.id === state.model)) state.model = MODELS[0].id;

const t = (key) => STRINGS[state.lang][key];
const apiKey = () => store.get("gc_key", "");

const chatEl = $("chat");
const welcomeEl = $("welcome");
const inputEl = $("input");
const sendBtn = $("sendBtn");
const modelSel = $("model");
const taglineEl = $("tagline");
const splashEl = $("splash");

/* -------------------------------------------------------------------------- */
/* formatting                                                                 */
/* -------------------------------------------------------------------------- */
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatRich(input) {
  const codeBlocks = [];
  let src = String(input || "").replace(
    /```[a-zA-Z0-9_+\-.#]*\n?([\s\S]*?)```/g,
    (_match, code) => {
      codeBlocks.push(escapeHtml(code.replace(/\n$/, "")));
      return `\u0000${codeBlocks.length - 1}\u0000`;
    }
  );
  src = escapeHtml(src);

  const inline = (text) =>
    text
      .replace(/\*\*([^*\n]+)\*\*/g, "<b>$1</b>")
      .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,!?:;]|$)/g, "$1<i>$2</i>")
      .replace(/`([^`\n]+)`/g, "<code>$1</code>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_m, label, url) => {
        const safe = url.replace(/"/g, "%22").replace(/'/g, "%27");
        return `<a href="${safe}" target="_blank" rel="noopener">${label}</a>`;
      });

  const html = [];
  let paragraph = [];
  let quote = [];
  let list = null;

  const flushParagraph = () => {
    if (paragraph.length) {
      html.push(`<p>${inline(paragraph.join("<br>"))}</p>`);
      paragraph = [];
    }
  };
  const flushQuote = () => {
    if (quote.length) {
      html.push(`<blockquote>${inline(quote.join("<br>"))}</blockquote>`);
      quote = [];
    }
  };
  const flushList = () => {
    if (list) {
      html.push(`</${list}>`);
      list = null;
    }
  };
  const flushAll = () => {
    flushParagraph();
    flushQuote();
    flushList();
  };

  for (const line of src.split("\n")) {
    const trimmed = line.trim();

    if (/^\u0000\d+\u0000$/.test(trimmed)) {
      flushAll();
      const index = Number(trimmed.replace(/\u0000/g, ""));
      html.push(`<pre><code>${codeBlocks[index] || ""}</code></pre>`);
      continue;
    }

    if (!trimmed) {
      flushAll();
      continue;
    }

    const heading = trimmed.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      flushAll();
      html.push(`<div class="md-h">${inline(heading[2])}</div>`);
      continue;
    }

    if (/^(---+|___+|\*\*\*+)$/.test(trimmed)) {
      flushAll();
      html.push("<hr>");
      continue;
    }

    const bullet = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      flushQuote();
      if (list !== "ul") {
        flushList();
        html.push("<ul>");
        list = "ul";
      }
      html.push(`<li>${inline(bullet[1])}</li>`);
      continue;
    }

    const numbered = trimmed.match(/^\d+[.)]\s+(.*)$/);
    if (numbered) {
      flushParagraph();
      flushQuote();
      if (list !== "ol") {
        flushList();
        html.push("<ol>");
        list = "ol";
      }
      html.push(`<li>${inline(numbered[1])}</li>`);
      continue;
    }

    if (trimmed.startsWith("&gt;")) {
      flushParagraph();
      flushList();
      quote.push(trimmed.replace(/^&gt;\s?/, ""));
      continue;
    }

    flushQuote();
    flushList();
    paragraph.push(line);
  }

  flushAll();
  return html.join("").replace(/\u0000(\d+)\u0000/g, (_m, index) =>
    `<pre><code>${codeBlocks[Number(index)] || ""}</code></pre>`
  );
}

/* -------------------------------------------------------------------------- */
/* rendering                                                                  */
/* -------------------------------------------------------------------------- */
function scrollToEnd(force = false) {
  requestAnimationFrame(() => {
    const nearBottom =
      chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight < 160;
    if (force || nearBottom) chatEl.scrollTop = chatEl.scrollHeight;
  });
}

function setStatus(text) {
  taglineEl.textContent = text || t("tagline");
}

function createBubble(role, text, { pending = false, error = false } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role === "user" ? "user" : "bot"}${error ? " error" : ""}`;

  const who = document.createElement("div");
  who.className = "who";
  const nameSpan = document.createElement("span");
  nameSpan.textContent = role === "user" ? t("you") : t("assistant");
  who.appendChild(nameSpan);

  const copyBtn = document.createElement("button");
  copyBtn.className = "copy";
  copyBtn.type = "button";
  copyBtn.textContent = t("copy");
  who.appendChild(copyBtn);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const body = document.createElement("div");
  bubble.appendChild(body);

  wrap.appendChild(who);
  wrap.appendChild(bubble);
  chatEl.appendChild(wrap);

  const record = {
    role,
    el: wrap,
    body,
    nameSpan,
    copyBtn,
    raw: text,
    setRaw(next) {
      this.raw = next;
      body.innerHTML = formatRich(next);
    },
    setStreaming(next) {
      this.raw = next;
      body.textContent = next;
      const caret = document.createElement("span");
      caret.className = "caret";
      body.appendChild(caret);
    },
    setPending() {
      body.innerHTML = '<span class="dots"><span></span><span></span><span></span></span>';
    },
    setError(message) {
      this.raw = message;
      body.innerHTML = formatRich(message);
    },
    retranslate() {
      nameSpan.textContent = role === "user" ? t("you") : t("assistant");
      copyBtn.textContent = t("copy");
    },
  };

  copyBtn.addEventListener("click", () => {
    copyText(record.raw || "");
    copyBtn.textContent = t("copied");
    setTimeout(() => (copyBtn.textContent = t("copy")), 1200);
  });

  if (pending) record.setPending();
  else record.setRaw(text);

  state.bubbles.push(record);
  return record;
}

function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  try { document.execCommand("copy"); } catch (_) { /* ignore */ }
  area.remove();
}

function renderWelcome() {
  $("welcomeTitle").textContent = t("welcomeTitle");
  $("welcomeSub").textContent = t("welcomeSub");
  const splashTag = $("splashTag");
  if (splashTag) splashTag.textContent = t("tagline");

  const connectWrap = $("connectWrap");
  connectWrap.innerHTML = "";
  if (!apiKey()) {
    const connect = document.createElement("button");
    connect.type = "button";
    connect.className = "connect";
    connect.textContent = t("connectGroq");
    connect.addEventListener("click", () => openSettings());
    connectWrap.appendChild(connect);
  }

  const chips = $("chips");
  chips.innerHTML = "";
  t("suggestions").forEach((text) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.textContent = text;
    chip.addEventListener("click", () => {
      inputEl.value = text;
      autoResize();
      send();
    });
    chips.appendChild(chip);
  });

  welcomeEl.style.display = "";
  document.body.classList.remove("chatting");
}

function hideWelcome() {
  welcomeEl.style.display = "none";
  document.body.classList.add("chatting");
}

function showWelcome() {
  welcomeEl.style.display = "";
  document.body.classList.remove("chatting");
}

function rerenderWelcome() {
  const chatting = state.bubbles.length > 0;
  renderWelcome();
  if (chatting) hideWelcome();
}

/* -------------------------------------------------------------------------- */
/* theme + language + model                                                   */
/* -------------------------------------------------------------------------- */
function applyTheme() {
  document.documentElement.dataset.theme = state.theme;
  store.set("gc_theme", state.theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", state.theme === "dark" ? "#0b0f16" : "#eef3fa");
  refreshThemeButtons();
  refreshStats();
}

function refreshThemeButtons() {
  $("themeDark").classList.toggle("on", state.theme === "dark");
  $("themeLight").classList.toggle("on", state.theme === "light");
  $("themeDark").setAttribute("aria-pressed", String(state.theme === "dark"));
  $("themeLight").setAttribute("aria-pressed", String(state.theme === "light"));
  $("langEn").classList.toggle("on", state.lang === "en");
  $("langBn").classList.toggle("on", state.lang === "bn");
  $("langEn").setAttribute("aria-pressed", String(state.lang === "en"));
  $("langBn").setAttribute("aria-pressed", String(state.lang === "bn"));
}

function setTheme(theme) {
  if (!["dark", "light"].includes(theme) || theme === state.theme) return;
  state.theme = theme;
  applyTheme();
}

function toggleTheme() {
  setTheme(state.theme === "dark" ? "light" : "dark");
}

function setLanguage(lang) {
  if (!STRINGS[lang] || lang === state.lang) return;
  state.lang = lang;
  store.set("gc_lang", lang);
  applyLanguage();
}

function refreshModelSelect() {
  modelSel.innerHTML = "";
  MODELS.forEach((model) => {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = `${model.name} · ${t("model" + model.tag[0].toUpperCase() + model.tag.slice(1))}`;
    modelSel.appendChild(option);
  });
  modelSel.value = state.model;
}

function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.title = t("appTitle");
  $("appTitle").textContent = t("appTitle");
  if (!state.busy) setStatus(t("tagline"));
  const splashTag = $("splashTag");
  if (splashTag) splashTag.textContent = t("tagline");
  inputEl.placeholder = t("placeholder");
  $("menuBtn").setAttribute("aria-label", t("menu"));
  $("newBtn").setAttribute("aria-label", t("newChat"));
  $("newBtn").title = t("newChat");
  $("drawerSub").textContent = t("dashboard");
  $("drawerStatsLabel").textContent = t("atAGlance");
  $("drawerActionsLabel").textContent = t("quickActions");
  $("drawerSystemLabel").textContent = t("system");
  $("statMessagesLabel").textContent = t("statMessages");
  $("statModelLabel").textContent = t("statModel");
  $("statLangLabel").textContent = t("statLang");
  $("statThemeLabel").textContent = t("statTheme");
  $("drawerNewText").textContent = t("newChat");
  $("drawerLangText").textContent = state.lang === "en" ? t("toBengali") : t("toEnglish");
  $("drawerClearText").textContent = t("clearHistory");
  $("drawerSettingsText").textContent = t("settingsAction");
  $("sysHistory").textContent = t("sysHistory");
  $("sysStreaming").textContent = t("sysStreaming");
  $("drawerVersion").textContent = `GroqChatbot ${APP_VERSION}`;
  $("modalTitle").textContent = t("settingsTitle");
  $("modelLabel").textContent = t("modelLabel");
  $("modelHint").textContent = t("modelHint");
  $("appearanceLabel").textContent = t("appearance");
  $("languageLabel").textContent = t("languageLabel");
  $("privacyNote").textContent = t("privacy");
  $("aboutLine").textContent = t("aboutLine");
  $("themeDark").textContent = t("themeDark");
  $("themeLight").textContent = t("themeLight");
  $("langEn").textContent = t("english");
  $("langBn").textContent = t("bengali");
  $("modalClose").setAttribute("aria-label", t("close"));
  $("keyLink").textContent = t("keyGet");
  $("removeBtn").textContent = t("keyRemove");
  $("revealBtn").textContent =
    $("keyInput").type === "password" ? t("keyShow") : t("keyHide");

  refreshModelSelect();
  state.bubbles.forEach((bubble) => bubble.retranslate());
  rerenderWelcome();
  refreshThemeButtons();
  refreshKeyUi();
  refreshSendButton();
  refreshStats();
}

$("menuBtn").addEventListener("click", openDrawer);
$("drawerClose").addEventListener("click", closeDrawer);
$("newBtn").addEventListener("click", newChat);

modelSel.addEventListener("change", () => {
  state.model = modelSel.value;
  store.set("gc_model", state.model);
  refreshStats();
});

/* -------------------------------------------------------------------------- */
/* drawer                                                                      */
/* -------------------------------------------------------------------------- */
function openDrawer() {
  closeSettings();
  refreshStats();
  $("drawer").classList.add("open");
  $("drawer").setAttribute("aria-hidden", "false");
  $("scrim").classList.remove("hidden");
}

function closeDrawer() {
  $("drawer").classList.remove("open");
  $("drawer").setAttribute("aria-hidden", "true");
  $("scrim").classList.add("hidden");
}

$("scrim").addEventListener("click", closeDrawer);
$("drawerTheme").addEventListener("click", toggleTheme);
$("drawerLang").addEventListener("click", () => setLanguage(state.lang === "en" ? "bn" : "en"));
$("drawerSettings").addEventListener("click", () => openSettings());
$("drawerNew").addEventListener("click", () => { closeDrawer(); newChat(); });
$("drawerClear").addEventListener("click", () => { closeDrawer(); clearHistory(); });

/* -------------------------------------------------------------------------- */
/* composer                                                                    */
/* -------------------------------------------------------------------------- */
function autoResize() {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 128) + "px";
}

function refreshSendButton() {
  document.body.classList.toggle("busy", state.busy);
  if (state.busy) {
    sendBtn.className = "stop";
    sendBtn.innerHTML = ICON_STOP;
    sendBtn.disabled = false;
    sendBtn.setAttribute("aria-label", t("stop"));
  } else {
    sendBtn.className = "";
    sendBtn.innerHTML = ICON_ARROW;
    sendBtn.disabled = !inputEl.value.trim();
    sendBtn.setAttribute("aria-label", t("send"));
  }
}

inputEl.addEventListener("input", () => {
  autoResize();
  refreshSendButton();
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  if (!state.busy) send();
});

sendBtn.addEventListener("click", () => {
  if (state.busy) stopStreaming();
  else send();
});

/* -------------------------------------------------------------------------- */
/* send + stream                                                               */
/* -------------------------------------------------------------------------- */
async function send() {
  const text = inputEl.value.trim();
  if (!text || state.busy) return;

  if (!apiKey()) {
    openSettings(t("keyMissing"));
    return;
  }

  hideWelcome();
  state.messages.push({ role: "user", content: text });
  createBubble("user", text);
  saveChat();
  refreshStats();

  inputEl.value = "";
  autoResize();

  const bubble = createBubble("assistant", "", { pending: true });
  state.busy = true;
  refreshSendButton();
  setStatus(t("thinking"));
  scrollToEnd(true);

  state.controller = new AbortController();
  const controller = state.controller;
  let full = "";
  let sawContent = false;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey()}`,
      },
      body: JSON.stringify({
        model: state.model,
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...state.messages.slice(-40)],
        temperature: 0.7,
        max_tokens: 2048,
        stream: true,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const raw = await response.text();
      if (response.status === 401 || response.status === 403) throw new Error(t("keyInvalid"));
      if (response.status === 429) throw new Error(t("rateLimit"));
      let detail = raw.slice(0, 300);
      try {
        const parsed = JSON.parse(raw);
        detail = parsed?.error?.message || detail;
      } catch (_) { /* plain text error */ }
      throw new Error(detail || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() || "";

      for (const event of events) {
        for (const line of event.split(/\r?\n/)) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            const json = JSON.parse(payload);
            const delta = json.choices?.[0]?.delta?.content || "";
            if (delta) {
              if (!sawContent) {
                sawContent = true;
                setStatus(t("streaming"));
              }
              full += delta;
              bubble.setStreaming(full);
              scrollToEnd();
            }
          } catch (_) { /* partial JSON — wait for the next chunk */ }
        }
      }
    }

    const finalText = full.trim();
    state.messages.push({ role: "assistant", content: finalText || t("stopped") });
    bubble.setRaw(finalText || t("stopped"));
    saveChat();
  } catch (error) {
    if (error.name === "AbortError") {
      const partial = full.trim();
      state.messages.push({ role: "assistant", content: partial || t("stopped") });
      bubble.setRaw(partial || t("stopped"));
      saveChat();
    } else {
      const message = error.message || t("netError");
      bubble.el.classList.add("error");
      bubble.setError(message);
      if (message === t("keyInvalid")) openSettings(t("keyInvalid2"));
      else if (!navigator.onLine) bubble.setError(t("netError"));
    }
  } finally {
    if (state.controller === controller) state.controller = null;
    state.busy = false;
    refreshSendButton();
    setStatus(t("tagline"));
    refreshStats();
    scrollToEnd();
    if (state.bubbles.length) hideWelcome();
  }
}

function stopStreaming() {
  if (state.controller) state.controller.abort();
}

/* -------------------------------------------------------------------------- */
/* persistence + stats                                                        */
/* -------------------------------------------------------------------------- */
function saveChat() {
  store.set("gc_chat", JSON.stringify(state.messages.slice(-60)));
}

function restoreChat() {
  let saved = [];
  try {
    saved = JSON.parse(store.get("gc_chat", "[]"));
  } catch (_) {
    saved = [];
  }
  if (!Array.isArray(saved) || !saved.length) return;
  state.messages = saved.filter(
    (message) =>
      message &&
      typeof message.content === "string" &&
      (message.role === "user" || message.role === "assistant")
  );
  if (!state.messages.length) return;
  hideWelcome();
  state.messages.forEach((message) => createBubble(message.role, message.content));
  scrollToEnd(true);
}

function refreshStats() {
  $("statMessages").textContent = String(state.messages.length);
  const model = MODELS.find((item) => item.id === state.model) || MODELS[0];
  $("statModel").textContent = model.name;
  $("statLang").textContent = state.lang === "en" ? "EN" : "বাংলা";
  $("statTheme").textContent = t(state.theme === "dark" ? "themeDark" : "themeLight");
  $("drawerThemeText").textContent =
    state.theme === "dark" ? t("switchLight") : t("switchDark");
  if (state.theme === "dark") $("drawerTheme").querySelector(".drawerActionIcon").textContent = "🌙";
  else $("drawerTheme").querySelector(".drawerActionIcon").textContent = "☀️";
}

function newChat() {
  if (state.busy) return;
  state.messages = [];
  state.bubbles = [];
  [...chatEl.querySelectorAll(".msg")].forEach((node) => node.remove());
  store.remove("gc_chat");
  renderWelcome();
  refreshSendButton();
  refreshStats();
  inputEl.focus();
}

function clearHistory() {
  if (state.busy) return;
  if (!window.confirm(t("clearAsk"))) return;
  newChat();
  toast(t("historyCleared"));
}

/* -------------------------------------------------------------------------- */
/* settings — guided Groq API key setup                                       */
/* -------------------------------------------------------------------------- */
const KEY_PATTERN = /^gsk_[A-Za-z0-9_-]{20,}$/;

function cleanKey(raw) {
  return String(raw || "")
    .trim()
    .replace(/^export\s+/i, "")
    .replace(/^GROQ_API_KEY\s*=\s*/i, "")
    .replace(/^Bearer\s+/i, "")
    .replace(/^["'`]|["'`]$/g, "")
    .trim();
}

function maskKey(key) {
  if (!key) return "";
  if (key.length <= 12) return key.slice(0, 3) + "…";
  return key.slice(0, 6) + "…" + key.slice(-4);
}

let keyBusy = false;
let toastTimer = 0;

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add("hidden"), 2800);
}

function setKeyError(message) {
  const el = $("keyError");
  el.textContent = message || "";
  el.classList.toggle("hidden", !message);
}

function refreshKeyUi() {
  const key = apiKey();
  const has = Boolean(key);
  const label = has ? t("keySet") : t("keyNotSet");
  $("keyBtn").classList.toggle("needs-key", !has);
  $("keyBtn").setAttribute("aria-label", has ? t("settingsTitle") : label);
  $("keyBtn").title = has ? t("settingsTitle") : label;

  $("sysKey").textContent = has ? t("sysKeyOn") : t("sysKeyOff");
  $("sysKeyDot").classList.toggle("ok", has);

  const meta = $("keyMeta");
  meta.textContent = has ? t("keyCurrent").replace("{key}", maskKey(key)) : "";
  meta.classList.toggle("hidden", !has);

  $("keySteps").classList.toggle("hidden", has);
  $("keyLink").classList.toggle("hidden", has);
  $("removeBtn").classList.toggle("hidden", !has);
}

function openSettings(errorMessage) {
  closeDrawer();
  keyBusy = false;
  const has = Boolean(apiKey());

  $("modalTitle").textContent = t("settingsTitle");
  $("modalBody").textContent = t(has ? "keyBodyExisting" : "keyBodyNew");
  $("step1").textContent = t("keyStep1");
  $("step2").textContent = t("keyStep2");
  $("step3").textContent = t("keyStep3");
  $("keyLink").textContent = t("keyGet");
  $("modalSave").textContent = t("keySave");
  $("modalSave").disabled = false;
  $("removeBtn").textContent = t("keyRemove");
  $("modalClose").setAttribute("aria-label", t("close"));
  $("revealBtn").textContent = t("keyShow");
  $("keyInput").type = "password";
  $("keyInput").value = apiKey();

  refreshModelSelect();
  refreshThemeButtons();
  setKeyError(errorMessage || "");
  refreshKeyUi();

  $("modal").classList.remove("hidden");
  if (!has) setTimeout(() => $("keyInput").focus(), 140);
}

function closeSettings() {
  $("modal").classList.add("hidden");
}

function toggleReveal() {
  const input = $("keyInput");
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  $("revealBtn").textContent = show ? t("keyHide") : t("keyShow");
}

async function testKey(key) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(MODELS_URL, {
      headers: { Authorization: `Bearer ${key}` },
      signal: controller.signal,
    });
    if (response.status === 401 || response.status === 403) {
      return { ok: false, reason: "invalid" };
    }
    if (!response.ok) return { ok: false, reason: "unverified" };
    return { ok: true };
  } catch (_) {
    return { ok: false, reason: "unverified" };
  } finally {
    clearTimeout(timer);
  }
}

function storeKey(key) {
  store.set("gc_key", key);
  $("keyInput").value = key;
  refreshKeyUi();
  rerenderWelcome();
  refreshSendButton();
  refreshStats();
}

async function saveKey() {
  if (keyBusy) return;

  const key = cleanKey($("keyInput").value);
  if (!key) {
    setKeyError(t("keyEmpty"));
    $("keyInput").focus();
    return;
  }
  if (!KEY_PATTERN.test(key)) {
    setKeyError(t("keyBadFormat"));
    $("keyInput").focus();
    return;
  }

  keyBusy = true;
  setKeyError("");
  const saveBtn = $("modalSave");
  saveBtn.disabled = true;
  saveBtn.textContent = t("keyTesting");

  const result = await testKey(key);

  keyBusy = false;
  saveBtn.disabled = false;
  saveBtn.textContent = t("keySave");

  if (result.ok) {
    storeKey(key);
    closeSettings();
    toast(t("keyOk"));
  } else if (result.reason === "invalid") {
    setKeyError(t("keyInvalid2"));
  } else {
    storeKey(key);
    closeSettings();
    toast(t("keySavedOffline"));
  }
}

function removeKey() {
  if (!apiKey()) return;
  if (!window.confirm(t("keyRemoveAsk"))) return;
  store.remove("gc_key");
  $("keyInput").value = "";
  setKeyError("");
  closeSettings();
  refreshKeyUi();
  rerenderWelcome();
  refreshSendButton();
  refreshStats();
  toast(t("keyRemoved"));
}

$("keyBtn").addEventListener("click", () => openSettings());
$("modalSave").addEventListener("click", saveKey);
$("modalClose").addEventListener("click", closeSettings);
$("revealBtn").addEventListener("click", toggleReveal);
$("removeBtn").addEventListener("click", removeKey);

$("keyInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    saveKey();
  }
});

$("modal").addEventListener("click", (event) => {
  if (event.target === $("modal")) closeSettings();
});

$("themeDark").addEventListener("click", () => setTheme("dark"));
$("themeLight").addEventListener("click", () => setTheme("light"));
$("langEn").addEventListener("click", () => setLanguage("en"));
$("langBn").addEventListener("click", () => setLanguage("bn"));

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (!$("modal").classList.contains("hidden")) closeSettings();
  else if ($("drawer").classList.contains("open")) closeDrawer();
});

/* -------------------------------------------------------------------------- */
/* boot                                                                       */
/* -------------------------------------------------------------------------- */
function hideSplash() {
  if (!splashEl) return;
  splashEl.classList.add("hide");
  setTimeout(() => splashEl.remove(), 500);
}

function boot() {
  applyTheme();
  applyLanguage();
  restoreChat();
  autoResize();
  refreshSendButton();
  refreshStats();

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", () => {
      autoResize();
      scrollToEnd();
    });
  }

  setTimeout(hideSplash, 850);

  if (!apiKey()) {
    setTimeout(() => openSettings(), 1150);
  }
}

boot();
