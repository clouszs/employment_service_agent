"""大语言模型客户端：DashScope qwen3.7-max（OpenAI 兼容接口）。"""

from collections.abc import Iterator
from functools import lru_cache

from openai import OpenAI

from app.core.config import settings


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_base_url)


def chat(messages: list[dict], temperature: float = 0.3) -> str:
    """非流式对话，返回完整答案文本。

    messages: [{"role": "system|user|assistant", "content": "..."}]
    """
    resp = _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def chat_stream(messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
    """流式对话，逐段产出文本增量(token)。"""
    stream = _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
