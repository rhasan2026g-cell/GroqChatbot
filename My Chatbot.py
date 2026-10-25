"""Groq Chat — a bilingual (English / বাংলা) desktop chatbot.

Main application file. Run with:
    python "My Chatbot.py"

Or double-click start_chatbot.bat for a console-free launch.
"""

from __future__ import annotations

import html
import os
import re
import sys
import json
import uuid
from datetime import datetime

from dotenv import load_dotenv
from groq import Groq
from PySide6.QtCore import QEvent, QSettings, Qt, QThread, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import (
    QDesktopServices,
    QFont,
    QFontDatabase,
    QKeySequence,
    QShortcut,
    QTextDocument,
    QPixmap,
    QPainter,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QMenuBar,
    QMenu,
    QToolBar,
    QAction,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QSlider,
    QTextEdit,
    QListWidget,
    QSplitter,
    QStatusBar,
    QSplashScreen,
)

# Agent and Memory imports
try:
    from memory_system import MemorySystem
    from agent_tools import ToolRegistry
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Agent features not available: {e}")
    AGENT_AVAILABLE = False
    MemorySystem = None
    ToolRegistry = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the .env that sits next to this file, regardless of the working directory.
load_dotenv(os.path.join(BASE_DIR, ".env"))

ENV_PATH = os.path.join(BASE_DIR, ".env")
KEY_PATTERN = re.compile(r"^gsk_[A-Za-z0-9_-]{20,}$")
ENV_KEY_LINE = re.compile(r"^\s*(?:export\s+)?GROQ_API_KEY\s*=", re.IGNORECASE)


def clean_key(raw: str) -> str:
    """Accept a bare key, a whole .env line, `export …`, `Bearer …` or a quoted value."""
    value = (raw or "").strip()
    value = re.sub(r"^export\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^GROQ_API_KEY\s*=\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^Bearer\s+", "", value, flags=re.IGNORECASE)
    return value.strip().strip("\"'`").strip()


def mask_key(key: str) -> str:
    return f"{key[:4]}…{key[-4:]}" if len(key) > 8 else "…"


def button_text(value: str) -> str:
    """Keep a literal & in button labels instead of creating a mnemonic."""
    return value.replace("&", "&&")


def _read_env_lines() -> list[str]:
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as handle:
            return handle.read().splitlines()
    except FileNotFoundError:
        return []


def _write_env_lines(lines: list[str]) -> None:
    """Rewrite .env atomically, keeping comments and every other setting intact."""
    tmp_path = ENV_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines).rstrip("\n") + "\n")
    os.replace(tmp_path, ENV_PATH)


def save_key_to_env(key: str) -> None:
    lines: list[str] = []
    replaced = False
    for line in _read_env_lines():
        if ENV_KEY_LINE.match(line):
            if not replaced:
                lines.append(f"GROQ_API_KEY={key}")
                replaced = True
            continue
        lines.append(line)
    if not replaced:
        lines.append(f"GROQ_API_KEY={key}")
    _write_env_lines(lines)


def remove_key_from_env() -> None:
    _write_env_lines([line for line in _read_env_lines() if not ENV_KEY_LINE.match(line)])

APP_TITLE = "GroqChatbot"
DEFAULT_MODEL = "openai/gpt-oss-20b"

MODELS = [
    ("openai/gpt-oss-20b", "GPT-OSS 20B", "fast"),
    ("openai/gpt-oss-120b", "GPT-OSS 120B", "smart"),
    ("qwen/qwen3.8-27b", "Qwen 3.8 27B", "fastest"),
]

SYSTEM_PROMPT = (
    "You are GroqChatbot, an intelligent AI agent with memory and tools. "
    "You are bilingual and always answer in the same language the user writes in: "
    "if they write in Bengali (বাংলা), answer in natural Bengali; "
    "if they write in English, answer in English. "
    "Match their script and tone. "
    "You have access to tools and long-term memory. Use tools when they would help provide accurate, up-to-date information. "
    "Remember important facts about the user across conversations. "
    "Be helpful, proactive, and thorough while keeping answers clear and concise. "
    "Use markdown formatting, wrap code in triple backticks."
)

COLORS = {
    "bg": "#0f131a",
    "panel": "#161c26",
    "user_card": "#1c3354",
    "bot_card": "#171e2a",
    "error_card": "#33191d",
    "border": "#232d3d",
    "text": "#dbe4f3",
    "muted": "#7c8aa0",
    "accent": "#4c8dff",
    "user_name": "#93c5fd",
    "bot_name": "#86efac",
    "error_name": "#fca5a5",
}

