"""Launcher for GroqChatbot.
 
The application itself lives in "My Chatbot.py". This file simply runs it, so
both of these commands open the same GUI:
 
    python "My Chatbot.py"
    python app.py
"""
 
from __future__ import annotations
 
import os
import runpy
import sys
 
 
def main() -> int:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "My Chatbot.py")
    if not os.path.exists(path):
        print(f"Could not find the application file:\n  {path}")
        print("Keep 'My Chatbot.py' and 'app.py' in the same folder.")
        return 1
    runpy.run_path(path, run_name="__main__")
    return 0
 
 
if __name__ == "__main__":
    sys.exit(main())
