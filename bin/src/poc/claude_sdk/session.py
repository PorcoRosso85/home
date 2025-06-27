#!/usr/bin/env python3
"""Session management for Claude CLI continuity"""
import json
from typing import Union, TypedDict, Optional, List, Tuple

# Error types
class ParseError(TypedDict):
    ok: bool
    error: str

# Success types  
class ParseSuccess(TypedDict):
    ok: bool
    data: dict

# Result type
ParseResult = Union[ParseSuccess, ParseError]

# Session state
SessionHistory = List[Tuple[str, str]]

# Pure functions
def parse_json(line: str) -> ParseResult:
    """Parse JSON line, return result or error"""
    try:
        data = json.loads(line)
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def add_to_history(history: SessionHistory, role: str, content: str) -> SessionHistory:
    """Add message to history (immutable)"""
    return history + [(role, content)]

def build_context(history: SessionHistory, max_items: int = 6) -> str:
    """Build context from recent history"""
    recent = history[-max_items:] if len(history) > max_items else history
    return "\n".join([f"{role}: {content}" for role, content in recent])

def extract_assistant_text(message: dict) -> Optional[str]:
    """Extract text from assistant message"""
    if content := message.get("message", {}).get("content", []):
        texts = [item.get("text", "") for item in content if item.get("type") == "text"]
        return "".join(texts) if texts else None
    return None

# In-source tests
def test_parse_json_success():
    result = parse_json('{"type": "test"}')
    assert result["ok"] == True
    assert result["data"]["type"] == "test"

def test_parse_json_error():
    result = parse_json("invalid json")
    assert result["ok"] == False
    assert "error" in result

def test_add_to_history_immutable():
    h1 = [("user", "hello")]
    h2 = add_to_history(h1, "assistant", "hi")
    assert len(h1) == 1
    assert len(h2) == 2
    assert h2[-1] == ("assistant", "hi")

def test_build_context_limits():
    history = [("user", str(i)) for i in range(10)]
    context = build_context(history, max_items=3)
    assert "7" in context
    assert "8" in context
    assert "9" in context
    assert "0" not in context