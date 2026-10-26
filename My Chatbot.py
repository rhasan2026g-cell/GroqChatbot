"""
GroqChatbot — a bilingual (English / বাংলা) local-first AI agent.

Run with:
    python "My Chatbot.py"

Highlights
----------
* Groq LPU streaming chat (GPT-OSS 20B / 120B, Qwen)
* Long-term SQLite memory with optional sqlite-vec semantic recall
* Document RAG for PDF, DOCX, TXT, MD, HTML, CSV, JSON, XLSX and source code
* Real tool calling: web search, page reader, calculator, files, Python, weather
* Image / illustration / music / video studio with several providers
* Live database browser, tool workbench and a system dashboard
* English and বাংলা interface, dark and light themes
"""

from __future__ import annotations

import html as html_module
import json
import os
import re
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from PySide6.QtCore import QEvent, QSettings, Qt, QThread, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QFont,
    QFontDatabase,
    QKeySequence,
    QPixmap,
    QShortcut,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplashScreen,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from agent_tools import ToolRegistry
from app_paths import BASE_DIR, DATA_DIR, GENERATED_DIR, readable_size
from generation import GenerationEngine
from memory_system import MemorySystem
from rag_system import RAGSystem
from ui_dialogs import (
    AboutDialog,
    DatabaseDialog,
    GenerateDialog,
    SettingsDialog,
    ToolsDialog,
)
from ui_theme import (
    APP_TAGLINE,
    APP_VERSION,
    build_stylesheet,
    make_app_icon,
    make_logo,
    make_qt_palette,
    make_splash_pixmap,
    palette as make_palette,
)
from ui_widgets import Badge, MiniChart, StatCard

APP_NAME = "GroqChatbot"
ORG_NAME = "GroqChatbot"

MODELS = [
    ("openai/gpt-oss-20b", "GPT-OSS 20B", "fast"),
    ("openai/gpt-oss-120b", "GPT-OSS 120B", "smart"),
    ("qwen/qwen3.8-27b", "Qwen 3.8 27B", "fastest"),
]
DEFAULT_MODEL = MODELS[0][0]

DEFAULT_SYSTEM_PROMPT = (
    "You are GroqChatbot, a brilliant, warm and practical AI agent running on the "
    "user's own computer. Always answer in the same language the user writes in: "
    "natural Bengali (বাংলা) for Bengali messages, English for English messages. "
    "Match their script, tone and level of formality.\n\n"
    "You can remember facts about the user, read their uploaded documents and use "
    "tools (web search, web pages, calculator, files, Python, weather, time). Use a "
    "tool whenever it makes the answer more accurate, and never invent tool results. "
    "If a tool fails, say what failed and continue with what you know.\n\n"
    "Answer with clear structure: a direct answer first, then the details. Use short "
    "paragraphs, bullet points and fenced code blocks with a language tag. Be honest "
    "about uncertainty, and ask one focused question when the request is ambiguous. "
    "For arithmetic and simple maths write plain readable text with Unicode symbols "
    "(×, ÷, ², √, ≈) instead of LaTeX; only use LaTeX when the user asks for it."
)

TOOL_GUIDANCE = (
    "\n\nAgent context:\n{context}\n\n"
    "Use the provided tools when needed. Today is {today}."
)

STRINGS = {
    "en": {
        "app_title": "GroqChatbot",
        "tagline": "Local-first AI agent · memory · RAG · studio",
        "model_fast": "fast",
        "model_smart": "smart",
        "model_fastest": "fastest",
        "lang_button": "বাংলা",
        "new_chat": "New chat",
        "settings": "Settings",
        "theme": "Toggle theme",
        "sidebar": "Dashboard",
        "copy": "Copy",
        "copied": "Copied",
        "regenerate": "Regenerate",
        "stop": "Stop",
        "send": "Send",
        "attach": "Add document",
        "tools": "Tools",
        "generate": "Create",
        "clear": "Clear chat",
        "export": "Export",
        "welcome_title": "How can I help you today?",
        "welcome_sub": "Ask anything in English or বাংলা. I can search the web, read your "
                       "documents, remember what matters and create images, music or video.",
        "you": "You",
        "assistant": "GroqChatbot",
        "composer_placeholder": "Message GroqChatbot…",
        "composer_hint": "Enter ↵ to send · Shift+Enter for a newline",
        "status_ready": "Ready",
        "status_thinking": "Thinking…",
        "status_streaming": "Streaming… {tokens} tokens",
        "status_stopped": "Stopped",
        "status_exported": "Exported {name}",
        "status_tool": "Running {tool}…",
        "status_error": "Something went wrong",
        "status_saved": "Saved",
        "status_docs": "Added {name} · {chunks} chunks",
        "status_memory": "Memory updated",
        "status_cleared": "Chat cleared",
        "tokens": "tokens",
        "messages": "Messages",
        "facts": "Facts",
        "documents": "Documents",
        "chunks": "Chunks",
        "vectors": "Vectors",
        "activity": "Activity",
        "quick_actions": "Quick actions",
        "system": "System",
        "memory_mode": "Memory",
        "search_mode": "Search",
        "providers": "Providers",
        "no_activity": "No activity yet",
        "menu_file": "File",
        "menu_chat": "Chat",
        "menu_agent": "Agent",
        "menu_view": "View",
        "menu_help": "Help",
        "action_export_md": "Export transcript (.md)",
        "action_export_json": "Export transcript (.json)",
        "action_exit": "Exit",
        "action_database": "Database browser",
        "action_tools": "Tool workbench",
        "action_studio": "Generation studio",
        "action_upload": "Upload documents…",
        "action_manage_docs": "Manage documents",
        "action_clear_memory": "Clear memories…",
        "action_clear_rag": "Clear document library…",
        "action_reindex": "Rebuild vector index",
        "action_key": "Groq API key…",
        "action_theme": "Toggle dark / light",
        "action_sidebar": "Show dashboard",
        "action_about": "About GroqChatbot",
        "action_docs": "Documentation",
        "action_github": "GitHub repository",
        "action_shortcuts": "Keyboard shortcuts",
        "action_export_all": "Export all data (JSON)",
        "banner_no_key_title": "Connect your Groq API key",
        "banner_no_key_body": "Groq is free to start and extremely fast. It takes about a minute.",
        "banner_no_key_button": "Set up key",
        "banner_optional": "No generation provider configured — add one to create images, "
                          "music or video.",
        "confirm_clear_title": "Clear this chat?",
        "confirm_clear_body": "The transcript is removed from the window. Long-term memories "
                             "and documents stay in the database.",
        "confirm_memory_title": "Delete all memories?",
        "confirm_memory_body": "Every saved fact and conversation is deleted from the memory "
                              "database. This cannot be undone.",
        "confirm_rag_title": "Delete every document?",
        "confirm_rag_body": "All documents and chunks are removed from the RAG database. "
                           "This cannot be undone.",
        "key_title": "Connect to Groq",
        "key_intro": "GroqChatbot runs on Groq's LPU inference. Create a free API key — it "
                    "stays on this computer and is never uploaded anywhere.",
        "key_step1": "1. Open console.groq.com/keys and sign in (Google or GitHub works).",
        "key_step2": "2. Press “Create API Key”, give it a name like GroqChatbot, and copy it.",
        "key_step3": "3. Paste the key below. It starts with gsk_.",
        "key_label": "API key",
        "key_placeholder": "gsk_…",
        "key_open": "Open Groq console ↗",
        "key_test": "Test and save",
        "key_testing": "Checking the key with Groq…",
        "key_ok": "Connected! Key saved. You can start chatting.",
        "key_bad": "That key did not work: {error}",
        "key_format": "A Groq key starts with gsk_ and is at least 40 characters long.",
        "key_skip": "Later",
        "key_env_note": "Saved to .env in the app folder.",
        "saved_settings": "Settings saved",
        "error_title": "GroqChatbot",
        "empty_message": "Write a message first.",
        "model_no_tools": "This model does not support tools — answering without them.",
        "tool_result": "Tool result",
        "thinking_label": "Working…",
        "recent_tools": "Recent tool calls",
        "chips": [
            "Explain quantum computing simply",
            "Summarise this document",
            "Write a Python script to rename files",
            "What's the weather in Dhaka?",
            "Design a poster for a tea brand",
        ],
    },
    "bn": {
        "app_title": "GroqChatbot",
        "tagline": "লোকাল-ফার্স্ট এআই এজেন্ট · মেমোরি · RAG · স্টুডিও",
        "model_fast": "দ্রুত",
        "model_smart": "স্মার্ট",
        "model_fastest": "সবচেয়ে দ্রুত",
        "lang_button": "English",
        "new_chat": "নতুন চ্যাট",
        "settings": "সেটিংস",
        "theme": "থিম বদলান",
        "sidebar": "ড্যাশবোর্ড",
        "copy": "কপি",
        "copied": "কপি হয়েছে",
        "regenerate": "আবার তৈরি",
        "stop": "থামান",
        "send": "পাঠান",
        "attach": "ডকুমেন্ট যোগ করুন",
        "tools": "টুল",
        "generate": "তৈরি করুন",
        "clear": "চ্যাট মুছুন",
        "export": "এক্সপোর্ট",
        "welcome_title": "আজ কীভাবে সাহায্য করতে পারি?",
        "welcome_sub": "ইংরেজি বা বাংলায় যেকোনো প্রশ্ন করুন। আমি ওয়েব খুঁজতে, আপনার "
                       "ডকুমেন্ট পড়তে, প্রয়োজনীয় কথা মনে রাখতে এবং ছবি, গান বা ভিডিও "
                       "তৈরি করতে পারি।",
        "you": "আপনি",
        "assistant": "GroqChatbot",
        "composer_placeholder": "GroqChatbot-কে লিখুন…",
        "composer_hint": "পাঠাতে Enter ↵ · নতুন লাইনে Shift+Enter",
        "status_ready": "প্রস্তুত",
        "status_thinking": "ভাবছে…",
        "status_streaming": "লেখা হচ্ছে… {tokens} টোকেন",
        "status_stopped": "থামানো হয়েছে",
        "status_exported": "{name} এক্সপোর্ট হয়েছে",
        "status_tool": "{tool} চলছে…",
        "status_error": "কিছু একটা ভুল হয়েছে",
        "status_saved": "সংরক্ষিত",
        "status_docs": "{name} যোগ হয়েছে · {chunks} চাঙ্ক",
        "status_memory": "মেমোরি হালনাগাদ হয়েছে",
        "status_cleared": "চ্যাট মুছে ফেলা হয়েছে",
        "tokens": "টোকেন",
        "messages": "বার্তা",
        "facts": "তথ্য",
        "documents": "ডকুমেন্ট",
        "chunks": "চাঙ্ক",
        "vectors": "ভেক্টর",
        "activity": "কার্যক্রম",
        "quick_actions": "দ্রুত কাজ",
        "system": "সিস্টেম",
        "memory_mode": "মেমোরি",
        "search_mode": "সার্চ",
        "providers": "প্রোভাইডার",
        "no_activity": "এখনো কোনো কার্যক্রম নেই",
        "menu_file": "ফাইল",
        "menu_chat": "চ্যাট",
        "menu_agent": "এজেন্ট",
        "menu_view": "ভিউ",
        "menu_help": "সহায়তা",
        "action_export_md": "চ্যাট এক্সপোর্ট (.md)",
        "action_export_json": "চ্যাট এক্সপোর্ট (.json)",
        "action_exit": "বন্ধ করুন",
        "action_database": "ডেটাবেস ব্রাউজার",
        "action_tools": "টুল ওয়ার্কবেঞ্চ",
        "action_studio": "জেনারেশন স্টুডিও",
        "action_upload": "ডকুমেন্ট আপলোড…",
        "action_manage_docs": "ডকুমেন্ট ব্যবস্থাপনা",
        "action_clear_memory": "মেমোরি মুছুন…",
        "action_clear_rag": "ডকুমেন্ট লাইব্রেরি মুছুন…",
        "action_reindex": "ভেক্টর ইনডেক্স নতুন করে তৈরি",
        "action_key": "Groq API কী…",
        "action_theme": "ডার্ক / লাইট বদলান",
        "action_sidebar": "ড্যাশবোর্ড দেখান",
        "action_about": "GroqChatbot সম্পর্কে",
        "action_docs": "ডকুমেন্টেশন",
        "action_github": "GitHub রিপোজিটরি",
        "action_shortcuts": "কীবোর্ড শর্টকাট",
        "action_export_all": "সব ডেটা এক্সপোর্ট (JSON)",
        "banner_no_key_title": "আপনার Groq API কী যুক্ত করুন",
        "banner_no_key_body": "Groq বিনামূল্যে শুরু করা যায় এবং খুব দ্রুত। এক মিনিটের কাজ।",
        "banner_no_key_button": "কী সেটআপ",
        "banner_optional": "কোনো জেনারেশন প্রোভাইডার নেই — ছবি, গান বা ভিডিও তৈরি করতে "
                          "একটি কী যোগ করুন।",
        "confirm_clear_title": "এই চ্যাট মুছবেন?",
        "confirm_clear_body": "উইন্ডো থেকে কথোপকথন মুছে যাবে। দীর্ঘমেয়াদি মেমোরি ও "
                             "ডকুমেন্ট ডেটাবেসে থেকে যাবে।",
        "confirm_memory_title": "সব মেমোরি মুছবেন?",
        "confirm_memory_body": "সংরক্ষিত সব তথ্য ও কথোপকথন মেমোরি ডেটাবেস থেকে মুছে যাবে। "
                              "এটি ফেরানো যাবে না।",
        "confirm_rag_title": "সব ডকুমেন্ট মুছবেন?",
        "confirm_rag_body": "সব ডকুমেন্ট ও চাঙ্ক RAG ডেটাবেস থেকে মুছে যাবে। এটি ফেরানো "
                           "যাবে না।",
        "key_title": "Groq-এ সংযুক্ত করুন",
        "key_intro": "GroqChatbot, Groq-এর LPU ইনফারেন্সে চলে। বিনামূল্যে একটি API কী "
                    "তৈরি করুন — এটি এই কম্পিউটারেই থাকে, কোথাও আপলোড হয় না।",
        "key_step1": "১. console.groq.com/keys খুলে সাইন ইন করুন (Google বা GitHub)।",
        "key_step2": "২. “Create API Key” চেপে GroqChatbot-এর মতো নাম দিন, তারপর কপি করুন।",
        "key_step3": "৩. নিচে কী-টি পেস্ট করুন। এটি gsk_ দিয়ে শুরু হয়।",
        "key_label": "API কী",
        "key_placeholder": "gsk_…",
        "key_open": "Groq কনসোল খুলুন ↗",
        "key_test": "পরীক্ষা ও সংরক্ষণ",
        "key_testing": "Groq-এর সাথে কী যাচাই হচ্ছে…",
        "key_ok": "সংযুক্ত! কী সংরক্ষিত হয়েছে। এখন চ্যাট শুরু করতে পারেন।",
        "key_bad": "কী-টি কাজ করেনি: {error}",
        "key_format": "Groq কী gsk_ দিয়ে শুরু হয় এবং কমপক্ষে ৪০ অক্ষরের হয়।",
        "key_skip": "পরে",
        "key_env_note": "অ্যাপ ফোল্ডারের .env ফাইলে সংরক্ষিত।",
        "saved_settings": "সেটিংস সংরক্ষিত",
        "error_title": "GroqChatbot",
        "empty_message": "প্রথমে একটি বার্তা লিখুন।",
        "model_no_tools": "এই মডেল টুল সমর্থন করে না — টুল ছাড়াই উত্তর দিচ্ছি।",
        "tool_result": "টুলের ফল",
        "thinking_label": "কাজ চলছে…",
        "recent_tools": "সাম্প্রতিক টুল কল",
        "chips": [
            "কোয়ান্টাম কম্পিউটিং সহজভাবে বোঝাও",
            "এই ডকুমেন্টটি সারসংক্ষেপ করো",
            "ফাইল নাম বদলানোর পাইথন স্ক্রিপ্ট লেখো",
            "ঢাকার আবহাওয়া কেমন?",
            "একটি চা ব্র্যান্ডের পোস্টার ডিজাইন করো",
        ],
    },
}


