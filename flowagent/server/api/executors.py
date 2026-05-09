"""Node executors - Real implementations for each node type."""

from __future__ import annotations

import asyncio
import io
import json
import contextlib
import traceback
from typing import Any, Dict, List, Optional


def resolve_variables(text: str, context: Dict[str, Any], label_map: Optional[Dict[str, str]] = None) -> str:
    """Resolve {{node_id.field}} or {{Node Label.field}} template variables in text."""
    if not isinstance(text, str):
        return text
    import re

    # Build merged context with label-based keys
    merged = dict(context)
    if label_map:
        for label, node_id in label_map.items():
            if node_id in context:
                merged[label] = context[node_id]

    def replacer(match):
        path = match.group(1).strip()
        parts = path.split(".")
        value = merged
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return match.group(0)  # Return original if not found
        return str(value)
    return re.sub(r'\{\{(.+?)\}\}', replacer, text)


def resolve_config(config: Dict[str, Any], context: Dict[str, Any], label_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Resolve all template variables in a config dict."""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str):
            resolved[key] = resolve_variables(value, context, label_map)
        else:
            resolved[key] = value
    return resolved


async def execute_node(
    node_type: str,
    config: Dict[str, Any],
    input_data: Any,
    context: Dict[str, Any],
    label_map: Optional[Dict[str, str]] = None,
    global_settings: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a node and return its output."""
    # Resolve template variables in config
    resolved_config = resolve_config(config, context, label_map)

    # Apply global settings as fallback for AI nodes
    if global_settings:
        ai_types = {"llm_chat", "text_summarize", "text_translate", "text_classify", "agent"}
        if node_type in ai_types:
            if not resolved_config.get("api_key") and global_settings.get("api_key"):
                resolved_config["api_key"] = global_settings["api_key"]
            if not resolved_config.get("api_base") or resolved_config.get("api_base") == "https://api.openai.com/v1":
                if global_settings.get("api_base"):
                    resolved_config["api_base"] = global_settings["api_base"]
            if not resolved_config.get("model") or resolved_config.get("model") == "gpt-4o":
                if global_settings.get("model"):
                    resolved_config["model"] = global_settings["model"]

    executor = _get_executor(node_type)
    result = await executor(resolved_config, input_data, context)
    return result


def _get_executor(node_type: str):
    """Get the executor function for a node type."""
    executors = {
        # Triggers
        "manual_trigger": _exec_manual_trigger,
        "webhook_trigger": _exec_webhook_trigger,
        "schedule_trigger": _exec_schedule_trigger,
        # Data
        "http_request": _exec_http_request,
        "json_parse": _exec_json_parse,
        "data_filter": _exec_data_filter,
        "data_transform": _exec_data_transform,
        "set_variable": _exec_set_variable,
        "csv_parse": _exec_csv_parse,
        "text_join": _exec_text_join,
        "text_split": _exec_text_split,
        "aggregate": _exec_aggregate,
        # AI
        "llm_chat": _exec_llm_chat,
        "text_summarize": _exec_text_summarize,
        "text_translate": _exec_text_translate,
        "text_classify": _exec_text_classify,
        "agent": _exec_agent,
        "knowledge_base": _exec_knowledge_base,
        # Logic
        "condition": _exec_condition,
        "delay": _exec_delay,
        "loop": _exec_loop,
        "code": _exec_code,
        # Output
        "send_email": _exec_send_email,
        "webhook_response": _exec_webhook_response,
        "save_file": _exec_save_file,
        "log_output": _exec_log_output,
    }
    return executors.get(node_type, _exec_unknown)


# --- Trigger Executors ---

async def _exec_manual_trigger(config: Dict, input_data: Any, context: Dict) -> Dict:
    return {"triggered": True, "time": _now_iso()}


async def _exec_webhook_trigger(config: Dict, input_data: Any, context: Dict) -> Dict:
    return {"triggered": True, "url_path": config.get("url_path", "/webhook"), "method": config.get("method", "POST")}


async def _exec_schedule_trigger(config: Dict, input_data: Any, context: Dict) -> Dict:
    return {"triggered": True, "cron": config.get("cron", "0 * * * *")}


# --- Data Executors ---

async def _exec_http_request(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Execute a real HTTP request."""
    import httpx

    url = config.get("url", "")
    method = config.get("method", "GET").upper()
    headers_str = config.get("headers", "{}")
    body = config.get("body", "")

    if not url:
        return {"error": "URL is required", "status_code": 0}

    try:
        headers = json.loads(headers_str) if isinstance(headers_str, str) else headers_str
    except json.JSONDecodeError:
        headers = {}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, headers=headers, content=body)
            elif method == "PUT":
                resp = await client.put(url, headers=headers, content=body)
            elif method == "DELETE":
                resp = await client.delete(url, headers=headers)
            elif method == "PATCH":
                resp = await client.patch(url, headers=headers, content=body)
            else:
                return {"error": f"Unsupported method: {method}", "status_code": 0}

            try:
                body_json = resp.json()
            except Exception:
                body_json = None

            return {
                "status_code": resp.status_code,
                "body": body_json if body_json else resp.text,
                "headers": dict(resp.headers),
                "success": 200 <= resp.status_code < 300,
            }
        except httpx.ConnectError as e:
            return {"error": f"Connection failed: {e}", "status_code": 0}
        except Exception as e:
            return {"error": str(e), "status_code": 0}


async def _exec_json_parse(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Parse JSON and extract a path."""
    path = config.get("path", "")
    data = input_data

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON input", "value": None}

    # Unwrap wrapper dicts (from set_variable, code, etc.)
    if isinstance(data, dict) and path:
        path_first = path.split(".")[0]
        # Single-key dict wrapper
        if len(data) == 1:
            key = list(data.keys())[0]
            inner = data[key]
            if path.startswith(key + "."):
                path = path[len(key) + 1:]
                data = inner
            elif isinstance(inner, dict) and path_first in inner:
                data = inner
            elif isinstance(inner, dict):
                data = inner
            elif isinstance(inner, str):
                try:
                    data = json.loads(inner)
                except (json.JSONDecodeError, ValueError):
                    data = inner
        # Multi-key dict with "output" key (from code node)
        elif "output" in data and isinstance(data["output"], dict) and path_first in data["output"]:
            data = data["output"]
        # Path not found in current dict but might be in nested structure
        elif path_first not in data and len(data) <= 3:
            for k, v in data.items():
                if isinstance(v, dict) and path_first in v:
                    data = v
                    break

    if not path:
        return {"value": data}

    # Simple dot-notation path extraction
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return {"error": f"Path not found: {path}", "value": None}
        else:
            return {"error": f"Path not found: {path}", "value": None}

    return {"value": current}


async def _exec_data_filter(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Filter data based on conditions."""
    field = config.get("field", "")
    operator = config.get("operator", "equals")
    value = config.get("value", "")

    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    # Unwrap wrapper dicts (from set_variable, code, etc.)
    if isinstance(data, dict) and field:
        field_first = field.split(".")[0]
        if len(data) == 1:
            key = list(data.keys())[0]
            inner = data[key]
            if field.startswith(key + "."):
                field = field[len(key) + 1:]
                data = inner
            elif field not in data:
                if isinstance(inner, dict) and field_first in inner:
                    data = inner
                elif isinstance(inner, str):
                    try:
                        parsed = json.loads(inner)
                        if isinstance(parsed, dict) and field_first in parsed:
                            data = parsed
                    except (json.JSONDecodeError, ValueError):
                        pass
        elif "output" in data and isinstance(data["output"], dict) and field_first in data["output"]:
            data = data["output"]
        elif field_first not in data and len(data) <= 3:
            for k, v in data.items():
                if isinstance(v, dict) and field_first in v:
                    data = v
                    break
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                pass

    if not field:
        return {"filtered": data, "matched": True}

    # Get field value from data
    field_value = data
    if isinstance(data, dict):
        for part in field.split("."):
            if isinstance(field_value, dict) and part in field_value:
                field_value = field_value[part]
            else:
                field_value = None
                break

    # Apply filter
    matched = False
    if operator == "equals":
        matched = str(field_value) == str(value)
    elif operator == "not_equals":
        matched = str(field_value) != str(value)
    elif operator == "contains":
        matched = str(value) in str(field_value)
    elif operator == "gt":
        try:
            matched = float(field_value) > float(value)
        except (ValueError, TypeError):
            matched = False
    elif operator == "lt":
        try:
            matched = float(field_value) < float(value)
        except (ValueError, TypeError):
            matched = False
    elif operator == "is_empty":
        matched = not field_value
    elif operator == "is_not_empty":
        matched = bool(field_value)

    return {"filtered": data if matched else None, "matched": matched, "field_value": field_value}


async def _exec_data_transform(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Transform data using a simple expression."""
    expression = config.get("expression", "")

    if not expression:
        return {"transformed": input_data}

    # Safe evaluation context
    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    # Unwrap single-key dict (from set_variable node)
    if isinstance(data, dict) and len(data) == 1:
        key = list(data.keys())[0]
        inner = data[key]
        if isinstance(inner, (dict, list)):
            data = inner
        elif isinstance(inner, str):
            try:
                data = json.loads(inner)
            except (json.JSONDecodeError, ValueError):
                data = inner

    try:
        # Allow simple expressions like: data['key'], len(data), data.upper()
        result = eval(expression, {"__builtins__": {}}, {"data": data, "input": data, "json": json, "len": len, "str": str, "int": int, "float": float})
        return {"transformed": result}
    except Exception as e:
        return {"error": f"Transform error: {e}", "transformed": input_data}


async def _exec_set_variable(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Set a variable value."""
    name = config.get("name", "")
    value = config.get("value", "")

    if not name:
        return {"error": "Variable name is required"}

    # Try to parse JSON strings into objects
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass  # Keep as string

    return {name: value}


# --- AI Executors ---

async def _exec_llm_chat(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Execute LLM chat - tries real API if key provided, otherwise simulated."""
    api_key = config.get("api_key", "")
    api_base = config.get("api_base", "https://api.openai.com/v1")
    model = config.get("model", "gpt-4o")
    system_prompt = config.get("system_prompt", "")
    user_prompt = config.get("user_prompt", "")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 4096)

    # Resolve input data into user prompt if not set
    if not user_prompt and input_data:
        user_prompt = str(input_data) if not isinstance(input_data, str) else input_data

    if not user_prompt:
        return {"error": "No user prompt provided", "response": ""}

    if api_key:
        # Real API call
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                resp = await client.post(
                    f"{api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {"response": content, "model": model, "tokens_used": data.get("usage", {})}
                else:
                    return {"error": f"API error {resp.status_code}: {resp.text}", "response": ""}
        except Exception as e:
            return {"error": str(e), "response": ""}
    else:
        # Simulated response
        return {
            "response": f"[Simulated LLM Response]\nModel: {model}\nSystem: {system_prompt}\nUser: {user_prompt}\n\nThis is a simulated response. Configure an API Key to get real responses.",
            "model": model,
            "simulated": True,
        }


async def _exec_text_summarize(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Summarize text using LLM."""
    api_key = config.get("api_key", "")
    model = config.get("model", "gpt-4o")
    max_length = config.get("max_length", 200)

    text = str(input_data) if input_data else ""
    if not text:
        return {"error": "No input text", "summary": ""}

    if api_key:
        config_copy = dict(config)
        config_copy["system_prompt"] = f"Summarize the following text in under {max_length} words."
        config_copy["user_prompt"] = text
        return await _exec_llm_chat(config_copy, None, context)

    return {"summary": text[:max_length] + ("..." if len(text) > max_length else ""), "simulated": True}


async def _exec_text_translate(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Translate text using LLM."""
    api_key = config.get("api_key", "")
    model = config.get("model", "gpt-4o")
    target_lang = config.get("target_language", "English")

    text = str(input_data) if input_data else ""
    if not text:
        return {"error": "No input text", "translation": ""}

    if api_key:
        config_copy = dict(config)
        config_copy["system_prompt"] = f"Translate the following text to {target_lang}. Only output the translation."
        config_copy["user_prompt"] = text
        return await _exec_llm_chat(config_copy, None, context)

    return {"translation": f"[Translated to {target_lang}] {text}", "target_language": target_lang, "simulated": True}


async def _exec_text_classify(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Classify text using LLM."""
    api_key = config.get("api_key", "")
    model = config.get("model", "gpt-4o")
    categories = config.get("categories", "正面,负面,中性")

    text = str(input_data) if input_data else ""
    if not text:
        return {"error": "No input text", "category": ""}

    if api_key:
        config_copy = dict(config)
        config_copy["system_prompt"] = f"Classify the following text into one of these categories: {categories}. Only output the category name."
        config_copy["user_prompt"] = text
        return await _exec_llm_chat(config_copy, None, context)

    return {"category": categories.split(",")[0] if categories else "unknown", "simulated": True}


# --- Logic Executors ---

async def _exec_condition(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Evaluate a condition and return true/false branch."""
    field = config.get("field", "")
    operator = config.get("operator", "equals")
    value = config.get("value", "")

    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    field_value = data
    if isinstance(data, dict) and field:
        for part in field.split("."):
            if isinstance(field_value, dict) and part in field_value:
                field_value = field_value[part]
            else:
                field_value = None
                break

    result = False
    if operator == "equals":
        result = str(field_value) == str(value)
    elif operator == "not_equals":
        result = str(field_value) != str(value)
    elif operator == "contains":
        result = str(value) in str(field_value)
    elif operator == "gt":
        try:
            result = float(field_value) > float(value)
        except (ValueError, TypeError):
            pass
    elif operator == "lt":
        try:
            result = float(field_value) < float(value)
        except (ValueError, TypeError):
            pass
    elif operator == "is_empty":
        result = not field_value
    elif operator == "is_not_empty":
        result = bool(field_value)

    return {"condition_result": result, "branch": "true" if result else "false", "field_value": field_value}


async def _exec_delay(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Wait for specified seconds."""
    seconds = config.get("seconds", 1)
    await asyncio.sleep(float(seconds))
    return {"waited_seconds": seconds, "input": input_data}


async def _exec_loop(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Loop over items in input data."""
    items_path = config.get("items_path", "")

    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    if items_path and isinstance(data, dict):
        for part in items_path.split("."):
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return {"error": f"Path not found: {items_path}", "items": [], "count": 0}

    if not isinstance(data, list):
        data = [data]

    return {"items": data, "count": len(data)}


async def _exec_code(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Execute Python code in a sandboxed environment."""
    code = config.get("code", "")

    if not code:
        return {"error": "No code provided", "output": None}

    # Create sandboxed globals
    safe_builtins = {
        "print": print, "len": len, "str": str, "int": int, "float": float,
        "bool": bool, "list": list, "dict": dict, "tuple": tuple, "set": set,
        "range": range, "enumerate": enumerate, "zip": zip, "map": map,
        "filter": filter, "sorted": sorted, "reversed": reversed,
        "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
        "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
        "True": True, "False": False, "None": None,
    }

    sandbox = {"__builtins__": safe_builtins, "input_data": input_data, "json": json}
    output_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(code, sandbox)

        # Try to get return value from main() function
        result = None
        if "main" in sandbox and callable(sandbox["main"]):
            result = sandbox["main"](input_data)

        stdout = output_buffer.getvalue()
        return {"output": result, "stdout": stdout if stdout else None}
    except Exception as e:
        return {"error": f"Code error: {traceback.format_exc()}", "output": None}


# --- Output Executors ---

async def _exec_send_email(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Send email (simulated - needs SMTP config)."""
    to = config.get("to", "")
    subject = config.get("subject", "")
    body = config.get("body", "")

    if not to:
        return {"error": "Recipient email is required", "sent": False}

    # In production, use aiosmtplib
    return {"sent": True, "to": to, "subject": subject, "simulated": True}


async def _exec_webhook_response(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Send data to a webhook URL."""
    import httpx

    url = config.get("url", "")
    method = config.get("method", "POST").upper()

    if not url:
        return {"error": "URL is required", "sent": False}

    payload = input_data if input_data else {}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "POST":
                resp = await client.post(url, json=payload)
            else:
                resp = await client.put(url, json=payload)

            return {"sent": True, "status_code": resp.status_code, "response": resp.text}
    except Exception as e:
        return {"error": str(e), "sent": False}


async def _exec_save_file(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Save data to a file."""
    import os

    filename = config.get("filename", "output.json")
    fmt = config.get("format", "json")

    save_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)

    try:
        if fmt == "json":
            content = json.dumps(input_data, indent=2, ensure_ascii=False) if not isinstance(input_data, str) else input_data
        elif fmt == "csv":
            if isinstance(input_data, list) and input_data and isinstance(input_data[0], dict):
                import csv
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=input_data[0].keys())
                writer.writeheader()
                writer.writerows(input_data)
                content = output.getvalue()
            else:
                content = str(input_data)
        else:
            content = str(input_data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {"saved": True, "filepath": filepath, "format": fmt, "size": len(content)}
    except Exception as e:
        return {"error": str(e), "saved": False}


async def _exec_log_output(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Log output message."""
    message = config.get("message", "")
    if not message and input_data:
        message = str(input_data)
    return {"logged": True, "message": message}


# --- New Data Executors ---

async def _exec_csv_parse(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Parse CSV text into list of dicts."""
    import csv

    delimiter = config.get("delimiter", ",")
    has_header = config.get("has_header", "true") == "true"

    text = str(input_data) if input_data else ""
    if not text:
        return {"error": "No input data", "rows": []}

    try:
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return {"rows": [], "count": 0}

        if has_header:
            headers = rows[0]
            data = [dict(zip(headers, row)) for row in rows[1:]]
        else:
            data = [row for row in rows]

        return {"rows": data, "count": len(data)}
    except Exception as e:
        return {"error": f"CSV parse error: {e}", "rows": []}


async def _exec_text_join(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Join list items into a single string."""
    separator = config.get("separator", ", ")
    field = config.get("field", "")

    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {"result": data}

    if isinstance(data, dict) and len(data) == 1:
        data = list(data.values())[0]

    if not isinstance(data, list):
        data = [str(data)]

    if field:
        items = []
        for item in data:
            if isinstance(item, dict):
                val = item
                for part in field.split("."):
                    if isinstance(val, dict) and part in val:
                        val = val[part]
                    else:
                        val = ""
                        break
                items.append(str(val))
            else:
                items.append(str(item))
    else:
        items = [str(item) for item in data]

    return {"result": separator.join(items), "count": len(items)}


async def _exec_text_split(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Split text into a list."""
    delimiter = config.get("delimiter", ",")
    trim = config.get("trim", "true") == "true"

    text = str(input_data) if input_data else ""
    parts = text.split(delimiter)
    if trim:
        parts = [p.strip() for p in parts]

    return {"items": parts, "count": len(parts)}


async def _exec_aggregate(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Aggregate list data."""
    operation = config.get("operation", "count")
    field = config.get("field", "")

    data = input_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    if isinstance(data, dict) and len(data) == 1:
        inner = list(data.values())[0]
        if isinstance(inner, list):
            data = inner

    if not isinstance(data, list):
        data = [data]

    # Extract field values if specified
    values = data
    if field:
        values = []
        for item in data:
            if isinstance(item, dict):
                val = item
                for part in field.split("."):
                    if isinstance(val, dict) and part in val:
                        val = val[part]
                    else:
                        val = None
                        break
                values.append(val)
            else:
                values.append(item)

    # Convert to numbers for numeric operations
    numeric = []
    for v in values:
        try:
            numeric.append(float(v))
        except (ValueError, TypeError):
            pass

    if operation == "count":
        result = len(data)
    elif operation == "sum":
        result = sum(numeric) if numeric else 0
    elif operation == "avg":
        result = sum(numeric) / len(numeric) if numeric else 0
    elif operation == "min":
        result = min(numeric) if numeric else None
    elif operation == "max":
        result = max(numeric) if numeric else None
    elif operation == "first":
        result = data[0] if data else None
    elif operation == "last":
        result = data[-1] if data else None
    else:
        result = len(data)

    return {"result": result, "input_count": len(data), "operation": operation}


async def _exec_agent(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Execute an AI Agent with tool use and multi-step reasoning."""
    import httpx

    api_key = config.get("api_key", "")
    api_base = config.get("api_base", "https://api.openai.com/v1")
    model = config.get("model", "gpt-4o")
    system_prompt = config.get("system_prompt", "你是一个有用的AI助手。")
    tools_str = config.get("tools", "[]")
    max_steps = config.get("max_steps", 5)

    user_input = str(input_data) if input_data else ""
    if not user_input:
        return {"error": "No input provided", "response": ""}

    # Parse tools
    try:
        tools = json.loads(tools_str) if isinstance(tools_str, str) else tools_str
    except json.JSONDecodeError:
        tools = []

    if not api_key:
        # Simulated agent
        return {
            "response": f"[Simulated Agent]\nInput: {user_input}\nTools: {len(tools)} available\nSteps: 0/{max_steps}\n\nAgent would use tools to process this request with a real API key.",
            "steps": 0,
            "tools_used": [],
            "simulated": True,
        }

    # Real agent loop
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # Convert tools to OpenAI format
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": "string", "description": v} if isinstance(v, str) else {"type": v.get("type", "string"), "description": v.get("description", "")}
                        for k, v in tool.get("parameters", {}).items()
                    },
                    "required": list(tool.get("parameters", {}).keys()),
                },
            },
        })

    tools_used = []
    steps = 0

    async with httpx.AsyncClient(timeout=60) as client:
        for step in range(max_steps):
            steps += 1
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            if openai_tools:
                payload["tools"] = openai_tools

            try:
                resp = await client.post(
                    f"{api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code != 200:
                    return {"error": f"API error {resp.status_code}: {resp.text}", "response": "", "steps": steps}

                data = resp.json()
                choice = data["choices"][0]
                message = choice["message"]

                # Check for tool calls
                if message.get("tool_calls"):
                    messages.append(message)
                    for tc in message["tool_calls"]:
                        func = tc["function"]
                        tool_name = func["name"]
                        try:
                            tool_args = json.loads(func["arguments"])
                        except json.JSONDecodeError:
                            tool_args = {}

                        # Execute tool
                        tool_result = await _execute_agent_tool(tool_name, tool_args)
                        tools_used.append({"name": tool_name, "args": tool_args, "result": str(tool_result)[:200]})
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(tool_result, ensure_ascii=False),
                        })
                else:
                    # No tool calls, agent is done
                    return {
                        "response": message["content"],
                        "steps": steps,
                        "tools_used": tools_used,
                        "tokens_used": data.get("usage", {}),
                    }
            except Exception as e:
                return {"error": str(e), "response": "", "steps": steps, "tools_used": tools_used}

    return {
        "response": messages[-1].get("content", "Max steps reached"),
        "steps": steps,
        "tools_used": tools_used,
    }


async def _execute_agent_tool(name: str, args: Dict) -> Any:
    """Execute a tool used by the agent."""
    if name == "http_get":
        url = args.get("url", "")
        if not url:
            return {"error": "No URL provided"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                return {"status_code": resp.status_code, "body": resp.text[:2000]}
        except Exception as e:
            return {"error": str(e)}
    elif name == "python_exec":
        code = args.get("code", "")
        if not code:
            return {"error": "No code provided"}
        result = await _exec_code({"code": code}, None, {})
        return result
    else:
        return {"error": f"Unknown tool: {name}"}


async def _exec_knowledge_base(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Simple knowledge base retrieval using keyword matching."""
    documents_str = config.get("documents", "")
    top_k = int(config.get("top_k", 3))
    separator = config.get("separator", "---")

    query = str(input_data) if input_data else ""
    if not query:
        return {"error": "No query provided", "results": []}

    if not documents_str:
        return {"error": "No documents provided", "results": []}

    # Split documents
    docs = [d.strip().strip(separator).strip() for d in documents_str.split(separator) if d.strip()]
    if not docs:
        return {"results": [], "count": 0}

    # Simple keyword-based scoring
    query_words = set(query.lower().split())
    scored = []
    for i, doc in enumerate(docs):
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        # Boost for exact phrase match
        if query.lower() in doc.lower():
            overlap += 10
        scored.append((overlap, i, doc))

    # Sort by score descending
    scored.sort(key=lambda x: -x[0])
    top_results = scored[:top_k]

    return {
        "results": [{"content": doc, "score": score, "index": idx} for score, idx, doc in top_results],
        "total_docs": len(docs),
        "query": query,
    }


async def _exec_unknown(config: Dict, input_data: Any, context: Dict) -> Dict:
    """Unknown node type."""
    return {"error": "Unknown node type", "output": None}


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