STRINGS: dict[str, dict] = {
    "en": {
        "app_title": "Groq Chat",
        "tagline": "Fast, friendly AI chat",
        "new_chat": "New chat",
        "export": "Export",
        "language": "Language",
        "welcome_title": "How can I help you today?",
        "welcome_sub": "Ask anything — in English or বাংলা.",
        "placeholder": "Message Groq Chat…",
        "composer_hint": "Enter sends · Shift+Enter adds a new line",
        "send": "Send",
        "stop": "Stop",
        "ready": "Ready",
        "thinking": "Thinking…",
        "streaming": "Streaming…",
        "stopping": "Stopping…",
        "you": "You",
        "assistant": "Assistant",
        "copy": "Copy",
        "copied": "Copied",
        "model_fast": "fast",
        "model_smart": "smart",
        "model_fastest": "fastest",
        "suggestions": [
            "Explain quantum computing",
            "Write a poem in বাংলা",
            "Python loop example",
        ],
        "no_key_title": "Connect to Groq",
        "no_key_body": "Add your Groq API key to start chatting.",
        "key_title_new": "Connect to Groq",
        "key_title_existing": "Groq connection",
        "key_body_new": "Groq is free to use. You just need your own API key — it takes about a minute.",
        "key_body_existing": "Your key is saved on this computer. Replace it or run a quick test.",
        "key_step1": "Open console.groq.com/keys and sign in — it's free.",
        "key_step2": "Click “Create API Key”, then give it any name.",
        "key_step3": "Copy the key that starts with gsk_ and paste it below.",
        "key_get": "Get a free key ↗",
        "key_save": "Save & test",
        "key_testing": "Testing…",
        "key_show": "Show",
        "key_hide": "Hide",
        "key_remove": "Remove",
        "key_remove_ask": "Remove the saved Groq API key from this computer?",
        "key_empty": "Paste your key first.",
        "key_bad_format": "That doesn't look like a Groq key — it should start with gsk_.",
        "key_invalid": "Invalid API key. Add a new one from settings (⚙).",
        "key_invalid2": "Groq rejected this key. Copy it again from console.groq.com/keys.",
        "key_current": "Saved key: {key}",
        "key_env_failed": "Could not update the .env file. The key works for this session only.",
        "key_not_set": "No API key yet — click to connect",
        "key_set": "Groq key connected",
        "connect_groq": "Connect Groq key",
        "status_connected": "Connected — you're ready to chat.",
        "status_key_unverified": "Key saved. It could not be verified right now.",
        "status_key_removed": "API key removed from this computer.",
        "export_empty_title": "Nothing to export",
        "export_empty_body": "Start a conversation first.",
        "export_failed": "Export failed",
        "empty_reply": "(stopped)",
        "status_exported": "Saved → {name}",
        "export_title": "Groq Chat — Transcript",
        "export_exported": "Exported",
        "export_model": "Model",
        "export_turns": "Turns",
    },
    "bn": {
        "app_title": "গ্রক চ্যাট",
        "tagline": "দ্রুত ও সহজ এআই চ্যাট",
        "new_chat": "নতুন চ্যাট",
        "export": "সংরক্ষণ",
        "language": "ভাষা",
        "welcome_title": "আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
        "welcome_sub": "ইংরেজি বা বাংলায় যেকোনো কিছু জিজ্ঞাসা করুন।",
        "placeholder": "গ্রক চ্যাটকে কিছু লিখুন…",
        "composer_hint": "পাঠাতে Enter · নতুন লাইনে Shift+Enter",
        "send": "পাঠান",
        "stop": "থামান",
        "ready": "প্রস্তুত",
        "thinking": "ভাবছি…",
        "streaming": "উত্তর আসছে…",
        "stopping": "থামানো হচ্ছে…",
        "you": "আপনি",
        "assistant": "সহকারী",
        "copy": "কপি",
        "copied": "কপি হয়েছে",
        "model_fast": "দ্রুত",
        "model_smart": "স্মার্ট",
        "model_fastest": "সবচেয়ে দ্রুত",
        "suggestions": [
            "কোয়ান্টাম কম্পিউটিং কী?",
            "বাংলায় কবিতা লেখো",
            "পাইথন লুপ শেখাও",
        ],
        "no_key_title": "গ্রকে সংযোগ করুন",
        "no_key_body": "চ্যাট শুরু করতে আপনার গ্রক এপিআই কী যোগ করুন।",
        "key_title_new": "গ্রকে সংযোগ করুন",
        "key_title_existing": "গ্রক সংযোগ",
        "key_body_new": "গ্রক ব্যবহার বিনামূল্যে। শুধু আপনার নিজের এপিআই কী দরকার — এক মিনিটের কাজ।",
        "key_body_existing": "আপনার কী এই কম্পিউটারে সংরক্ষিত আছে। বদলাতে পারেন বা পরীক্ষা করতে পারেন।",
        "key_step1": "console.groq.com/keys খুলে বিনামূল্যে সাইন ইন করুন।",
        "key_step2": "“Create API Key” চাপুন, তারপর যেকোনো নাম দিন।",
        "key_step3": "gsk_ দিয়ে শুরু হওয়া কী-টি কপি করে নিচে পেস্ট করুন।",
        "key_get": "বিনামূল্যে কী নিন ↗",
        "key_save": "সংরক্ষণ ও পরীক্ষা",
        "key_testing": "পরীক্ষা চলছে…",
        "key_show": "দেখান",
        "key_hide": "লুকান",
        "key_remove": "মুছুন",
        "key_remove_ask": "এই কম্পিউটার থেকে সংরক্ষিত গ্রক এপিআই কী মুছে ফেলবেন?",
        "key_empty": "আগে আপনার কী-টি পেস্ট করুন।",
        "key_bad_format": "এটি গ্রক কী-এর মতো দেখাচ্ছে না — শুরুতে gsk_ থাকা উচিত।",
        "key_invalid": "এপিআই কী সঠিক নয়। সেটিংস (⚙) থেকে নতুন কী যোগ করুন।",
        "key_invalid2": "গ্রক এই কী গ্রহণ করেনি। console.groq.com/keys থেকে আবার কপি করুন।",
        "key_current": "সংরক্ষিত কী: {key}",
        "key_env_failed": ".env ফাইল আপডেট করা যায়নি। কী-টি শুধু এই সেশনে কাজ করবে।",
        "key_not_set": "এখনো এপিআই কী নেই — সংযোগ করতে ক্লিক করুন",
        "key_set": "গ্রক কী সংযুক্ত",
        "connect_groq": "গ্রক কী সংযুক্ত করুন",
        "status_connected": "সংযোগ হয়েছে — এখন চ্যাট করতে পারেন।",
        "status_key_unverified": "কী সংরক্ষণ হয়েছে। এখন যাচাই করা যায়নি।",
        "status_key_removed": "এই কম্পিউটার থেকে এপিআই কী মুছে ফেলা হয়েছে।",
        "export_empty_title": "সংরক্ষণের কিছু নেই",
        "export_empty_body": "প্রথমে একটি কথোপকথন শুরু করুন।",
        "export_failed": "সংরক্ষণ ব্যর্থ হয়েছে",
        "empty_reply": "(থামানো হয়েছে)",
        "status_exported": "সংরক্ষিত → {name}",
        "export_title": "গ্রক চ্যাট — কথোপকথন",
        "export_exported": "সংরক্ষিত",
        "export_model": "মডেল",
        "export_turns": "বার্তা",
    },
}


# --------------------------------------------------------------------------- #
# Rich-text formatting (Qt supports only a small HTML/CSS subset)
# --------------------------------------------------------------------------- #
def format_rich(text: str) -> str:
    """Escape HTML, then apply bold / inline code / links / code blocks."""
    blocks: list[str] = []

    def stash(match: re.Match) -> str:
        blocks.append(html.escape(match.group(1).strip("\n")))
        return f"\x00B{len(blocks) - 1}\x00"

    text = re.sub(r"```[a-zA-Z0-9_+-]*\n?(.*?)```", stash, text, flags=re.S)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: f"<b>{m.group(1)}</b>", text)
    text = re.sub(
        r"`([^`\n]+)`",
        lambda m: (
            '<code style="background-color:#0b1119; color:#9fd0ff;">'
            f"{m.group(1)}</code>"
        ),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}" style="color:#6ea8ff;">{m.group(1)}</a>',
        text,
    )
    text = text.replace("\n", "<br>")
    for index, code in enumerate(blocks):
        text = text.replace(
            f"\x00B{index}\x00",
            '<pre style="background-color:#0b1119; color:#cdd8ea; padding:8px; margin:0;">'
            f"{code}</pre>",
        )
    return text