def tr(lang: str, key: str) -> str:
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))


def env_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(BASE_DIR) / ".env"


def read_env() -> dict:
    path = env_path()
    values: dict = {}
    if not path.exists():
        return values
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    except OSError:
        pass
    return values


def write_env(updates: dict) -> Path:
    """Merge key/value pairs into .env without destroying comments."""
    path = env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if path.exists():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            lines = []
    seen = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                value = str(updates[key] or "").replace('"', "")
                output.append(f'{key}="{value}"')
                seen.add(key)
                continue
        output.append(line)
    for key, value in updates.items():
        if key not in seen:
            output.append(f'{key}="{str(value or "").replace(chr(34), "")}"')
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8", newline="\n")
    return path


def mask_key(key: str) -> str:
    key = (key or "").strip()
    if len(key) <= 10:
        return "•" * len(key)
    return f"{key[:6]}…{key[-4:]}"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 3.6))


def escape_html(text: str) -> str:
    return html_module.escape(text or "", quote=False)


_LATEX_SYMBOLS = {
    "times": "×", "cdot": "·", "div": "÷", "pm": "±", "mp": "∓",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "neq": "≠", "ne": "≠",
    "approx": "≈", "sim": "∼", "equiv": "≡", "infty": "∞",
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "lambda": "λ", "mu": "μ",
    "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ",
    "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Pi": "Π",
    "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "sum": "Σ", "prod": "∏", "int": "∫", "partial": "∂", "nabla": "∇",
    "propto": "∝", "in": "∈", "notin": "∉", "subset": "⊂", "supset": "⊃",
    "rightarrow": "→", "to": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "leftrightarrow": "↔", "mapsto": "↦", "ldots": "…", "dots": "…",
    "degree": "°", "circ": "°", "angle": "∠", "perp": "⊥", "parallel": "∥",
    "quad": " ", "qquad": "  ", "space": " ",
}

_SUPERSCRIPTS = dict(zip("0123456789+-()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾ⁿ"))
_SUBSCRIPTS = dict(zip("0123456789+-()n", "₀₁₂₃₄₅₆₇₈₉₊₋₍₎ₙ"))


def _script(value: str, table: dict, marker: str) -> str:
    value = value.strip()
    converted = "".join(table.get(char, "") for char in value)
    if converted and len(converted) == len(value):
        return converted
    return f"{marker}({value})" if value else ""


def _latex_segment(text: str) -> str:
    """Turn the LaTeX that small models emit into readable Unicode text."""
    if not text or not re.search(r"[\\$^]|_\{", text):
        return text
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: f"\n{m.group(1)}\n", text, flags=re.S)
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: f"\n{m.group(1)}\n", text, flags=re.S)
    text = text.replace("\\(", "").replace("\\)", "")
    text = re.sub(r"\$([^$\n]*(?:\\[A-Za-z]|[\^_])[^$\n]*)\$", r"\1", text)
    text = re.sub(r"\\left(?![A-Za-z])|\\right(?![A-Za-z])", "", text)
    text = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\(?:sqrt)\s*\{([^{}]*)\}", r"√(\1)", text)
    text = re.sub(
        r"\\(?:text|mathrm|mathbf|mathit|operatorname|mathcal)\s*\{([^{}]*)\}", r"\1", text
    )
    text = re.sub(
        r"\^\{([^{}]*)\}",
        lambda m: _script(m.group(1), _SUPERSCRIPTS, "^"),
        text,
    )
    text = re.sub(
        r"\^([0-9A-Za-z])",
        lambda m: _script(m.group(1), _SUPERSCRIPTS, "^"),
        text,
    )
    text = re.sub(
        r"_\{([^{}]*)\}",
        lambda m: _script(m.group(1), _SUBSCRIPTS, "_"),
        text,
    )
    text = re.sub(
        r"(?<=[0-9A-Za-z])_([0-9A-Za-z])",
        lambda m: _script(m.group(1), _SUBSCRIPTS, "_"),
        text,
    )
    for command, symbol in _LATEX_SYMBOLS.items():
        text = re.sub(r"\\" + command + r"(?![A-Za-z])", symbol, text)
    text = re.sub(r"\\[A-Za-z]+", "", text)
    text = text.replace("\\\\", "\n")
    for spacing in ("\\,", "\\;", "\\:", "\\!", "\\ "):
        text = text.replace(spacing, " ")
    return text.replace("~", " ")


def latex_to_text(text: str) -> str:
    """Clean LaTeX outside inline code, leaving `code spans` untouched."""
    if not text or not re.search(r"[\\$^]|_\{", text):
        return text
    parts = re.split(r"(`[^`\n]*`)", text)
    cleaned: list[str] = []
    for index, part in enumerate(parts):
        cleaned.append(part if index % 2 else _latex_segment(part))
    return "".join(cleaned)


def _inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(
        r"(?<![\"=>])\b(https?://[^\s<)]+)",
        r'<a href="\1">\1</a>',
        text,
    )
    return text


def markdown_to_html(text: str, palette: dict | None = None) -> str:
    """Small, safe Markdown renderer for chat bubbles (no external deps)."""
    p = palette or make_palette()
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"```", text)
    out: list[str] = []
    for index, block in enumerate(blocks):
        if index % 2 == 1:
            body = block
            language = ""
            if "\n" in body:
                first, rest = body.split("\n", 1)
                if re.fullmatch(r"[A-Za-z0-9_+#.-]{1,20}", first.strip() or "x"):
                    language = first.strip()
                    body = rest
            code = escape_html(body.strip("\n"))
            label = (
                f'<div style="color:{p["muted"]};font-size:9px;margin:0 0 3px 0;'
                f'letter-spacing:.6px;">{escape_html(language.upper())}</div>'
                if language else ""
            )
            out.append(
                f'<div style="background:{p["code_bg"]};border:1px solid {p["border"]};'
                f'border-radius:8px;padding:9px 11px;margin:7px 0;">'
                f'{label}<pre style="margin:0;color:{p["code_text"]};font-family:'
                f"'Cascadia Code','Consolas',monospace;font-size:11.5px;"
                f'white-space:pre-wrap;word-wrap:break-word;">{code}</pre></div>'
            )
            continue

        block = latex_to_text(block)
        lines = block.split("\n")
        paragraph: list[str] = []
        in_list = False
        in_quote = False

        def flush_paragraph() -> None:
            if paragraph:
                joined = "<br>".join(_inline_markdown(escape_html(line)) for line in paragraph)
                out.append(f'<p style="margin:0 0 7px 0;">{joined}</p>')
                paragraph.clear()

        def close_list() -> None:
            nonlocal in_list
            if in_list:
                out.append("</ul>")
                in_list = False

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                flush_paragraph()
                close_list()
                continue
            heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
            if heading:
                flush_paragraph()
                close_list()
                level = len(heading.group(1))
                size = {1: 17, 2: 15.5, 3: 14, 4: 13}.get(level, 13)
                out.append(
                    f'<p style="margin:8px 0 6px 0;font-size:{size}px;font-weight:700;">'
                    f"{_inline_markdown(escape_html(heading.group(2)))}</p>"
                )
                continue
            if re.fullmatch(r"([-*_])\1{2,}", stripped):
                flush_paragraph()
                close_list()
                out.append(
                    f'<hr style="border:none;border-top:1px solid {p["border"]};margin:9px 0;">'
                )
                continue
            bullet = re.match(r"^[-*•]\s+(.*)$", stripped)
            numbered = re.match(r"^(\d{1,3})[.)]\s+(.*)$", stripped)
            if bullet or numbered:
                flush_paragraph()
                if not in_list:
                    out.append(f'<ul style="margin:3px 0 7px 0;padding-left:19px;">')
                    in_list = True
                if bullet:
                    body = bullet.group(1)
                    marker = "•"
                else:
                    body = numbered.group(2)
                    marker = f"{numbered.group(1)}."
                out.append(
                    f'<li style="margin:2px 0;">'
                    f'<span style="color:{p["accent"]};font-weight:700;">{marker}</span> '
                    f"{_inline_markdown(escape_html(body))}</li>"
                )
                continue
            quote = re.match(r"^>\s?(.*)$", stripped)
            if quote:
                flush_paragraph()
                close_list()
                out.append(
                    f'<div style="border-left:3px solid {p["accent"]};padding:2px 0 2px 10px;'
                    f'margin:6px 0;color:{p["muted"]};">'
                    f"{_inline_markdown(escape_html(quote.group(1)))}</div>"
                )
                continue
            close_list()
            paragraph.append(stripped)
        flush_paragraph()
        close_list()
    return "".join(out) or f'<p style="color:{p["muted"]};">…</p>'


