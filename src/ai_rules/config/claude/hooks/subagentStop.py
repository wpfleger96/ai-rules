#!/usr/bin/env python3
"""SubagentStop Hook - Block premature exits and ensure task completion."""

import json
import sys

from pathlib import Path


def main() -> None:
    try:
        event_data = json.loads(sys.stdin.read())
        transcript_path = event_data.get("transcript_path", "")
    except Exception as e:
        print(f"Error loading event data: {e}", file=sys.stderr)
        print(json.dumps({"decision": "approve"}))
        return

    if not transcript_path:
        print(json.dumps({"decision": "approve"}))
        return

    transcript_file = Path(transcript_path).expanduser()
    if not transcript_file.exists():
        print(json.dumps({"decision": "approve"}))
        return

    pending_todos = []
    all_assistant_text = ""

    with open(transcript_file) as f:
        for line in f:
            try:
                msg = json.loads(line)

                if "message" in msg:
                    msg = msg["message"]

                if msg.get("role") == "assistant":
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if (
                                item.get("type") == "tool_use"
                                and item.get("name") == "TodoWrite"
                            ):
                                todos = item.get("input", {}).get("todos", [])
                                pending_todos = [
                                    t["content"]
                                    for t in todos
                                    if t.get("status") == "pending"
                                ]
                            elif item.get("type") == "text":
                                all_assistant_text += item.get("text", "") + " "
            except Exception as e:
                print(f"Error parsing message: {e}", file=sys.stderr)
                continue

    last_assistant_text = all_assistant_text[-2000:]

    if pending_todos:
        reason = f"INCOMPLETE: {len(pending_todos)} pending tasks:\n"
        reason += "\n".join(f"- {todo}" for todo in pending_todos)
        reason += "\n\nContinue working autonomously until ALL tasks complete."
        print(json.dumps({"decision": "block", "reason": reason}), file=sys.stderr)
        return

    check_patterns = [
        "would you like me to",
        "should i continue",
        "shall i proceed",
        "let me check with",
    ]

    text_lower = last_assistant_text.lower()
    if any(pattern in text_lower for pattern in check_patterns):
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": "INCOMPLETE: Do NOT ask for permission. Continue working autonomously.",
                }
            ),
            file=sys.stderr,
        )
        return

    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
