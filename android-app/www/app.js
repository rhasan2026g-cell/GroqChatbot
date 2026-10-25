/* Groq Chat — mobile client (English / বাংলা) */

const API_URL = "https://api.groq.com/openai/v1/chat/completions";

const SYSTEM_PROMPT =
  "You are a helpful, friendly assistant inside a mobile chat app. " +
  "Always answer in the same language the user writes in: if they write in Bengali (বাংলা), " +
  "answer in natural Bengali; if they write in English, answer in English. Match their script " +
  "and tone. Keep answers clear and concise, use short paragraphs, and wrap code in triple backticks.";

const MODELS = [
  { id: "openai/gpt-oss-20b", name: "GPT-OSS 20B", tag: "fast" },
  { id: "openai/gpt-oss-120b", name: "GPT-OSS 120B", tag: "smart" },
  { id: "qwen/qwen3.8-27b", name: "Qwen 3.8 27B", tag: "fastest" },
];

const STRINGS = {
  en: {
    appTitle: "Groq Chat",
    tagline: "Fast, friendly AI chat",
    welcomeTitle: "How can I help you today?",
    welcomeSub: "Ask anything — in English or বাংলা.",
    placeholder: "Message Groq Chat…",
    send: "Send",
    stop: "Stop",
    stopped: "(stopped)",
    you: "You",
    assistant: "Assistant",
    copy: "Copy",
    copied: "Copied",
    newChat: "New chat",
    thinking: "Thinking",
    suggestions: [
      "Explain quantum computing",
      "Write a poem in বাংলা",
      "Python loop example",
    ],
    modelFast: "fast",
    modelSmart: "smart",
    modelFastest: "fastest",
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
    appTitle: "গ্রক চ্যাট",
    tagline: "দ্রুত ও সহজ এআই চ্যাট",
    welcomeTitle: "আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
    welcomeSub: "ইংরেজি বা বাংলায় যেকোনো কিছু জিজ্ঞাসা করুন।",
    placeholder: "গ্রক চ্যাটকে কিছু লিখুন…",
    send: "পাঠান",
    stop: "থামান",
    stopped: "(থামানো হয়েছে)",
    you: "আপনি",
    assistant: "সহকারী",
    copy: "কপি",
    copied: "কপি হয়েছে",
    newChat: "নতুন চ্যাট",
    thinking: "ভাবছি",
    suggestions: [
      "কোয়ান্টাম কম্পিউটিং কী?",
      "বাংলায় কবিতা লেখো",
      "পাইথন লুপ শেখাও",
    ],
    modelFast: "দ্রুত",
    modelSmart: "স্মার্ট",
    modelFastest: "সবচেয়ে দ্রুত",
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

const $ = (id) => document.getElementById(id);
const chatEl = $("chat");
const welcomeEl = $("welcome");
const inputEl = $("input");
const sendBtn = $("sendBtn");
const modelSel = $("model");
const langBtn = $("langBtn");
const newBtn = $("newBtn");
const keyBtn = $("keyBtn");
const topbar = $("topbar");
const taglineEl = $("tagline");

const state = {
  lang: localStorage.getItem("gc_lang") || "en",
  model: localStorage.getItem("gc_model") || MODELS[0].id,
  messages: [],
  bubbles: [],
  busy: false,
  controller: null,
};

if (!STRINGS[state.lang]) state.lang = "en";
const t = (key) => STRINGS[state.lang][key];
const apiKey = () => localStorage.getItem("gc_key") || "";

/* ------------------------------------------------------------------ */
/* text formatting                                                     */
/* ------------------------------------------------------------------ */
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatRich(text) {
  const blocks = [];
  let out = text.replace(/```[a-zA-Z0-9_+\-.#]*\n?([\s\S]*?)```/g, (_m, code) => {
    blocks.push(escapeHtml(code.replace(/\n$/, "")));
    return `\u0000${blocks.length - 1}\u0000`;
  });
  out = escapeHtml(out);
  out = out.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  out = out.replace(/`([^`\n]+)`/g, "<code>$1</code>");
  out = out.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>'
  );
  out = out.replace(/\n/g, "<br>");
  out = out.replace(/\u0000(\d+)\u0000/g, (_m, i) => `<pre><code>${blocks[+i]}</code></pre>`);
  return out;
}

/* ------------------------------------------------------------------ */
/* rendering                                                           */
/* ------------------------------------------------------------------ */
function scrollToEnd() {
  requestAnimationFrame(() => {
    chatEl.scrollTop = chatEl.scrollHeight;
  });
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
      body.appendChild(makeCaret());
    },
    setPending() {
      body.innerHTML = '<span class="dots"><span></span><span></span><span></span></span>';
    },
    setError(msg) {
      this.raw = msg;
      body.innerHTML = formatRich(msg);
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

  if (pending) {
    record.setPending();
  } else {
    record.setRaw(text);
  }

  state.bubbles.push(record);
  return record;
}

function makeCaret() {
  const span = document.createElement("span");
  span.style.color = "#4c8dff";
  span.textContent = "▌";
  return span;
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
  try { document.execCommand("copy"); } catch (_) {}
  area.remove();
}

function renderWelcome() {
  welcomeEl.innerHTML = "";
  const h = document.createElement("h2");
  h.textContent = t("welcomeTitle");
  const p = document.createElement("p");
  p.textContent = t("welcomeSub");
  welcomeEl.append(h, p);

  // One-tap setup straight from the welcome screen when no key is saved.
  if (!apiKey()) {
    const connect = document.createElement("button");
    connect.type = "button";
    connect.className = "connect";
    connect.textContent = t("connectGroq");
    connect.addEventListener("click", () => openSettings());
    welcomeEl.appendChild(connect);
  }

  const chips = document.createElement("div");
  chips.id = "chips";
  t("suggestions").forEach((text) => {
    const b = document.createElement("button");
    b.textContent = text;
    b.addEventListener("click", () => {
      inputEl.value = text;
      autoResize();
      send();
    });
    chips.appendChild(b);
  });
  welcomeEl.appendChild(chips);
  welcomeEl.style.display = "";
  document.body.classList.remove("chatting");
}

function rerenderWelcome() {
  const chatting = state.bubbles.length > 0;
  renderWelcome();
  if (chatting) hideWelcome();
}

function hideWelcome() {
  welcomeEl.style.display = "none";
  document.body.classList.add("chatting");
}

/* ------------------------------------------------------------------ */
/* language + model                                                    */
/* ------------------------------------------------------------------ */
function applyLanguage() {
  document.documentElement.lang = state.lang;
  $("appTitle").textContent = t("appTitle");
  taglineEl.textContent = t("tagline");
  inputEl.placeholder = t("placeholder");
  langBtn.textContent = state.lang === "en" ? "বাংলা" : "English";
  newBtn.title = t("newChat");
  modelSel.setAttribute("aria-label", "Model");
  document.title = t("appTitle");

  const current = state.model;
  modelSel.innerHTML = "";
  MODELS.forEach((m) => {
    const option = document.createElement("option");
    option.value = m.id;
    option.textContent = `${m.name} · ${t("model" + m.tag[0].toUpperCase() + m.tag.slice(1))}`;
    modelSel.appendChild(option);
  });
  modelSel.value = current;

  state.bubbles.forEach((b) => b.retranslate());
  rerenderWelcome();
  refreshSendButton();
  refreshKeyUi();
}

langBtn.addEventListener("click", () => {
  state.lang = state.lang === "en" ? "bn" : "en";
  localStorage.setItem("gc_lang", state.lang);
  applyLanguage();
});

modelSel.addEventListener("change", () => {
  state.model = modelSel.value;
  localStorage.setItem("gc_model", state.model);
});

/* ------------------------------------------------------------------ */
/* composer                                                            */
/* ------------------------------------------------------------------ */
function autoResize() {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
}

function refreshSendButton() {
  if (state.busy) {
    sendBtn.textContent = "■";
    sendBtn.classList.add("stop");
    sendBtn.disabled = false;
    sendBtn.setAttribute("aria-label", t("stop"));
  } else {
    sendBtn.textContent = "↑";
    sendBtn.classList.remove("stop");
    sendBtn.disabled = !inputEl.value.trim();
    sendBtn.setAttribute("aria-label", t("send"));
  }
}

inputEl.addEventListener("input", () => {
  autoResize();
  refreshSendButton();
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) return;
  // On a touch keyboard Enter must insert a newline; the round button sends.
  if (window.matchMedia("(pointer: coarse)").matches) return;
  event.preventDefault();
  if (!state.busy) send();
});

sendBtn.addEventListener("click", () => {
  if (state.busy) stopStreaming();
  else send();
});

/* ------------------------------------------------------------------ */
/* send + stream                                                       */
/* ------------------------------------------------------------------ */
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

  inputEl.value = "";
  autoResize();

  const bubble = createBubble("assistant", "", { pending: true });
  state.busy = true;
  refreshSendButton();
  scrollToEnd();

  state.controller = new AbortController();
  let full = "";

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
      signal: state.controller.signal,
    });

    if (!response.ok) {
      const raw = await response.text();
      if (response.status === 401) throw new Error(t("keyInvalid"));
      if (response.status === 429) throw new Error(t("rateLimit"));
      throw new Error(raw.slice(0, 300) || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const evt of events) {
        for (const line of evt.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            const json = JSON.parse(payload);
            const delta = json.choices?.[0]?.delta?.content || "";
            if (delta) {
              full += delta;
              bubble.setStreaming(full);
              scrollToEnd();
            }
          } catch (_) { /* partial json, ignore */ }
        }
      }
    }

    const finalText = full.trim();
    state.messages.push({ role: "assistant", content: finalText || t("stopped") });
    bubble.setRaw(finalText || t("stopped"));
    saveChat();
  } catch (err) {
    if (err.name === "AbortError") {
      const partial = full.trim();
      state.messages.push({ role: "assistant", content: partial || t("stopped") });
      bubble.setRaw(partial || t("stopped"));
      saveChat();
    } else {
      const message = err.message || t("netError");
      bubble.el.classList.add("error");
      bubble.setError(message);
      if (message === t("keyInvalid")) openSettings(t("keyInvalid2"));
    }
  } finally {
    state.busy = false;
    state.controller = null;
    refreshSendButton();
    scrollToEnd();
    if (state.bubbles.length) hideWelcome();
  }
}

function stopStreaming() {
  if (state.controller) state.controller.abort();
}

/* ------------------------------------------------------------------ */
/* persistence                                                         */
/* ------------------------------------------------------------------ */
function saveChat() {
  try {
    localStorage.setItem("gc_chat", JSON.stringify(state.messages.slice(-60)));
  } catch (_) { /* quota — ignore */ }
}

function restoreChat() {
  let saved = [];
  try {
    saved = JSON.parse(localStorage.getItem("gc_chat") || "[]");
  } catch (_) {
    saved = [];
  }
  if (!Array.isArray(saved) || !saved.length) return;
  state.messages = saved.filter(
    (m) => m && typeof m.content === "string" && (m.role === "user" || m.role === "assistant")
  );
  if (!state.messages.length) return;
  hideWelcome();
  state.messages.forEach((m) => createBubble(m.role, m.content));
  scrollToEnd();
}

/* ------------------------------------------------------------------ */
/* new chat                                                            */
/* ------------------------------------------------------------------ */
newBtn.addEventListener("click", () => {
  if (state.busy) return;
  state.messages = [];
  state.bubbles = [];
  [...chatEl.querySelectorAll(".msg")].forEach((n) => n.remove());
  localStorage.removeItem("gc_chat");
  renderWelcome();
  refreshSendButton();
});

/* ------------------------------------------------------------------ */
/* settings — guided Groq API key setup                                */
/* ------------------------------------------------------------------ */
const KEY_PATTERN = /^gsk_[A-Za-z0-9_-]{20,}$/;
const MODELS_URL = "https://api.groq.com/openai/v1/models";

// Accept a bare key, "GROQ_API_KEY=…", "export GROQ_API_KEY=…", "Bearer …" or a quoted value.
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
  return key.slice(0, 4) + "…" + key.slice(-4);
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
  const has = !!key;
  const label = has ? t("keySet") : t("keyNotSet");
  keyBtn.classList.toggle("needs-key", !has);
  keyBtn.setAttribute("aria-label", label);
  keyBtn.title = label;

  const meta = $("keyMeta");
  meta.textContent = has ? t("keyCurrent").replace("{key}", maskKey(key)) : "";
  meta.classList.toggle("hidden", !has);

  $("keySteps").classList.toggle("hidden", has);
  $("keyLink").classList.toggle("hidden", has);
  $("removeBtn").classList.toggle("hidden", !has);
}

function openSettings(errorMessage) {
  keyBusy = false;
  const has = !!apiKey();

  $("modalTitle").textContent = t(has ? "keyTitleExisting" : "keyTitleNew");
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

  setKeyError(errorMessage || "");
  refreshKeyUi();

  $("modal").classList.remove("hidden");

  // Auto-focus only when the user actually needs to type something.
  if (!has) setTimeout(() => $("keyInput").focus(), 120);
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

// Ask Groq whether the key works. Offline/timeout is not a rejection.
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
  } catch (err) {
    return { ok: false, reason: "unverified" };
  } finally {
    clearTimeout(timer);
  }
}

function storeKey(key) {
  localStorage.setItem("gc_key", key);
  $("keyInput").value = key;
  refreshKeyUi();
  rerenderWelcome();
  refreshSendButton();
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
    // Do not overwrite a working key with a rejected one.
    setKeyError(t("keyInvalid2"));
  } else {
    // Can't verify right now (offline / Groq hiccup) — keep it and say so.
    storeKey(key);
    closeSettings();
    toast(t("keySavedOffline"));
  }
}

function removeKey() {
  if (!apiKey()) return;
  if (!window.confirm(t("keyRemoveAsk"))) return;
  localStorage.removeItem("gc_key");
  $("keyInput").value = "";
  setKeyError("");
  closeSettings();
  refreshKeyUi();
  rerenderWelcome();
  refreshSendButton();
  toast(t("keyRemoved"));
}

keyBtn.addEventListener("click", () => openSettings());
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

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("modal").classList.contains("hidden")) closeSettings();
});

/* ------------------------------------------------------------------ */
/* boot                                                                */
/* ------------------------------------------------------------------ */
function boot() {
  state.model = localStorage.getItem("gc_model") || MODELS[0].id;
  applyLanguage();
  restoreChat();
  autoResize();
  refreshSendButton();

  // Keep the newest message visible when the on-screen keyboard opens.
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", () => {
      autoResize();
      scrollToEnd();
    });
  }

  if (!apiKey()) {
    setTimeout(() => openSettings(), 350);
  }
  refreshKeyUi();
}

boot();