def plain_text(text: str) -> str:
    try:
        document = QTextDocument()
        document.setHtml(markdown_to_html(text))
        return document.toPlainText()
    except Exception:
        return text or ""


# --------------------------------------------------------------------------- #
# Workers
# --------------------------------------------------------------------------- #
class ChatWorker(QThread):
    """Streams a Groq completion and runs the agent tool loop."""

    chunk = Signal(str)
    reasoning = Signal(str)
    tool_started = Signal(str, dict)
    tool_finished = Signal(str, dict)
    notice = Signal(str)
    finished_ok = Signal(dict)
    failed = Signal(str)

    MAX_ROUNDS = 5

    def __init__(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        tools_schema: list[dict] | None = None,
        registry: ToolRegistry | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.api_key = api_key
        self.model = model
        self.messages = [dict(m) for m in messages]
        self.tools_schema = tools_schema or []
        self.registry = registry
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self._stop = threading.Event()
        self._stream = None

    def request_stop(self) -> None:
        self._stop.set()
        stream = self._stream
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ run
    def _client(self) -> Groq:
        return Groq(api_key=self.api_key)

    def _create_stream(self, client: Groq, messages: list[dict], use_tools: bool):
        base = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": max(0.0, min(self.temperature, 2.0)),
            "max_tokens": max(64, min(self.max_tokens, 32768)),
        }
        attempts = []
        if use_tools and self.tools_schema:
            attempts.append({**base, "tools": self.tools_schema, "tool_choice": "auto"})
        attempts.append(dict(base))
        last_error: Exception | None = None
        for kwargs in attempts:
            try:
                return client.chat.completions.create(**kwargs), "tools" in kwargs
            except Exception as exc:  # noqa: BLE001 - try a simpler request
                last_error = exc
                message = str(exc).lower()
                if any(
                    token in message
                    for token in ("tool", "function", "schema", "unsupported", "not supported")
                ):
                    continue
                break
        raise last_error or RuntimeError("Groq request failed")

    def run(self) -> None:  # noqa: C901 - explicit streaming state machine
        try:
            client = self._client()
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Could not create the Groq client: {exc}")
            return

        conversation = list(self.messages)
        preamble: list[str] = []
        reasoning_parts: list[str] = []
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        tool_events: list[dict] = []
        final_text = ""
        stopped = False
        tools_enabled = bool(self.tools_schema)

        for round_index in range(self.MAX_ROUNDS):
            if self._stop.is_set():
                stopped = True
                break
            text_parts: list[str] = []
            calls: dict[int, dict] = {}
            tools_requested = tools_enabled and bool(self.tools_schema)
            try:
                stream, tools_used = self._create_stream(
                    client, conversation, tools_requested
                )
                if tools_requested and not tools_used:
                    tools_enabled = False
                    self.notice.emit(
                        "This model does not support tools — answering without them."
                    )
                self._stream = stream
                for event in stream:
                    if self._stop.is_set():
                        stopped = True
                        break
                    event_usage = getattr(event, "usage", None)
                    if event_usage is not None:
                        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                            value = getattr(event_usage, field, None)
                            if isinstance(value, int):
                                usage[field] = value
                    choices = getattr(event, "choices", None) or []
                    if not choices:
                        continue
                    choice = choices[0]
                    delta = getattr(choice, "delta", None)
                    if delta is not None:
                        reasoning = getattr(delta, "reasoning", None)
                        if reasoning:
                            reasoning_parts.append(reasoning)
                            self.reasoning.emit(reasoning)
                        content = getattr(delta, "content", None)
                        if content:
                            text_parts.append(content)
                            self.chunk.emit(content)
                        for call in getattr(delta, "tool_calls", None) or []:
                            index = getattr(call, "index", 0) or 0
                            entry = calls.setdefault(
                                index, {"id": "", "name": "", "arguments": ""}
                            )
                            call_id = getattr(call, "id", None)
                            if call_id:
                                entry["id"] = call_id
                            function = getattr(call, "function", None)
                            if function is not None:
                                name = getattr(function, "name", None)
                                arguments = getattr(function, "arguments", None)
                                if name:
                                    entry["name"] += name
                                if arguments:
                                    entry["arguments"] += arguments
                    if getattr(choice, "finish_reason", None):
                        pass
            except Exception as exc:  # noqa: BLE001
                if self._stop.is_set():
                    stopped = True
                    break
                message = str(exc)
                lowered = message.lower()
                if (
                    tools_requested
                    and not text_parts
                    and ("tool" in lowered or "function" in lowered)
                ):
                    tools_enabled = False
                    self.notice.emit(
                        "This model does not support tools — answering without them."
                    )
                    continue
                self.failed.emit(self._friendly_error(message))
                return
            finally:
                self._stream = None

            round_text = "".join(text_parts)
            if round_text.strip():
                preamble.append(round_text)

            if stopped:
                final_text = "\n\n".join(part for part in preamble if part.strip())
                break

            if not calls:
                final_text = "\n\n".join(part for part in preamble if part.strip())
                break

            ordered = [calls[key] for key in sorted(calls)]
            prepared: list[dict] = []
            tool_calls_payload: list[dict] = []
            for call in ordered:
                call_id = call["id"] or f"call_{uuid.uuid4().hex[:10]}"
                name = call["name"] or "unknown_tool"
                raw_arguments = call["arguments"] or "{}"
                tool_calls_payload.append({
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": raw_arguments},
                })
                try:
                    arguments = json.loads(raw_arguments) if raw_arguments.strip() else {}
                    if not isinstance(arguments, dict):
                        arguments = {}
                except Exception:
                    arguments = {}
                prepared.append({
                    "id": call_id,
                    "name": name,
                    "arguments": arguments,
                })

            # The assistant tool-call message must precede the tool results.
            conversation.append({
                "role": "assistant",
                "content": round_text.strip() or None,
                "tool_calls": tool_calls_payload,
            })

            for item in prepared:
                name = item["name"]
                arguments = item["arguments"]
                call_id = item["id"]
                self.tool_started.emit(name, arguments)
                if self.registry is None:
                    result = {"success": False, "error": "Tool registry unavailable."}
                else:
                    result = self.registry.execute_tool(name, arguments)
                tool_events.append({
                    "round": round_index + 1,
                    "name": name,
                    "arguments": arguments,
                    "result": result,
                })
                self.tool_finished.emit(name, result)
                try:
                    payload = json.dumps(result, ensure_ascii=False, default=str)
                except Exception:
                    payload = json.dumps({"success": False, "error": "Unserialisable result"})
                conversation.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": payload[:12000],
                })

        if not final_text:
            final_text = "\n\n".join(part for part in preamble if part.strip())
        if not usage.get("completion_tokens"):
            usage["completion_tokens"] = estimate_tokens(final_text)
        if not usage.get("prompt_tokens"):
            usage["prompt_tokens"] = sum(
                estimate_tokens(str(message.get("content") or "")) for message in conversation
            )
        usage["total_tokens"] = max(
            usage.get("total_tokens", 0),
            int(usage.get("prompt_tokens", 0)) + int(usage.get("completion_tokens", 0)),
        )
        self.finished_ok.emit({
            "text": final_text,
            "usage": usage,
            "tools": tool_events,
            "reasoning": "".join(reasoning_parts)[-4000:],
            "stopped": stopped,
            "model": self.model,
        })

    @staticmethod
    def _friendly_error(message: str) -> str:
        text = message or "Unknown error"
        lower = text.lower()
        if "invalid_api_key" in lower or "401" in lower or "unauthorized" in lower:
            return "Groq rejected the API key. Open Settings → API keys and paste a valid key."
        if "rate limit" in lower or "429" in lower:
            return "Groq rate limit reached. Wait a few seconds and try again."
        if "model_not_found" in lower or "does not exist" in lower:
            return "That model is not available on your Groq account. Pick another model."
        if "context_length" in lower or "too large" in lower:
            return "The conversation is too long for this model. Start a new chat or export and clear."
        if "connection" in lower or "timeout" in lower or "timed out" in lower:
            return "Could not reach Groq. Check your internet connection and try again."
        return text


class KeyWorker(QThread):
    """Validates a Groq key without blocking the dialog."""

    ok = Signal(str)
    bad = Signal(str)

    def __init__(self, key: str, parent=None) -> None:
        super().__init__(parent)
        self.key = key

    def run(self) -> None:
        try:
            client = Groq(api_key=self.key)
            models = client.models.list()
            names = [getattr(item, "id", "") for item in getattr(models, "data", []) or []]
            if not names:
                self.bad.emit("Groq accepted the request but returned no models.")
                return
            self.ok.emit(names[0] if names else "")
        except Exception as exc:  # noqa: BLE001
            self.bad.emit(str(exc))


# --------------------------------------------------------------------------- #
# Chat widgets
# --------------------------------------------------------------------------- #
class MessageBubble(QFrame):
    """One chat message: avatar, name, rendered body, copy and tool notes."""

    def __init__(
        self,
        role: str,
        text: str = "",
        lang: str = "en",
        palette: dict | None = None,
        timestamp: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.lang = lang
        self.palette = palette or make_palette()
        self.raw_text = text
        self.stamp = timestamp or datetime.now().strftime("%H:%M")
        self.setObjectName(
            "userCard" if role == "user" else ("errorCard" if role == "error" else "botCard")
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setMaximumWidth(780)

        column = QVBoxLayout(self)
        column.setContentsMargins(13, 9, 13, 10)
        column.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(7)
        avatar = QLabel("🧑" if role == "user" else ("⚠️" if role == "error" else "🤖"))
        avatar.setFixedSize(21, 21)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"background:{'rgba(76,141,255,0.16)' if role == 'user' else 'rgba(52,211,153,0.14)'};"
            f"border-radius:10px;font-size:11px;"
        )
        header.addWidget(avatar)
        name = QLabel(
            tr(lang, "you") if role == "user"
            else ("GroqChatbot" if role == "assistant" else tr(lang, "error_title"))
        )
        name.setStyleSheet(
            f"color:{self.palette['accent'] if role == 'user' else self.palette['success']};"
            f"font-size:10.5px;font-weight:700;"
        )
        header.addWidget(name)
        stamp = QLabel(self.stamp)
        stamp.setStyleSheet(f"color:{self.palette['faint']};font-size:9.5px;")
        header.addWidget(stamp)
        header.addStretch()
        self.copy_button = QPushButton(tr(lang, "copy"))
        self.copy_button.setObjectName("copyBtn")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setToolTip("Copy this message")
        self.copy_button.clicked.connect(self._copy)
        header.addWidget(self.copy_button)
        column.addLayout(header)

        self.body = QLabel()
        self.body.setObjectName("bubbleBody")
        self.body.setWordWrap(True)
        self.body.setTextFormat(Qt.RichText)
        self.body.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        )
        self.body.setOpenExternalLinks(True)
        self.body.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        column.addWidget(self.body)

        self.notes = QVBoxLayout()
        self.notes.setSpacing(3)
        self.notes.setContentsMargins(0, 2, 0, 0)
        column.addLayout(self.notes)
        self.set_text(text)

    # --------------------------------------------------------------- content
    def set_text(self, text: str, streaming: bool = False) -> None:
        self.raw_text = text or ""
        body = markdown_to_html(self.raw_text or "…", self.palette)
        if streaming:
            body += (
                f'<span style="color:{self.palette["accent"]};font-weight:700;">▍</span>'
            )
        self.body.setText(body)
        self._fit_width()

    def _fit_width(self) -> None:
        """Keep short messages on one line instead of wrapping in a narrow bubble."""
        lines = [line for line in (self.raw_text or "…").splitlines() if line.strip()] or ["…"]
        metrics = self.fontMetrics()
        widest = max(metrics.horizontalAdvance(line) for line in lines[:60])
        self.body.setMinimumWidth(max(240, min(widest + 24, 700)))

    def set_error(self, text: str) -> None:
        self.role = "error"
        self.setObjectName("errorCard")
        self.style().unpolish(self)
        self.style().polish(self)
        self.raw_text = text
        self.body.setText(
            f'<p style="margin:0;color:{self.palette["danger"]};">{escape_html(text)}</p>'
        )

    def add_note(self, text: str, kind: str = "muted") -> None:
        colors = {
            "ok": (self.palette["success"], "rgba(52,211,153,0.10)"),
            "bad": (self.palette["danger"], "rgba(248,113,113,0.10)"),
            "muted": (self.palette["muted"], "rgba(138,152,173,0.08)"),
            "accent": (self.palette["accent"], "rgba(76,141,255,0.10)"),
        }
        fg, bg = colors.get(kind, colors["muted"])
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(
            f"background:{bg};border:1px solid {fg}33;border-radius:7px;"
            f"color:{fg};font-size:10px;padding:4px 8px;"
        )
        self.notes.addWidget(label)

    def _copy(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.raw_text or "")
        self.copy_button.setText("✓ " + tr(self.lang, "copied"))
        QTimer.singleShot(1600, lambda: self.copy_button.setText(tr(self.lang, "copy")))