# --------------------------------------------------------------------------- #
# Background workers
# --------------------------------------------------------------------------- #
class KeyTestWorker(QThread):
    """Checks a key against Groq's /models endpoint off the UI thread."""

    tested = Signal(str)  # "ok" | "invalid" | "unverified"

    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key

    def run(self) -> None:
        try:
            client = Groq(api_key=self.api_key, timeout=12.0, max_retries=0)
            client.models.list()
            self.tested.emit("ok")
        except Exception as exc:  # noqa: BLE001 - verdict is what matters
            status = getattr(exc, "status_code", None)
            text = str(exc).lower()
            if status in (401, 403) or "invalid_api_key" in text or "401" in text:
                self.tested.emit("invalid")
            else:
                self.tested.emit("unverified")


class ChatWorker(QThread):
    """Streams a chat completion off the UI thread."""

    chunk_received = Signal(str)
    response_finished = Signal(str)
    error_occurred = Signal(str)
    auth_failed = Signal()

    def __init__(self, api_key: str, model: str, messages: list[dict], parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model = model
        self.messages = messages
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        full_text = ""
        try:
            client = Groq(api_key=self.api_key)
            stream = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                if self._stop_requested:
                    break
                if not chunk.choices:
                    continue
                piece = chunk.choices[0].delta.content
                if piece:
                    full_text += piece
                    self.chunk_received.emit(piece)
            self.response_finished.emit(full_text)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            message = str(exc)
            low = message.lower()
            if "401" in message or "invalid_api_key" in low:
                message = "Invalid API key."
                self.auth_failed.emit()
            elif "429" in message or "rate_limit" in low:
                message = "Rate limit reached. Wait a moment and try again."
            self.error_occurred.emit(message)


# --------------------------------------------------------------------------- #
# Widgets
# --------------------------------------------------------------------------- #
class Composer(QPlainTextEdit):
    """Multi-line input: Enter sends, Shift+Enter makes a new line."""

    submitted = Signal()
    MIN_HEIGHT = 46
    MAX_HEIGHT = 140

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("composer")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)
        self.textChanged.connect(self._auto_resize)
        self._auto_resize()

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt signature
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submitted.emit()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt signature
        super().resizeEvent(event)
        self._auto_resize()

    def set_text(self, text: str) -> None:
        self.setPlainText(text)
        self.moveCursor(self.textCursor().End)

    def _auto_resize(self) -> None:
        """Grow with the content using an independent layout measurement."""
        width = self.viewport().width()
        if width <= 0:
            width = max(120, self.width() - 28)
        doc = QTextDocument()
        doc.setDefaultFont(self.font())
        doc.setDocumentMargin(0)
        doc.setPlainText(self.toPlainText() or " ")
        doc.setTextWidth(width)
        height = int(doc.size().height()) + 28  # stylesheet padding + frame + slack
        height = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, height))
        if height != self.height():
            self.setFixedHeight(height)


class MessageBubble(QWidget):
    """One chat message with a name, copy button and rounded card."""

    MAX_WIDTH = 620
    MIN_WIDTH = 150

    def __init__(self, role: str, text: str, strings: dict, error: bool = False, parent=None):
        super().__init__(parent)
        self.role = role
        self.raw_text = text
        self.strings = strings
        self.is_user = role == "user"
        self._body_html = ""
        self._available = self.MAX_WIDTH

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        if error:
            card_name = "errorCard"
        else:
            card_name = "userCard" if self.is_user else "botCard"

        card = QFrame()
        card.setObjectName(card_name)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.card = card

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 9, 14, 11)
        inner.setSpacing(3)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)

        if error:
            name_color = COLORS["error_name"]
            name_text = strings["assistant"]
        elif self.is_user:
            name_color = COLORS["user_name"]
            name_text = strings["you"]
        else:
            name_color = COLORS["bot_name"]
            name_text = strings["assistant"]

        self.name_label = QLabel(name_text)
        self.name_label.setStyleSheet(
            f"color:{name_color}; font-size:11px; font-weight:600; background:transparent;"
        )
        head.addWidget(self.name_label)
        head.addStretch()

        self.copy_btn = QPushButton(strings["copy"])
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_text)
        head.addWidget(self.copy_btn)
        inner.addLayout(head)

        self.body = QLabel()
        self.body.setObjectName("bubbleBody")
        self.body.setTextFormat(Qt.RichText)
        self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.setOpenExternalLinks(True)
        self.body.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        inner.addWidget(self.body)

        if self.is_user:
            outer.addStretch(1)
            outer.addWidget(card)
        else:
            outer.addWidget(card)
            outer.addStretch(1)

        self.set_text(text)

    def set_text(self, text: str, streaming: bool = False) -> None:
        self.raw_text = text
        body = format_rich(text) if text else ""
        if streaming and not text:
            body = f'<span style="color:{COLORS["muted"]};">●●●</span>'
        elif streaming:
            body += f'<span style="color:{COLORS["accent"]};">▌</span>'
        self._body_html = body
        self._measure()

    def set_available_width(self, available: int) -> None:
        self._available = max(self.MIN_WIDTH, available)
        self._measure()

    def _measure(self) -> None:
        """Size the label to its ideal width (capped) and exact wrapped height."""
        doc = QTextDocument()
        doc.setDefaultFont(self.body.font())
        doc.setDocumentMargin(0)
        doc.setHtml(self._body_html)

        doc.setTextWidth(-1)
        ideal = doc.idealWidth()
        width = max(self.MIN_WIDTH, min(ideal + 2, self.MAX_WIDTH, self._available))

        doc.setTextWidth(width)
        height = doc.size().height()

        self.body.setText(self._body_html)
        self.body.setFixedWidth(int(width))
        self.body.setFixedHeight(int(height) + 4)

    def retranslate(self, strings: dict) -> None:
        self.strings = strings
        self.name_label.setText(
            strings["you"] if self.is_user else strings["assistant"]
        )
        self.copy_btn.setText(strings["copy"])

    def copy_text(self) -> None:
        QApplication.clipboard().setText(self.raw_text)
        self.copy_btn.setText(self.strings["copied"])
        QTimer.singleShot(1200, lambda: self.copy_btn.setText(self.strings["copy"]))


