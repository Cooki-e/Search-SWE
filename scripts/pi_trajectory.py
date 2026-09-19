"""Convert Pi's JSON event stream to an auditable ATIF trajectory."""

import json


def convert_events(text, instruction, model_name, version):
    steps = [{"step_id": 1, "source": "user", "message": instruction}]
    calls = {}
    last_assistant = None
    retry_error = None
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # CLI diagnostics are interleaved with JSON events.
        if not isinstance(event, dict):
            continue
        if event.get("type") == "auto_retry_end":
            retry_error = None if event.get("success") else event.get("finalError", "retry failed")
        if event.get("type") != "message_end":
            continue
        message = event.get("message", {})
        role = message.get("role")
        if role == "toolResult":
            call_id = message.get("toolCallId")
            if call_id not in calls:
                raise ValueError(f"Pi tool result has no matching call: {call_id}")
            step = calls[call_id]
            step.setdefault("observation", {"results": []})["results"].append({
                "source_call_id": call_id,
                "content": json.dumps(message.get("content", []), ensure_ascii=False),
            })
            continue
        if role not in ("assistant", "user", "system"):
            continue
        step = {"step_id": len(steps) + 1,
                "source": "agent" if role == "assistant" else role,
                "message": json.dumps(message.get("content", []), ensure_ascii=False),
                "extra": {"pi_message": message}}
        if role == "assistant":
            last_assistant = message
            for part in message.get("content", []):
                if isinstance(part, dict) and part.get("type") == "toolCall":
                    step.setdefault("tool_calls", []).append({
                        "tool_call_id": part["id"], "function_name": part["name"],
                        "arguments": part.get("arguments", {}),
                    })
                    calls[part["id"]] = step
        steps.append(step)
    error = retry_error
    if last_assistant is None:
        error = error or "Pi produced no assistant messages"
    elif last_assistant.get("stopReason") in ("error", "aborted"):
        error = error or last_assistant.get("errorMessage", "Pi aborted")
    elif last_assistant.get("stopReason") == "toolUse":
        error = error or "Pi ended before completing its final turn"
    return {
        "schema_version": "ATIF-v1.7",
        "agent": {"name": "pi", "version": version, "model_name": model_name},
        "steps": steps,
    }, error