class WelcomePanel(QWidget):
    """Empty-state panel with suggestions and a capability summary."""

    chip_clicked = Signal(str)

    def __init__(self, lang: str = "en", palette: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.lang = lang
        self.palette = palette or make_palette()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 26, 28, 26)
        outer.setSpacing(6)
        outer.addStretch(1)

        self.logo = QLabel()
        self.logo.setPixmap(make_logo(58, self.palette))
        self.logo.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.logo)

        self.title = QLabel()
        self.title.setObjectName("welcomeTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        outer.addWidget(self.title)

        self.subtitle = QLabel()
        self.subtitle.setObjectName("welcomeSub")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)
        self.subtitle.setMaximumWidth(640)
        outer.addWidget(self.subtitle, 0, Qt.AlignHCenter)

        chips = QWidget()
        self.chip_layout = QGridLayout(chips)
        self.chip_layout.setContentsMargins(0, 10, 0, 6)
        self.chip_layout.setHorizontalSpacing(7)
        self.chip_layout.setVerticalSpacing(7)
        outer.addWidget(chips, 0, Qt.AlignHCenter)

        features = QHBoxLayout()
        features.setSpacing(7)
        features.addStretch()
        self.feature_labels: list[QLabel] = []
        for icon, en, bn in (
            ("🧠", "Long-term memory", "দীর্ঘমেয়াদি মেমোরি"),
            ("📚", "Document RAG", "ডকুমেন্ট RAG"),
            ("🛠", "Agent tools", "এজেন্ট টুল"),
            ("🎨", "Creation studio", "ক্রিয়েশন স্টুডিও"),
        ):
            label = QLabel(f"{icon}  {bn if lang == 'bn' else en}")
            label.setStyleSheet(
                f"background:{self.palette['panel2']};border:1px solid {self.palette['border']};"
                f"border-radius:12px;padding:5px 10px;color:{self.palette['muted']};font-size:10px;"
            )
            self.feature_labels.append(label)
            features.addWidget(label)
        features.addStretch()
        outer.addLayout(features)
        outer.addStretch(1)
        self.set_lang(lang, palette)

    def set_lang(self, lang: str, palette: dict | None = None) -> None:
        self.lang = lang
        if palette:
            self.palette = palette
        self.title.setText(tr(lang, "welcome_title"))
        self.subtitle.setText(tr(lang, "welcome_sub"))
        while self.chip_layout.count():
            item = self.chip_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        chips = tr(lang, "chips")
        if isinstance(chips, str):
            chips = [chips]
        for index, chip in enumerate(chips):
            button = QPushButton(chip)
            button.setObjectName("chip")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, text=chip: self.chip_clicked.emit(text))
            self.chip_layout.addWidget(button, index // 2, index % 2)
        for label, (icon, en, bn) in zip(
            self.feature_labels,
            (
                ("🧠", "Long-term memory", "দীর্ঘমেয়াদি মেমোরি"),
                ("📚", "Document RAG", "ডকুমেন্ট RAG"),
                ("🛠", "Agent tools", "এজেন্ট টুল"),
                ("🎨", "Creation studio", "ক্রিয়েশন স্টুডিও"),
            ),
        ):
            label.setText(f"{icon}  {bn if lang == 'bn' else en}")


# --------------------------------------------------------------------------- #
# Guided API-key dialog
# --------------------------------------------------------------------------- #
class KeyDialog(QDialog):
    """Friendly, step-by-step Groq key setup with live validation."""

    def __init__(self, host) -> None:
        super().__init__(host)
        self.host = host
        self.worker: KeyWorker | None = None
        lang = host.lang
        self.setWindowTitle(tr(lang, "key_title"))
        self.setModal(True)
        self.setFixedWidth(560)
        self.setStyleSheet(host.styleSheet())

        column = QVBoxLayout(self)
        column.setContentsMargins(22, 20, 22, 18)
        column.setSpacing(10)

        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(make_logo(44, host.palette))
        head.addWidget(logo)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel(tr(lang, "key_title"))
        title.setObjectName("dlgTitle")
        titles.addWidget(title)
        subtitle = QLabel(tr(lang, "key_intro"))
        subtitle.setObjectName("dlgBody")
        subtitle.setWordWrap(True)
        titles.addWidget(subtitle)
        head.addLayout(titles, 1)
        close = QPushButton("✕")
        close.setObjectName("dialClose")
        close.setFixedSize(28, 28)
        close.clicked.connect(self.reject)
        head.addWidget(close)
        column.addLayout(head)

        steps = QLabel(
            f"<div style='line-height:155%;'>{tr(lang, 'key_step1')}<br>"
            f"{tr(lang, 'key_step2')}<br>{tr(lang, 'key_step3')}</div>"
        )
        steps.setObjectName("dlgSteps")
        steps.setWordWrap(True)
        steps.setTextFormat(Qt.RichText)
        column.addWidget(steps)

        open_console = QPushButton(tr(lang, "key_open"))
        open_console.setObjectName("link")
        open_console.setCursor(Qt.PointingHandCursor)
        open_console.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys"))
        )
        column.addWidget(open_console, 0, Qt.AlignLeft)

        column.addWidget(QLabel(tr(lang, "key_label")))
        field_row = QHBoxLayout()
        self.field = QLineEdit()
        self.field.setEchoMode(QLineEdit.Password)
        self.field.setPlaceholderText(tr(lang, "key_placeholder"))
        self.field.setText(host.api_key or "")
        self.field.returnPressed.connect(self._save)
        field_row.addWidget(self.field, 1)
        show = QPushButton("👁")
        show.setObjectName("iconBtn")
        show.setFixedSize(30, 30)
        show.setCheckable(True)
        show.setToolTip("Show / hide key")
        show.toggled.connect(
            lambda checked: self.field.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        field_row.addWidget(show)
        column.addLayout(field_row)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        column.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(5)
        self.progress.hide()
        column.addWidget(self.progress)

        footer = QHBoxLayout()
        note = QLabel(tr(lang, "key_env_note"))
        note.setStyleSheet(f"color:{host.palette['faint']};font-size:9.5px;")
        footer.addWidget(note)
        footer.addStretch()
        later = QPushButton(tr(lang, "key_skip"))
        later.clicked.connect(self.reject)
        footer.addWidget(later)
        self.save_button = QPushButton(tr(lang, "key_test"))
        self.save_button.setObjectName("connect")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self._save)
        footer.addWidget(self.save_button)
        column.addLayout(footer)

    def _save(self) -> None:
        key = self.field.text().strip()
        if len(key) < 40 or not key.startswith("gsk_"):
            self.status.setText(tr(self.host.lang, "key_format"))
            self.status.setStyleSheet("color:#fbbf24;font-size:11px;")
            return
        if self.worker and self.worker.isRunning():
            return
        self.save_button.setEnabled(False)
        self.progress.show()
        self.status.setText(tr(self.host.lang, "key_testing"))
        self.status.setStyleSheet(f"color:{self.host.palette['muted']};font-size:11px;")
        self.worker = KeyWorker(key, self)
        self.worker.ok.connect(lambda _model: self._success(key))
        self.worker.bad.connect(self._fail)
        self.worker.finished.connect(self._finish)
        self.worker.start()

    def _finish(self) -> None:
        self.progress.hide()
        self.save_button.setEnabled(True)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _success(self, key: str) -> None:
        try:
            write_env({"GROQ_API_KEY": key})
            self.host.set_api_key(key)
        except Exception as exc:  # noqa: BLE001
            self._fail(str(exc))
            return
        self.status.setText(tr(self.host.lang, "key_ok"))
        self.status.setStyleSheet(f"color:{self.host.palette['success']};font-size:11px;")
        QTimer.singleShot(650, self.accept)

    def _fail(self, error: str) -> None:
        self._finish()
        text = tr(self.host.lang, "key_bad").format(error=str(error)[:280])
        self.status.setText(text)
        self.status.setStyleSheet(f"color:{self.host.palette['danger']};font-size:11px;")


