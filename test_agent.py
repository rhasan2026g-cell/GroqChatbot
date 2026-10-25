#!/usr/bin/env python3
"""Test agent components"""
import sys
import os

def test_imports():
    print("Testing imports...")
    try:
        from memory_system import MemorySystem
        print("[OK] MemorySystem imported")
    except Exception as e:
        print(f"[FAIL] MemorySystem failed: {e}")
    
    try:
        from agent_tools import ToolRegistry
        print("[OK] ToolRegistry imported")
    except Exception as e:
        print(f"[FAIL] ToolRegistry failed: {e}")
    
    try:
        import sqlite_vec
        print("[OK] sqlite-vec available")
    except:
        print("[WARN] sqlite-vec not available")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("[OK] sentence-transformers available")
    except Exception as e:
        print(f"[FAIL] sentence-transformers failed: {e}")

def test_memory():
    print("\nTesting memory system...")
    try:
        from memory_system import MemorySystem
        mem = MemorySystem("test_memory.db")
        mem.add_fact("Test fact", "test")
        mem.add_conversation("test", "user", "Hello")
        mem.add_conversation("test", "assistant", "Hi there")
        results = mem.search_memories("hello")
        print(f"[OK] Memory search returned {len(results)} results")
        context = mem.get_memory_context("hello")
        print(f"[OK] Memory context generated ({len(context)} chars)")
        if os.path.exists("test_memory.db"):
            os.remove("test_memory.db")
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")

def test_tools():
    print("\nTesting tools...")
    try:
        from agent_tools import ToolRegistry
        tools = ToolRegistry()
        schemas = tools.get_tools_schema()
        print(f"[OK] {len(schemas)} tools registered")
        
        # Test calculator
        result = tools.execute_tool("calculator", {"expression": "2+2"})
        print(f"[OK] Calculator: {result}")
        
        # Test time
        result = tools.execute_tool("get_current_time", {"timezone": "UTC"})
        if result.get('success'):
            print(f"[OK] Time: {result['datetime']}")
        else:
            print(f"[WARN] Time: {result}")
    except Exception as e:
        print(f"[FAIL] Tools test failed: {e}")

if __name__ == "__main__":
    test_imports()
    test_memory()
    test_tools()
    print("\n[OK] All tests completed!")
