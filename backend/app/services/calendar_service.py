"""日历/面试日程服务。

纯计算：把面试信息渲染为 ICS 文本，前端可下载为 .ics 文件。无状态、无外部依赖。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def build_ics(
    title: str,
    start_time: str,
    end_time: str | None = None,
    location: str = "",
    description: str = "",
) -> dict:
    """生成面试日程 ICS 内容。

    Args:
        title: 事件标题
        start_time: 开始时间（ISO 8601，如 2026-07-01T14:00:00）
        end_time: 结束时间（缺省为开始 +1 小时）
        location: 地点
        description: 备注

    Returns:
        {"ics_content": str, "title": str, "start_time": str, "end_time": str}
    Raises:
        ValueError: 时间格式非法。
    """
    try:
        start_dt = datetime.fromisoformat(start_time)
    except (ValueError, TypeError) as exc:
        raise ValueError("start_time 格式非法，应为 ISO 8601") from exc

    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except (ValueError, TypeError) as exc:
            raise ValueError("end_time 格式非法，应为 ISO 8601") from exc
    else:
        end_dt = start_dt + timedelta(hours=1)

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
        "ics_content": ics,
        "title": title,
        "start_time": start_time,
        "end_time": end_dt.isoformat(),
    }
