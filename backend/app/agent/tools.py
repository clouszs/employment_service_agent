"""Agent 外部检索工具：Bing 搜索 + 网页抓取（通过外部 MCP 服务）+ 本地 RAG 检索。

架构约束（三层定位法，2026-06-28 冻结）：
本文件仅承载「Agent 推理过程中需要的检索能力」，分两类：
  1. 进程内 RAG 检索：knowledge_search（直接查本地向量库）。
  2. 外部第三方能力：bing_search / fetch_webpage（通过 _MCPClient 调用外部 MCP 服务）。

禁止在此文件新增业务逻辑函数（LLM 生成、数据库写入、日期/文件计算等）。新增能力请按性质归位：
  - 对话式推理 → app/agent/nodes.py 的图节点
  - 我方 DB/文件上的确定性业务操作 → app/services/*_service.py + REST 端点
  - 真·外部第三方能力且需隔离 → 在此通过 _MCPClient 调外部 MCP server
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ==================== MCP 客户端 ====================


class _MCPClient:
    """轻量 MCP 客户端：通过 JSON-RPC over HTTP 调用远程 MCP 工具。"""

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session_id: str | None = None
        self._tools_cache: list[dict] | None = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """发送 JSON-RPC 请求并返回 result。"""
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.post(self.base_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

            # 保存 session id
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self._session_id = sid

            if "error" in data and data["error"]:
                raise RuntimeError(f"MCP error: {data['error']}")
            return data.get("result", {})

    def initialize(self) -> None:
        """初始化 MCP 会话（只需一次）。"""
        if self._session_id:
            return
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "employment-agent", "version": "1.0.0"},
            },
        }
        result = self._request(payload)
        self._session_id = result.get("sessionId") or self._session_id

    def list_tools(self) -> list[dict]:
        """获取可用工具列表（带缓存）。"""
        if self._tools_cache is not None:
            return self._tools_cache
        self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        result = self._request(payload)
        self._tools_cache = result.get("tools", [])
        return self._tools_cache

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """调用指定工具。"""
        self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
        result = self._request(payload)
        return result.get("content", [])

    def find_tool(self, candidates: list[str]) -> str | None:
        """在工具列表中查找匹配的工具名。"""
        tools = self.list_tools()
        names = {t.get("name", "") for t in tools}
        for c in candidates:
            if c in names:
                return c
        return None


# ==================== Bing 搜索 ====================


def bing_search(query: str, page_size: int = 5, site_filter: str | None = None) -> list[dict]:
    """通过 Bing MCP 服务搜索，返回标准化引用片段。

    如果 MCP 调用失败，返回空列表。
    """
    try:
        client = _MCPClient(
            base_url=settings.bing_search_url,
            timeout=settings.bing_search_timeout,
        )

        # 查找可用工具名
        tool_name = client.find_tool([
            "bing_search",
            "bing-cn_search",
            "web_search",
            "search",
            "bing_web_search",
        ])
        if not tool_name:
            logger.warning("Bing MCP 未找到可用搜索工具")
            return []

        # 构造查询参数
        args: dict[str, Any] = {"query": query, "count": page_size}
        if site_filter:
            args["site"] = site_filter

        content = client.call_tool(tool_name, args)
        return _parse_bing_results(content)
    except Exception as exc:  # noqa: BLE001
        logger.warning("bing_search 失败: %s", exc)
        return []


def _parse_bing_results(content: list[dict]) -> list[dict]:
    """将 Bing MCP 返回内容解析为标准化 hits。"""
    hits: list[dict] = []

    # MCP content 是 [{type: "text", text: "..."}] 格式
    raw_text = ""
    for item in content:
        if item.get("type") == "text":
            raw_text = item.get("text", "")
            break

    if not raw_text:
        return []

    # 尝试解析为 JSON（部分 MCP 服务直接返回结构化结果）
    parsed = None
    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 提取结果条目
    items = []
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        for key in ("results", "items", "webPages", "value"):
            if key in parsed and isinstance(parsed[key], list):
                items = parsed[key]
                break
        else:
            items = [parsed]

    for rank, item in enumerate(items[:10], start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name") or ""
        snippet = item.get("snippet") or item.get("description") or item.get("content") or ""
        url = item.get("url") or item.get("link") or item.get("sourceUrl") or ""
        source = item.get("source") or item.get("siteName") or _extract_domain(url)
        published_at = item.get("publishedAt") or item.get("date") or item.get("published_date")

        if not title and not snippet:
            continue

        hits.append(
            {
                "chunk_id": None,
                "document_id": None,
                "document_title": title,
                "content": f"{title}\n{snippet}".strip(),
                "score": 0.0,
                "page_no": None,
                "metadata": {
                    "source_type": "web",
                    "url": url,
                    "source": source,
                    "published_at": published_at,
                    "author": item.get("author"),
                },
            }
        )

    return hits


def _extract_domain(url: str) -> str | None:
    """从 URL 提取域名。"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or None
    except Exception:  # noqa: BLE001
        return None


# ==================== Fetch 网页抓取 ====================


def fetch_webpage(url: str, max_length: int | None = None) -> str | None:
    """通过 Fetch MCP 服务抓取网页正文。

    返回提取后的正文文本，失败返回 None。
    """
    if not url:
        return None

    try:
        client = _MCPClient(
            base_url=settings.fetch_url,
            timeout=settings.fetch_timeout,
        )

        tool_name = client.find_tool([
            "fetch",
            "fetch_url",
            "web_fetch",
            "get_page",
            "fetch_webpage",
        ])
        if not tool_name:
            logger.warning("Fetch MCP 未找到可用抓取工具")
            return None

        args: dict[str, Any] = {"url": url}
        if max_length:
            args["max_length"] = max_length
        else:
            args["max_length"] = settings.fetch_max_length

        content = client.call_tool(tool_name, args)

        # 提取文本内容
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                if text:
                    return text
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch_webpage 失败: url=%s err=%s", url, exc)
        return None


# ==================== 工具注册表 ====================


class ToolCallTracker:
    """工具调用计数器 + 调用记录。"""

    def __init__(self) -> None:
        self.count: int = 0
        self.calls: list[dict] = []

    def record(self, tool_name: str, args: dict, result: Any) -> None:
        self.count += 1
        self.calls.append(
            {
                "tool": tool_name,
                "args": args,
                "result_summary": str(result)[:200] if result else None,
            }
        )

    def should_stop(self, max_calls: int = 3) -> bool:
        return self.count >= max_calls


# 延迟导入 knowledge_search，避免循环依赖
def _get_knowledge_search():
    from app.services.rag_service import search as rag_search
    def _search(query: str, top_k: int = 5) -> list[dict]:
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            return rag_search(db, query, top_k=top_k)
        finally:
            db.close()
    return _search


class _LazyKnowledgeSearch:
    """延迟加载的 knowledge_search，避免循环导入。"""

    def __call__(self, query: str, top_k: int = 5) -> list[dict]:
        fn = _get_knowledge_search()
        return fn(query, top_k=top_k)


knowledge_search = _LazyKnowledgeSearch()