# --------------------------------------------------------------------------- #
# Guided API-key dialog
# --------------------------------------------------------------------------- #
KEY_DIALOG_STYLE = """
QDialog#keyDialog { background-color: #161c26; }
QLabel#dlgTitle { color: #eef4ff; font-size: 17px; font-weight: 600; }
QLabel#dlgBody { color: #9fb0c9; font-size: 12.5px; }
QLabel#dlgMeta { color: #8fa1ba; font-size: 11.5px; }
QLabel#dlgSteps { color: #a9b6cb; font-size: 12.5px; }
QLabel#dlgError {
    background-color: #33191d; border: 1px solid #5a2a2f; border-radius: 8px;
    color: #ffb4b4; font-size: 12px; padding: 8px 10px;
}
QLineEdit#keyInput {
    background-color: #0f131a; color: #dbe4f3;
    border: 1px solid #2b3a52; border-radius: 9px;
    padding: 9px 11px; font-size: 13px;
}
QLineEdit#keyInput:focus { border-color: #4c8dff; }
QPushButton#primary {
    background-color: #4c8dff; color: #061020; border: none;
    border-radius: 9px; padding: 9px 18px; font-size: 13px; font-weight: 600;
}
QPushButton#primary:hover { background-color: #6ba6ff; }
QPushButton#primary:disabled { background-color: #2b3d59; color: #7f92ad; }
QPushButton#dlgDanger {
    background: transparent; color: #ff7b7b; border: 1px solid #5a2a2f;
}
QPushButton#dlgDanger:hover { background: #33191d; border-color: #7a3a40; }
QPushButton#link {
    background: transparent; border: none; color: #4c8dff;
    padding: 4px 0; font-size: 12px;
}
QPushButton#link:hover { color: #6ba6ff; background: transparent; }
QPushButton#eye { padding: 7px 10px; font-size: 11.5px; }
QPushButton#dlgClose {
    background: transparent; border: none; color: #7c8aa0; font-size: 14px;
}
QPushButton#dlgClose:hover { color: #dbe4f3; background: #223049; }
"""


