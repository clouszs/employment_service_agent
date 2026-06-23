"""文档解析：从文件提取纯文本。

支持：txt / md / pdf
返回结构：[{"text": 段文本, "page_no": 页码或None}]
  - txt/md：整篇作为一段，page_no=None
  - pdf：按页提取，每页一段，带 page_no（从1开始）
"""

from pathlib import Path

from pypdf import PdfReader

_TEXT_EXTS = {".txt", ".md", ".markdown"}


def parse_file(file_path: str) -> list[dict]:
    """按文件类型解析为带页码的文本段列表。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = path.suffix.lower()
    if ext in _TEXT_EXTS:
        return _parse_text(path)
    if ext == ".pdf":
        return _parse_pdf(path)
    raise ValueError(f"暂不支持的文件类型: {ext}（当前支持 txt/md/pdf）")


def _parse_text(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    return [{"text": text, "page_no": None}] if text else []


def _parse_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    segments: list[dict] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            segments.append({"text": text, "page_no": i})
    return segments
