#!/usr/bin/env python3
"""Shared utilities for calling LLM APIs."""

import os
import re
from typing import Dict, Optional

try:  # OpenAI SDK
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None

try:  # Anthropic SDK
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency
    Anthropic = None

try:  # Google GenAI SDK
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except ImportError:  # pragma: no cover - optional dependency
    google_genai = None
    google_genai_types = None


def load_dotenv(path: str = ".env") -> None:
    """Load environment variables from a .env file if present."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def render_template(text: str, variables: Dict[str, str]) -> str:
    """Replace {{var}} placeholders with values."""
    pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return pattern.sub(replace, text)


def _require_sdk(sdk: object, name: str, install_hint: str) -> None:
    if sdk is None:
        raise RuntimeError(f"{name} SDK is not installed. Install with: {install_hint}")

def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def call_openai(
    prompt: str,
    model: str,
    system: Optional[str] = None,
    response_json: bool = False,
    enable_search_tool: bool = False,
    temperature: float = 0.0,
    timeout: int = 60,
) -> str:
    _require_sdk(OpenAI, "OpenAI", "pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if enable_search_tool:
        request: Dict[str, object] = {
            "model": model,
            "input": prompt,
            "temperature": temperature,
            "tools": [{"type": "web_search"}],
        }
        if system:
            request["instructions"] = system
        response = client.responses.create(**request)
        return response.output_text or ""

    request = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_json:
        request["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**request)
    return response.choices[0].message.content or ""


def call_anthropic(
    prompt: str,
    model: str,
    system: Optional[str] = None,
    response_json: bool = False,
    enable_search_tool: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    timeout: int = 60,
) -> str:
    _require_sdk(Anthropic, "Anthropic", "pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    client = Anthropic(api_key=api_key, base_url=base_url, timeout=timeout)

    if enable_search_tool:
        raise RuntimeError(
            "Anthropic SDK does not provide a built-in web search tool. "
            "Disable --enable-search-tool or integrate an external search tool."
        )

    request: Dict[str, object] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        request["system"] = system
    if response_json:
        request["stop_sequences"] = []

    response = client.messages.create(**request)
    parts = []
    for part in response.content or []:
        if part.type == "text":
            parts.append(part.text)
    return "".join(parts)


def call_gemini(
    prompt: str,
    model: str,
    system: Optional[str] = None,
    response_json: bool = False,
    enable_search_tool: bool = False,
    temperature: float = 0.0,
    timeout: int = 60,
) -> str:
    _require_sdk(google_genai, "Google GenAI", "pip install google-genai")
    _require_sdk(google_genai_types, "Google GenAI", "pip install google-genai")
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

    base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
    client = google_genai.Client(api_key=api_key, http_options={"base_url": base_url})

    config_kwargs: Dict[str, object] = {"temperature": temperature}
    if response_json:
        config_kwargs["response_mime_type"] = "application/json"
    if system:
        config_kwargs["system_instruction"] = system
    if enable_search_tool:
        config_kwargs["tools"] = [google_genai_types.Tool(google_search=google_genai_types.GoogleSearch())]

    config = google_genai_types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return response.text or ""


def call_provider(
    provider: str,
    prompt: str,
    model: str,
    system: Optional[str] = None,
    response_json: bool = False,
    enable_search_tool: bool = False,
    temperature: float = 0,
    max_tokens: int = 2048,
    timeout: int = 60,
) -> str:
    provider = provider.lower()
    if provider == "openai":
        return call_openai(
            prompt,
            model,
            system=system,
            response_json=response_json,
            enable_search_tool=enable_search_tool,
            temperature=temperature,
            timeout=timeout,
        )
    if provider == "anthropic":
        return call_anthropic(
            prompt,
            model,
            system=system,
            response_json=response_json,
            enable_search_tool=enable_search_tool,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    if provider == "gemini":
        return call_gemini(
            prompt,
            model,
            system=system,
            response_json=response_json,
            enable_search_tool=enable_search_tool,
            temperature=temperature,
            timeout=timeout,
        )
    raise RuntimeError(f"Unknown provider: {provider}")