# --------------------------------------------------------------------------- #
# Composer
# --------------------------------------------------------------------------- #
class ComposerEdit(QPlainTextEdit):
    """Chat input that grows a little and sends on Enter."""

    submitted = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("composer")
        self.setPlaceholderText(tr("en", "composer_placeholder"))
        self.setMinimumHeight(64)
        self.setMaximumHeight(150)
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._autosize)
        self._autosize()

    def _autosize(self) -> None:
        lines = max(1, self.document().blockCount())
        spacing = self.fontMetrics().lineSpacing()
        height = spacing * lines + 27
        self.setFixedHeight(max(64, min(height, 150)))

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt signature
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
                return
            if event.modifiers() & Qt.ControlModifier:
                super().keyPressEvent(event)
                return
            self.submitted.emit()
            return
        super().keyPressEvent(event)


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #
class ChatBotWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.lang = str(self.get_setting("lang", "en"))
        if self.lang not in STRINGS:
            self.lang = "en"
        self.theme = str(self.get_setting("theme", "dark"))
        self.accent = str(self.get_setting("accent", "blue"))
        self.palette = make_palette(self.theme, self.accent)
        self.default_system_prompt = DEFAULT_SYSTEM_PROMPT

        self.session_id = uuid.uuid4().hex
        self.messages: list[dict] = []
        self.bubbles: list[MessageBubble] = []
        self.holders: list[QWidget] = []
        self.quick_buttons: list[QPushButton] = []
        self.worker: ChatWorker | None = None
        self.current_bubble: MessageBubble | None = None
        self.assistant_text = ""
        self.stream_buffer = ""
        self.tool_events: list[dict] = []
        self._pending_user: str = ""
        self._pending_attachments: list[str] = []
        self._status_key = "status_ready"
        self._status_args: dict = {}
        self._sidebar_visible = bool(self.get_setting("sidebar_visible", True))
        self._compact = bool(self.get_setting("compact", False))

        self.api_key = (
            os.getenv("GROQ_API_KEY", "")
            or read_env().get("GROQ_API_KEY", "")
            or ""
        ).strip()

        self.session_tokens = 0
        self.reasoning_chars = 0
        self.total_tokens = int(float(self.get_setting("total_tokens", 0) or 0))
        self.memory = None
        self.rag = None
        self.tools = None
        self.gen: GenerationEngine | None = None
        self.system_errors: list[str] = []
        self._init_systems()

        load_dotenv(env_path(), override=False)
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(980, 680)
        self.resize(1180, 790)
        self.setWindowIcon(make_app_icon(self.palette))

        self._build_ui()
        self._build_menus()
        self._apply_theme()
        self._retranslate()
        self._update_banner()
        self.show_welcome()
        self.refresh_stats()
        self._start_timers()

        if not self.api_key:
            QTimer.singleShot(750, self.open_key_dialog)
        elif self.system_errors:
            QTimer.singleShot(1100, self._report_system_errors)

    # ------------------------------------------------------------- systems
    def _init_systems(self) -> None:
        try:
            self.memory = MemorySystem()
        except Exception as exc:  # noqa: BLE001
            self.memory = None
            self.system_errors.append(f"Memory system unavailable: {exc}")
        try:
            self.rag = RAGSystem()
        except Exception as exc:  # noqa: BLE001
            self.rag = None
            self.system_errors.append(f"Document search unavailable: {exc}")
        try:
            self.tools = ToolRegistry(
                allow_file_write=bool(self.get_setting("allow_file_write", True)),
                allow_code_execution=bool(self.get_setting("allow_code_execution", True)),
                allow_network=bool(self.get_setting("allow_network", True)),
            )
        except Exception as exc:  # noqa: BLE001
            self.tools = None
            self.system_errors.append(f"Tool system unavailable: {exc}")
        try:
            self.gen = GenerationEngine(self.provider_keys())
        except Exception as exc:  # noqa: BLE001
            self.gen = None
            self.system_errors.append(f"Generation studio unavailable: {exc}")

    def provider_keys(self) -> dict:
        raw = self.settings.value("provider_keys", "")
        if isinstance(raw, str) and raw.strip().startswith("{"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items() if v}
            except Exception:
                pass
        return {}

    def _report_system_errors(self) -> None:
        if not self.system_errors:
            return
        QMessageBox.warning(
            self,
            APP_NAME,
            "Some optional systems could not start, but chat still works:\n\n"
            + "\n".join(f"• {error}" for error in self.system_errors),
        )

    # --------------------------------------------------------------- build
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())

        self.banner = QFrame()
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(14, 9, 12, 9)
        banner_layout.setSpacing(10)
        banner_icon = QLabel("🔑")
        banner_icon.setStyleSheet("font-size:17px;")
        banner_layout.addWidget(banner_icon)
        banner_text = QVBoxLayout()
        banner_text.setSpacing(0)
        self.banner_title = QLabel(tr(self.lang, "banner_no_key_title"))
        self.banner_body = QLabel(tr(self.lang, "banner_no_key_body"))
        self.banner_body.setWordWrap(True)
        self._style_banner()
        banner_text.addWidget(self.banner_title)
        banner_text.addWidget(self.banner_body)
        banner_layout.addLayout(banner_text, 1)
        self.banner_button = QPushButton(tr(self.lang, "banner_no_key_button"))
        self.banner_button.setObjectName("primary")
        self.banner_button.setCursor(Qt.PointingHandCursor)
        self.banner_button.clicked.connect(self.open_key_dialog)
        banner_layout.addWidget(self.banner_button)
        banner_wrap = QWidget()
        banner_wrap_layout = QHBoxLayout(banner_wrap)
        banner_wrap_layout.setContentsMargins(14, 8, 14, 4)
        banner_wrap_layout.addWidget(self.banner)

        self.banner_wrap = banner_wrap
        outer.addWidget(self.banner_wrap)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._build_chat_area())
        self.splitter.addWidget(self._build_sidebar())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([880, 330])
        outer.addWidget(self.splitter, 1)
        outer.addWidget(self._build_composer())

        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)
        self.status_label = QLabel()
        self.status_label.setObjectName("status")
        status.addWidget(self.status_label, 1)
        self.tokens_label = QLabel()
        self.tokens_label.setObjectName("stats")
        status.addPermanentWidget(self.tokens_label)
        self.mode_label = QLabel()
        self.mode_label.setObjectName("stats")
        status.addPermanentWidget(self.mode_label)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(9)

        self.logo_label = QLabel()
        self.logo_label.setPixmap(make_logo(36, self.palette))
        layout.addWidget(self.logo_label)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        self.title_label = QLabel(APP_NAME)
        self.title_label.setObjectName("appTitle")
        brand.addWidget(self.title_label)
        self.tagline_label = QLabel(APP_TAGLINE)
        self.tagline_label.setObjectName("tagline")
        brand.addWidget(self.tagline_label)
        layout.addLayout(brand)
        layout.addStretch(1)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(205)
        self.model_combo.setToolTip("Model")
        self.model_combo.currentIndexChanged.connect(self._model_changed)
        layout.addWidget(self.model_combo)

        self.sidebar_button = self._icon_button("▤", "Toggle dashboard", self.toggle_sidebar)
        self.sidebar_button.setCheckable(True)
        self.sidebar_button.setChecked(self._sidebar_visible)
        layout.addWidget(self.sidebar_button)

        self.theme_button = self._icon_button("◐", "Toggle theme", self.toggle_theme)
        layout.addWidget(self.theme_button)

        self.lang_button = QPushButton(tr(self.lang, "lang_button"))
        self.lang_button.setObjectName("chip")
        self.lang_button.setCursor(Qt.PointingHandCursor)
        self.lang_button.setToolTip("English / বাংলা")
        self.lang_button.clicked.connect(self.toggle_language)
        layout.addWidget(self.lang_button)

        self.new_button = self._icon_button("＋", "New chat", self.new_chat)
        layout.addWidget(self.new_button)

        self.settings_button = self._icon_button("⚙", "Settings", self.open_settings)
        layout.addWidget(self.settings_button)

        self.groq_badge = Badge("", "muted")
        layout.addWidget(self.groq_badge)
        return header

    def _icon_button(self, glyph: str, tip: str, slot) -> QPushButton:
        button = QPushButton(glyph)
        button.setObjectName("iconBtn")
        button.setFixedSize(30, 30)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(tip)
        button.clicked.connect(slot)
        return button

    def _build_chat_area(self) -> QWidget:
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("scroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        canvas = QWidget()
        canvas.setObjectName("canvas")
        self.chat_layout = QVBoxLayout(canvas)
        self.chat_layout.setContentsMargins(20, 16, 20, 16)
        self.chat_layout.setSpacing(11 if not self._compact else 6)

        self.welcome = WelcomePanel(self.lang, self.palette)
        self.welcome.chip_clicked.connect(self._use_chip)
        self.chat_layout.addWidget(self.welcome, 1)
        self.chat_layout.addStretch(0)
        self.chat_scroll.setWidget(canvas)
        return self.chat_scroll

    def _build_sidebar(self) -> QWidget:
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(360)
        self.sidebar.setVisible(self._sidebar_visible)

        scroll = QScrollArea()
        scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("sidebarInner")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(13, 14, 13, 14)
        layout.setSpacing(8)

        self.sidebar_top = self._section_label("DASHBOARD")
        layout.addWidget(self.sidebar_top)

        self.card_messages = StatCard(tr(self.lang, "messages"), "0", "", "💬",
                                      self.palette["accent"])
        self.card_facts = StatCard(tr(self.lang, "facts"), "0", "", "🧠",
                                   self.palette["success"])
        self.card_documents = StatCard(tr(self.lang, "documents"), "0", "", "📚",
                                       self.palette["warning"])
        self.card_tokens = StatCard(tr(self.lang, "tokens").title(), "0", "", "⚡",
                                    self.palette["accent2"])
        self.stat_cards = [self.card_messages, self.card_facts,
                           self.card_documents, self.card_tokens]
        stats_grid = QGridLayout()
        stats_grid.setSpacing(6)
        for index, card in enumerate(self.stat_cards):
            card.set_theme(self.palette["text"], self.palette["muted"],
                           self.palette["accent"], self.palette["panel2"],
                           self.palette["border"])
            stats_grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(stats_grid)

        self.sidebar_activity = self._section_label("ACTIVITY")
        layout.addWidget(self.sidebar_activity)
        self.chart = MiniChart()
        layout.addWidget(self.chart)

        self.sidebar_quick = self._section_label("QUICK ACTIONS")
        layout.addWidget(self.sidebar_quick)
        grid = QGridLayout()
        grid.setSpacing(5)
        quick = [
            ("🗃", "Database", self.open_database),
            ("🛠", "Tools", self.open_tools),
            ("🎨", "Studio", self.open_generator),
            ("📎", "Upload", self.upload_file),
            ("🧹", "Memories", self.clear_memories),
            ("📂", "Data", self.open_data_folder),
        ]
        for index, (icon, label, slot) in enumerate(quick):
            button = QPushButton(f"{icon}  {label}")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(slot)
            self.quick_buttons.append(button)
            grid.addWidget(button, index // 2, index % 2)
        self._style_quick_buttons()
        layout.addLayout(grid)

        self.sidebar_system = self._section_label("SYSTEM")
        layout.addWidget(self.sidebar_system)
        self.memory_badge = Badge("Memory · —", "muted")
        self.search_badge = Badge("Search · —", "muted")
        self.provider_badge = Badge("Studio · —", "muted")
        for badge in (self.memory_badge, self.search_badge, self.provider_badge):
            badge.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            layout.addWidget(badge, 0, Qt.AlignLeft)

        self.data_label = QLabel(str(DATA_DIR))
        self.data_label.setWordWrap(True)
        self.data_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.data_label.setStyleSheet(
            f"color:{self.palette['faint']}; font-size:9px;"
        )
        layout.addWidget(self.data_label)

        self.sidebar_errors = QLabel("")
        self.sidebar_errors.setWordWrap(True)
        self.sidebar_errors.setStyleSheet(
            f"color:{self.palette['warning']}; font-size:9.5px;"
        )
        layout.addWidget(self.sidebar_errors)
        layout.addStretch(1)

        scroll.setWidget(inner)
        wrap = QVBoxLayout(self.sidebar)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.addWidget(scroll)
        return self.sidebar

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _style_quick_buttons(self) -> None:
        for button in self.quick_buttons:
            button.setStyleSheet(
                f"QPushButton {{ background:{self.palette['panel2']};"
                f" color:{self.palette['text']};"
                f" border:1px solid {self.palette['border']}; border-radius:8px;"
                f" padding:6px 4px; font-size:10.5px; text-align:left; }}"
                f"QPushButton:hover {{ border-color:{self.palette['accent']};"
                f" color:{self.palette['accent']}; }}"
            )

    def _style_banner(self) -> None:
        if not hasattr(self, "banner"):
            return
        self.banner.setStyleSheet(
            f"QFrame {{ background:{self.palette['panel2']};"
            f" border:1px solid {self.palette['border2']}; border-radius:10px; }}"
        )
        self.banner_title.setStyleSheet(
            f"font-weight:700; font-size:12px; border:none;"
            f" color:{self.palette['text']};"
        )
        self.banner_body.setStyleSheet(
            f"color:{self.palette['muted']}; font-size:10.5px; border:none;"
        )

    def _build_composer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.composer = ComposerEdit()
        self.composer.submitted.connect(self.send_message)
        row.addWidget(self.composer, 1)
        self.send_button = QPushButton(tr(self.lang, "send"))
        self.send_button.setObjectName("send")
        self.send_button.setFixedWidth(88)
        self.send_button.setMinimumHeight(64)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self._send_clicked)
        row.addWidget(self.send_button)
        layout.addLayout(row)

        actions = QHBoxLayout()
        actions.setSpacing(5)
        self.attach_button = self._small_action("📎", "Add document", self.upload_file)
        self.tools_button = self._small_action("🛠", "Tool workbench", self.open_tools)
        self.studio_button = self._small_action("🎨", "Creation studio", self.open_generator)
        self.database_button = self._small_action("🗃", "Database browser", self.open_database)
        self.clear_button = self._small_action("🧹", "Clear chat", self.clear_chat)
        self.regenerate_button = self._small_action("↻", "Regenerate", self.regenerate)
        for button in (self.attach_button, self.tools_button, self.studio_button,
                       self.database_button, self.clear_button, self.regenerate_button):
            actions.addWidget(button)
        actions.addStretch()
        self.hint_label = QLabel(tr(self.lang, "composer_hint"))
        self.hint_label.setObjectName("stats")
        actions.addWidget(self.hint_label)
        layout.addLayout(actions)
        return footer

    def _small_action(self, glyph: str, tip: str, slot) -> QPushButton:
        button = QPushButton(glyph)
        button.setObjectName("iconBtn")
        button.setFixedSize(28, 24)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(tip)
        button.clicked.connect(slot)
        return button

    # -------------------------------------------------------------- theme
    def _apply_theme(self) -> None:
        self.palette = make_palette(self.theme, self.accent)
        style = build_stylesheet(self.palette, compact=self._compact)
        app = QApplication.instance()
        if app is not None:
            app.setPalette(make_qt_palette(self.palette))
            app.setStyleSheet(style)
        self.setStyleSheet(style)
        self.setWindowIcon(make_app_icon(self.palette))
        self.logo_label.setPixmap(make_logo(36, self.palette))
        self.welcome.logo.setPixmap(make_logo(58, self.palette))
        self.welcome.set_lang(self.lang, self.palette)
        for bubble in self.bubbles:
            bubble.palette = self.palette
            bubble.set_text(bubble.raw_text)
        self.data_label.setStyleSheet(
            f"color:{self.palette['faint']}; font-size:9px;"
        )
        if hasattr(self, "sidebar_errors"):
            self.sidebar_errors.setStyleSheet(
                f"color:{self.palette['warning']}; font-size:9.5px;"
            )
        for card in getattr(self, "stat_cards", []):
            card.set_theme(self.palette["text"], self.palette["muted"],
                           self.palette["accent"], self.palette["panel2"],
                           self.palette["border"])
        self._style_quick_buttons()
        self._style_banner()
        self.chart.set_values(self._chart_values(), self.palette["accent"],
                              self.palette["accent2"], self.palette["faint"],
                              self.palette["faint"])
        self.refresh_stats()

    def _retranslate(self) -> None:
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} · {tr(self.lang, 'tagline')}")
        self.tagline_label.setText(tr(self.lang, "tagline"))
        self.lang_button.setText(tr(self.lang, "lang_button"))
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model_id, name, tag in MODELS:
            self.model_combo.addItem(f"{name} · {tr(self.lang, f'model_{tag}')}", model_id)
        index = self.model_combo.findData(
            str(self.get_setting("model", DEFAULT_MODEL))
        )
        self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        self.model_combo.blockSignals(False)
        self.composer.setPlaceholderText(tr(self.lang, "composer_placeholder"))
        self.banner_title.setText(tr(self.lang, "banner_no_key_title"))
        self.banner_body.setText(tr(self.lang, "banner_no_key_body"))
        self.banner_button.setText(tr(self.lang, "banner_no_key_button"))
        self.card_messages.title_label.setText(tr(self.lang, "messages"))
        self.card_facts.title_label.setText(tr(self.lang, "facts"))
        self.card_documents.title_label.setText(tr(self.lang, "documents"))
        self.card_tokens.title_label.setText(tr(self.lang, "tokens").title())
        self.sidebar_top.setText(tr(self.lang, "sidebar").upper())
        self.sidebar_activity.setText(tr(self.lang, "activity").upper())
        self.sidebar_quick.setText(tr(self.lang, "quick_actions").upper())
        self.sidebar_system.setText(tr(self.lang, "system").upper())
        self.new_button.setToolTip(tr(self.lang, "new_chat"))
        self.settings_button.setToolTip(tr(self.lang, "settings"))
        self.theme_button.setToolTip(tr(self.lang, "theme"))
        self.sidebar_button.setToolTip(tr(self.lang, "sidebar"))
        self.attach_button.setToolTip(tr(self.lang, "attach"))
        self.tools_button.setToolTip(tr(self.lang, "tools"))
        self.studio_button.setToolTip(tr(self.lang, "generate"))
        self.clear_button.setToolTip(tr(self.lang, "clear"))
        self.regenerate_button.setToolTip(tr(self.lang, "regenerate"))
        self.hint_label.setText(tr(self.lang, "composer_hint"))
        self.welcome.set_lang(self.lang, self.palette)
        self._apply_status()
        self._update_tokens_label()
        self._build_menus()
        if not (self.worker and self.worker.isRunning()):
            self.send_button.setText(tr(self.lang, "send"))

    def _build_menus(self) -> None:
        self.menuBar().clear()
        file_menu = self.menuBar().addMenu(tr(self.lang, "menu_file"))
        self._action(file_menu, tr(self.lang, "new_chat"), self.new_chat, "Ctrl+N")
        self._action(file_menu, tr(self.lang, "action_export_md"), self.export_markdown, "Ctrl+S")
        self._action(file_menu, tr(self.lang, "action_export_json"), self.export_json)
        self._action(file_menu, tr(self.lang, "action_export_all"), self.export_all_data)
        file_menu.addSeparator()
        self._action(file_menu, tr(self.lang, "action_database"), self.open_database, "Ctrl+D")
        self._action(file_menu, tr(self.lang, "action_exit"), self.close, "Ctrl+Q")

        chat_menu = self.menuBar().addMenu(tr(self.lang, "menu_chat"))
        self._action(chat_menu, tr(self.lang, "clear"), self.clear_chat, "Ctrl+L")
        self._action(chat_menu, tr(self.lang, "regenerate"), self.regenerate, "Ctrl+R")
        self._action(chat_menu, tr(self.lang, "stop"), self.stop_generation, "Esc")

        agent_menu = self.menuBar().addMenu(tr(self.lang, "menu_agent"))
        self._action(agent_menu, tr(self.lang, "action_key"), self.open_key_dialog)
        self._action(agent_menu, tr(self.lang, "action_tools"), self.open_tools, "Ctrl+T")
        self._action(agent_menu, tr(self.lang, "action_studio"), self.open_generator, "Ctrl+G")
        agent_menu.addSeparator()
        self._action(agent_menu, tr(self.lang, "action_upload"), self.upload_file)
        self._action(agent_menu, tr(self.lang, "action_manage_docs"), self.open_documents)
        self._action(agent_menu, tr(self.lang, "action_reindex"), self.reindex_embeddings)
        agent_menu.addSeparator()
        self._action(agent_menu, tr(self.lang, "action_clear_memory"), self.clear_memories)
        self._action(agent_menu, tr(self.lang, "action_clear_rag"), self.clear_rag)

        view_menu = self.menuBar().addMenu(tr(self.lang, "menu_view"))
        self._action(view_menu, tr(self.lang, "action_theme"), self.toggle_theme)
        self._action(view_menu, tr(self.lang, "action_sidebar"), self.toggle_sidebar)
        self._action(view_menu, tr(self.lang, "settings"), self.open_settings, "Ctrl+,")

        help_menu = self.menuBar().addMenu(tr(self.lang, "menu_help"))
        self._action(help_menu, tr(self.lang, "action_shortcuts"), self.show_shortcuts)
        self._action(help_menu, tr(self.lang, "action_docs"), self.open_docs)
        self._action(help_menu, tr(self.lang, "action_github"), self.open_github)
        self._action(help_menu, tr(self.lang, "action_about"), self.show_about)

    def _action(self, menu: QMenu, text: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(lambda _checked=False: slot())
        menu.addAction(action)
        return action

    # -------------------------------------------------------------- status
    def set_status(self, key: str, **kwargs) -> None:
        self._status_key = key
        self._status_args = kwargs
        self._apply_status()

    def _apply_status(self) -> None:
        text = tr(self.lang, self._status_key)
        try:
            text = text.format(**self._status_args)
        except (KeyError, IndexError):
            pass
        if hasattr(self, "status_label"):
            self.status_label.setText(text)

    def _update_tokens_label(self) -> None:
        if not hasattr(self, "tokens_label"):
            return
        live = estimate_tokens(self.assistant_text) if self.assistant_text else 0
        self.tokens_label.setText(
            f"⚡ {self.session_tokens + live:,} {tr(self.lang, 'tokens')} · "
            f"{self.total_tokens:,} all time"
        )

    def _start_timers(self) -> None:
        self.flush_timer = QTimer(self)
        self.flush_timer.setInterval(55)
        self.flush_timer.timeout.connect(self._flush_stream)
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(6000)
        self.stats_timer.timeout.connect(self.refresh_stats)
        self.stats_timer.start()

    # --------------------------------------------------------------- stats
    def _chart_values(self) -> list[float]:
        if not self.memory:
            return []
        try:
            rows = self.memory.recent_conversations(limit=400)
        except Exception:
            return []
        buckets = [0] * 7
        today = datetime.now().date()
        for row in rows:
            try:
                day = datetime.fromtimestamp(row["timestamp"]).date()
            except Exception:
                continue
            delta = (today - day).days
            if 0 <= delta < 7:
                buckets[6 - delta] += 1
        return [float(value) for value in buckets]

    def refresh_stats(self) -> None:
        mem_stats: dict = {}
        rag_stats: dict = {}
        try:
            mem_stats = self.memory.stats() if self.memory else {}
        except Exception as exc:  # noqa: BLE001
            self.sidebar_errors.setText(f"Memory stats failed: {exc}")
        try:
            rag_stats = self.rag.stats() if self.rag else {}
        except Exception as exc:  # noqa: BLE001
            self.sidebar_errors.setText(f"Document stats failed: {exc}")

        self.card_messages.set_value(str(mem_stats.get("conversations", 0)))
        self.card_facts.set_value(str(mem_stats.get("facts", 0)))
        self.card_documents.set_value(str(rag_stats.get("documents", 0)))
        self.card_tokens.set_value(f"{self.total_tokens:,}")

        self.chart.set_values(self._chart_values(), self.palette["accent"],
                              self.palette["accent2"], self.palette["faint"],
                              self.palette["faint"])

        memory_mode = mem_stats.get("memory_mode", "keyword")
        search_mode = rag_stats.get("search_mode", "full-text")
        self.memory_badge.setText(f"🧠 Memory · {memory_mode}")
        self.memory_badge.set_kind("ok" if memory_mode == "semantic" else "accent")
        self.search_badge.setText(f"📚 Search · {search_mode}")
        self.search_badge.set_kind("ok" if search_mode == "hybrid" else "accent")
        configured = len(self.gen.configured_providers()) if self.gen else 0
        self.provider_badge.setText(
            f"🎨 Studio · {configured} provider{'s' if configured != 1 else ''}"
        )
        self.provider_badge.set_kind("ok" if configured else "muted")

        if hasattr(self, "mode_label"):
            self.mode_label.setText(f"🧠 {memory_mode}   📚 {search_mode}")
        if hasattr(self, "groq_badge"):
            if self.api_key:
                self.groq_badge.setText("Groq · connected")
                self.groq_badge.set_kind("ok")
            else:
                self.groq_badge.setText("Groq · key needed")
                self.groq_badge.set_kind("warn")
        errors = list(self.system_errors)
        if not self.system_errors:
            self.sidebar_errors.setText("")
        else:
            self.sidebar_errors.setText("\n".join(f"⚠ {e}" for e in errors[:3]))
        self._update_tokens_label()

    def get_setting(self, key: str, default):
        value = self.settings.value(key, default)
        if value is None:
            return default
        if isinstance(default, bool):
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("true", "1", "yes", "on")
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        if isinstance(default, int) and not isinstance(default, bool):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default
        return value

    # ------------------------------------------------------------- welcome
    def show_welcome(self) -> None:
        if hasattr(self, "welcome"):
            self.welcome.show()
            self.welcome.set_lang(self.lang, self.palette)
        self._update_banner()

    def _hide_welcome(self) -> None:
        if hasattr(self, "welcome"):
            self.welcome.hide()

    def _use_chip(self, text: str) -> None:
        self.composer.setPlainText(text)
        self.composer.setFocus()
        cursor = self.composer.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.composer.setTextCursor(cursor)

    # -------------------------------------------------------------- bubbles
    def _add_bubble(self, bubble: MessageBubble) -> None:
        holder = QWidget()
        holder.setStyleSheet("background: transparent;")
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        if bubble.role == "user":
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, holder)
        self.bubbles.append(bubble)
        self.holders.append(holder)

    def _scroll_bottom(self, force: bool = False) -> None:
        bar = self.chat_scroll.verticalScrollBar()
        if force or bar.value() >= bar.maximum() - 160:
            QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))

    def _clear_bubbles(self) -> None:
        for holder in self.holders:
            holder.setParent(None)
            holder.deleteLater()
        self.holders.clear()
        self.bubbles.clear()
        self.current_bubble = None

    # -------------------------------------------------------------- sending
    def send_message(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        text = self.composer.toPlainText().strip()
        if not text:
            self.set_status("empty_message")
            return
        if not self.api_key:
            self._pending_user = text
            self.open_key_dialog()
            return
        self._pending_user = ""
        self._hide_welcome()
        self.composer.clear()

        user_bubble = MessageBubble("user", text, self.lang, self.palette)
        self._add_bubble(user_bubble)
        self.messages.append({"role": "user", "content": text})
        if self.memory:
            try:
                self.memory.add_conversation(self.session_id, "user", text)
                self.memory.remember_from_message(text)
            except Exception:
                pass

        self.assistant_text = ""
        self.stream_buffer = ""
        self.tool_events = []
        self.reasoning_chars = 0
        self.current_bubble = MessageBubble("assistant", "", self.lang, self.palette)
        self.current_bubble.set_text("", streaming=True)
        self._add_bubble(self.current_bubble)
        self._scroll_bottom(force=True)

        self.send_button.setText(tr(self.lang, "stop"))
        self.send_button.setObjectName("danger")
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)
        self.set_status("status_thinking")

        messages = self._build_messages(text)
        tools_schema = (
            self.tools.get_tools_schema()
            if (self.tools and self.get_setting("agent_mode", True)
                and self.get_setting("tools_enabled", True))
            else []
        )
        model = self.model_combo.currentData() or DEFAULT_MODEL
        self.worker = ChatWorker(
            self.api_key,
            str(model),
            messages,
            tools_schema,
            self.tools,
            float(self.get_setting("temperature", 0.7)),
            int(self.get_setting("max_tokens", 2048)),
        )
        self.worker.chunk.connect(self._on_chunk)
        self.worker.reasoning.connect(self._on_reasoning)
        self.worker.tool_started.connect(self._on_tool_started)
        self.worker.tool_finished.connect(self._on_tool_finished)
        self.worker.notice.connect(self._on_notice)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_worker_done)
        self.worker.start()

    def _build_messages(self, text: str) -> list[dict]:
        prompt = str(self.get_setting("system_prompt", DEFAULT_SYSTEM_PROMPT) or "").strip()
        if not prompt:
            prompt = DEFAULT_SYSTEM_PROMPT
        context_parts: list[str] = []
        if self.memory and self.get_setting("memory_enabled", True):
            try:
                context_parts.append(self.memory.get_memory_context(text, max_items=6))
            except Exception:
                pass
        if self.rag and self.get_setting("rag_enabled", True):
            try:
                stats = self.rag.stats()
                if stats.get("documents"):
                    context_parts.append(self.rag.get_context(text, max_chunks=3, max_chars=5200))
            except Exception:
                pass
        context_parts = [part for part in context_parts if part.strip()]
        system = prompt
        if context_parts:
            system += "\n\n" + "\n\n".join(context_parts)
        if self.tools and self.get_setting("agent_mode", True) and self.get_setting("tools_enabled", True):
            labels = ", ".join(
                f"{info['label']}" for info in self.tools.describe()
            )
            system += TOOL_GUIDANCE.format(
                context=f"Available tools: {labels}.",
                today=datetime.now().strftime("%A, %d %B %Y"),
            )
        turns = int(self.get_setting("history_turns", 24))
        history = [
            {"role": message["role"], "content": message["content"]}
            for message in self.messages
            if message.get("role") in ("user", "assistant") and message.get("content")
        ][-max(2, turns):]
        return [{"role": "system", "content": system}] + history

    def _send_clicked(self) -> None:
        if self.worker and self.worker.isRunning():
            self.stop_generation()
        else:
            self.send_message()

    # ------------------------------------------------------------- streaming
    @Slot(str)
    def _on_chunk(self, text: str) -> None:
        self.stream_buffer += text
        if not self.flush_timer.isActive():
            self.flush_timer.start()
        self.set_status(
            "status_streaming",
            tokens=estimate_tokens(self.assistant_text + self.stream_buffer),
        )

    def _flush_stream(self) -> None:
        if not self.stream_buffer:
            return
        self.assistant_text += self.stream_buffer
        self.stream_buffer = ""
        if self.current_bubble:
            self.current_bubble.set_text(self.assistant_text, streaming=True)
        self._update_tokens_label()
        self._scroll_bottom()

    @Slot(str)
    def _on_reasoning(self, text: str) -> None:
        """GPT-OSS streams a private analysis channel — show that it is working."""
        self.reasoning_chars += len(text)
        if hasattr(self, "status_label"):
            self.status_label.setText(
                f"💭 {tr(self.lang, 'status_thinking')} · {self.reasoning_chars:,}"
            )

    @Slot(str, dict)
    def _on_tool_started(self, name: str, arguments: dict) -> None:
        label = name
        if self.tools:
            tool = self.tools.tools.get(name)
            if tool:
                label = f"{tool['icon']} {tool['label']}"
        self.set_status("status_tool", tool=label)
        if self.current_bubble:
            preview = json.dumps(arguments, ensure_ascii=False)
            if len(preview) > 120:
                preview = preview[:117] + "…"
            self.current_bubble.add_note(
                f"⏳ <b>{escape_html(label)}</b> · <code>{escape_html(preview)}</code>",
                "accent",
            )

    @Slot(str, dict)
    def _on_tool_finished(self, name: str, result: dict) -> None:
        self.tool_events.append({"name": name, "result": result})
        if not self.current_bubble:
            return
        text, kind = self._tool_summary(name, result)
        self.current_bubble.add_note(text, kind)
        self._scroll_bottom()

    @Slot(str)
    def _on_notice(self, message: str) -> None:
        if self.current_bubble:
            text = (
                tr(self.lang, "model_no_tools")
                if "tool" in message.lower()
                else message
            )
            self.current_bubble.add_note(f"ℹ️ {escape_html(text)}", "muted")

    def _tool_summary(self, name: str, result: dict) -> tuple[str, str]:
        label = name.replace("_", " ").title()
        icon = "🔧"
        if self.tools:
            tool = self.tools.tools.get(name)
            if tool:
                label = tool["label"]
                icon = tool["icon"]
        ok = bool(result.get("success"))
        if not ok:
            error = str(result.get("error") or "failed")[:150]
            return f"⚠️ <b>{escape_html(label)}</b> — {escape_html(error)}", "bad"
        detail = ""
        if "formatted" in result:
            detail = str(result["formatted"])
        elif "results" in result and isinstance(result["results"], list):
            detail = f"{len(result['results'])} results"
        elif "stdout" in result:
            first = str(result["stdout"] or "").strip().splitlines()
            detail = first[0][:120] if first else "no output"
        elif "temperature_c" in result:
            detail = f"{result.get('temperature_c')}°C · {result.get('description', '')}"
        elif "datetime" in result:
            detail = f"{result['datetime']} ({result.get('timezone', '')})"
        elif "chars" in result:
            detail = f"{result['chars']} characters"
        elif "entries" in result and isinstance(result["entries"], list):
            detail = f"{len(result['entries'])} entries"
        elif "result" in result:
            detail = str(result["result"])
        elif "bytes_written" in result:
            detail = f"{result['bytes_written']} bytes written"
        text = f"✅ <b>{escape_html(icon)} {escape_html(label)}</b>"
        if detail:
            text += f" · {escape_html(detail[:160])}"
        return text, "ok"

    @Slot(dict)
    def _on_finished(self, payload: dict) -> None:
        self.flush_timer.stop()
        self._flush_stream()
        text = payload.get("text") or self.assistant_text
        if not text.strip() and payload.get("tools"):
            names = ", ".join(event["name"].replace("_", " ") for event in payload["tools"])
            text = f"I used **{names}** but the model returned no written answer. Try asking again."
        if not text.strip():
            text = "*(The model returned an empty response. Try again or pick another model.)*"
        self.assistant_text = text
        if self.current_bubble:
            self.current_bubble.set_text(text)
        self.messages.append({"role": "assistant", "content": text})
        if self.memory:
            try:
                self.memory.add_conversation(self.session_id, "assistant", text)
            except Exception:
                pass
        usage = payload.get("usage") or {}
        tokens = int(usage.get("total_tokens") or estimate_tokens(text))
        self.session_tokens += tokens
        self.total_tokens += tokens
        self.settings.setValue("total_tokens", self.total_tokens)
        self.tool_events = payload.get("tools") or self.tool_events
        self.reasoning_chars = 0
        self.set_status("status_stopped" if payload.get("stopped") else "status_ready")
        self._update_tokens_label()
        self._scroll_bottom(force=True)
        self.refresh_stats()

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.flush_timer.stop()
        self._flush_stream()
        if self.current_bubble:
            partial = self.assistant_text.strip()
            self.current_bubble.set_error(
                (partial + "\n\n" if partial else "") + message
            )
        self.reasoning_chars = 0
        self.set_status("status_error")
        self.status_label.setToolTip(message)
        self._scroll_bottom(force=True)

    @Slot()
    def _on_worker_done(self) -> None:
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self.send_button.setText(tr(self.lang, "send"))
        self.send_button.setObjectName("send")
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)
        self.send_button.setEnabled(True)
        self.composer.setFocus()
        self.current_bubble = None
        if self._pending_user:
            pending = self._pending_user
            self._pending_user = ""
            QTimer.singleShot(250, lambda: self._resume_pending(pending))

    def _resume_pending(self, text: str) -> None:
        self.composer.setPlainText(text)
        self.send_message()

    def stop_generation(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.set_status("status_stopped")

    # ---------------------------------------------------------------- chat
    def new_chat(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
        self._clear_bubbles()
        self.messages.clear()
        self.assistant_text = ""
        self.stream_buffer = ""
        self.tool_events = []
        self.session_id = uuid.uuid4().hex
        self.composer.clear()
        self.show_welcome()
        self.set_status("status_ready")
        self.composer.setFocus()

    def clear_chat(self) -> None:
        if not self.bubbles:
            self.new_chat()
            return
        answer = QMessageBox.question(
            self,
            tr(self.lang, "confirm_clear_title"),
            tr(self.lang, "confirm_clear_body"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.new_chat()
            self.set_status("status_cleared")

    def regenerate(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        text = ""
        for message in reversed(self.messages):
            if message.get("role") == "user":
                text = message.get("content", "")
                break
        if not text:
            return
        while self.messages and self.messages[-1].get("role") != "user":
            self.messages.pop()
        if self.messages:
            self.messages.pop()
        removed_user = False
        while self.bubbles:
            bubble = self.bubbles.pop()
            holder = self.holders.pop()
            holder.setParent(None)
            holder.deleteLater()
            if bubble.role == "user" and not removed_user:
                removed_user = True
                break
        self.current_bubble = None
        self.composer.setPlainText(text)
        self.send_message()

    # -------------------------------------------------------------- exports
    def _transcript_markdown(self) -> str:
        lines = [
            f"# {APP_NAME} transcript",
            "",
            f"- Session: `{self.session_id}`",
            f"- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"- Model: {self.model_combo.currentData() or DEFAULT_MODEL}",
            "",
            "---",
            "",
        ]
        for bubble in self.bubbles:
            if bubble.role == "user":
                lines += ["## 🧑 You", "", bubble.raw_text, ""]
            elif bubble.role == "assistant" and bubble.raw_text:
                lines += ["## 🤖 GroqChatbot", "", bubble.raw_text, ""]
        return "\n".join(lines)

    def export_markdown(self) -> None:
        if not self.bubbles:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr(self.lang, "export"),
            str(Path.home() / "Desktop" / f"groqchat-{datetime.now():%Y%m%d-%H%M}.md"),
            "Markdown (*.md);;Text (*.txt)",
        )
        if not path:
            return
        try:
            Path(path).write_text(self._transcript_markdown(), encoding="utf-8", newline="\n")
        except OSError as exc:
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        self.set_status("status_exported", name=Path(path).name)

    def export_json(self) -> None:
        if not self.bubbles:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr(self.lang, "export"),
            str(Path.home() / "Desktop" / f"groqchat-{datetime.now():%Y%m%d-%H%M}.json"),
            "JSON (*.json)",
        )
        if not path:
            return
        payload = {
            "app": APP_NAME,
            "version": APP_VERSION,
            "session": self.session_id,
            "exported": datetime.now().isoformat(timespec="seconds"),
            "model": self.model_combo.currentData(),
            "messages": [
                {"role": bubble.role, "content": bubble.raw_text, "time": bubble.stamp}
                for bubble in self.bubbles
                if bubble.role in ("user", "assistant")
            ],
            "tools": self.tool_events,
            "tokens": {"session": self.session_tokens, "total": self.total_tokens},
        }
        try:
            Path(path).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        self.set_status("status_exported", name=Path(path).name)

    def export_all_data(self) -> None:
        if not self.memory:
            QMessageBox.information(self, APP_NAME, "The memory system is unavailable.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr(self.lang, "action_export_all"),
            str(Path.home() / "Desktop" / "groqchatbot-data.json"),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            self.memory.export_json(path)
            if self.rag:
                self.rag.export_json(str(Path(path).with_name(Path(path).stem + "-rag.json")))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        self.set_status("status_exported", name=Path(path).name)

    def export_memory(self) -> None:
        self.export_all_data()

    # --------------------------------------------------------------- dialogs
    def open_key_dialog(self) -> None:
        dialog = KeyDialog(self)
        accepted = dialog.exec() == QDialog.Accepted
        self._update_banner()
        self.refresh_stats()
        if accepted and self._pending_user:
            pending = self._pending_user
            self._pending_user = ""
            self.composer.setPlainText(pending)
            QTimer.singleShot(200, self.send_message)

    def open_settings(self) -> None:
        try:
            dialog = SettingsDialog(self, MODELS)
            dialog.exec()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, APP_NAME, f"Could not open settings:\n{exc}")

    def open_database(self) -> None:
        try:
            dialog = DatabaseDialog(self)
            dialog.exec()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, APP_NAME, f"Could not open the database browser:\n{exc}")
        self.refresh_stats()

    def open_documents(self) -> None:
        try:
            dialog = DatabaseDialog(self, 3)
            dialog.exec()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, APP_NAME, f"Could not open documents:\n{exc}")
        self.refresh_stats()

    def open_tools(self) -> None:
        if not self.tools:
            QMessageBox.information(self, APP_NAME, "The tool system is not available.")
            return
        try:
            dialog = ToolsDialog(self)
            dialog.exec()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, APP_NAME, f"Could not open the tool workbench:\n{exc}")
        self.refresh_stats()

    def open_generator(self, kind: str = "image") -> None:
        if not isinstance(kind, str):
            kind = "image"
        if not self.gen:
            QMessageBox.information(self, APP_NAME, "The generation engine is not available.")
            return
        try:
            dialog = GenerateDialog(self, kind)
            dialog.exec()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, APP_NAME, f"Could not open the studio:\n{exc}")
        self.refresh_stats()

    def show_about(self) -> None:
        AboutDialog(self).exec()

    def show_shortcuts(self) -> None:
        QMessageBox.information(
            self,
            tr(self.lang, "action_shortcuts"),
            "<table cellspacing='7'>"
            "<tr><td><b>Ctrl+N</b></td><td>New chat</td></tr>"
            "<tr><td><b>Ctrl+S</b></td><td>Export transcript (.md)</td></tr>"
            "<tr><td><b>Ctrl+D</b></td><td>Database browser</td></tr>"
            "<tr><td><b>Ctrl+T</b></td><td>Tool workbench</td></tr>"
            "<tr><td><b>Ctrl+G</b></td><td>Generation studio</td></tr>"
            "<tr><td><b>Ctrl+R</b></td><td>Regenerate the last answer</td></tr>"
            "<tr><td><b>Ctrl+L</b></td><td>Clear this chat</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>"
            "<tr><td><b>Esc</b></td><td>Stop generating</td></tr>"
            "<tr><td><b>Enter</b></td><td>Send · Shift+Enter for a new line</td></tr>"
            "</table>",
        )

    def open_docs(self) -> None:
        local = Path(BASE_DIR) / "README.md"
        if local.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(local)))
        else:
            self.open_github()

    def open_github(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/rhasan2026g-cell/GroqChatbot"))

    # --------------------------------------------------------------- actions
    def open_path(self, path) -> None:
        target = Path(path)
        try:
            target.mkdir(parents=True, exist_ok=True) if not target.suffix else None
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def open_data_folder(self, *_args) -> None:
        self.open_path(DATA_DIR)

    def upload_file(self, *_args) -> None:
        if not self.rag:
            QMessageBox.information(self, APP_NAME, "Document search is not available.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr(self.lang, "attach"),
            str(Path.home()),
            "Documents (*.pdf *.docx *.txt *.md *.markdown *.html *.htm *.csv *.json "
            "*.xlsx *.log *.py *.js *.ts *.sql *.yaml *.yml);;All files (*.*)",
        )
        if not paths:
            return
        added = 0
        errors: list[str] = []
        for path in paths:
            result = self.rag.add_document(path)
            if result.get("success"):
                added += 1
                self.set_status(
                    "status_docs",
                    name=result.get("filename", Path(path).name),
                    chunks=result.get("chunks", 0),
                )
            else:
                errors.append(f"{Path(path).name}: {result.get('error', 'unknown error')}")
        self.refresh_stats()
        if errors:
            QMessageBox.warning(
                self, tr(self.lang, "error_title"),
                "Some files could not be added:\n\n" + "\n".join(errors[:8]),
            )
        elif added:
            self._hide_welcome()
            bubble = MessageBubble(
                "assistant",
                f"📚 Added **{added}** document{'s' if added != 1 else ''} to the knowledge base. "
                "Ask me anything about them — I will quote the relevant passages.",
                self.lang,
                self.palette,
            )
            self._add_bubble(bubble)
            self._scroll_bottom(force=True)
        self.composer.setFocus()

    def clear_memories(self, *_args) -> None:
        if not self.memory:
            return
        answer = QMessageBox.question(
            self,
            tr(self.lang, "confirm_memory_title"),
            tr(self.lang, "confirm_memory_body"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.memory.clear_all()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        self.refresh_stats()
        self.set_status("status_memory")

    def clear_rag(self, *_args) -> None:
        if not self.rag:
            return
        answer = QMessageBox.question(
            self,
            tr(self.lang, "confirm_rag_title"),
            tr(self.lang, "confirm_rag_body"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.rag.clear_all()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        self.refresh_stats()
        self.set_status("status_ready")

    def reindex_embeddings(self, *_args) -> None:
        if not self.rag:
            return
        if not getattr(self.rag, "enable_embeddings", False):
            QMessageBox.information(
                self,
                tr(self.lang, "action_reindex"),
                "Semantic search needs the optional packages:\n\n"
                "    python -m pip install -r requirements-optional.txt\n\n"
                "Without them the app already searches documents with full-text "
                "indexing, which works well for most questions.",
            )
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            count = self.rag.reindex_embeddings()
        except Exception as exc:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, tr(self.lang, "error_title"), str(exc))
            return
        QApplication.restoreOverrideCursor()
        self.refresh_stats()
        QMessageBox.information(
            self, tr(self.lang, "action_reindex"),
            f"Vector index ready. {count} chunk(s) embedded.",
        )

    # -------------------------------------------------------------- settings
    def set_api_key(self, key: str) -> None:
        self.api_key = (key or "").strip()
        if self.api_key:
            os.environ["GROQ_API_KEY"] = self.api_key
        self._update_banner()
        self.refresh_stats()
        self.set_status("status_ready")

    def mask_key(self, key: str) -> str:
        return mask_key(key)

    def _update_banner(self) -> None:
        if not hasattr(self, "banner_wrap"):
            return
        self.banner_wrap.setVisible(not bool(self.api_key))

    def apply_settings(self, values: dict) -> None:
        provider_keys = values.pop("provider_keys", None)
        groq_key = values.pop("groq_key", None)
        for key, value in values.items():
            self.settings.setValue(key, value)
        if groq_key:
            self.set_api_key(str(groq_key))
            write_env({"GROQ_API_KEY": str(groq_key)})
        if provider_keys is not None:
            env_map = {
                "huggingface": "HUGGINGFACE_API_KEY",
                "replicate": "REPLICATE_API_TOKEN",
                "stability": "STABILITY_API_KEY",
                "fal": "FAL_KEY",
                "together": "TOGETHER_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }
            cleaned = {str(k): str(v or "").strip() for k, v in provider_keys.items()}
            try:
                write_env({env_map[k]: v for k, v in cleaned.items() if k in env_map})
            except OSError as exc:
                QMessageBox.warning(self, APP_NAME, f"Could not write .env: {exc}")
            for key, env_name in env_map.items():
                value = cleaned.get(key, "")
                if value:
                    os.environ[env_name] = value
                else:
                    os.environ.pop(env_name, None)
            self.settings.setValue(
                "provider_keys",
                json.dumps({k: v for k, v in cleaned.items() if v}),
            )
            self.gen = GenerationEngine({k: v for k, v in cleaned.items() if v})

        self.lang = str(values.get("lang", self.lang))
        if self.lang not in STRINGS:
            self.lang = "en"
        self.theme = str(values.get("theme", self.theme))
        self.accent = str(values.get("accent", self.accent))
        self._compact = bool(values.get("compact", self._compact))
        self.apply_tool_permissions(
            bool(values.get("allow_file_write", self.get_setting("allow_file_write", True))),
            bool(values.get("allow_code_execution",
                            self.get_setting("allow_code_execution", True))),
            bool(values.get("allow_network", self.get_setting("allow_network", True))),
        )
        info = self.memory if self.memory else None
        self._apply_theme()
        self._retranslate()
        self._update_banner()
        self.refresh_stats()
        self.set_status("saved_settings")
        if info is not None:
            try:
                info.stats()
            except Exception:
                pass

    def apply_tool_permissions(self, write: bool, code: bool, network: bool) -> None:
        self.settings.setValue("allow_file_write", bool(write))
        self.settings.setValue("allow_code_execution", bool(code))
        self.settings.setValue("allow_network", bool(network))
        if self.tools:
            self.tools.set_permissions(write, code, network)

    def track_generation(self, result: dict) -> None:
        if not result.get("success"):
            return
        self._hide_welcome()
        kind = str(result.get("type", "image")).title()
        provider = str(result.get("provider", "provider"))
        path = Path(str(result.get("filepath", "")))
        size = "—"
        try:
            size = readable_size(path.stat().st_size)
        except OSError:
            pass
        bubble = MessageBubble("assistant", "", self.lang, self.palette)
        bubble.set_text(
            f"**{kind} created** · `{path.name}`\n\n"
            f"Provider: **{provider}**  ·  Size: **{size}**  ·  "
            f"Saved in your local data folder."
        )
        bubble.add_note(f"📂 {escape_html(str(path))}", "ok")
        self._add_bubble(bubble)
        self._scroll_bottom(force=True)
        self.set_status("status_saved")

    def toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings.setValue("theme", self.theme)
        self._apply_theme()

    def toggle_language(self) -> None:
        self.lang = "bn" if self.lang == "en" else "en"
        self.settings.setValue("lang", self.lang)
        self._retranslate()
        self.refresh_stats()

    def toggle_sidebar(self) -> None:
        self._sidebar_visible = not self._sidebar_visible
        self.settings.setValue("sidebar_visible", self._sidebar_visible)
        self.sidebar.setVisible(self._sidebar_visible)
        self.sidebar_button.setChecked(self._sidebar_visible)

    def _model_changed(self, _index: int = 0) -> None:
        model = self.model_combo.currentData()
        if model:
            self.settings.setValue("model", model)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt signature
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.worker.wait(1500)
        self.settings.setValue("total_tokens", self.total_tokens)
        self.settings.setValue("sidebar_visible", self._sidebar_visible)
        super().closeEvent(event)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    load_dotenv(env_path(), override=False)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")

    font = QFont()
    families = ["Segoe UI", "Nirmala UI", "Noto Sans Bengali", "Noto Sans", "Arial"]
    available = set(QFontDatabase.families())
    chosen = [name for name in families if name in available] or ["Segoe UI"]
    try:
        font.setFamilies(chosen)
    except Exception:
        font.setFamily(chosen[0])
    font.setPointSize(10)
    app.setFont(font)

    theme = "dark"
    accent = "blue"
    try:
        preview = QSettings(ORG_NAME, APP_NAME)
        theme = str(preview.value("theme", "dark"))
        accent = str(preview.value("accent", "blue"))
    except Exception:
        pass
    startup_palette = make_palette(theme, accent)
    app.setPalette(make_qt_palette(startup_palette))
    app.setStyleSheet(build_stylesheet(startup_palette))
    splash = QSplashScreen(make_splash_pixmap(startup_palette))
    splash.show()
    app.processEvents()

    window = ChatBotWindow()
    window.show()
    splash.finish(window)
    window.raise_()
    window.activateWindow()

    smoke = os.getenv("GROQCHATBOT_SMOKE") or "--smoke" in sys.argv
    if smoke:
        delay = int(float(os.getenv("GROQCHATBOT_SMOKE_MS", "2500")))
        QTimer.singleShot(delay, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())




