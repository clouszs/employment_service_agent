"""大语言模型客户端：DashScope qwen3.7-max（OpenAI 兼容接口）。"""

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.core.config import settings


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_base_url)


def _chat_completion(messages: list[dict], temperature: float, **kwargs: Any) -> Any:
    """执行一次 DashScope chat.completions.create，返回完整响应对象。"""
    return _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        timeout=30,
        **kwargs,
    )


def chat(messages: list[dict], temperature: float = 0.3) -> str:
    """非流式对话，返回完整答案文本。

    messages: [{"role": "system|user|assistant", "content": "..."}]
    """
    resp = _chat_completion(messages, temperature)
    return resp.choices[0].message.content or ""


def chat_stream(messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
    """流式对话，逐段产出文本增量(token)。"""
    stream = _chat_completion(messages, temperature, stream=True)
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def chat_with_usage(messages: list[dict], temperature: float = 0.3) -> tuple[str, dict[str, int]]:
    """非流式对话，返回 (答案文本, {prompt_tokens, completion_tokens})。

    用于需要精确追踪 token 消耗的场景（如 Agent 工作流）。
    """
    resp = _chat_completion(messages, temperature)
    usage = resp.usage or {}
    return (
        resp.choices[0].message.content or "",
        {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        },
    )
