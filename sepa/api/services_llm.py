from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from config.settings import Settings, load_settings
from sepa.api.assistant_prompts import get_prompt, prompt_catalog_payload


class AssistantProviderError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AssistantMessage:
    role: str
    content: str


def _http_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    req = Request(
        url=url,
        data=json.dumps(body).encode('utf-8') if body is not None else None,
        headers=headers or {},
        method=method,
    )
    try:
        with urlopen(req, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='ignore')
        raise AssistantProviderError(exc.code, raw[:500] or 'LLM request failed') from exc
    except URLError as exc:
        raise AssistantProviderError(503, f'LLM network error: {exc}') from exc
    except TimeoutError as exc:
        raise AssistantProviderError(504, 'LLM request timed out while waiting for the model response') from exc
    except json.JSONDecodeError as exc:
        raise AssistantProviderError(502, 'LLM returned invalid JSON') from exc


def _trim_messages(messages: list[dict[str, Any]], max_messages: int) -> list[AssistantMessage]:
    trimmed = messages[-max_messages:]
    out: list[AssistantMessage] = []
    for item in trimmed:
        role = str(item.get('role') or '').strip().lower()
        content = str(item.get('content') or '').strip()
        if role not in {'user', 'assistant'} or not content:
            continue
        out.append(AssistantMessage(role=role, content=content[:4000]))
    return out


def _compact_context(context: Any, limit: int = 5000) -> str:
    if context in (None, '', {}, []):
        return ''
    try:
        serialized = json.dumps(context, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        serialized = str(context)
    if len(serialized) <= limit:
        return serialized
    return serialized[:limit] + '\n...<truncated>'


def _system_prompt(page_id: str, context: Any) -> str:
    prompt = get_prompt(page_id)
    compact_context = _compact_context(context)
    suffix = ''
    if compact_context:
        suffix = f'\n\nCurrent page context (JSON):\n{compact_context}'
    return (
        f"{prompt['system_prompt']}\n\n"
        'Important constraints:\n'
        '- Do not fabricate prices, fills, or backtest results.\n'
        '- If current context lacks evidence, say so clearly.\n'
        '- Keep answers concise, useful, and specific to this page.\n'
        '- Treat outputs as analysis assistance, not guaranteed financial advice.'
        f'{suffix}'
    )


class OllamaClient:
    def __init__(self, current_settings: Settings) -> None:
        self.base_url = current_settings.ollama_base_url.rstrip('/')
        self.model = current_settings.ollama_model
        self.timeout = current_settings.llm_timeout_seconds
        self.temperature = current_settings.llm_temperature

    def health(self) -> dict:
        payload = _http_json('GET', f'{self.base_url}/api/tags', timeout=self.timeout)
        models = payload.get('models') or []
        installed_names = [str(item.get('name') or item.get('model') or '').strip() for item in models]
        return {
            'provider': 'ollama',
            'base_url': self.base_url,
            'model': self.model,
            'available': True,
            'model_installed': self.model in installed_names,
            'installed_models': installed_names[:12],
        }

    def chat(self, *, page_id: str, messages: list[AssistantMessage], context: Any) -> dict:
        body = {
            'model': self.model,
            'stream': False,
            'messages': [
                {'role': 'system', 'content': _system_prompt(page_id, context)},
                *({'role': item.role, 'content': item.content} for item in messages),
            ],
            'options': {
                'temperature': self.temperature,
            },
        }
        payload = _http_json(
            'POST',
            f'{self.base_url}/api/chat',
            headers={'Content-Type': 'application/json'},
            body=body,
            timeout=self.timeout,
        )
        content = str(((payload.get('message') or {}).get('content')) or '').strip()
        if not content:
            raise AssistantProviderError(502, 'Ollama returned an empty response')
        return {
            'provider': 'ollama',
            'model': self.model,
            'content': content,
        }


class GeminiClient:
    def __init__(self, current_settings: Settings) -> None:
        self.api_key = current_settings.gemini_api_key
        self.model = current_settings.gemini_model
        self.timeout = current_settings.llm_timeout_seconds
        self.temperature = current_settings.llm_temperature

    def health(self) -> dict:
        return {
            'provider': 'gemini',
            'model': self.model,
            'configured': bool(self.api_key),
            'available': bool(self.api_key),
        }

    def chat(self, *, page_id: str, messages: list[AssistantMessage], context: Any) -> dict:
        if not self.api_key:
            raise AssistantProviderError(503, 'Gemini API key is not configured')

        contents = []
        for item in messages:
            role = 'model' if item.role == 'assistant' else 'user'
            contents.append({'role': role, 'parts': [{'text': item.content}]})

        payload = _http_json(
            'POST',
            f"https://generativelanguage.googleapis.com/v1beta/models/{quote(self.model)}:generateContent",
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key,
            },
            body={
                'systemInstruction': {
                    'parts': [{'text': _system_prompt(page_id, context)}],
                },
                'contents': contents,
                'generationConfig': {
                    'temperature': self.temperature,
                },
            },
            timeout=self.timeout,
        )
        candidates = payload.get('candidates') or []
        parts = (((candidates[0] if candidates else {}).get('content') or {}).get('parts') or [])
        content = '\n'.join(str(part.get('text') or '').strip() for part in parts if part.get('text')).strip()
        if not content:
            raise AssistantProviderError(502, 'Gemini returned an empty response')
        return {
            'provider': 'gemini',
            'model': self.model,
            'content': content,
        }


def _resolve_provider(current_settings: Settings) -> tuple[str, Any]:
    provider = str(current_settings.llm_provider or 'ollama').strip().lower()
    ollama = OllamaClient(current_settings)
    gemini = GeminiClient(current_settings)
    if provider == 'ollama':
        return provider, ollama
    if provider == 'gemini':
        return provider, gemini
    if provider == 'auto':
        try:
            health = ollama.health()
            if health.get('available'):
                return 'ollama', ollama
        except AssistantProviderError:
            pass
        return 'gemini', gemini
    raise AssistantProviderError(400, f'Unsupported SEPA_LLM_PROVIDER: {provider}')


def assistant_health_payload(current_settings: Settings | None = None) -> dict:
    current_settings = current_settings or load_settings()
    try:
        provider_name, provider = _resolve_provider(current_settings)
        provider_health = provider.health()
        ready = bool(provider_health.get('available'))
    except AssistantProviderError as exc:
        provider_name = str(current_settings.llm_provider or 'unknown')
        provider_health = {'error': str(exc)}
        ready = False
    return {
        'provider': provider_name,
        'ready': ready,
        'provider_health': provider_health,
        'personas': prompt_catalog_payload(),
    }


def assistant_chat_payload(
    *,
    page_id: str,
    messages: list[dict[str, Any]],
    context: Any,
    current_settings: Settings | None = None,
) -> dict:
    current_settings = current_settings or load_settings()
    trimmed = _trim_messages(messages, current_settings.llm_max_history_messages)
    if not trimmed:
        raise AssistantProviderError(400, 'At least one chat message is required')
    _, provider = _resolve_provider(current_settings)
    result = provider.chat(page_id=page_id, messages=trimmed, context=context)
    persona = get_prompt(page_id)
    return {
        **result,
        'page_id': page_id,
        'persona_title': persona['title'],
    }
