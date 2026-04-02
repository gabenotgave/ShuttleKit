import sys
from pathlib import Path

# Ensure `api/` is on path when tests are collected from subdirs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shuttlekit.agent.shuttle_agent import _stringify_ai_content


def test_stringify_plain_string():
    assert _stringify_ai_content("hello") == "hello"


def test_stringify_gemini_text_blocks():
    content = [
        {"type": "text", "text": "No, the shuttle is not running.\n\nNext at **6 PM**."},
    ]
    assert _stringify_ai_content(content) == "No, the shuttle is not running.\n\nNext at **6 PM**."


def test_stringify_multiple_text_blocks():
    content = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    assert _stringify_ai_content(content) == "ab"


def test_stringify_mixed_list():
    assert _stringify_ai_content(["x", {"text": "y"}]) == "xy"
