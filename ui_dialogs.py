"""Advanced dialogs for GroqChatbot.

Settings, the live database browser, the tool workbench and the generation
studio live here so the main window stays readable. Every dialog works with
the plain objects exposed by ``ChatBotWindow`` (memory, rag, tools, gen).
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_paths import DATA_DIR, GENERATED_DIR, readable_size
from ui_theme import APP_VERSION, make_logo
from ui_widgets import Badge


def L(host, en: str, bn: Optional[str] = None) -> str:
    if getattr(host, "lang", "en") == "bn" and bn:
        return bn
    return en


def _muted(text: str, size: float = 10.5) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(f"color:#8a98ad; font-size:{size}px;")
    return label


def _plural(count, singular: str, plural: str | None = None) -> str:
    value = int(count or 0)
    word = singular if value == 1 else (plural or singular + "s")
    return f"{value} {word}"


def _button(text: str, primary: bool = False, danger: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    if primary:
        button.setObjectName("primary")
    if danger:
        button.setObjectName("danger")
    return button


def _page(tabs: QTabWidget, title: str) -> tuple[QScrollArea, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    inner = QWidget()
    inner.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(16, 14, 16, 16)
    layout.setSpacing(11)
    scroll.setWidget(inner)
    tabs.addTab(scroll, title)
    return scroll, layout


def _group(title: str, parent_layout: QVBoxLayout) -> tuple[QGroupBox, QVBoxLayout]:
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(12, 14, 12, 10)
    layout.setSpacing(8)
    parent_layout.addWidget(box)
    return box, layout


class SettingsDialog(QDialog):
    """One place for models, agent behaviour, keys, memory and studio defaults."""

    def __init__(self, host, models: List[tuple]) -> None:
        super().__init__(host)
        self.host = host
        self.models = models
        self.provider_inputs: Dict[str, QLineEdit] = {}
        self.stat_labels: Dict[str, QLabel] = {}
        self.setWindowTitle(L(host, "Settings", "সেটিংস"))
        self.setModal(True)
        self.setMinimumSize(790, 660)
        self.resize(840, 700)
        self.setStyleSheet(host.styleSheet())
        self._build()
        self._load()
        self._refresh_stats()

    # ------------------------------------------------------------- scaffold
    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(18, 16, 18, 16)
        column.setSpacing(10)

        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(make_logo(38, self.host.palette))
        head.addWidget(logo)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = QLabel(L(self.host, "Settings & system", "সেটিংস ও সিস্টেম"))
        title.setObjectName("dlgTitle")
        titles.addWidget(title)
        titles.addWidget(_muted(
            L(self.host, "Everything is stored locally on this computer.",
              "সবকিছু এই কম্পিউটারেই সংরক্ষিত থাকে।")
        ))
        head.addLayout(titles)
        head.addStretch()
        close = QPushButton("✕")
        close.setObjectName("dialClose")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.reject)
        head.addWidget(close)
        column.addLayout(head)

        self.tabs = QTabWidget()
        column.addWidget(self.tabs, 1)
        self._build_chat_page()
        self._build_keys_page()
        self._build_memory_page()
        self._build_studio_page()
        self._build_about_page()

        footer = QHBoxLayout()
        footer.addWidget(_muted(f"GroqChatbot v{APP_VERSION}"))
        footer.addStretch()
        cancel = _button(L(self.host, "Cancel", "বাতিল"))
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        save = _button(L(self.host, "Save changes", "পরিবর্তন সংরক্ষণ"), primary=True)
        save.clicked.connect(self._save)
        footer.addWidget(save)
        column.addLayout(footer)

    # -------------------------------------------------------------- chat
    def _build_chat_page(self) -> None:
        _, layout = _page(self.tabs, L(self.host, "Chat & agent", "চ্যাট ও এজেন্ট"))

        box, form_layout = _group(L(self.host, "Model & interface", "মডেল ও ইন্টারফেস"), layout)
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)
        self.model_combo = QComboBox()
        for model_id, name, tag in self.models:
            self.model_combo.addItem(f"{name}  ·  {tag}", model_id)
        form.addRow("Model", self.model_combo)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("বাংলা", "bn")
        form.addRow("Language", self.lang_combo)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Midnight (dark)", "dark")
        self.theme_combo.addItem("Daylight (light)", "light")
        form.addRow("Theme", self.theme_combo)
        self.accent_combo = QComboBox()
        for label, key in (("Blue / violet", "blue"), ("Violet / pink", "violet"),
                           ("Emerald / cyan", "emerald"), ("Amber / red", "amber"),
                           ("Rose / violet", "rose")):
            self.accent_combo.addItem(label, key)
        form.addRow("Accent", self.accent_combo)
        self.compact_check = QCheckBox(L(self.host, "Compact message spacing", "সংক্ষিপ্ত বার্তা ব্যবধান"))
        form.addRow("", self.compact_check)
        form_layout.addLayout(form)

        box, form_layout = _group(L(self.host, "Response behaviour", "উত্তরের আচরণ"), layout)
        temp_row = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setSingleStep(5)
        self.temp_value = QLabel("0.70")
        self.temp_value.setMinimumWidth(38)
        self.temp_slider.valueChanged.connect(
            lambda value: self.temp_value.setText(f"{value / 100:.2f}")
        )
        temp_row.addWidget(self.temp_slider, 1)
        temp_row.addWidget(self.temp_value)
        form_layout.addWidget(QLabel("Creativity / temperature"))
        form_layout.addLayout(temp_row)
        form_layout.addWidget(_muted(
            "Lower is precise, higher is more creative. 0.6–0.8 works well for most chats."
        ))

        tokens_row = QHBoxLayout()
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(256, 8192)
        self.tokens_spin.setSingleStep(256)
        self.tokens_spin.setSuffix(" tokens")
        tokens_row.addWidget(self.tokens_spin)
        self.history_spin = QSpinBox()
        self.history_spin.setRange(2, 100)
        self.history_spin.setSuffix(" turns kept")
        tokens_row.addWidget(self.history_spin)
        tokens_row.addStretch()
        form_layout.addLayout(tokens_row)

        prompt_head = QHBoxLayout()
        prompt_head.addWidget(QLabel(L(self.host, "System prompt", "সিস্টেম প্রম্পট")))
        prompt_head.addStretch()
        reset = _button(L(self.host, "Reset", "রিসেট"))
        reset.clicked.connect(self._reset_prompt)
        prompt_head.addWidget(reset)
        form_layout.addLayout(prompt_head)
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setMinimumHeight(108)
        self.prompt_edit.setPlaceholderText("Instructions the assistant always follows…")
        form_layout.addWidget(self.prompt_edit)

        box, form_layout = _group(L(self.host, "Agent systems", "এজেন্ট সিস্টেম"), layout)
        self.agent_check = QCheckBox(
            L(self.host, "Enable agent mode (tools, memory and RAG)",
              "এজেন্ট মোড চালু (টুল, মেমোরি ও RAG)")
        )
        form_layout.addWidget(self.agent_check)
        self.memory_check = QCheckBox(
            L(self.host, "Long-term memory — remember facts and past chats",
              "দীর্ঘমেয়াদি মেমোরি — তথ্য ও পুরনো চ্যাট মনে রাখে")
        )
        self.rag_check = QCheckBox(
            L(self.host, "Document RAG — answer from uploaded files",
              "ডকুমেন্ট RAG — আপলোড করা ফাইল থেকে উত্তর")
        )
        self.tools_check = QCheckBox(
            L(self.host, "Tool calling — web, calculator, files, Python",
              "টুল কলিং — ওয়েব, ক্যালকুলেটর, ফাইল, পাইথন")
        )
        form_layout.addWidget(self.memory_check)
        form_layout.addWidget(self.rag_check)
        form_layout.addWidget(self.tools_check)

        perms = QHBoxLayout()
        self.write_check = QCheckBox(L(self.host, "Allow file writing", "ফাইল লেখা অনুমোদন"))
        self.code_check = QCheckBox(L(self.host, "Allow Python execution", "পাইথন চালানো অনুমোদন"))
        self.net_check = QCheckBox(L(self.host, "Allow network tools", "নেটওয়ার্ক টুল অনুমোদন"))
        perms.addWidget(self.write_check)
        perms.addWidget(self.code_check)
        perms.addWidget(self.net_check)
        perms.addStretch()
        form_layout.addLayout(perms)
        form_layout.addWidget(_muted(
            "File tools are sandboxed to your home folder, the app folder and temp. "
            "Code runs in a separate process with a 20 second timeout."
        ))
        layout.addStretch()

    # -------------------------------------------------------------- keys
    def _build_keys_page(self) -> None:
        _, layout = _page(self.tabs, L(self.host, "API keys", "এপিআই কী"))
        layout.addWidget(_muted(
            "Keys are written to the local .env file and never leave this computer. "
            "Only Groq is required. Everything else unlocks optional providers."
        ))

        box, box_layout = _group("Groq (required)", layout)
        row = QHBoxLayout()
        self.groq_input = QLineEdit()
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.groq_input.setPlaceholderText("gsk_… (leave blank to keep the current key)")
        row.addWidget(self.groq_input, 1)
        guided = _button(L(self.host, "Guided setup…", "গাইডেড সেটআপ…"))
        guided.clicked.connect(self._guided_key)
        row.addWidget(guided)
        link = QPushButton("console.groq.com/keys ↗")
        link.setObjectName("link")
        link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys")))
        row.addWidget(link)
        box_layout.addLayout(row)
        self.groq_state = _muted("")
        box_layout.addWidget(self.groq_state)

        box, box_layout = _group(
            L(self.host, "Optional generation providers", "ঐচ্ছিক জেনারেশন প্রোভাইডার"), layout
        )
        providers = [
            ("huggingface", "HuggingFace", "HUGGINGFACE_API_KEY",
             "https://huggingface.co/settings/tokens", "Free tier · images & music"),
            ("replicate", "Replicate", "REPLICATE_API_TOKEN",
             "https://replicate.com/account/api-tokens", "Images, music & video"),
            ("stability", "Stability AI", "STABILITY_API_KEY",
             "https://platform.stability.ai/account/keys", "Stable Image Core"),
            ("fal", "fal.ai", "FAL_KEY",
             "https://fal.ai/dashboard/keys", "Fast FLUX & video"),
            ("together", "Together AI", "TOGETHER_API_KEY",
             "https://api.together.ai/settings/api-keys", "FLUX images"),
            ("openrouter", "OpenRouter", "OPENROUTER_API_KEY",
             "https://openrouter.ai/keys", "Extra model gateway"),
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(7)
        for row_index, (key, label, env_name, url, hint) in enumerate(providers):
            name = QLabel(label)
            name.setMinimumWidth(96)
            field = QLineEdit()
            field.setEchoMode(QLineEdit.Password)
            field.setPlaceholderText(hint)
            self.provider_inputs[key] = field
            pill = Badge("", "muted")
            pill.setFixedWidth(76)
            get_link = QPushButton("Get key ↗")
            get_link.setObjectName("link")
            get_link.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            grid.addWidget(name, row_index, 0)
            grid.addWidget(field, row_index, 1)
            grid.addWidget(pill, row_index, 2)
            grid.addWidget(get_link, row_index, 3)
            field.setProperty("badge", pill)
        box_layout.addLayout(grid)

        row = QHBoxLayout()
        self.show_keys = QCheckBox(L(self.host, "Show keys", "কী দেখান"))
        self.show_keys.toggled.connect(self._toggle_keys)
        row.addWidget(self.show_keys)
        row.addStretch()
        save_tip = _muted("Saved when you press “Save changes”.")
        row.addWidget(save_tip)
        box_layout.addLayout(row)
        layout.addStretch()

    # ------------------------------------------------------------ memory
    def _build_memory_page(self) -> None:
        _, layout = _page(self.tabs, L(self.host, "Memory & RAG", "মেমোরি ও RAG"))
        layout.addWidget(_muted(
            "The assistant's brain lives in two SQLite databases. Open the browser to "
            "inspect, search or delete individual rows."
        ))

        box, box_layout = _group("Live database", layout)
        grid = QGridLayout()
        grid.setSpacing(8)
        entries = [
            ("conversations", "Conversations", "💬"),
            ("facts", "Known facts", "🧠"),
            ("vectors", "Vector memories", "🧭"),
            ("documents", "Documents", "📚"),
            ("chunks", "RAG chunks", "🧩"),
            ("db_size", "Database size", "💾"),
        ]
        for index, (key, label, icon) in enumerate(entries):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:{self.host.palette['panel2']};"
                f" border:1px solid {self.host.palette['border']}; border-radius:9px; }}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 7, 10, 7)
            top = QLabel(f"{icon}  {label}")
            top.setStyleSheet(f"color:{self.host.palette['muted']}; font-size:9.5px;")
            value = QLabel("—")
            value.setStyleSheet(
                f"color:{self.host.palette['text']}; font-size:16px; font-weight:700;"
            )
            self.stat_labels[key] = value
            card_layout.addWidget(top)
            card_layout.addWidget(value)
            grid.addWidget(card, index // 3, index % 3)
        box_layout.addLayout(grid)

        self.mode_label = _muted("")
        self.path_label = _muted("")
        box_layout.addWidget(self.mode_label)
        box_layout.addWidget(self.path_label)

        actions = QGridLayout()
        actions.setSpacing(7)
        buttons = [
            ("🗃  Open database browser", self.host.open_database, False),
            ("📎  Upload documents", self.host.upload_file, True),
            ("📚  Manage documents", self.host.open_documents, False),
            ("🧠  Clear memories", self.host.clear_memories, False),
            ("📚  Clear document library", self.host.clear_rag, False),
            ("🔄  Rebuild vector index", self.host.reindex_embeddings, False),
            ("⬇  Export memory JSON", self.host.export_memory, False),
            ("📂  Open data folder", self.host.open_data_folder, False),
        ]
        for index, (label, slot, primary) in enumerate(buttons):
            btn = _button(label, primary=primary)
            btn.clicked.connect(slot)
            actions.addWidget(btn, index // 2, index % 2)
        box_layout.addLayout(actions)

        layout.addWidget(_muted(
            "Semantic recall needs the optional sentence-transformers and sqlite-vec packages. "
            "Without them every feature still works through fast full-text search."
        ))
        layout.addStretch()

    # ------------------------------------------------------------ studio
    def _build_studio_page(self) -> None:
        _, layout = _page(self.tabs, L(self.host, "Creation studio", "ক্রিয়েশন স্টুডিও"))
        layout.addWidget(_muted(
            "Choose defaults for image, illustration, music and video generation. "
            "Open the studio from the 🎨 button or the Generate menu."
        ))

        box, form_layout = _group("Defaults", layout)
        form = QFormLayout()
        form.setSpacing(8)
        self.image_model = QComboBox()
        self.music_model = QComboBox()
        self.video_model = QComboBox()
        self.style_combo = QComboBox()
        if getattr(self.host, "gen", None):
            for key, label in self.host.gen.model_labels("image").items():
                self.image_model.addItem(label, key)
            for key, label in self.host.gen.model_labels("music").items():
                self.music_model.addItem(label, key)
            for key, label in self.host.gen.model_labels("video").items():
                self.video_model.addItem(label, key)
        for style in ("digital art", "cinematic", "watercolour", "anime", "3D render",
                      "pencil sketch", "vintage poster", "isometric"):
            self.style_combo.addItem(style, style)
        form.addRow("Image model", self.image_model)
        form.addRow("Illustration style", self.style_combo)
        form.addRow("Music model", self.music_model)
        form.addRow("Video model", self.video_model)
        form_layout.addLayout(form)

        box_layout = QVBoxLayout()
        box, box_layout = _group("Provider status", layout)
        self.provider_grid = QGridLayout()
        self.provider_grid.setSpacing(5)
        box_layout.addLayout(self.provider_grid)

        row = QHBoxLayout()
        open_studio = _button(L(self.host, "🎨  Open generation studio", "🎨  জেনারেশন স্টুডিও"), primary=True)
        open_studio.clicked.connect(self._open_studio)
        row.addWidget(open_studio)
        open_folder = _button(L(self.host, "📂  Output folder", "📂  আউটপুট ফোল্ডার"))
        open_folder.clicked.connect(lambda: self.host.open_path(GENERATED_DIR))
        row.addWidget(open_folder)
        row.addStretch()
        box_layout.addLayout(row)
        layout.addStretch()

    # ------------------------------------------------------------- about
    def _build_about_page(self) -> None:
        _, layout = _page(self.tabs, L(self.host, "About", "পরিচিতি"))
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(make_logo(66, self.host.palette))
        head.addWidget(logo)
        titles = QVBoxLayout()
        name = QLabel(f"GroqChatbot {APP_VERSION}")
        name.setStyleSheet("font-size:20px; font-weight:700;")
        titles.addWidget(name)
        titles.addWidget(_muted(
            "Bilingual, local-first AI agent with long-term memory, document RAG, "
            "tool calling and a multi-provider creation studio."
        ))
        head.addLayout(titles, 1)
        layout.addLayout(head)

        features = QLabel(
            "<ul style='line-height:150%; margin-left:-18px;'>"
            "<li><b>Groq LPU</b> — GPT-OSS 20B/120B and Qwen models with live streaming</li>"
            "<li><b>Memory</b> — SQLite facts, conversations and optional vector recall</li>"
            "<li><b>RAG</b> — PDF, DOCX, TXT, MD, HTML, CSV, JSON, XLSX and source code</li>"
            "<li><b>Tools</b> — web search, page reader, calculator, files, Python, weather</li>"
            "<li><b>Studio</b> — FLUX / SDXL images, MusicGen audio, AI video</li>"
            "<li><b>Bilingual</b> — English and বাংলা throughout the interface</li>"
            "</ul>"
        )
        features.setTextFormat(Qt.RichText)
        features.setWordWrap(True)
        layout.addWidget(features)

        box, box_layout = _group("Keyboard shortcuts", layout)
        shortcuts = QLabel(
            "<table cellspacing='6'>"
            "<tr><td><b>Ctrl+N</b></td><td>New chat</td></tr>"
            "<tr><td><b>Ctrl+S</b></td><td>Export transcript</td></tr>"
            "<tr><td><b>Ctrl+D</b></td><td>Database browser</td></tr>"
            "<tr><td><b>Ctrl+T</b></td><td>Tool workbench</td></tr>"
            "<tr><td><b>Ctrl+G</b></td><td>Generation studio</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>Settings</td></tr>"
            "<tr><td><b>Esc</b></td><td>Stop generating</td></tr>"
            "</table>"
        )
        shortcuts.setTextFormat(Qt.RichText)
        box_layout.addWidget(shortcuts)

        links = QHBoxLayout()
        for label, url in (
            ("GitHub", "https://github.com/rhasan2026g-cell/GroqChatbot"),
            ("Groq Console", "https://console.groq.com"),
            ("Report an issue", "https://github.com/rhasan2026g-cell/GroqChatbot/issues"),
        ):
            button = QPushButton(label + " ↗")
            button.setObjectName("link")
            button.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(button)
        links.addStretch()
        layout.addLayout(links)
        layout.addWidget(_muted("MIT licensed. Built with PySide6 and the Groq SDK."))
        layout.addStretch()

    # -------------------------------------------------------------- state
    def _setting(self, key: str, default):
        value = self.host.settings.value(key, default)
        if isinstance(default, bool):
            try:
                return bool(value) if not isinstance(value, str) else value.lower() in ("true", "1", "yes")
            except Exception:
                return default
        return value

    def _load(self) -> None:
        host = self.host
        index = self.model_combo.findData(self._setting("model", self.models[0][0]))
        self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        index = self.lang_combo.findData(host.lang)
        self.lang_combo.setCurrentIndex(index if index >= 0 else 0)
        index = self.theme_combo.findData(self._setting("theme", "dark"))
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        index = self.accent_combo.findData(self._setting("accent", "blue"))
        self.accent_combo.setCurrentIndex(index if index >= 0 else 0)
        self.compact_check.setChecked(self._setting("compact", False))
        self.temp_slider.setValue(int(float(self._setting("temperature", 0.7)) * 100))
        self.tokens_spin.setValue(int(self._setting("max_tokens", 2048)))
        self.history_spin.setValue(int(self._setting("history_turns", 24)))
        self.prompt_edit.setPlainText(self._setting("system_prompt", host.default_system_prompt))
        self.agent_check.setChecked(self._setting("agent_mode", True))
        self.memory_check.setChecked(self._setting("memory_enabled", True))
        self.rag_check.setChecked(self._setting("rag_enabled", True))
        self.tools_check.setChecked(self._setting("tools_enabled", True))
        self.write_check.setChecked(self._setting("allow_file_write", True))
        self.code_check.setChecked(self._setting("allow_code_execution", True))
        self.net_check.setChecked(self._setting("allow_network", True))
        for key, field in self.provider_inputs.items():
            value = ""
            if getattr(host, "gen", None):
                value = host.gen.api_keys.get(key, "")
            field.setText(value)
            badge = field.property("badge")
            if isinstance(badge, Badge):
                badge.setText("Configured" if value else "Missing")
                badge.set_kind("ok" if value else "muted")
        if host.api_key:
            self.groq_state.setText(f"Connected · {host.mask_key(host.api_key)}")
            self.groq_state.setStyleSheet("color:#34d399; font-size:10.5px;")
        else:
            self.groq_state.setText("No Groq key yet.")
            self.groq_state.setStyleSheet("color:#fbbf24; font-size:10.5px;")
        index = self.image_model.findData(self._setting("default_image_model", "flux-schnell"))
        self.image_model.setCurrentIndex(index if index >= 0 else 0)
        index = self.music_model.findData(self._setting("default_music_model", "musicgen-small"))
        self.music_model.setCurrentIndex(index if index >= 0 else 0)
        index = self.video_model.findData(self._setting("default_video_model", "hunyuan"))
        self.video_model.setCurrentIndex(index if index >= 0 else 0)
        index = self.style_combo.findData(self._setting("illustration_style", "digital art"))
        self.style_combo.setCurrentIndex(index if index >= 0 else 0)
        self._refresh_providers()

    def _refresh_providers(self) -> None:
        while self.provider_grid.count():
            item = self.provider_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        gen = getattr(self.host, "gen", None)
        if not gen:
            self.provider_grid.addWidget(_muted("Generation engine unavailable."), 0, 0)
            return
        for index, (key, info) in enumerate(gen.provider_status().items()):
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{'#34d399' if info['configured'] else '#5f6f86'};")
            self.provider_grid.addWidget(dot, index // 2, (index % 2) * 2)
            self.provider_grid.addWidget(
                _muted(f"{info['label']} — {'ready' if info['configured'] else 'add a key'}", 10.5),
                index // 2, (index % 2) * 2 + 1,
            )

    def _refresh_stats(self) -> None:
        try:
            mem = self.host.memory.stats() if self.host.memory else {}
            rag = self.host.rag.stats() if self.host.rag else {}
        except Exception as exc:
            self.mode_label.setText(f"Could not read database stats: {exc}")
            return
        values = {
            "conversations": mem.get("conversations", 0),
            "facts": mem.get("facts", 0),
            "vectors": mem.get("vectors", 0),
            "documents": rag.get("documents", 0),
            "chunks": rag.get("chunks", 0),
            "db_size": mem.get("size_text", "0 B"),
        }
        for key, label in self.stat_labels.items():
            label.setText(str(values.get(key, "—")))
        self.mode_label.setText(
            f"Memory recall: {mem.get('memory_mode', 'keyword')}  ·  "
            f"Document search: {rag.get('search_mode', 'full-text')}  ·  "
            f"Vector engine: {'ready' if mem.get('vector_ready') else 'optional / not installed'}"
        )
        self.path_label.setText(
            f"Memory database: {mem.get('path', '—')}\nDocument database: {rag.get('path', '—')}"
        )

    # ------------------------------------------------------------- actions
    def _toggle_keys(self, show: bool) -> None:
        mode = QLineEdit.Normal if show else QLineEdit.Password
        self.groq_input.setEchoMode(mode)
        for field in self.provider_inputs.values():
            field.setEchoMode(mode)

    def _reset_prompt(self) -> None:
        self.prompt_edit.setPlainText(self.host.default_system_prompt)

    def _guided_key(self) -> None:
        self.host.open_key_dialog()
        QTimer.singleShot(200, self._sync_groq_state)

    def _sync_groq_state(self) -> None:
        if self.host.api_key:
            self.groq_state.setText(f"Connected · {self.host.mask_key(self.host.api_key)}")
            self.groq_state.setStyleSheet("color:#34d399; font-size:10.5px;")
        else:
            self.groq_state.setText("No Groq key yet.")
            self.groq_state.setStyleSheet("color:#fbbf24; font-size:10.5px;")

    def _open_studio(self) -> None:
        self.host.open_generator()
        self.accept()

    def _save(self) -> None:
        keys = {name: field.text().strip() for name, field in self.provider_inputs.items()}
        values = {
            "model": self.model_combo.currentData(),
            "lang": self.lang_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "accent": self.accent_combo.currentData(),
            "compact": self.compact_check.isChecked(),
            "temperature": round(self.temp_slider.value() / 100, 2),
            "max_tokens": self.tokens_spin.value(),
            "history_turns": self.history_spin.value(),
            "system_prompt": self.prompt_edit.toPlainText().strip(),
            "agent_mode": self.agent_check.isChecked(),
            "memory_enabled": self.memory_check.isChecked(),
            "rag_enabled": self.rag_check.isChecked(),
            "tools_enabled": self.tools_check.isChecked(),
            "allow_file_write": self.write_check.isChecked(),
            "allow_code_execution": self.code_check.isChecked(),
            "allow_network": self.net_check.isChecked(),
            "default_image_model": self.image_model.currentData(),
            "default_music_model": self.music_model.currentData(),
            "default_video_model": self.video_model.currentData(),
            "illustration_style": self.style_combo.currentData(),
            "provider_keys": keys,
        }
        groq_key = self.groq_input.text().strip()
        if groq_key:
            values["groq_key"] = groq_key
        try:
            self.host.apply_settings(values)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Settings", f"Could not save settings:\n{exc}")
            return
        self.accept()


# --------------------------------------------------------------------------- #
# Database browser
# --------------------------------------------------------------------------- #
class DatabaseDialog(QDialog):
    """Live window into conversations, facts, memories, documents and chunks."""

    def __init__(self, host, initial_tab: int = 0) -> None:
        super().__init__(host)
        self.host = host
        self.setWindowTitle(L(host, "Database browser", "ডেটাবেস ব্রাউজার"))
        self.setModal(True)
        self.setMinimumSize(940, 640)
        self.resize(1040, 720)
        self.setStyleSheet(host.styleSheet())
        self._build()
        self.tabs.setCurrentIndex(initial_tab)
        self.refresh()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(16, 14, 16, 14)
        column.setSpacing(9)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel(L(self.host, "Memory & data", "মেমোরি ও ডেটা"))
        title.setObjectName("dlgTitle")
        titles.addWidget(title)
        self.subtitle = _muted("")
        titles.addWidget(self.subtitle)
        head.addLayout(titles, 1)
        close = QPushButton("✕")
        close.setObjectName("dialClose")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.accept)
        head.addWidget(close)
        column.addLayout(head)

        tools_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(L(self.host, "Filter current table…", "বর্তমান টেবিল ফিল্টার…"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        tools_row.addWidget(self.search, 1)
        refresh = _button(L(self.host, "↻  Refresh", "↻  রিফ্রেশ"))
        refresh.clicked.connect(self.refresh)
        tools_row.addWidget(refresh)
        export = _button(L(self.host, "⬇  Export JSON", "⬇  JSON এক্সপোর্ট"))
        export.clicked.connect(self._export)
        tools_row.addWidget(export)
        open_folder = _button(L(self.host, "📂  Data folder", "📂  ডেটা ফোল্ডার"))
        open_folder.clicked.connect(self.host.open_data_folder)
        tools_row.addWidget(open_folder)
        column.addLayout(tools_row)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._sync_delete_button)
        self.table_conv = self._make_table(["ID", "When", "Role", "Session", "Content"])
        self.table_facts = self._make_table(["ID", "Fact", "Category", "Confidence", "When"])
        self.table_mem = self._make_table(["ID", "Type", "Ref", "Content"])
        self.table_docs = self._make_table(["ID", "File", "Type", "Chunks", "Size", "Added", "Path"])
        self.table_chunks = self._make_table(["ID", "Document", "#", "Text"])
        self.tabs.addTab(self.table_conv, f"💬 {L(self.host, 'Conversations', 'কথোপকথন')}")
        self.tabs.addTab(self.table_facts, f"🧠 {L(self.host, 'Facts', 'তথ্য')}")
        self.tabs.addTab(self.table_mem, f"🧭 {L(self.host, 'Memory index', 'মেমোরি ইনডেক্স')}")
        self.tabs.addTab(self.table_docs, f"📚 {L(self.host, 'Documents', 'ডকুমেন্ট')}")
        self.tabs.addTab(self.table_chunks, f"🧩 {L(self.host, 'RAG chunks', 'RAG চাঙ্ক')}")
        column.addWidget(self.tabs, 1)

        footer = QHBoxLayout()
        self.stats_label = _muted("")
        footer.addWidget(self.stats_label, 1)
        self.delete_btn = _button(L(self.host, "🗑  Delete selected", "🗑  নির্বাচিত মুছুন"), danger=True)
        self.delete_btn.clicked.connect(self._delete_selected)
        footer.addWidget(self.delete_btn)
        done = _button(L(self.host, "Done", "সম্পন্ন"), primary=True)
        done.clicked.connect(self.accept)
        footer.addWidget(done)
        column.addLayout(footer)

    def _make_table(self, headers: List[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        if headers:
            header.setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
        return table

    def _fill(self, table: QTableWidget, rows: List[List[Any]]) -> None:
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem()
                if isinstance(value, int) and not isinstance(value, bool):
                    item.setData(Qt.DisplayRole, value)
                else:
                    item.setData(Qt.DisplayRole, "" if value is None else str(value))
                if column_index == 0:
                    item.setData(Qt.UserRole, value)
                item.setToolTip(str(value)[:500])
                table.setItem(row_index, column_index, item)
        table.setSortingEnabled(True)

    def refresh(self) -> None:
        memory = self.host.memory
        rag = self.host.rag
        if not memory and not rag:
            self.stats_label.setText("Agent systems are not available.")
            return
        filter_text = self.search.text().strip().lower()
        if memory:
            convs = memory.search_conversations("", limit=1000)
            convs = sorted(
                convs,
                key=lambda row: (float(row.get("timestamp") or 0), int(row.get("id") or 0)),
                reverse=True,
            )
            rows = []
            for row in convs:
                stamp = datetime.fromtimestamp(row["timestamp"]).strftime("%Y-%m-%d %H:%M")
                rows.append([row["id"], stamp, row["role"], row["session_id"][:8], row["content"][:600]])
            self._fill(self.table_conv, rows)
            facts = memory.get_facts(limit=2000)
            self._fill(self.table_facts, [
                [f["id"], f["fact"], f["category"],
                 f"{float(f['confidence']):.2f}",
                 datetime.fromtimestamp(f["timestamp"]).strftime("%Y-%m-%d %H:%M")]
                for f in facts
            ])
            self._fill(self.table_mem, [
                [m["id"], m["type"], m["ref_id"], m["content"][:500]]
                for m in memory.list_memories(limit=2000)
            ])
        if rag:
            docs = rag.list_documents()
            self._fill(self.table_docs, [
                [d["id"], d["filename"], d["file_type"],
                 d["chunk_count"], readable_size(d["size_bytes"] or 0),
                 datetime.fromtimestamp(d["upload_date"]).strftime("%Y-%m-%d %H:%M"),
                 d["filepath"]]
                for d in docs
            ])
            self._fill(self.table_chunks, [
                [c["id"], c["filename"], c["chunk_index"], c["chunk_text"][:500]]
                for c in rag.list_chunks(limit=1000)
            ])
        mem_stats = memory.stats() if memory else {}
        rag_stats = rag.stats() if rag else {}
        self.subtitle.setText(
            f"{_plural(mem_stats.get('conversations', 0), 'conversation')} · "
            f"{_plural(mem_stats.get('facts', 0), 'fact')} · "
            f"{_plural(mem_stats.get('vectors', 0), 'vector memory', 'vector memories')} · "
            f"{_plural(rag_stats.get('documents', 0), 'document')} · "
            f"{_plural(rag_stats.get('chunks', 0), 'chunk')}"
        )
        self.stats_label.setText(
            f"Memory: {mem_stats.get('size_text', '—')} ({mem_stats.get('memory_mode', '—')})   ·   "
            f"RAG: {rag_stats.get('size_text', '—')} ({rag_stats.get('search_mode', '—')})"
        )
        self._apply_filter()
        self._sync_delete_button()

    def _apply_filter(self) -> None:
        needle = self.search.text().strip().lower()
        table = self.tabs.currentWidget()
        if not isinstance(table, QTableWidget):
            return
        for row in range(table.rowCount()):
            if not needle:
                table.setRowHidden(row, False)
                continue
            haystack = " ".join(
                table.item(row, column).text().lower()
                for column in range(table.columnCount())
                if table.item(row, column)
            )
            table.setRowHidden(row, needle not in haystack)

    def _sync_delete_button(self) -> None:
        if not hasattr(self, "delete_btn"):
            return
        index = self.tabs.currentIndex()
        self.delete_btn.setEnabled(index in (0, 1, 3))

    def _delete_selected(self) -> None:
        index = self.tabs.currentIndex()
        table = self.tabs.currentWidget()
        if not isinstance(table, QTableWidget):
            return
        rows = sorted({item.row() for item in table.selectedItems()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Delete", "Select one or more rows first.")
            return
        if QMessageBox.question(
            self, "Delete",
            f"Delete {len(rows)} selected row(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        for row in rows:
            item = table.item(row, 0)
            if not item:
                continue
            try:
                row_id = int(item.data(Qt.UserRole) or item.text())
            except Exception:
                continue
            if index == 0 and self.host.memory:
                self.host.memory.delete_conversation(row_id)
            elif index == 1 and self.host.memory:
                self.host.memory.delete_fact(row_id)
            elif index == 3 and self.host.rag:
                self.host.rag.delete_document(row_id)
        self.refresh()
        self.host.refresh_stats()
        self.host.set_status("ready")

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export data", str(Path.home() / "Desktop" / "groqchatbot-data.json"),
            "JSON (*.json)",
        )
        if not path:
            return
        payload = {
            "exported": datetime.now().isoformat(timespec="seconds"),
            "memory": self.host.memory.stats() if self.host.memory else {},
            "rag": self.host.rag.stats() if self.host.rag else {},
            "facts": self.host.memory.get_facts(limit=5000) if self.host.memory else [],
            "conversations": self.host.memory.recent_conversations(limit=5000) if self.host.memory else [],
            "documents": self.host.rag.list_documents() if self.host.rag else [],
        }
        try:
            Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.host.set_status("status_exported", name=os.path.basename(path))


# --------------------------------------------------------------------------- #
# Tool workbench
# --------------------------------------------------------------------------- #
class ToolWorker(QThread):
    finished_result = Signal(dict)

    def __init__(self, registry, name: str, arguments: dict, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.name = name
        self.arguments = arguments

    def run(self) -> None:
        try:
            result = self.registry.execute_tool(self.name, self.arguments)
        except Exception as exc:  # noqa: BLE001
            result = {"success": False, "error": str(exc)}
        self.finished_result.emit(result)


class ToolsDialog(QDialog):
    """Inspect and run any agent tool, with explicit permissions."""

    def __init__(self, host) -> None:
        super().__init__(host)
        self.host = host
        self.worker: ToolWorker | None = None
        self.setWindowTitle(L(host, "Tool workbench", "টুল ওয়ার্কবেঞ্চ"))
        self.setModal(True)
        self.setMinimumSize(860, 600)
        self.resize(940, 660)
        self.setStyleSheet(host.styleSheet())
        self._build()
        self._load_tools()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(16, 14, 16, 14)
        column.setSpacing(9)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel(L(self.host, "Tool workbench", "টুল ওয়ার্কবেঞ্চ"))
        title.setObjectName("dlgTitle")
        titles.addWidget(title)
        titles.addWidget(_muted(
            "Run any tool manually to see exactly what the agent can do. "
            "The model uses the same functions automatically during chat."
        ))
        head.addLayout(titles, 1)
        close = QPushButton("✕")
        close.setObjectName("dialClose")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.accept)
        head.addWidget(close)
        column.addLayout(head)

        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(_muted("AVAILABLE TOOLS", 9))
        self.tool_list = QListWidget()
        self.tool_list.currentItemChanged.connect(self._select_tool)
        left_layout.addWidget(self.tool_list, 1)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        self.tool_title = QLabel("—")
        self.tool_title.setObjectName("cardTitle")
        right_layout.addWidget(self.tool_title)
        self.tool_desc = _muted("")
        right_layout.addWidget(self.tool_desc)
        right_layout.addWidget(QLabel("Arguments (JSON)"))
        self.args_edit = QPlainTextEdit("{}")
        self.args_edit.setMinimumHeight(82)
        self.args_edit.setMaximumHeight(120)
        right_layout.addWidget(self.args_edit)
        run_row = QHBoxLayout()
        self.run_btn = _button(L(self.host, "▶  Run tool", "▶  টুল চালান"), primary=True)
        self.run_btn.clicked.connect(self._run)
        run_row.addWidget(self.run_btn)
        self.example_btn = _button(L(self.host, "Insert example", "উদাহরণ দিন"))
        self.example_btn.clicked.connect(self._insert_example)
        run_row.addWidget(self.example_btn)
        self.busy = QProgressBar()
        self.busy.setRange(0, 0)
        self.busy.setMaximumWidth(90)
        self.busy.hide()
        run_row.addWidget(self.busy)
        run_row.addStretch()
        right_layout.addLayout(run_row)
        right_layout.addWidget(QLabel("Result"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Tool output appears here…")
        right_layout.addWidget(self.output, 1)
        splitter.addWidget(right)
        splitter.setSizes([240, 600])
        column.addWidget(splitter, 1)

        perms = QHBoxLayout()
        self.write_check = QCheckBox("File writing")
        self.code_check = QCheckBox("Python execution")
        self.net_check = QCheckBox("Network")
        for check, key in ((self.write_check, "allow_file_write"),
                           (self.code_check, "allow_code_execution"),
                           (self.net_check, "allow_network")):
            check.setChecked(bool(self.host.get_setting(key, True)))
            perms.addWidget(check)
        apply_btn = _button(L(self.host, "Apply permissions", "অনুমতি প্রয়োগ"))
        apply_btn.clicked.connect(self._apply_permissions)
        perms.addWidget(apply_btn)
        perms.addStretch()
        column.addLayout(perms)

    def _load_tools(self) -> None:
        self.tool_list.clear()
        registry = self.host.tools
        if not registry:
            item = QListWidgetItem("Tools unavailable")
            item.setFlags(Qt.NoItemFlags)
            self.tool_list.addItem(item)
            return
        for info in registry.describe():
            item = QListWidgetItem(f"{info['icon']}  {info['label']}")
            item.setData(Qt.UserRole, info["name"])
            item.setToolTip(info["description"])
            self.tool_list.addItem(item)
        self.tool_list.setCurrentRow(0)

    def _select_tool(self, current: Optional[QListWidgetItem], _previous=None) -> None:
        if current is None or not self.host.tools:
            return
        name = current.data(Qt.UserRole)
        tool = self.host.tools.tools.get(name)
        if not tool:
            return
        self.tool_title.setText(f"{tool['icon']}  {tool['label']}")
        self.tool_desc.setText(tool["description"] + f"\nRequired: {', '.join(tool['required']) or 'none'}")
        example = {}
        for prop, schema in tool["properties"].items():
            if "default" in schema:
                example[prop] = schema["default"]
            elif schema.get("type") == "integer":
                example[prop] = 1
            elif schema.get("type") == "string":
                example[prop] = {"query": "Groq LPU", "expression": "2+2", "url": "https://example.com",
                                 "timezone": "Asia/Dhaka", "filepath": "notes.txt", "path": ".",
                                 "location": "Dhaka", "code": "print('hello')", "content": "hello"}.get(prop, "")
        self.args_edit.setPlainText(json.dumps(example, indent=2, ensure_ascii=False))
        self.output.clear()

    def _insert_example(self) -> None:
        current = self.tool_list.currentItem()
        if current:
            self._select_tool(current)

    def _run(self) -> None:
        current = self.tool_list.currentItem()
        if not current or not self.host.tools:
            return
        if self.worker and self.worker.isRunning():
            return
        try:
            arguments = json.loads(self.args_edit.toPlainText() or "{}")
            if not isinstance(arguments, dict):
                raise ValueError("Arguments must be a JSON object")
        except Exception as exc:
            QMessageBox.warning(self, "Invalid JSON", str(exc))
            return
        name = current.data(Qt.UserRole)
        self.output.setPlainText("Running…")
        self.busy.show()
        self.run_btn.setEnabled(False)
        self.worker = ToolWorker(self.host.tools, name, arguments, self)
        self.worker.finished_result.connect(self._show_result)
        self.worker.finished.connect(self._done)
        self.worker.start()

    def _show_result(self, result: dict) -> None:
        text = json.dumps(result, ensure_ascii=False, indent=2)
        self.output.setPlainText(text)
        self.host.set_status("ready")

    def _done(self) -> None:
        self.busy.hide()
        self.run_btn.setEnabled(True)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _apply_permissions(self) -> None:
        self.host.apply_tool_permissions(
            self.write_check.isChecked(),
            self.code_check.isChecked(),
            self.net_check.isChecked(),
        )
        self._load_tools()
        self.host.set_status("ready")


# --------------------------------------------------------------------------- #
# Generation studio
# --------------------------------------------------------------------------- #
class GenerationWorker(QThread):
    finished_result = Signal(dict)

    def __init__(self, engine, kind: str, params: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.kind = kind
        self.params = params

    def run(self) -> None:
        try:
            if self.kind == "image":
                result = self.engine.generate_image(**self.params)
            elif self.kind == "illustration":
                result = self.engine.generate_illustration(**self.params)
            elif self.kind == "music":
                result = self.engine.generate_music(**self.params)
            elif self.kind == "video":
                result = self.engine.generate_video(**self.params)
            else:
                result = {"success": False, "error": f"Unknown kind: {self.kind}"}
        except Exception as exc:  # noqa: BLE001
            result = {"success": False, "error": str(exc)}
        self.finished_result.emit(result)


class GenerateDialog(QDialog):
    """Prompt-to-image, illustration, music and video with a live preview."""

    KINDS = [
        ("image", "🖼  Image"),
        ("illustration", "🎨  Illustration"),
        ("music", "🎵  Music"),
        ("video", "🎬  Video"),
    ]

    def __init__(self, host, kind: str = "image") -> None:
        super().__init__(host)
        self.host = host
        self.worker: GenerationWorker | None = None
        self.current_file = ""
        self.setWindowTitle(L(host, "Generation studio", "জেনারেশন স্টুডিও"))
        self.setModal(True)
        self.setMinimumSize(940, 650)
        self.resize(1040, 720)
        self.setStyleSheet(host.styleSheet())
        self._build()
        self.tabs.setCurrentIndex(max(0, [k for k, _ in self.KINDS].index(kind))
                                  if kind in [k for k, _ in self.KINDS] else 0)
        self._refresh_recent()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(16, 14, 16, 14)
        column.setSpacing(9)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel(L(self.host, "Generation studio", "জেনারেশন স্টুডিও"))
        title.setObjectName("dlgTitle")
        titles.addWidget(title)
        titles.addWidget(_muted(
            "Images and illustrations use your image provider. Music and video need "
            "HuggingFace or Replicate / fal.ai. Outputs land in your local data folder."
        ))
        head.addLayout(titles, 1)
        close = QPushButton("✕")
        close.setObjectName("dialClose")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.accept)
        head.addWidget(close)
        column.addLayout(head)

        splitter = QSplitter(Qt.Horizontal)
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 8, 0)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._tab_changed)
        self._build_image_page()
        self._build_illustration_page()
        self._build_music_page()
        self._build_video_page()
        controls_layout.addWidget(self.tabs, 1)

        actions = QHBoxLayout()
        self.generate_btn = _button(L(self.host, "✨  Generate", "✨  তৈরি করুন"), primary=True)
        self.generate_btn.clicked.connect(self._generate)
        actions.addWidget(self.generate_btn)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        actions.addWidget(self.progress, 1)
        controls_layout.addLayout(actions)
        self.status = _muted("")
        controls_layout.addWidget(self.status)
        splitter.addWidget(controls)

        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(8, 0, 0, 0)
        self.preview = QLabel(L(self.host, "Your creation appears here", "আপনার তৈরি ছবি এখানে আসবে"))
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(360, 300)
        self.preview.setStyleSheet(
            f"background:{self.host.palette['bg']};"
            f" border:1px dashed {self.host.palette['border2']};"
            f" border-radius:12px; color:{self.host.palette['muted']};"
        )
        preview_layout.addWidget(self.preview, 1)
        self.file_label = _muted("")
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        preview_layout.addWidget(self.file_label)
        buttons = QHBoxLayout()
        self.open_btn = _button(L(self.host, "Open file", "ফাইল খুলুন"))
        self.open_btn.clicked.connect(self._open_file)
        self.open_btn.setEnabled(False)
        buttons.addWidget(self.open_btn)
        folder_btn = _button(L(self.host, "Open folder", "ফোল্ডার খুলুন"))
        folder_btn.clicked.connect(lambda: self.host.open_path(GENERATED_DIR))
        buttons.addWidget(folder_btn)
        buttons.addStretch()
        preview_layout.addLayout(buttons)
        preview_layout.addWidget(_muted("RECENT", 9))
        self.recent = QListWidget()
        self.recent.setMaximumHeight(120)
        self.recent.itemDoubleClicked.connect(self._open_recent)
        preview_layout.addWidget(self.recent)
        splitter.addWidget(preview)
        splitter.setSizes([480, 520])
        column.addWidget(splitter, 1)

    def _prompt_page(self, title: str) -> tuple[QVBoxLayout, QPlainTextEdit]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        scroll.setWidget(inner)
        self.tabs.addTab(scroll, title)
        prompt = QPlainTextEdit()
        prompt.setPlaceholderText(L(self.host, "Describe what you want to create…", "কী তৈরি করতে চান লিখুন…"))
        prompt.setMinimumHeight(100)
        layout.addWidget(QLabel("Prompt"))
        layout.addWidget(prompt)
        return layout, prompt

    def _build_image_page(self) -> None:
        layout, self.image_prompt = self._prompt_page("🖼  Image")
        self.image_negative = QPlainTextEdit()
        self.image_negative.setPlaceholderText("blurry, text, watermark (optional)")
        self.image_negative.setMaximumHeight(58)
        layout.addWidget(QLabel("Negative prompt"))
        layout.addWidget(self.image_negative)
        row = QHBoxLayout()
        self.image_model = QComboBox()
        if self.host.gen:
            for key, label in self.host.gen.model_labels("image").items():
                self.image_model.addItem(label, key)
        index = self.image_model.findData(self.host.get_setting("default_image_model", "flux-schnell"))
        self.image_model.setCurrentIndex(index if index >= 0 else 0)
        row.addWidget(QLabel("Model"))
        row.addWidget(self.image_model, 1)
        layout.addLayout(row)
        size_row = QHBoxLayout()
        self.image_width = QComboBox()
        self.image_height = QComboBox()
        for value in (512, 768, 1024, 1280):
            self.image_width.addItem(str(value), value)
            self.image_height.addItem(str(value), value)
        self.image_width.setCurrentIndex(2)
        self.image_height.setCurrentIndex(2)
        size_row.addWidget(QLabel("Width"))
        size_row.addWidget(self.image_width)
        size_row.addWidget(QLabel("Height"))
        size_row.addWidget(self.image_height)
        size_row.addStretch()
        layout.addLayout(size_row)
        surprise = _button(L(self.host, "🎲  Surprise me", "🎲  আইডিয়া দিন"))
        surprise.clicked.connect(lambda: self.image_prompt.setPlainText(random.choice(IMAGE_IDEAS)))
        layout.addWidget(surprise)
        layout.addStretch()

    def _build_illustration_page(self) -> None:
        layout, self.illustration_prompt = self._prompt_page("🎨  Illustration")
        row = QHBoxLayout()
        self.style_combo = QComboBox()
        for style in ("digital art", "cinematic", "watercolour", "anime", "3D render",
                      "pencil sketch", "vintage poster", "isometric"):
            self.style_combo.addItem(style, style)
        index = self.style_combo.findData(self.host.get_setting("illustration_style", "digital art"))
        self.style_combo.setCurrentIndex(index if index >= 0 else 0)
        row.addWidget(QLabel("Style"))
        row.addWidget(self.style_combo, 1)
        layout.addLayout(row)
        self.illustration_model = QComboBox()
        if self.host.gen:
            for key, label in self.host.gen.model_labels("illustration").items():
                self.illustration_model.addItem(label, key)
        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.illustration_model)
        layout.addWidget(_muted(
            "Illustrations are steered with a curated style suffix; add your own "
            "details in the prompt for characters, palette and composition."
        ))
        layout.addStretch()

    def _build_music_page(self) -> None:
        layout, self.music_prompt = self._prompt_page("🎵  Music")
        self.music_model = QComboBox()
        if self.host.gen:
            for key, label in self.host.gen.model_labels("music").items():
                self.music_model.addItem(label, key)
        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.music_model)
        self.duration_slider = QSlider(Qt.Horizontal)
        self.duration_slider.setRange(5, 60)
        self.duration_slider.setValue(30)
        self.duration_value = QLabel("30 s")
        self.duration_slider.valueChanged.connect(
            lambda value: self.duration_value.setText(f"{value} s")
        )
        row = QHBoxLayout()
        row.addWidget(self.duration_slider, 1)
        row.addWidget(self.duration_value)
        layout.addWidget(QLabel("Duration"))
        layout.addLayout(row)
        layout.addWidget(_muted("Try: ‘lo-fi hip hop with rain, warm vinyl crackle, 80 bpm’."))
        layout.addStretch()

    def _build_video_page(self) -> None:
        layout, self.video_prompt = self._prompt_page("🎬  Video")
        self.video_model = QComboBox()
        if self.host.gen:
            for key, label in self.host.gen.model_labels("video").items():
                self.video_model.addItem(label, key)
        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.video_model)
        self.video_duration = QSlider(Qt.Horizontal)
        self.video_duration.setRange(3, 10)
        self.video_duration.setValue(5)
        self.video_value = QLabel("5 s")
        self.video_duration.valueChanged.connect(
            lambda value: self.video_value.setText(f"{value} s")
        )
        row = QHBoxLayout()
        row.addWidget(self.video_duration, 1)
        row.addWidget(self.video_value)
        layout.addWidget(QLabel("Duration"))
        layout.addLayout(row)
        layout.addWidget(_muted(
            "Video generation is the most expensive mode and needs Replicate or fal.ai. "
            "Short, concrete shots with a camera direction work best."
        ))
        layout.addStretch()

    # ------------------------------------------------------------ actions
    def _tab_changed(self, index: int) -> None:
        if hasattr(self, "status"):
            self.status.setText("")

    def _generate(self) -> None:
        if not self.host.gen:
            QMessageBox.information(self, "Studio", "Generation engine is not available.")
            return
        if self.worker and self.worker.isRunning():
            return
        kind = self.KINDS[self.tabs.currentIndex()][0]
        if kind == "image":
            if not self.image_prompt.toPlainText().strip():
                self.status.setText("Write a prompt first.")
                return
            params = {
                "prompt": self.image_prompt.toPlainText().strip(),
                "model": self.image_model.currentData(),
                "width": self.image_width.currentData(),
                "height": self.image_height.currentData(),
                "negative_prompt": self.image_negative.toPlainText().strip(),
            }
        elif kind == "illustration":
            if not self.illustration_prompt.toPlainText().strip():
                self.status.setText("Write a prompt first.")
                return
            params = {
                "prompt": self.illustration_prompt.toPlainText().strip(),
                "style": self.style_combo.currentData(),
                "model": self.illustration_model.currentData() or "flux-schnell",
            }
        elif kind == "music":
            if not self.music_prompt.toPlainText().strip():
                self.status.setText("Write a prompt first.")
                return
            params = {
                "prompt": self.music_prompt.toPlainText().strip(),
                "duration": self.duration_slider.value(),
                "model": self.music_model.currentData(),
            }
        else:
            if not self.video_prompt.toPlainText().strip():
                self.status.setText("Write a prompt first.")
                return
            params = {
                "prompt": self.video_prompt.toPlainText().strip(),
                "duration": self.video_duration.value(),
                "model": self.video_model.currentData(),
            }
        if not self.host.gen.configured_providers():
            self.status.setText(
                "No provider key configured. Open Settings → API keys and add HuggingFace, "
                "Replicate or fal.ai."
            )
            return
        self.progress.show()
        self.generate_btn.setEnabled(False)
        self.status.setText("Generating… this can take a minute.")
        self.worker = GenerationWorker(self.host.gen, kind, params, self)
        self.worker.finished_result.connect(self._done)
        self.worker.start()

    def _done(self, result: dict) -> None:
        self.progress.hide()
        self.generate_btn.setEnabled(True)
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        if result.get("success"):
            path = result.get("filepath", "")
            self.current_file = path
            self.file_label.setText(
                f"Saved · {Path(path).name}  ·  {readable_size(Path(path).stat().st_size)}  ·  "
                f"{result.get('provider', '')}"
            )
            self.status.setText("Ready. Your creation is saved locally.")
            self.open_btn.setEnabled(True)
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                pix = QPixmap(path)
                if not pix.isNull():
                    self.preview.setPixmap(pix.scaled(
                        520, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
            else:
                icon = "🎵" if result.get("type") == "music" else "🎬"
                self.preview.setText(f"{icon}\n\n{Path(path).name}")
                self.preview.setStyleSheet(
                    f"background:{self.host.palette['bg']};"
                    f" border:1px solid {self.host.palette['border2']};"
                    f" border-radius:12px; color:{self.host.palette['text']}; font-size:16px;"
                )
            self._refresh_recent()
            self.host.track_generation(result)
        else:
            self.status.setText(result.get("error", "Generation failed."))
            QMessageBox.warning(self, "Generation failed", result.get("error", "Unknown error"))

    def _open_file(self) -> None:
        if self.current_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_file))

    def _refresh_recent(self) -> None:
        self.recent.clear()
        folder = Path(GENERATED_DIR)
        if not folder.exists():
            return
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in
                 (".png", ".jpg", ".jpeg", ".webp", ".wav", ".mp3", ".mp4")]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files[:20]:
            item = QListWidgetItem(f"{path.name}  ·  {readable_size(path.stat().st_size)}")
            item.setData(Qt.UserRole, str(path))
            self.recent.addItem(item)

    def _open_recent(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))


IMAGE_IDEAS = [
    "A tiny astronaut sitting on a crescent moon, retro poster style, warm gradient sky",
    "Bangladeshi village at golden hour, fishing boats on a river, cinematic photography",
    "A neon cyberpunk tea stall in Dhaka during monsoon rain, reflections on the street",
    "An isometric library floating among clouds, glowing books, soft pastel palette",
    "A majestic Bengal tiger made of constellations, deep space background",
    "A cozy reading nook inside a giant tree, fairy lights, Studio Ghibli inspired",
]


# --------------------------------------------------------------------------- #
# About
# --------------------------------------------------------------------------- #
class AboutDialog(QDialog):
    def __init__(self, host) -> None:
        super().__init__(host)
        self.setWindowTitle("About GroqChatbot")
        self.setModal(True)
        self.setFixedWidth(470)
        self.setStyleSheet(host.styleSheet())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(9)
        logo = QLabel()
        logo.setPixmap(make_logo(72, host.palette))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        title = QLabel(f"GroqChatbot {APP_VERSION}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:700;")
        layout.addWidget(title)
        sub = _muted("Bilingual AI agent with memory, tools, RAG and a creation studio.")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
        body = QLabel(
            "Runs entirely on your device. Your Groq key and databases stay local.\n\n"
            "Built with PySide6, the Groq SDK, SQLite and optional sqlite-vec / "
            "sentence-transformers for semantic recall."
        )
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body)
        links = QHBoxLayout()
        for label, url in (
            ("GitHub", "https://github.com/rhasan2026g-cell/GroqChatbot"),
            ("Groq", "https://console.groq.com"),
        ):
            button = QPushButton(label + " ↗")
            button.setObjectName("link")
            button.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(button)
        links.addStretch()
        layout.addLayout(links)
        close = _button("Close", primary=True)
        close.clicked.connect(self.accept)
        layout.addWidget(close)