class KeyDialog(QDialog):
    """Steps, validation, live test and save/remove for the Groq API key."""

    CONTENT_WIDTH = 476

    def __init__(self, host: "ChatBotWindow") -> None:
        super().__init__(host)
        self.host = host
        self._worker: KeyTestWorker | None = None
        self.setObjectName("keyDialog")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedWidth(520)
        self.setStyleSheet(host.styleSheet() + KEY_DIALOG_STYLE)
        self._build()

    # ------------------------------ layout --------------------------------
    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(22, 18, 22, 18)
        column.setSpacing(8)

        head = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName("dlgTitle")
        head.addWidget(self.title_label)
        head.addStretch()
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("dlgClose")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.reject)
        head.addWidget(self.btn_close)
        column.addLayout(head)

        self.body_label = QLabel()
        self.body_label.setObjectName("dlgBody")
        self.body_label.setWordWrap(True)
        self.body_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        column.addWidget(self.body_label)

        self.meta_label = QLabel()
        self.meta_label.setObjectName("dlgMeta")
        self.meta_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        column.addWidget(self.meta_label)

        self.steps_label = QLabel()
        self.steps_label.setObjectName("dlgSteps")
        self.steps_label.setWordWrap(True)
        self.steps_label.setTextFormat(Qt.RichText)
        self.steps_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        column.addWidget(self.steps_label)

        column.addSpacing(2)

        field_row = QHBoxLayout()
        field_row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setObjectName("keyInput")
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setPlaceholderText("gsk_…")
        self.input.returnPressed.connect(self._save)
        field_row.addWidget(self.input, 1)
        self.btn_eye = QPushButton()
        self.btn_eye.setObjectName("eye")
        self.btn_eye.setCheckable(True)
        self.btn_eye.setCursor(Qt.PointingHandCursor)
        self.btn_eye.setMinimumWidth(64)
        self.btn_eye.toggled.connect(self._toggle_eye)
        field_row.addWidget(self.btn_eye)
        column.addLayout(field_row)

        self.error_label = QLabel()
        self.error_label.setObjectName("dlgError")
        self.error_label.setWordWrap(True)
        self.error_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.error_label.hide()
        column.addWidget(self.error_label)

        column.addSpacing(4)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.btn_link = QPushButton()
        self.btn_link.setObjectName("link")
        self.btn_link.setCursor(Qt.PointingHandCursor)
        self.btn_link.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys"))
        )
        actions.addWidget(self.btn_link)
        actions.addStretch()
        self.btn_remove = QPushButton()
        self.btn_remove.setObjectName("dlgDanger")
        self.btn_remove.setCursor(Qt.PointingHandCursor)
        self.btn_remove.clicked.connect(self._remove)
        actions.addWidget(self.btn_remove)
        self.btn_save = QPushButton()
        self.btn_save.setObjectName("primary")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._save)
        actions.addWidget(self.btn_save)
        column.addLayout(actions)

    # ----------------------------- state ----------------------------------
    def configure(self, error: str = "") -> None:
        s = STRINGS[self.host.lang]
        has = bool(self.host.api_key)
        title = s["key_title_existing" if has else "key_title_new"]
        self.setWindowTitle(title)
        self.title_label.setText(title)
        self.body_label.setText(s["key_body_existing" if has else "key_body_new"])

        self.steps_label.setText(
            '<div style="line-height:150%">'
            f'<span style="color:#4c8dff;font-weight:600;">1.</span> {html.escape(s["key_step1"])}<br>'
            f'<span style="color:#4c8dff;font-weight:600;">2.</span> {html.escape(s["key_step2"])}<br>'
            f'<span style="color:#4c8dff;font-weight:600;">3.</span> {html.escape(s["key_step3"])}'
            "</div>"
        )
        self.steps_label.setVisible(not has)
        self.btn_link.setVisible(not has)
        self.btn_link.setText(button_text(s["key_get"]))
        if not has:
            self._fit_wrapped(self.steps_label, pad=0)

        self.meta_label.setVisible(has)
        if has:
            self.meta_label.setText(s["key_current"].format(key=mask_key(self.host.api_key)))

        self.btn_remove.setVisible(has)
        self.btn_remove.setText(button_text(s["key_remove"]))
        self.btn_remove.setEnabled(True)
        self.btn_save.setText(button_text(s["key_save"]))
        self.btn_save.setEnabled(True)

        self.btn_eye.setChecked(False)
        self.btn_eye.setText(button_text(s["key_show"]))
        self.input.setEnabled(True)
        self.input.setText(self.host.api_key)
        self.input.setCursorPosition(0)

        self._show_error(error)

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))
        if message:
            self._fit_wrapped(self.error_label, pad=18)

    def _fit_wrapped(self, label: QLabel, pad: int = 0) -> None:
        """QLabel's size hint ignores the real width; pin the wrapped height."""
        height = label.heightForWidth(self.CONTENT_WIDTH)
        if height > 0:
            label.setFixedHeight(height + pad)

    def _set_busy(self, busy: bool) -> None:
        s = STRINGS[self.host.lang]
        self.btn_save.setEnabled(not busy)
        self.btn_save.setText(button_text(s["key_testing"] if busy else s["key_save"]))
        self.btn_remove.setEnabled(not busy)
        self.input.setEnabled(not busy)

    def _toggle_eye(self, checked: bool) -> None:
        self.input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.btn_eye.setText(button_text(self.host.t("key_hide" if checked else "key_show")))

    # ---------------------------- actions ---------------------------------
    def _save(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        s = STRINGS[self.host.lang]
        key = clean_key(self.input.text())
        if not key:
            self._show_error(s["key_empty"])
            self.input.setFocus()
            return
        if not KEY_PATTERN.match(key):
            self._show_error(s["key_bad_format"])
            self.input.setFocus()
            return

        self._show_error("")
        self._set_busy(True)

        worker = KeyTestWorker(key, self)
        self._worker = worker
        worker.tested.connect(lambda verdict, k=key: self._on_tested(k, verdict))
        worker.finished.connect(self._worker_done)
        worker.start()

    def _worker_done(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self.isVisible():
            self._set_busy(False)

    def _on_tested(self, key: str, verdict: str) -> None:
        if not self.isVisible():
            return  # the user closed the sheet while the test was running
        if verdict == "invalid":
            self._show_error(STRINGS[self.host.lang]["key_invalid2"])
            self.input.setFocus()
            self.input.selectAll()
            return
        self.host.apply_api_key(key, verified=verdict == "ok")
        self.accept()

    def _remove(self) -> None:
        s = STRINGS[self.host.lang]
        answer = QMessageBox.question(
            self,
            s["key_title_existing"],
            s["key_remove_ask"],
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.host.clear_api_key()
        self.accept()


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #
class ChatBotWindow(QMainWindow):
    MAX_HISTORY_TURNS = 20

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("RBK", "GroqChatbot")
        self.lang = self.settings.value("lang", "en", type=str)
        if self.lang not in STRINGS:
            self.lang = "en"

        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.history: list[dict] = []
        self.bubbles: list[MessageBubble] = []
        self.worker: ChatWorker | None = None
        self.streaming_text = ""
        self.live_bubble: MessageBubble | None = None
        self.models_used: set[str] = set()
        self._status_key = "ready"
        self._status_args: dict = {}
        self.key_dialog: KeyDialog | None = None
        self._auth_failed = False
        self.session_id = str(uuid.uuid4())
        
        # Initialize agent systems
        self.memory = None
        self.tools = None
        self.rag = None
        self.gen = None
        self.agent_mode = self.settings.value("agent_mode", True, type=bool)
        if AGENT_AVAILABLE:
            try:
                self.memory = MemorySystem()
                self.tools = ToolRegistry()
                from rag_system import RAGSystem
                from generation import GenerationEngine
                self.rag = RAGSystem()
                self.gen = GenerationEngine()
                print("Agent systems initialized successfully")
            except Exception as e:
                print(f"Failed to initialize agent systems: {e}")

        self._stream_timer = QTimer(self)
        self._stream_timer.setInterval(60)
        self._stream_timer.timeout.connect(self._repaint_stream)

        self.setMinimumSize(660, 560)
        self._build_ui()
        self._apply_theme()
        self._restore_state()
        self._retranslate()
        self.input_field.setFocus()

        # First run: guide the user straight into key setup.
        if not self.api_key:
            QTimer.singleShot(450, self.open_key_dialog)

    # ------------------------------ helpers --------------------------------
    def t(self, key: str) -> str:
        return STRINGS[self.lang][key]

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_chat_area(), stretch=1)
        layout.addWidget(self._build_footer())

        self.shortcut_save = QShortcut(QKeySequence.StandardKey.Save, self)
        self.shortcut_save.activated.connect(self.export_markdown)
        self.shortcut_new = QShortcut(QKeySequence.StandardKey.New, self)
        self.shortcut_new.activated.connect(self.new_chat)
        self.shortcut_stop = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut_stop.activated.connect(self.stop_generation)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        row = QHBoxLayout(header)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(12)

        logo = QLabel("G")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(34, 34)
        row.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.title_label = QLabel()
        self.title_label.setObjectName("appTitle")
        self.tagline_label = QLabel()
        self.tagline_label.setObjectName("tagline")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.tagline_label)
        row.addLayout(title_box)
        row.addStretch()

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(190)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        row.addWidget(self.model_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.setCursor(Qt.PointingHandCursor)
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("বাংলা", "bn")
        self.lang_combo.setMinimumWidth(104)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        row.addWidget(self.lang_combo)

        self.btn_export = QPushButton()
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.clicked.connect(self.export_markdown)
        row.addWidget(self.btn_export)

        self.btn_new = QPushButton()
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_chat)
        row.addWidget(self.btn_new)

        self.btn_upload = QPushButton("📁")
        self.btn_upload.setObjectName("settings")
        self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setFixedSize(38, 32)
        self.btn_upload.setToolTip("Upload files for RAG")
        if hasattr(self, 'upload_file'):
            self.btn_upload.clicked.connect(self.upload_file)
        row.addWidget(self.btn_upload)

        self.btn_clear = QPushButton("🗑")
        self.btn_clear.setObjectName("settings")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setFixedSize(38, 32)
        self.btn_clear.setToolTip("Clear all memories")
        if hasattr(self, 'clear_memories'):
            self.btn_clear.clicked.connect(self.clear_memories)
        row.addWidget(self.btn_clear)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setObjectName("settings")
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setFixedSize(38, 32)
        self.btn_settings.clicked.connect(lambda: self.open_key_dialog())
        row.addWidget(self.btn_settings)
        return header

    def _build_chat_area(self) -> QWidget:
        self.scroll = QScrollArea()
        self.scroll.setObjectName("scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        canvas = QWidget()
        canvas.setObjectName("canvas")
        self.chat_layout = QVBoxLayout(canvas)
        self.chat_layout.setContentsMargins(20, 18, 20, 18)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch(0)

        self.welcome = self._build_welcome()
        self.chat_layout.insertWidget(0, self.welcome, 1)

        self.scroll.setWidget(canvas)
        self.scroll.viewport().installEventFilter(self)
        return self.scroll

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 - Qt signature
        if obj is self.scroll.viewport() and event.type() == QEvent.Resize:
            self._relayout_bubbles()
        return super().eventFilter(obj, event)

    def _relayout_bubbles(self) -> None:
        available = self.scroll.viewport().width() - 84
        for bubble in self.bubbles:
            bubble.set_available_width(available)

    def _build_welcome(self) -> QWidget:
        box = QWidget()
        box.setObjectName("welcome")
        column = QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)
        column.addStretch(1)

        self.welcome_title = QLabel()
        self.welcome_title.setObjectName("welcomeTitle")
        self.welcome_title.setAlignment(Qt.AlignCenter)
        self.welcome_title.setWordWrap(True)
        column.addWidget(self.welcome_title)

        self.welcome_sub = QLabel()
        self.welcome_sub.setObjectName("welcomeSub")
        self.welcome_sub.setAlignment(Qt.AlignCenter)
        self.welcome_sub.setWordWrap(True)
        column.addWidget(self.welcome_sub)

        connect_row = QHBoxLayout()
        connect_row.setContentsMargins(0, 8, 0, 0)
        connect_row.addStretch()
        self.btn_connect = QPushButton()
        self.btn_connect.setObjectName("connect")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.clicked.connect(lambda: self.open_key_dialog())
        connect_row.addWidget(self.btn_connect)
        connect_row.addStretch()
        column.addLayout(connect_row)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.setContentsMargins(0, 18, 0, 0)
        chips.addStretch()
        self.chip_buttons: list[QPushButton] = []
        for _ in range(3):
            chip = QPushButton()
            chip.setObjectName("chip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _=False, b=chip: self._use_suggestion(b.text()))
            chips.addWidget(chip)
            self.chip_buttons.append(chip)
        chips.addStretch()
        column.addLayout(chips)
        column.addStretch(1)
        return box

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("footer")
        column = QVBoxLayout(footer)
        column.setContentsMargins(18, 8, 18, 14)
        column.setSpacing(7)

        self.status_label = QLabel()
        self.status_label.setObjectName("status")
        column.addWidget(self.status_label)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.input_field = Composer()
        self.input_field.submitted.connect(self.send_message)
        self.input_field.textChanged.connect(self._update_send_state)
        row.addWidget(self.input_field, stretch=1)

        self.btn_send = QPushButton()
        self.btn_send.setObjectName("send")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setFixedHeight(46)
        self.btn_send.setMinimumWidth(96)
        self.btn_send.clicked.connect(self.send_message)
        row.addWidget(self.btn_send)

        column.addLayout(row)
        return footer

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#root {{ background-color: {COLORS['bg']}; }}
            QFrame#header {{
                background-color: {COLORS['panel']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            QFrame#footer {{
                background-color: {COLORS['panel']};
                border-top: 1px solid {COLORS['border']};
            }}
            QLabel#logo {{
                background-color: {COLORS['accent']};
                color: #061020;
                border-radius: 9px;
                font-size: 17px;
                font-weight: 700;
            }}
            QLabel#appTitle {{ color: #eef4ff; font-size: 15px; font-weight: 600; }}
            QLabel#tagline {{ color: {COLORS['muted']}; font-size: 11px; }}
            QLabel#status {{ color: {COLORS['muted']}; font-size: 11px; }}
            QLabel#welcomeTitle {{
                color: #e9f0fb; font-size: 22px; font-weight: 600;
            }}
            QLabel#welcomeSub {{ color: {COLORS['muted']}; font-size: 13px; }}
            QScrollArea#scroll {{ background-color: {COLORS['bg']}; border: none; }}
            QWidget#canvas {{ background-color: {COLORS['bg']}; }}

            QFrame#userCard {{
                background-color: {COLORS['user_card']};
                border: 1px solid #2a4a76;
                border-radius: 14px;
            }}
            QFrame#botCard {{
                background-color: {COLORS['bot_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
            }}
            QFrame#errorCard {{
                background-color: {COLORS['error_card']};
                border: 1px solid #5a2a2f;
                border-radius: 14px;
            }}
            QLabel#bubbleBody {{
                color: {COLORS['text']};
                font-size: 13px;
                background: transparent;
            }}

            QPushButton#copyBtn {{
                background: transparent;
                border: none;
                color: {COLORS['muted']};
                font-size: 10px;
                padding: 1px 6px;
                border-radius: 5px;
            }}
            QPushButton#copyBtn:hover {{ color: {COLORS['accent']}; background: #223047; }}

            QPushButton#chip {{
                background-color: transparent;
                color: #b9c6dc;
                border: 1px solid #2b3a52;
                border-radius: 15px;
                padding: 7px 14px;
                font-size: 12px;
            }}
            QPushButton#chip:hover {{
                background-color: #1c2534;
                border-color: {COLORS['accent']};
                color: #e8f0ff;
            }}

            QPlainTextEdit#composer {{
                background-color: {COLORS['bg']};
                color: {COLORS['text']};
                border: 1px solid #2b3a52;
                border-radius: 12px;
                padding: 11px 13px;
                font-size: 13px;
                selection-background-color: {COLORS['accent']};
            }}
            QPlainTextEdit#composer:focus {{ border: 1px solid {COLORS['accent']}; }}

            QPushButton#send {{
                background-color: {COLORS['accent']};
                color: #061020;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#send:hover {{ background-color: #6ba6ff; }}
            QPushButton#send:disabled {{ background-color: #2b3d59; color: #7f92ad; }}

            QPushButton#connect {{
                background-color: {COLORS['accent']};
                color: #061020;
                border: none;
                border-radius: 10px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#connect:hover {{ background-color: #6ba6ff; }}

            QPushButton#settings {{ font-size: 15px; padding: 0; }}
            QPushButton#settings[needsKey="true"] {{
                color: #ffb020;
                border-color: #7a5a12;
                background-color: #241d0d;
            }}

            QPushButton {{
                background-color: #1d2635;
                color: #cfdaec;
                border: 1px solid #2b3a52;
                border-radius: 9px;
                padding: 7px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #253349; border-color: #3a4d6b; }}
            QPushButton:disabled {{ color: #5d6b80; background-color: #182030; }}

            QComboBox {{
                background-color: #1d2635;
                color: #cfdaec;
                border: 1px solid #2b3a52;
                border-radius: 9px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{ border-color: #3a4d6b; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{
                background-color: #1a2231;
                color: #cfdaec;
                border: 1px solid #2b3a52;
                selection-background-color: #26364f;
                outline: none;
            }}

            QScrollBar:vertical {{
                background: transparent; width: 10px; margin: 4px 2px 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: #2c3a52; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: #3d5171; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            """
        )

    # --------------------------- translations ------------------------------
    def _retranslate(self) -> None:
        s = STRINGS[self.lang]
        self.setWindowTitle(s["app_title"])
        self.title_label.setText(s["app_title"])
        self.tagline_label.setText(s["tagline"])
        self.btn_new.setText(s["new_chat"])
        self.btn_new.setToolTip(f"{s['new_chat']}  (Ctrl+N)")
        self.btn_export.setText(s["export"])
        self.btn_export.setToolTip(f"{s['export']} .md  (Ctrl+S)")
        self.lang_combo.setToolTip(s["language"])
        self.input_field.setPlaceholderText(s["placeholder"])
        self.input_field.setToolTip(s["composer_hint"])
        self.welcome_title.setText(s["welcome_title"])
        self.welcome_sub.setText(s["welcome_sub"])
        self.btn_connect.setText(s["connect_groq"])

        for chip, text in zip(self.chip_buttons, s["suggestions"]):
            chip.setText(text)

        self._refresh_model_combo()

        for bubble in self.bubbles:
            bubble.retranslate(s)

        if self.worker is not None and self.worker.isRunning():
            self.btn_send.setText(s["stop"])
        else:
            self.btn_send.setText(s["send"])
        self._update_send_state()
        self._apply_status()
        self._refresh_key_ui()

    def _refresh_model_combo(self) -> None:
        current = self.model_combo.currentData() or self.settings.value(
            "model", DEFAULT_MODEL, type=str
        )
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model_id, name, tag in MODELS:
            tag_text = STRINGS[self.lang][f"model_{tag}"]
            self.model_combo.addItem(f"{name}  ·  {tag_text}", model_id)
        index = self.model_combo.findData(current)
        self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        self.model_combo.blockSignals(False)

    def _apply_status(self) -> None:
        text = STRINGS[self.lang][self._status_key]
        try:
            text = text.format(**self._status_args)
        except (KeyError, IndexError):
            pass
        self.status_label.setText(text)

    def set_status(self, key: str, **kwargs) -> None:
        self._status_key = key
        self._status_args = kwargs
        self._apply_status()

    # ------------------------------ settings -------------------------------
    def _restore_state(self) -> None:
        model = self.settings.value("model", DEFAULT_MODEL, type=str)
        index = self.model_combo.findData(model)
        if index >= 0:
            self.model_combo.blockSignals(True)
            self.model_combo.setCurrentIndex(index)
            self.model_combo.blockSignals(False)
        lang_index = self.lang_combo.findData(self.lang)
        if lang_index >= 0:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(lang_index)
            self.lang_combo.blockSignals(False)
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(880, 720)

    def _save_state(self) -> None:
        self.settings.setValue("model", self.model_combo.currentData())
        self.settings.setValue("lang", self.lang)
        self.settings.setValue("geometry", self.saveGeometry())

    # --------------------------- API key setup ----------------------------
    def open_key_dialog(self, error: str = "") -> None:
        if self.key_dialog is None:
            self.key_dialog = KeyDialog(self)
        self.key_dialog.configure(error)
        self.key_dialog.adjustSize()
        self.key_dialog.show()
        self.key_dialog.raise_()
        self.key_dialog.activateWindow()
        if not self.api_key:
            self.key_dialog.input.setFocus()

    def apply_api_key(self, key: str, verified: bool = True) -> None:
        try:
            save_key_to_env(key)
        except OSError:
            QMessageBox.warning(
                self, self.t("key_title_existing"), self.t("key_env_failed")
            )
        self.api_key = key
        os.environ["GROQ_API_KEY"] = key
        self._refresh_key_ui()
        self._status_flash("status_connected" if verified else "status_key_unverified")

    def clear_api_key(self) -> None:
        try:
            remove_key_from_env()
        except OSError:
            pass
        self.api_key = ""
        os.environ.pop("GROQ_API_KEY", None)
        self._refresh_key_ui()
        self._status_flash("status_key_removed")

    def _refresh_key_ui(self) -> None:
        if not hasattr(self, "btn_settings"):
            return
        has = bool(self.api_key)
        label = self.t("key_set" if has else "key_not_set")
        self.btn_connect.setVisible(not has)
        self.btn_settings.setToolTip(label)
        self.btn_settings.setAccessibleName(label)
        self.btn_settings.setProperty("needsKey", not has)
        style = self.btn_settings.style()
        style.unpolish(self.btn_settings)
        style.polish(self.btn_settings)

    def _status_flash(self, key: str, timeout: int = 4500) -> None:
        self.set_status(key)
        QTimer.singleShot(timeout, self._status_reset)

    def _status_reset(self) -> None:
        if self.worker is None or not self.worker.isRunning():
            self.set_status("ready")

    @Slot()
    def _on_auth_failed(self) -> None:
        self._auth_failed = True
        # Let the error bubble paint before the dialog appears.
        QTimer.singleShot(0, lambda: self.open_key_dialog(self.t("key_invalid2")))

    # ------------------------------- events --------------------------------
    def _on_lang_changed(self) -> None:
        lang = self.lang_combo.currentData()
        if lang == self.lang:
            return
        self.lang = lang
        self._retranslate()
        self._save_state()

    def _on_model_changed(self) -> None:
        self._save_state()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt signature
        super().resizeEvent(event)
        self.tagline_label.setVisible(self.width() >= 860)

    def _update_send_state(self) -> None:
        running = self.worker is not None and self.worker.isRunning()
        if running:
            self.btn_send.setEnabled(True)
            return
        self.btn_send.setEnabled(bool(self.input_field.toPlainText().strip()))

    def _set_generating(self, generating: bool) -> None:
        self.input_field.setEnabled(not generating)
        self.btn_new.setEnabled(not generating)
        self.model_combo.setEnabled(not generating)
        self.btn_send.setText(self.t("stop") if generating else self.t("send"))
        self.btn_send.setEnabled(True)
        if not generating:
            self._update_send_state()

    # ------------------------------- actions -------------------------------
    @Slot()
    def new_chat(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        for bubble in self.bubbles:
            self.chat_layout.removeWidget(bubble)
            bubble.setParent(None)
            bubble.deleteLater()
        self.bubbles.clear()
        self.history.clear()
        self.models_used.clear()
        self.welcome.setVisible(True)
        self.set_status("ready")
        self.input_field.setFocus()

    def _use_suggestion(self, text: str) -> None:
        self.input_field.set_text(text)
        self.send_message()
    
    def upload_file(self) -> None:
        if not self.rag:
            QMessageBox.information(self, "RAG Not Available", "RAG system not initialized. Install dependencies.")
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Upload File for RAG", "", 
            "Documents (*.txt *.pdf *.docx *.md *.json);;All Files (*)"
        )
        if filepath:
            try:
                result = self.rag.add_document(filepath)
                if result.get('success'):
                    QMessageBox.information(self, "Success", f"Uploaded {result.get('chunks')} chunks from {filepath.split('/')[-1].split('\\\\')[-1]}")
                else:
                    QMessageBox.warning(self, "Error", result.get('error', 'Failed'))
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def clear_memories(self) -> None:
        if not self.memory:
            QMessageBox.information(self, "Memory Not Available", "Memory system not initialized.")
            return
        reply = QMessageBox.question(
            self, "Clear Memories", 
            "This will clear all conversation history and facts. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                import sqlite3
                conn = sqlite3.connect(self.memory.db_path)
                cur = conn.cursor()
                cur.execute('DELETE FROM conversations')
                cur.execute('DELETE FROM facts')
                cur.execute('DELETE FROM memory_map')
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "Memories cleared successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    @Slot()
    def send_message(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.stop_generation()
            return

        text = self.input_field.toPlainText().strip()
        if not text:
            return
        if not self.api_key:
            self.open_key_dialog()
            return

        self.welcome.setVisible(False)
        self.history.append({"role": "user", "content": text})
        self.models_used.add(self.model_combo.currentData())
        self._add_bubble("user", text)
        self.input_field.clear()
        
        # Store in memory
        if self.memory and self.agent_mode:
            try:
                self.memory.add_conversation(self.session_id, "user", text)
            except Exception as e:
                print(f"Memory error: {e}")

        self.streaming_text = ""
        self.live_bubble = self._add_bubble("assistant", "", streaming=True)
        self._stream_timer.start()

        self._set_generating(True)
        self.set_status("thinking")

        # Build messages with memory context
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add memory context if available
        if self.memory and self.agent_mode:
            try:
                memory_context = self.memory.get_memory_context(text)
                if memory_context:
                    messages.append({"role": "system", "content": f"Relevant context from memory:\n{memory_context}"})
            except Exception as e:
                print(f"Memory context error: {e}")
        
        # Add RAG context if available
        if self.rag and self.agent_mode:
            try:
                rag_context = self.rag.get_context(text)
                if rag_context:
                    messages.append({"role": "system", "content": rag_context})
            except Exception as e:
                print(f"RAG context error: {e}")
        
        messages += self._trimmed_history()
        self.worker = ChatWorker(
            api_key=self.api_key,
            model=self.model_combo.currentData(),
            messages=messages,
            parent=self,
        )
        self.worker.chunk_received.connect(self.on_chunk)
        self.worker.response_finished.connect(self.on_finished)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.auth_failed.connect(self._on_auth_failed)
        self.worker.finished.connect(self._on_worker_done)
        self.worker.start()

    def _trimmed_history(self) -> list[dict]:
        """Keep the last N turns so long chats stay within the context window."""
        limit = self.MAX_HISTORY_TURNS * 2
        if len(self.history) <= limit:
            return list(self.history)
        return self.history[-limit:]

    def _add_bubble(self, role: str, text: str, error: bool = False, streaming: bool = False) -> MessageBubble:
        bubble = MessageBubble(role, text, STRINGS[self.lang], error=error)
        bubble.set_available_width(self.scroll.viewport().width() - 84)
        if streaming:
            bubble.set_text(text, streaming=True)
        self.bubbles.append(bubble)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def _repaint_stream(self) -> None:
        if self.live_bubble is None:
            return
        self.live_bubble.set_text(self.streaming_text, streaming=True)
        self._scroll_to_bottom()

    @Slot(str)
    def on_chunk(self, piece: str) -> None:
        if not self.streaming_text:
            self.set_status("streaming")
        self.streaming_text += piece

    @Slot(str)
    def on_finished(self, full_text: str) -> None:
        self._stream_timer.stop()
        final = full_text.strip() or self.t("empty_reply")
        self.history.append({"role": "assistant", "content": final})
        if self.live_bubble is not None:
            self.live_bubble.set_text(final)
        self.live_bubble = None
        self._set_generating(False)
        self.set_status("ready")
        self.input_field.setFocus()
        
        # Store in memory
        if self.memory and self.agent_mode:
            try:
                self.memory.add_conversation(self.session_id, "assistant", final)
                # Extract potential facts (simple heuristic)
                if len(final) > 50 and any(word in final.lower() for word in ['you are', 'your', 'prefer', 'like', 'name is']):
                    pass  # Could add fact extraction logic here
            except Exception as e:
                print(f"Memory error: {e}")

    @Slot(str)
    def on_error(self, message: str) -> None:
        self._stream_timer.stop()
        if self.live_bubble is not None:
            self.live_bubble.setParent(None)
            self.live_bubble.deleteLater()
            if self.live_bubble in self.bubbles:
                self.bubbles.remove(self.live_bubble)
        self.live_bubble = None
        if self._auth_failed:
            message = self.t("key_invalid")
            self._auth_failed = False
        self.history.append({"role": "assistant", "content": f"**Error:** {message}"})
        self._add_bubble("assistant", message, error=True)
        self._set_generating(False)
        self.set_status("ready")

    def stop_generation(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.set_status("stopping")

    @Slot()
    def _on_worker_done(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll.verticalScrollBar()
        QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))

    # ------------------------------- export --------------------------------
    def build_markdown(self) -> str:
        s = STRINGS[self.lang]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        models = ", ".join(sorted(self.models_used)) or "n/a"
        turns = sum(1 for m in self.history if m["role"] == "user")
        lines = [
            f"# {s['export_title']}",
            "",
            f"- **{s['export_exported']}:** {now}",
            f"- **{s['export_model']}:** {models}",
            f"- **{s['export_turns']}:** {turns}",
            "",
            "---",
            "",
        ]
        for message in self.history:
            who = s["you"] if message["role"] == "user" else s["assistant"]
            lines += [f"**{who}**", "", message["content"].strip(), "", "---", ""]
        return "\n".join(lines)

    def write_markdown(self, path: str) -> None:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(self.build_markdown())

    @Slot()
    def export_markdown(self) -> None:
        if not self.history:
            QMessageBox.information(
                self, self.t("export_empty_title"), self.t("export_empty_body")
            )
            return
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        suggested = os.path.join(
            os.path.expanduser("~"), "Desktop", f"groq-chat-{stamp}.md"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, self.t("export"), suggested, "Markdown (*.md);;All files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".md"):
            path += ".md"
        try:
            self.write_markdown(path)
        except OSError as exc:
            QMessageBox.critical(self, self.t("export_failed"), str(exc))
            return
        self.set_status("status_exported", name=os.path.basename(path))

    # ------------------------------- shutdown ------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 - Qt signature
        self._save_state()
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()


# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
def install_fonts() -> None:
    """Make sure a Bengali-capable font is available for Qt."""
    families = set(QFontDatabase.families())
    if "Nirmala UI" in families:
        return
    for path in (
        r"C:\Windows\Fonts\Nirmala.ttc",
        r"C:\Windows\Fonts\Nirmala.ttf",
    ):
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
            return


def main() -> int:
    app = QApplication(sys.argv)
    install_fonts()

    # Create splash screen
    splash_pixmap = QPixmap(400, 300)
    splash_pixmap.fill(Qt.transparent)
    painter = QPainter(splash_pixmap)
    gradient = QLinearGradient(0, 0, 0, 300)
    gradient.setColorAt(0, Qt.darkBlue)
    gradient.setColorAt(1, Qt.black)
    painter.fillRect(0, 0, 400, 300, gradient)
    painter.setPen(Qt.white)
    font = QFont("Segoe UI", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 120, 400, 50, Qt.AlignCenter, "GroqChatbot")
    font2 = QFont("Segoe UI", 12)
    painter.setFont(font2)
    painter.drawText(0, 150, 400, 30, Qt.AlignCenter, "AI Agent with Memory & Tools")
    painter.drawText(0, 250, 400, 30, Qt.AlignCenter, "Loading...")
    painter.end()
    
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    app.processEvents()

    font = QFont()
    font.setFamilies(["Segoe UI", "Nirmala UI", "Noto Sans Bengali", "Segoe UI Emoji"])
    font.setPointSize(10)
    app.setFont(font)
    
    splash.showMessage("Initializing...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()

    window = ChatBotWindow()
    splash.finish(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
