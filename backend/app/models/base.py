"""所有 ORM 模型共享的声明式基类与通用建表参数。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM 声明式基类。"""


# 通用建表参数：utf8mb4 + InnoDB（与数据库设计.sql 一致）
TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}
