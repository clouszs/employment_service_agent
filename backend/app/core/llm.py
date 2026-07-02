"""大语言模型客户端：DashScope qwen3.7-max（OpenAI 兼容接口）。"""

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import settings


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_base_url)


def _chat_completion(messages: list[dict], temperature: float, model: str | None = None, **kwargs: Any) -> Any:
    """执行一次 DashScope chat.completions.create，返回完整响应对象。"""
    return _client().chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        timeout=30,
        **kwargs,
    )


def chat(messages: list[dict], temperature: float = 0.3, model: str | None = None) -> str:
    """非流式对话，返回完整答案文本。"""
    resp = _chat_completion(messages, temperature, model=model)
    return resp.choices[0].message.content or ""


def chat_stream(messages: list[dict], temperature: float = 0.3, model: str | None = None) -> Iterator[str]:
    """流式对话，逐段产出文本增量(token)。"""
    stream = _chat_completion(messages, temperature, model=model, stream=True)
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def chat_with_usage(messages: list[dict], temperature: float = 0.3, model: str | None = None) -> tuple[str, dict[str, int]]:
    """非流式对话，返回 (答案文本, {prompt_tokens, completion_tokens})。"""
    resp = _chat_completion(messages, temperature, model=model)
    usage = resp.usage or {}
    return (
        resp.choices[0].message.content or "",
        {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        },
    )
