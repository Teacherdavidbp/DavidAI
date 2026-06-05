"""DavidAI chat service — Ollama integration and mock web search."""

from __future__ import annotations

import json
import logging
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

logger = logging.getLogger(__name__)

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_CHAT_MODEL = "qwen2.5:7b"
FRONTEND_TIMEOUT_BUFFER = 15
MODEL_CHAT_TIMEOUT = 180

SEARCH_CONTEXT_INSTRUCTION = (
    "When the search context clearly answers the question:\n"
    "- Answer directly and concisely using the search context.\n"
    "- State the answer as current fact. Do not hedge.\n"
    "- Do not mention training data, knowledge cut-off dates, last update, or outdated information.\n"
    "- Do not say you lack access to current events when the search context already provides the answer."
)

SEARCH_CONTEXT_MISSING_INSTRUCTION = (
    "The search context does not contain a clear answer.\n"
    "- Say you could not find current information from the search results.\n"
    "- You may note uncertainty, but do not invent facts."
)

MOCK_SEARCH_RESULTS: dict[str, str] = {
    "who is the uk prime minister": (
        "The current Prime Minister of the United Kingdom is Keir Starmer."
    ),
    "who is the prime minister of the united kingdom": (
        "The current Prime Minister of the United Kingdom is Keir Starmer."
    ),
}


def get_uk_time() -> dict[str, str]:
    if ZoneInfo is not None:
        now = datetime.now(ZoneInfo("Europe/London"))
    else:
        now = datetime.now(timezone.utc)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": "Europe/London",
    }


def build_davidai_system_prompt() -> str:
    t = get_uk_time()
    return (
        "You are DavidAI.\n\n"
        f"Current UK Date: {t['date']}\n"
        f"Current UK Time: {t['time']}\n"
        f"Timezone: {t['timezone']}\n\n"
        "You support:\n"
        "* DavidAI\n"
        "* AI Quest\n"
        "* International STEM Academy\n"
        "* Research-AI\n"
        "* PaintMeModels\n\n"
        "Answer using current date/time information when relevant."
    )


def _http_get_json(url: str, timeout: int = 5) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def check_ollama_running() -> bool:
    return _http_get_json(OLLAMA_TAGS_URL) is not None


def check_model_installed(model: str = DEFAULT_CHAT_MODEL) -> bool:
    data = _http_get_json(OLLAMA_TAGS_URL)
    if not data or "models" not in data:
        return False
    model_lower = model.lower()
    for item in data["models"]:
        name = item.get("name", "").lower()
        if name == model_lower or name.startswith(f"{model_lower}:"):
            return True
    return False


def search_web(query: str) -> dict:
    """Mock web search — replace with Tavily, Brave, Serper, etc."""
    normalized = " ".join(query.lower().strip().split())

    for key, result in MOCK_SEARCH_RESULTS.items():
        if key in normalized or normalized in key:
            return {"ok": True, "query": query, "results": result, "source": "mock"}

    if "prime minister" in normalized and any(
        term in normalized for term in ("uk", "u.k.", "united kingdom", "britain", "british")
    ):
        return {
            "ok": True,
            "query": query,
            "results": MOCK_SEARCH_RESULTS["who is the uk prime minister"],
            "source": "mock",
        }

    return {
        "ok": True,
        "query": query,
        "results": f"No mock search results available for: {query}",
        "source": "mock",
    }


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    return "timed out" in str(exc).lower() or "timeout" in str(exc).lower()


def _messages_for_generate(messages: list[dict]) -> dict[str, str]:
    system_parts: list[str] = []
    conversation: list[str] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "user":
            conversation.append(f"User: {content}")
        elif role == "assistant":
            conversation.append(f"Assistant: {content}")

    prompt = "\n".join(conversation)
    if conversation and not conversation[-1].startswith("Assistant:"):
        prompt += "\nAssistant:"

    return {"system": "\n\n".join(system_parts), "prompt": prompt}


def _ollama_generate(payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def chat_with_ollama(
    messages: list[dict],
    model: str = DEFAULT_CHAT_MODEL,
) -> dict:
    if not check_ollama_running():
        return {
            "ok": False,
            "error": "Ollama is not running. Start Ollama and try again.",
            "error_code": "ollama_offline",
            "model": model,
        }

    if not check_model_installed(model):
        return {
            "ok": False,
            "error": f"Model '{model}' is not installed. Run: ollama pull {model}",
            "error_code": "model_missing",
            "model": model,
        }

    timeout = MODEL_CHAT_TIMEOUT
    frontend_timeout = timeout + FRONTEND_TIMEOUT_BUFFER
    start_perf = time.perf_counter()

    generate_payload = _messages_for_generate(messages)
    payload: dict = {
        "model": model,
        "prompt": generate_payload["prompt"],
        "stream": False,
    }
    if generate_payload["system"]:
        payload["system"] = generate_payload["system"]

    logger.info(
        "DavidAI chat starting model=%s backend_timeout=%ds frontend_timeout=%ds",
        model,
        timeout,
        frontend_timeout,
    )

    try:
        data = _ollama_generate(payload, timeout)
        content = data.get("response", "")
        duration = time.perf_counter() - start_perf
        logger.info(
            "DavidAI chat success model=%s duration=%.2fs",
            model,
            duration,
        )
        return {
            "ok": True,
            "message": content,
            "model": model,
            "duration_seconds": round(duration, 2),
            "timeout_seconds": timeout,
            "frontend_timeout_seconds": frontend_timeout,
        }
    except urllib.error.URLError as exc:
        duration = time.perf_counter() - start_perf
        reason = exc.reason
        if _is_timeout_error(exc) or (reason is not None and _is_timeout_error(reason)):
            return {
                "ok": False,
                "error": "Request timed out. Try a shorter question.",
                "error_code": "timeout",
                "model": model,
                "duration_seconds": round(duration, 2),
                "timeout_seconds": timeout,
            }
        return {
            "ok": False,
            "error": f"Ollama unavailable: {reason}",
            "error_code": "ollama_error",
            "model": model,
        }
    except (json.JSONDecodeError, TimeoutError, OSError) as exc:
        duration = time.perf_counter() - start_perf
        if _is_timeout_error(exc):
            return {
                "ok": False,
                "error": "Request timed out. Try a shorter question.",
                "error_code": "timeout",
                "model": model,
                "duration_seconds": round(duration, 2),
            }
        return {
            "ok": False,
            "error": str(exc),
            "error_code": "ollama_error",
            "model": model,
        }


def chat_with_search(
    message: str,
    model: str = DEFAULT_CHAT_MODEL,
    history: list[dict] | None = None,
) -> dict:
    history = history or []
    search = search_web(message)
    if not search.get("ok"):
        return {
            "ok": False,
            "error": "Web search is unavailable. Try again without web search.",
            "error_code": "search_unavailable",
            "model": model,
            "search_mode": True,
        }

    search_context = search.get("results", "")
    context_uncertain = (
        not search_context.strip()
        or search_context.lower().startswith("no mock search results")
    )
    search_instruction = (
        SEARCH_CONTEXT_MISSING_INSTRUCTION
        if context_uncertain
        else SEARCH_CONTEXT_INSTRUCTION
    )
    system_prompt = (
        f"{build_davidai_system_prompt()}\n\n"
        f"{search_instruction}\n\n"
        f"Search context:\n{search_context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        if msg.get("role") != "system":
            messages.append(msg)
    messages.append({"role": "user", "content": message})

    result = chat_with_ollama(messages, model)
    result["search_mode"] = True
    result["search_results"] = search_context
    result["search_source"] = search.get("source")
    return result
