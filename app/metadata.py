from __future__ import annotations

# -*- coding: utf-8 -*-
# Метаданные точек (описание, ссылка на файл с расположением)

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .utils import CHANNEL_ORDER


@dataclass(frozen=True)
class PointMeta:
    code: str         # например H1L
    title: str        # читаемое имя точки
    description: str  # краткое описание расположения
    link: str         # относительная ссылка на файл-описание


def make_default_metadata(points_dir: Path) -> Dict[str, PointMeta]:
    """Генерирует простые заглушки метаданных для всех 24 точек.
    Позже можно заменить чтением из CSV/JSON/Markdown.
    """
    meta: Dict[str, PointMeta] = {}
    for ch in CHANNEL_ORDER:
        for side in ("L", "R"):
            code = f"{ch}{side}"
            title = f"{ch} {('Left' if side=='L' else 'Right')}"
            # Краткое описание-заглушка
            description = "Локализация точки см. в файле-описании."
            # Ссылка на файл (может быть md с таким же именем)
            link_path = points_dir / f"{code}.md"
            meta[code] = PointMeta(code=code, title=title, description=description, link=str(link_path))
    return meta