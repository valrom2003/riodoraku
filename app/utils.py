from __future__ import annotations

# -*- coding: utf-8 -*-
# Вспомогательные структуры и константы для приложения Riodoraku

from typing import Dict, List, Tuple

# Список каналов и читаемые имена (без стороны)
CHANNELS_READABLE: Dict[str, str] = {
    "H1": "H1 (Lung)",
    "H2": "H2 (Pericardium)",
    "H3": "H3 (Heart)",
    "H4": "H4 (Small intestine)",
    "H5": "H5 (Triple Heater)",
    "H6": "H6 (Large intestine)",
    "F1": "F1 (Spleen/Pancreas)",
    "F2": "F2 (Liver)",
    "F3": "F3 (Kidney)",
    "F4": "F4 (Urinary Bladder)",
    "F5": "F5 (Gallbladder)",
    "F6": "F6 (Stomach)",
}

# Порядок вывода каналов на оси X
CHANNEL_ORDER: List[str] = [
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
]

# Полный список кодов с учетом стороны
SIDES: Tuple[str, str] = ("L", "R")
POINT_CODES_24: List[str] = [f"{ch}{side}" for ch in CHANNEL_ORDER for side in SIDES]

# Группы для расчетов
YIN_CHANNELS: List[str] = ["H1", "F1", "H3", "F3", "H2", "F2"]
YANG_CHANNELS: List[str] = ["H6", "F6", "H4", "F4", "H5", "F5"]

HANDS_CHANNELS: List[str] = ["H1", "H2", "H3", "H4", "H5", "H6"]
FEET_CHANNELS: List[str] = ["F1", "F2", "F3", "F4", "F5", "F6"]

INNER_CHANNELS: List[str] = ["H1", "H2", "H3", "F1", "F2", "F3"]
OUTER_CHANNELS: List[str] = ["H4", "H5", "H6", "F4", "F5", "F6"]

# Соответствие кода канала к имени меридиана
MERIDIAN_NAME: Dict[str, str] = {
    "H1": "Легкие",
    "H2": "Перикард",
    "H3": "Сердце",
    "H4": "Тонкий кишечник",
    "H5": "Тройной обогреватель",
    "H6": "Толстый кишечник",
    "F1": "Селезенка/Поджелудочная",
    "F2": "Печень",
    "F3": "Почки",
    "F4": "Мочевой пузырь",
    "F5": "Желчный пузырь",
    "F6": "Желудок",
}

# Цвета для визуализации (можно подстроить)
COLOR_SAFE = "#2ca02c"  # внутри коридора нормы
COLOR_HIGH = "#d62728"  # выше коридора
COLOR_LOW = "#1f77b4"   # ниже коридора
COLOR_NEUTRAL = "#7f7f7f"


def channels_to_side_codes(channels: List[str], side: str) -> List[str]:
    """Возвращает коды точек для указанного списка каналов и стороны."""
    return [f"{c}{side}" for c in channels]