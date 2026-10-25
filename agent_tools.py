#!/usr/bin/env python3
"""
GroqChatbot Agent Tools
Built-in tools for the AI agent
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Callable
import math
import random
import requests
from duckduckgo_search import DDGS
import pytz
from dateparser import parse

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.register_default_tools()
    
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict = None):
        self.tools[name] = {
            'function': func,
            'description': description,
            'parameters': parameters or {}
        }
    
    def register_default_tools(self):
        # Web search
        self.register_tool(
            "web_search",
            self.web_search,
            "Search the web for current information",
            {"query": {"type": "string", "description": "Search query"}}
        )
        
        # Calculator
        self.register_tool(
            "calculator",
            self.calculator,
            "Perform mathematical calculations",
            {"expression": {"type": "string", "description": "Math expression to evaluate"}}
        )
        
        # Get current time
        self.register_tool(
            "get_current_time",
            self.get_current_time,
            "Get current date and time",
            {"timezone": {"type": "string", "description": "Timezone (e.g., UTC, America/New_York)", "default": "UTC"}}
        )
        
        # File operations
        self.register_tool(
            "read_file",
            self.read_file,
            "Read contents of a file",
            {"filepath": {"type": "string", "description": "Path to file"}}
        )
        
        self.register_tool(
            "write_file",
            self.write_file,
            "Write content to a file",
            {"filepath": {"type": "string", "description": "Path to file"}, "content": {"type": "string", "description": "Content to write"}}
        )
        
        # Python code execution
        self.register_tool(
            "execute_python",
            self.execute_python,
            "Execute Python code safely",
            {"code": {"type": "string", "description": "Python code to execute"}}
        )
        
        # Weather
        self.register_tool(
            "get_weather",
            self.get_weather,
            "Get weather information for a location",
            {"location": {"type": "string", "description": "City name or location"}}
        )
        
        # Random
        self.register_tool(
            "random_number",
            self.random_number,
            "Generate random number",
            {"min": {"type": "number", "default": 0}, "max": {"type": "number", "default": 100}}
        )
    
    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        try:
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        'title': r['title'],
                        'href': r['href'],
                        'body': r['body']
                    })
                return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def calculator(self, expression: str) -> Dict[str, Any]:
        try:
            # Safe evaluation
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            allowed_names.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow})
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return {"success": True, "result": result, "expression": expression}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_current_time(self, timezone: str = "UTC") -> Dict[str, Any]:
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            return {
                "success": True,
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "timestamp": now.timestamp(),
                "timezone": timezone
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content, "filepath": filepath}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "filepath": filepath, "bytes_written": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_python(self, code: str) -> Dict[str, Any]:
        try:
            # Very basic sandbox - for production use better sandboxing
            result = {}
            exec(code, {"__builtins__": __builtins__, "print": lambda *args: result.update({"output": str(args)})}, result)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        try:
            # Using wttr.in as simple weather API
            response = requests.get(f"https://wttr.in/{location}?format=j1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                return {
                    "success": True,
                    "location": location,
                    "temperature_c": current['temp_C'],
                    "temperature_f": current['temp_F'],
                    "description": current['weatherDesc'][0]['value'],
                    "humidity": current['humidity'],
                    "wind_speed_kmph": current['windspeedKmph']
                }
            return {"success": False, "error": "Failed to fetch weather"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def random_number(self, min: int = 0, max: int = 100) -> Dict[str, Any]:
        return {"success": True, "result": random.randint(min, max), "min": min, "max": max}
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        try:
            func = self.tools[tool_name]['function']
            result = func(**arguments)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tools_schema(self) -> List[Dict]:
        """Get tools in format compatible with OpenAI function calling"""
        schemas = []
        for name, tool in self.tools.items():
            schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool['description'],
                    "parameters": {
                        "type": "object",
                        "properties": tool['parameters'],
                        "required": [k for k, v in tool['parameters'].items() if 'default' not in v]
                    }
                }
            }
            schemas.append(schema)
        return schemas

if __name__ == "__main__":
    registry = ToolRegistry()
    print(json.dumps(registry.get_tools_schema(), indent=2))
