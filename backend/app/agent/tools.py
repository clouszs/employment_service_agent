"""外部检索工具：Bing 搜索 + 网页抓取（通过 MCP 服务）。"""

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

# ==================== 业务工具（阶段 9 新增） ====================


def toggle_faq_status(faq_id: int, enabled: bool) -> dict:
    """切换 FAQ 启用状态。

    通过 ops_service 直接更新 FAQ 状态，返回操作结果。
    """
    try:
        from app.services.ops_service import update_faq_status

        result = update_faq_status(faq_id=faq_id, enabled=enabled)
        return {
            "success": True,
            "faq_id": faq_id,
            "enabled": enabled,
            "message": f"FAQ#{faq_id} 已{'启用' if enabled else '禁用'}",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("toggle_faq_status 失败: faq_id=%s err=%s", faq_id, exc)
        return {"success": False, "faq_id": faq_id, "enabled": enabled, "error": str(exc)}


def generate_resume(user_profile: dict | None = None, target_job: str = "") -> dict:
    """根据用户档案和目标岗位生成简历内容（V1 简化版）。

    调用 LLM 基于用户档案和目标岗位生成简历 JSON 结构。
    V1 不做真实模板渲染，只返回结构化 JSON。
    """
    try:
        from app.core.llm import chat_with_usage

        profile_text = str(user_profile or {})
        prompt = (
            "你是简历生成助手。请根据用户档案和目标岗位生成一份中文简历 JSON。\n"
            "格式要求：\n"
            '{"basics": {"name":"","email":"","phone":"","location":""},'
            '"summary":"","education":[],"experience":[],"skills":[]}\n'
            "只返回 JSON，不要其他内容。\n"
            f"用户档案：{profile_text}\n"
            f"目标岗位：{target_job or '未指定'}\n"
        )
        response, _ = chat_with_usage(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return {
            "success": True,
            "resume_json": response,
            "target_job": target_job,
            "note": "V1 简化版：返回 JSON 结构，不做模板渲染",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("generate_resume 失败: %s", exc)
        return {"success": False, "error": str(exc)}


def recommend_jobs(query: str, top_k: int = 5) -> dict:
    """职位推荐：基于知识库向量匹配 + 简单规则过滤。

    复用 RAG 检索，搜索职位类文档，返回匹配结果。
    V1 简化：不做外部 API 调用，只做本地知识库检索。
    """
    try:
        from app.services.rag_service import search as rag_search
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            hits = rag_search(db, query, top_k=top_k)
            jobs = []
            for hit in hits:
                meta = hit.get("metadata") or {}
                jobs.append(
                    {
                        "title": hit.get("document_title") or meta.get("title"),
                        "score": hit.get("score", 0.0),
                        "source": "knowledge_base",
                        "snippet": (hit.get("content") or "")[:200],
                    }
                )
            return {
                "success": True,
                "jobs": jobs,
                "count": len(jobs),
                "query": query,
                "note": "V1 简化版：基于知识库检索，不做外部 API 调用",
            }
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("recommend_jobs 失败: %s", exc)
        return {"success": False, "jobs": [], "query": query, "error": str(exc)}


def add_calendar_event(
    title: str,
    start_time: str,
    end_time: str | None = None,
    location: str = "",
    description: str = "",
) -> dict:
    """生成面试日程 ICS 文件内容（V1 简化版）。

    返回 ICS 格式字符串，前端可直接下载为 .ics 文件。
    V1 不做后端持久化，只生成 ICS 内容。
    """
    try:
        from datetime import datetime, timedelta

        start_dt = datetime.fromisoformat(start_time)
        end_dt = (
            datetime.fromisoformat(end_time)
            if end_time
            else start_dt + timedelta(hours=1)
        )

        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
        dtend = end_dt.strftime("%Y%m%dT%H%M%S")
        uid = f"interview-{int(start_dt.timestamp())}@employment-platform"

        ics = (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//Employment Platform//CN\n"
            "BEGIN:VEVENT\n"
            f"UID:{uid}\n"
            f"DTSTAMP:{dtstamp}\n"
            f"DTSTART:{dtstart}\n"
            f"DTEND:{dtend}\n"
            f"SUMMARY:{title}\n"
            f"LOCATION:{location}\n"
            f"DESCRIPTION:{description}\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )
        return {
            "success": True,
            "ics_content": ics,
            "title": title,
            "start_time": start_time,
            "end_time": end_time or (start_dt + timedelta(hours=1)).isoformat(),
            "note": "V1 简化版：返回 ICS 内容，前端负责下载",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("add_calendar_event 失败: %s", exc)
        return {"success": False, "error": str(exc)}


def fetch_announcement(query: str = "", max_results: int = 5) -> dict:
    """获取当前生效的公告列表（从 JSON 配置文件读取）。

    读取 data/announcements.json，过滤出当前时间在 effective_time 和 expire_time 之间的公告。
    如果 query 非空，则按标题/content 做简单关键词过滤。
    如果文件损坏或不存在，降级返回空列表。
    """
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        config_path = Path(__file__).resolve().parents[2] / "data" / "announcements.json"
        if not config_path.exists():
            logger.debug("公告配置文件不存在: %s", config_path)
            return {"success": True, "announcements": [], "count": 0, "source": "config"}

        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("announcements", [])

        now = datetime.now()
        active = []
        for item in items:
            if item.get("status") != "active":
                continue
            effective = item.get("effective_time")
            expire = item.get("expire_time")
            if effective:
                try:
                    eff_dt = datetime.fromisoformat(effective)
                    if now < eff_dt:
                        continue
                except (ValueError, TypeError):
                    continue
            if expire:
                try:
                    exp_dt = datetime.fromisoformat(expire)
                    if now > exp_dt:
                        continue
                except (ValueError, TypeError):
                    continue
            active.append(item)

        if query:
            q = query.lower()
            active = [
                a
                for a in active
                if q in a.get("title", "").lower() or q in a.get("content", "").lower()
            ]

        active = active[: max(1, max_results)]
        return {
            "success": True,
            "announcements": active,
            "count": len(active),
            "source": "config",
            "note": "V1 简化版：从 JSON 配置文件读取，不做后端查询",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch_announcement 失败: %s", exc)
        return {"success": True, "announcements": [], "count": 0, "error": str(exc)}


TOOLS: dict[str, Any] = {
    "knowledge_search": knowledge_search,
    "bing_search": bing_search,
    "fetch_webpage": fetch_webpage,
    # 阶段 9 新增工具
    "toggle_faq_status": toggle_faq_status,
    "generate_resume": generate_resume,
    "recommend_jobs": recommend_jobs,
    "add_calendar_event": add_calendar_event,
    "fetch_announcement": fetch_announcement,
}
