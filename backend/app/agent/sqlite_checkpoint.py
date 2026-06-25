"""LangGraph Checkpoint Saver：SQLite 持久化存储。

LangGraph 1.2.x 未内置 SqliteSaver，只有 MemorySaver。
本文件基于 BaseCheckpointSaver 实现最小可用的 SQLite 持久化。
"""

from __future__ import annotations

import json
import logging
import pickle
import sqlite3
import threading
from typing import Any, Iterator, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import RunnableConfig

logger = logging.getLogger(__name__)

# 默认 SQLite 文件路径（相对于项目根目录）
_DEFAULT_DB_PATH = "data/agent_checkpoints.db"


class SqliteSaver(BaseCheckpointSaver):
    """SQLite 持久化 Checkpoint Saver。

    存储结构：
    - checkpoints 表：存储每个 thread 的 checkpoint
    - checkpoint_writes 表：存储每次 checkpoint 的 writes
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接（线程局部）。"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        """初始化表结构。"""
        with self._lock:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    checkpoint TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL DEFAULT (julianday('now')),
                    PRIMARY KEY (thread_id, checkpoint_id)
                );
                CREATE TABLE IF NOT EXISTS checkpoint_writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    value TEXT,
                    PRIMARY KEY (thread_id, checkpoint_id, task_id, channel, idx)
                );
                CREATE INDEX IF NOT EXISTS idx_checkpoints_thread
                    ON checkpoints(thread_id, checkpoint_id);
            """)
            conn.commit()

    def get_tuple(self, config: RunnableConfig) -> Optional[Any]:
        """获取 checkpoint tuple。"""
        thread_id = (config.get("configurable") or {}).get("thread_id")
        if not thread_id:
            return None
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata "
                "FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
                (thread_id,),
            ).fetchone()
            if row is None:
                logger.debug("get_tuple: no row for thread_id=%s", thread_id)
                return None
            logger.debug("get_tuple: found row thread_id=%s checkpoint_id=%s", thread_id, row["checkpoint_id"])
            return self._row_to_tuple(row)
        except Exception as e:
            logger.error("get_tuple error: %s", e, exc_info=True)
            return None

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Any]:
        """列出 checkpoints。"""
        thread_id = (config or {}).get("configurable", {}).get("thread_id") if config else None
        if not thread_id:
            return iter([])
        conn = self._get_conn()
        try:
            sql = "SELECT checkpoint_id, parent_checkpoint_id, checkpoint, metadata FROM checkpoints WHERE thread_id = ?"
            params: list[Any] = [thread_id]
            if before:
                before_id = (before.get("configurable") or {}).get("checkpoint_id")
                if before_id:
                    sql += " AND checkpoint_id < ?"
                    params.append(before_id)
            sql += " ORDER BY checkpoint_id DESC"
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            for row in rows:
                yield self._row_to_tuple(row)
        except Exception as e:
            logger.warning("SqliteSaver list error: %s", e)
            return iter([])

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Any,
        metadata: Any,
        new_versions: Any,
    ) -> RunnableConfig:
        """写入 checkpoint。"""
        thread_id = (config.get("configurable") or {}).get("thread_id")
        checkpoint_id = checkpoint.get("id") if isinstance(checkpoint, dict) else getattr(checkpoint, "id", None)
        parent_checkpoint_id = (config.get("configurable") or {}).get("checkpoint_id")
        if not thread_id or not checkpoint_id:
            return config

        # 确保 checkpoint dict 包含 LangGraph 期望的版本字段
        if isinstance(checkpoint, dict) and "v" not in checkpoint:
            checkpoint["v"] = 1

        conn = self._get_conn()
        try:
            # 尝试 JSON 序列化；失败则降级到 pickle（binary 存 TEXT 会丢，但至少不崩）
            try:
                checkpoint_json = json.dumps(checkpoint, ensure_ascii=False, default=str)
                metadata_json = json.dumps(metadata, ensure_ascii=False, default=str) if metadata else None
            except (TypeError, ValueError, json.JSONDecodeError) as ser_err:
                logger.warning("Json serialize checkpoint failed, fallback to pickle: %s", ser_err)
                try:
                    checkpoint_json = pickle.dumps(checkpoint).hex()
                    metadata_json = pickle.dumps(metadata).hex() if metadata else None
                except Exception as pickle_err:
                    logger.error("Pickle serialize checkpoint also failed: %s", pickle_err)
                    return config

            conn.execute(
                "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint_json, metadata_json),
            )
            conn.commit()
        except Exception as e:
            logger.error("SqliteSaver put error: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
        task_path: str = "",
    ) -> None:
        """写入 checkpoint writes。"""
        thread_id = (config.get("configurable") or {}).get("thread_id")
        checkpoint_id = (config.get("configurable") or {}).get("checkpoint_id")
        if not thread_id or not checkpoint_id:
            return
        conn = self._get_conn()
        try:
            for idx, (channel, value) in enumerate(writes):
                conn.execute(
                    "INSERT OR REPLACE INTO checkpoint_writes (thread_id, checkpoint_id, task_id, channel, idx, value) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (thread_id, checkpoint_id, task_id, channel, idx, json.dumps(value, ensure_ascii=False, default=str)),
                )
            conn.commit()
        except Exception as e:
            logger.error("SqliteSaver put_writes error: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass

    def delete_thread(self, thread_id: str) -> None:
        """删除线程的所有 checkpoints。"""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (thread_id,))
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            conn.commit()
        except Exception as e:
            logger.error("SqliteSaver delete_thread error: %s", e)
            try:
                conn.rollback()
            except Exception:
                pass

    def _row_to_tuple(self, row: Any) -> Any:
        """将数据库行转为 CheckpointTuple。"""
        from langgraph.checkpoint.base import Checkpoint, CheckpointTuple

        # sqlite3.Row 支持键访问；某些版本可能返回 tuple，做兼容
        def _col(r: Any, name: str, fallback_index: int = 0) -> Any:
            try:
                return r[name]
            except (IndexError, KeyError, TypeError):
                try:
                    return r[fallback_index]
                except Exception:
                    return None

        thread_id = _col(row, "thread_id", 0)
        checkpoint_id = _col(row, "checkpoint_id", 1)
        parent_checkpoint_id = _col(row, "parent_checkpoint_id", 2)
        raw_checkpoint = _col(row, "checkpoint", 3)
        raw_metadata = _col(row, "metadata", 4)

        # 反序列化 checkpoint
        checkpoint_data = self._deserialize_json_or_pickle(raw_checkpoint)
        if not isinstance(checkpoint_data, dict):
            checkpoint_data = {"id": checkpoint_id}

        # 反序列化 metadata
        metadata = self._deserialize_json_or_pickle(raw_metadata) if raw_metadata else {}

        # 构造 Checkpoint：保留所有原始字段，只补缺省值
        checkpoint_obj = Checkpoint(
            id=checkpoint_data.get("id", checkpoint_id),
            v=checkpoint_data.get("v", 1),
            ts=checkpoint_data.get("ts"),
            channel_values=checkpoint_data.get("channel_values", {}),
            channel_versions=checkpoint_data.get("channel_versions", {}),
            versions_seen=checkpoint_data.get("versions_seen", {}),
            pending_sends=checkpoint_data.get("pending_sends", []),
        )

        return CheckpointTuple(
            config={"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}},
            checkpoint=checkpoint_obj,
            metadata=metadata if isinstance(metadata, dict) else {},
            parent_config={"configurable": {"thread_id": thread_id, "checkpoint_id": parent_checkpoint_id}} if parent_checkpoint_id else None,
        )

    def _deserialize_json_or_pickle(self, raw: Any) -> Any:
        """尝试 JSON 反序列化，失败则尝试 pickle hex fallback。"""
        if raw is None:
            return {}
        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            try:
                return pickle.loads(bytes.fromhex(raw))
            except Exception:
                return {}
