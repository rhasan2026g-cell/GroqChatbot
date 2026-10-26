#!/usr/bin/env python3
"""GroqChatbot agent tools.

The assistant can call these functions through Groq's OpenAI-compatible tool
API. Each tool returns a JSON-safe dict, never raises, and explains what is
missing when an optional package or permission is unavailable.
"""

from __future__ import annotations

import ast
import json
import math
import operator
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote_plus

from app_paths import BASE_DIR, DATA_DIR, SANDBOX_DIR

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from ddgs import DDGS  # newer package name
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS = None
        DDGS_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except Exception:  # pragma: no cover
    ZONEINFO_AVAILABLE = False

MAX_RESULT_CHARS = 9000


def _truncate(value: Any, limit: int = MAX_RESULT_CHARS) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"\n… truncated ({len(value) - limit} more characters)"
    return value


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


class ToolRegistry:
    """Small, auditable tool catalog used by the agent loop."""

    def __init__(
        self,
        allow_file_write: bool = True,
        allow_code_execution: bool = True,
        allow_network: bool = True,
    ) -> None:
        self.allow_file_write = allow_file_write
        self.allow_code_execution = allow_code_execution
        self.allow_network = allow_network
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._allowed_roots = [
            Path.home().resolve(),
            Path(BASE_DIR).resolve(),
            Path(DATA_DIR).resolve(),
            Path(tempfile.gettempdir()).resolve(),
        ]
        self.register_default_tools()

    # ------------------------------------------------------------ registry
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        properties: Optional[Dict[str, Dict[str, Any]]] = None,
        required: Optional[List[str]] = None,
        icon: str = "🔧",
        label: str = "",
    ) -> None:
        self.tools[name] = {
            "function": func,
            "description": description,
            "properties": properties or {},
            "required": required or [],
            "icon": icon,
            "label": label or name.replace("_", " ").title(),
        }

    def register_default_tools(self) -> None:
        self.register_tool(
            "web_search",
            self.web_search,
            "Search the web for current information, news, prices, or facts. "
            "Use this whenever the answer may have changed recently.",
            {"query": {"type": "string", "description": "Search query"},
             "max_results": {"type": "integer", "description": "How many results (1-8)", "default": 5}},
            ["query"], icon="🌐", label="Web search",
        )
        self.register_tool(
            "fetch_url",
            self.fetch_url,
            "Download a web page and return its readable text. Use after web_search "
            "when a result needs deeper reading.",
            {"url": {"type": "string", "description": "Full http(s) URL"}},
            ["url"], icon="🔗", label="Read web page",
        )
        self.register_tool(
            "calculator",
            self.calculator,
            "Evaluate a mathematical expression safely (supports + - * / ** %, sqrt, sin, cos, log).",
            {"expression": {"type": "string", "description": "Expression such as (12.5*4)/3"}},
            ["expression"], icon="🧮", label="Calculator",
        )
        self.register_tool(
            "get_current_time",
            self.get_current_time,
            "Get the current date and time in a named time zone.",
            {"timezone": {"type": "string", "description": "IANA zone, e.g. Asia/Dhaka or UTC", "default": "UTC"}},
            [], icon="🕒", label="Current time",
        )
        self.register_tool(
            "read_file",
            self.read_file,
            "Read a UTF-8 text file from the user's home folder or the app folder.",
            {"filepath": {"type": "string", "description": "Absolute path or path relative to the home folder"}},
            ["filepath"], icon="📄", label="Read file",
        )
        if self.allow_file_write:
            self.register_tool(
                "write_file",
                self.write_file,
                "Create or overwrite a text file inside the user's home folder or app folder.",
                {"filepath": {"type": "string", "description": "Destination path"},
                 "content": {"type": "string", "description": "Complete file content"}},
                ["filepath", "content"], icon="💾", label="Write file",
            )
        self.register_tool(
            "list_files",
            self.list_files,
            "List files and folders at a path so you can explore the workspace.",
            {"path": {"type": "string", "description": "Folder path", "default": "."}},
            [], icon="📁", label="List files",
        )
        if self.allow_code_execution:
            self.register_tool(
                "execute_python",
                self.execute_python,
                "Run a short Python snippet in an isolated process and return stdout. "
                "Useful for calculations, data transforms and quick checks.",
                {"code": {"type": "string", "description": "Python source code"}},
                ["code"], icon="🐍", label="Run Python",
            )
        self.register_tool(
            "get_weather",
            self.get_weather,
            "Get current weather for a city or place.",
            {"location": {"type": "string", "description": "City name, e.g. Dhaka"}},
            ["location"], icon="🌤️", label="Weather",
        )
        self.register_tool(
            "random_number",
            self.random_number,
            "Generate a random integer inside an inclusive range.",
            {"min": {"type": "integer", "description": "Minimum", "default": 0},
             "max": {"type": "integer", "description": "Maximum", "default": 100}},
            [], icon="🎲", label="Random number",
        )

    # ------------------------------------------------------------ security
    def _resolve(self, filepath: str) -> Path:
        candidate = Path(os.path.expandvars(os.path.expanduser(filepath)))
        if not candidate.is_absolute():
            candidate = Path.home() / candidate
        resolved = candidate.resolve()
        for root in self._allowed_roots:
            try:
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue
        raise PermissionError(
            "Path is outside the allowed workspace (home, app folder, data folder, temp)."
        )

    # --------------------------------------------------------------- tools
    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        if not self.allow_network:
            return {"success": False, "error": "Network tools are disabled in Settings."}
        query = (query or "").strip()
        if not query:
            return {"success": False, "error": "Search query is empty."}
        max_results = max(1, min(int(max_results or 5), 8))
        if DDGS_AVAILABLE:
            try:
                results = []
                with DDGS() as ddgs:
                    for item in ddgs.text(query, max_results=max_results):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("href") or item.get("url", ""),
                            "snippet": item.get("body") or item.get("snippet", ""),
                        })
                if results:
                    return {"success": True, "query": query, "results": results, "engine": "duckduckgo"}
            except Exception as exc:  # noqa: BLE001 - try the HTML endpoint
                fallback = self._search_html(query, max_results)
                if fallback.get("success"):
                    fallback["note"] = f"DDGS library failed ({exc}); used HTML endpoint."
                    return fallback
                return {"success": False, "error": f"Search failed: {exc}"}
        return self._search_html(query, max_results)

    def _search_html(self, query: str, max_results: int) -> Dict[str, Any]:
        if requests is None:
            return {"success": False, "error": "Install requests to use web search."}
        try:
            response = requests.get(
                f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GroqChatbot/1.1"},
                timeout=18,
            )
            if response.status_code != 200:
                return {"success": False, "error": f"Search HTTP {response.status_code}"}
            pattern = re.compile(
                r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                re.I | re.S,
            )
            snippet_pattern = re.compile(
                r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.I | re.S
            )
            links = pattern.findall(response.text)
            snippets = snippet_pattern.findall(response.text)
            results = []
            for index, (url, title) in enumerate(links[:max_results]):
                clean_title = re.sub(r"<[^>]+>", "", title)
                snippet = re.sub(r"<[^>]+>", "", snippets[index]) if index < len(snippets) else ""
                results.append({
                    "title": _clean_entities(clean_title),
                    "url": _clean_entities(url),
                    "snippet": _clean_entities(snippet),
                })
            if results:
                return {"success": True, "query": query, "results": results, "engine": "html"}
            return {"success": False, "error": "No results parsed (the search engine may be rate-limiting)."}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def fetch_url(self, url: str) -> Dict[str, Any]:
        if not self.allow_network:
            return {"success": False, "error": "Network tools are disabled in Settings."}
        if requests is None:
            return {"success": False, "error": "Install requests to fetch web pages."}
        if not re.match(r"^https?://", url or "", re.I):
            return {"success": False, "error": "Only http(s) URLs are supported."}
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GroqChatbot/1.1"},
                timeout=25,
            )
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            content_type = response.headers.get("content-type", "")
            text = response.text
            if "html" in content_type:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(text, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        tag.decompose()
                    text = soup.get_text("\n")
                except Exception:
                    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
                    text = re.sub(r"<[^>]+>", " ", text)
                    import html as html_module
                    text = html_module.unescape(text)
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            return {
                "success": True,
                "url": url,
                "title": _extract_title(response.text),
                "content": _truncate(text, 7000),
                "chars": len(text),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    _BIN_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    _UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    _FUNCS = {
        "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "exp": math.exp, "floor": math.floor,
        "ceil": math.ceil, "factorial": math.factorial, "pow": pow, "pi": math.pi,
        "e": math.e, "tau": math.tau,
    }

    def calculator(self, expression: str) -> Dict[str, Any]:
        expression = (expression or "").strip().replace("^", "**")
        if not expression:
            return {"success": False, "error": "Expression is empty."}
        if len(expression) > 400:
            return {"success": False, "error": "Expression is too long."}
        try:
            tree = ast.parse(expression, mode="eval")
            value = self._eval_node(tree.body)
            return {
                "success": True,
                "expression": expression,
                "result": value,
                "formatted": f"{value:,.10g}" if isinstance(value, (int, float)) else str(value),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"Invalid expression: {exc}"}

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self._BIN_OPS:
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large.")
            return self._BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._UNARY_OPS:
            return self._UNARY_OPS[type(node.op)](self._eval_node(node.operand))
        if isinstance(node, ast.Name) and node.id in self._FUNCS:
            value = self._FUNCS[node.id]
            if callable(value):
                raise ValueError(f"{node.id} needs arguments.")
            return value
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in self._FUNCS:
                raise ValueError("Only approved math functions are allowed.")
            func = self._FUNCS[node.func.id]
            if not callable(func):
                raise ValueError("That name is a constant, not a function.")
            args = [self._eval_node(arg) for arg in node.args]
            if len(args) > 8:
                raise ValueError("Too many arguments.")
            return func(*args)
        raise ValueError("Unsupported syntax.")

    def get_current_time(self, timezone: str = "UTC") -> Dict[str, Any]:
        zone = timezone or "UTC"
        try:
            if ZONEINFO_AVAILABLE:
                now = datetime.now(ZoneInfo(zone))
                label = now.tzname() or zone
            else:
                now = datetime.now(timezone)
                label = "local"
            return {
                "success": True,
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": zone,
                "tz_label": label,
                "iso": now.isoformat(timespec="seconds"),
                "weekday": now.strftime("%A"),
                "timestamp": now.timestamp(),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"Unknown time zone '{zone}': {exc}"}

    def read_file(self, filepath: str) -> Dict[str, Any]:
        try:
            path = self._resolve(filepath)
            if not path.exists():
                return {"success": False, "error": "File not found."}
            if not path.is_file():
                return {"success": False, "error": "That path is a folder."}
            if path.stat().st_size > 2 * 1024 * 1024:
                return {"success": False, "error": "File is larger than 2 MB."}
            raw = path.read_bytes()
            if b"\x00" in raw[:2000]:
                return {"success": False, "error": "This looks like a binary file."}
            text = raw.decode("utf-8", errors="replace")
            return {"success": True, "filepath": str(path), "content": _truncate(text, 7000), "chars": len(text)}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        if not self.allow_file_write:
            return {"success": False, "error": "File writing is disabled in Settings."}
        try:
            path = self._resolve(filepath)
            if path.exists() and path.is_dir():
                return {"success": False, "error": "That path is a folder."}
            path.parent.mkdir(parents=True, exist_ok=True)
            text = str(content)
            if len(text) > 2_000_000:
                return {"success": False, "error": "Content is too large to write."}
            path.write_text(text, encoding="utf-8", newline="\n")
            return {"success": True, "filepath": str(path), "bytes_written": len(text.encode("utf-8"))}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def list_files(self, path: str = ".") -> Dict[str, Any]:
        try:
            folder = self._resolve(path)
            if not folder.exists():
                return {"success": False, "error": "Folder not found."}
            if not folder.is_dir():
                return {"success": False, "error": "That path is a file."}
            entries = []
            for item in sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))[:120]:
                try:
                    size = item.stat().st_size if item.is_file() else 0
                except OSError:
                    size = 0
                entries.append({
                    "name": item.name,
                    "type": "file" if item.is_file() else "folder",
                    "size": size,
                })
            return {"success": True, "path": str(folder), "entries": entries}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def execute_python(self, code: str) -> Dict[str, Any]:
        if not self.allow_code_execution:
            return {"success": False, "error": "Code execution is disabled in Settings."}
        code = (code or "").strip()
        if not code:
            return {"success": False, "error": "No code supplied."}
        if len(code) > 20_000:
            return {"success": False, "error": "Code is too long (20k character limit)."}
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        script = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".py", dir=str(SANDBOX_DIR), delete=False, encoding="utf-8"
            ) as handle:
                handle.write(code)
                script = handle.name
            env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "TEMP": os.environ.get("TEMP", ""),
                "TMP": os.environ.get("TMP", ""),
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            completed = subprocess.run(
                [sys.executable, "-I", script],
                capture_output=True,
                text=True,
                timeout=20,
                cwd=str(SANDBOX_DIR),
                env=env,
                encoding="utf-8",
                errors="replace",
            )
            output = (completed.stdout or "").strip()
            error = (completed.stderr or "").strip()
            return {
                "success": completed.returncode == 0,
                "returncode": completed.returncode,
                "stdout": _truncate(output, 5000),
                "stderr": _truncate(error, 3000),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Python timed out after 20 seconds."}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}
        finally:
            if script and os.path.exists(script):
                try:
                    os.remove(script)
                except OSError:
                    pass

    def get_weather(self, location: str) -> Dict[str, Any]:
        if not self.allow_network:
            return {"success": False, "error": "Network tools are disabled in Settings."}
        if requests is None:
            return {"success": False, "error": "Install requests to fetch weather."}
        location = (location or "").strip()
        if not location:
            return {"success": False, "error": "Location is empty."}
        try:
            response = requests.get(
                f"https://wttr.in/{quote_plus(location)}?format=j1",
                headers={"User-Agent": "GroqChatbot/1.1"},
                timeout=15,
            )
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            data = response.json()
            current = data["current_condition"][0]
            nearest = (data.get("nearest_area") or [{}])[0]
            area = (nearest.get("areaName") or [{}])[0].get("value", location)
            country = (nearest.get("country") or [{}])[0].get("value", "")
            return {
                "success": True,
                "location": f"{area}, {country}".strip(", "),
                "temperature_c": current.get("temp_C"),
                "temperature_f": current.get("temp_F"),
                "feels_like_c": current.get("FeelsLikeC"),
                "description": (current.get("weatherDesc") or [{}])[0].get("value", ""),
                "humidity": current.get("humidity"),
                "wind_kmph": current.get("windspeedKmph"),
                "observation_time": current.get("observation_time"),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def random_number(self, min: int = 0, max: int = 100) -> Dict[str, Any]:
        try:
            low, high = int(min), int(max)
            if low > high:
                low, high = high, low
            if high - low > 1_000_000_000:
                return {"success": False, "error": "Range is too large."}
            return {"success": True, "result": random.randint(low, high), "min": low, "max": high}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------ dispatch
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(arguments, dict):
            arguments = {}
        try:
            result = tool["function"](**arguments)
            if not isinstance(result, dict):
                result = {"success": True, "result": result}
            return {key: _json_safe(value) for key, value in result.items()}
        except TypeError as exc:
            return {"success": False, "error": f"Bad arguments for {tool_name}: {exc}"}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        schemas = []
        for name, tool in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": tool["properties"],
                        "required": tool["required"],
                    },
                },
            })
        return schemas

    def describe(self) -> List[Dict[str, str]]:
        return [
            {
                "name": name,
                "label": tool["label"],
                "icon": tool["icon"],
                "description": tool["description"],
                "required": ", ".join(tool["required"]) or "none",
            }
            for name, tool in self.tools.items()
        ]

    def set_permissions(
        self,
        allow_file_write: Optional[bool] = None,
        allow_code_execution: Optional[bool] = None,
        allow_network: Optional[bool] = None,
    ) -> None:
        if allow_file_write is not None:
            self.allow_file_write = allow_file_write
        if allow_code_execution is not None:
            self.allow_code_execution = allow_code_execution
        if allow_network is not None:
            self.allow_network = allow_network
        self.tools.clear()
        self.register_default_tools()


def _clean_entities(text: str) -> str:
    import html as html_module

    return html_module.unescape(re.sub(r"\s+", " ", text)).strip()


def _extract_title(raw: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", raw or "", re.I | re.S)
    return _clean_entities(match.group(1)) if match else ""


if __name__ == "__main__":
    registry = ToolRegistry()
    print(json.dumps(registry.get_tools_schema(), indent=2))
    print(json.dumps(registry.calculator("sin(pi/2) * (12 + 3)"), indent=2))
    print(json.dumps(registry.get_current_time("Asia/Dhaka"), indent=2))
