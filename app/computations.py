from __future__ import annotations

# -*- coding: utf-8 -*-
# Вычисления агрегатов и аналитики Riodoraku

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .utils import (
    CHANNEL_ORDER,
    CHANNELS_READABLE,
    MERIDIAN_NAME,
    POINT_CODES_24,
    YIN_CHANNELS,
    YANG_CHANNELS,
    HANDS_CHANNELS,
    FEET_CHANNELS,
    INNER_CHANNELS,
    OUTER_CHANNELS,
    channels_to_side_codes,
)

# Карта точек тонизации/седатации (пять элементов) для 12 меридианов
# Примечание: это стандартные 5-shu точки; при необходимости можно уточнить
FIVE_ELEMENTS_POINTS: Dict[str, Dict[str, str]] = {
    # H-меридианы (руки)
    "H1": {"tonify": "LU9", "sedate": "LU5"},  # Легкие
    "H2": {"tonify": "PC9", "sedate": "PC7"},  # Перикард
    "H3": {"tonify": "HT9", "sedate": "HT7"},  # Сердце
    "H4": {"tonify": "SI3", "sedate": "SI8"},  # Тонкий кишечник
    "H5": {"tonify": "SJ3", "sedate": "SJ10"}, # Тройной обогреватель
    "H6": {"tonify": "LI11", "sedate": "LI2"}, # Толстый кишечник
    # F-меридианы (ноги)
    "F1": {"tonify": "SP2", "sedate": "SP5"},  # Селезенка/ПЖ
    "F2": {"tonify": "LV8", "sedate": "LV2"},  # Печень
    "F3": {"tonify": "KI7", "sedate": "KI1"},  # Почки
    "F4": {"tonify": "BL67", "sedate": "BL65"}, # Мочевой пузырь
    "F5": {"tonify": "GB43", "sedate": "GB38"}, # Желчный пузырь
    "F6": {"tonify": "ST41", "sedate": "ST45"}, # Желудок
}


@dataclass(frozen=True)
class Corridor:
    mean_all: float
    lower: float
    upper: float


@dataclass(frozen=True)
class ExtremePoint:
    code: str  # пример: H1L
    value: float
    meridian: str  # читаемое имя меридиана
    action: str  # "успокаивать" или "возбуждать"
    recommend_point: str | None = None  # точка для воздействия (для five_elements)


def compute_means_for_side(row: pd.Series, channels: List[str], side: str) -> float:
    """Среднее значение по заданным каналам и стороне."""
    cols = channels_to_side_codes(channels, side)
    values = [row.get(c) for c in cols]
    arr = np.array([v for v in values if pd.notna(v)], dtype=float)
    return float(arr.mean()) if arr.size else float("nan")


def compute_overall_mean(row: pd.Series) -> float:
    """Среднее значение по всем 24 точкам."""
    arr = np.array([row.get(c) for c in POINT_CODES_24 if pd.notna(row.get(c))], dtype=float)
    return float(arr.mean()) if arr.size else float("nan")


def compute_corridor(row: pd.Series, width: float = 0.10) -> Corridor:
    """Коридор нормы как ±width от среднего всех 24."""
    mean_all = compute_overall_mean(row)
    return Corridor(mean_all=mean_all, lower=mean_all * (1 - width), upper=mean_all * (1 + width))


def _recommend_point_for_meridian(meridian_code: str, action: str) -> str | None:
    """Возвращает точку воздействия по правилу пяти элементов.
    action: "успокаивать" -> sedate; "возбуждать" -> tonify
    """
    mapping = FIVE_ELEMENTS_POINTS.get(meridian_code)
    if not mapping:
        return None
    if action == "успокаивать":
        return mapping.get("sedate")
    if action == "возбуждать":
        return mapping.get("tonify")
    return None


def compute_extremes(row: pd.Series, recommendation_mode: str = "simple") -> Tuple[ExtremePoint, ExtremePoint]:
    """Находит минимальную и максимальную точки среди 24 и формирует рекомендации."""
    values = {code: row.get(code) for code in POINT_CODES_24}
    values = {k: v for k, v in values.items() if pd.notna(v)}
    if not values:
        ep = ExtremePoint(code="", value=float("nan"), meridian="", action="", recommend_point=None)
        return ep, ep
    max_code = max(values, key=lambda k: values[k])
    min_code = min(values, key=lambda k: values[k])
    max_mer_code = max_code[:-1]
    min_mer_code = min_code[:-1]
    max_mer = MERIDIAN_NAME[max_mer_code]
    min_mer = MERIDIAN_NAME[min_mer_code]
    max_action = "успокаивать"
    min_action = "возбуждать"
    max_rec = None
    min_rec = None
    if recommendation_mode == "five_elements":
        max_rec = _recommend_point_for_meridian(max_mer_code, max_action)
        min_rec = _recommend_point_for_meridian(min_mer_code, min_action)
    max_point = ExtremePoint(code=max_code, value=float(values[max_code]), meridian=max_mer, action=max_action, recommend_point=max_rec)
    min_point = ExtremePoint(code=min_code, value=float(values[min_code]), meridian=min_mer, action=min_action, recommend_point=min_rec)
    return max_point, min_point


def compute_all_metrics_for_row(row: pd.Series, recommendation_mode: str = "simple") -> Dict[str, float | str]:
    """Возвращает словарь всех требуемых метрик для одной строки (одной даты)."""
    corridor = compute_corridor(row)

    yin_l = compute_means_for_side(row, YIN_CHANNELS, "L")
    yin_r = compute_means_for_side(row, YIN_CHANNELS, "R")
    yang_l = compute_means_for_side(row, YANG_CHANNELS, "L")
    yang_r = compute_means_for_side(row, YANG_CHANNELS, "R")

    hands_l = compute_means_for_side(row, HANDS_CHANNELS, "L")
    hands_r = compute_means_for_side(row, HANDS_CHANNELS, "R")
    feet_l = compute_means_for_side(row, FEET_CHANNELS, "L")
    feet_r = compute_means_for_side(row, FEET_CHANNELS, "R")

    inner_l = compute_means_for_side(row, INNER_CHANNELS, "L")
    inner_r = compute_means_for_side(row, INNER_CHANNELS, "R")
    outer_l = compute_means_for_side(row, OUTER_CHANNELS, "L")
    outer_r = compute_means_for_side(row, OUTER_CHANNELS, "R")

    max_point, min_point = compute_extremes(row, recommendation_mode=recommendation_mode)

    metrics: Dict[str, float | str] = {
        "Yin_L": yin_l,
        "Yin_R": yin_r,
        "Yang_L": yang_l,
        "Yang_R": yang_r,
        "Hands_L": hands_l,
        "Hands_R": hands_r,
        "Feet_L": feet_l,
        "Feet_R": feet_r,
        "Inner_L": inner_l,
        "Inner_R": inner_r,
        "Outer_L": outer_l,
        "Outer_R": outer_r,
        "MeanAll": corridor.mean_all,
        "CorridorLower": corridor.lower,
        "CorridorUpper": corridor.upper,
        "MaxCode": max_point.code,
        "MaxValue": max_point.value,
        "MaxMeridian": max_point.meridian,
        "MaxAction": max_point.action,
        "MaxRecommendPoint": max_point.recommend_point or "",
        "MinCode": min_point.code,
        "MinValue": min_point.value,
        "MinMeridian": min_point.meridian,
        "MinAction": min_point.action,
        "MinRecommendPoint": min_point.recommend_point or "",
    }
    return metrics


def build_bar_dataframe(row: pd.Series) -> pd.DataFrame:
    """Формирует DataFrame для Bar-графика: строки = каналы, колонки = L/R."""
    data = []
    for ch in CHANNEL_ORDER:
        data.append({
            "Channel": CHANNELS_READABLE[ch],
            "L": row.get(f"{ch}L", np.nan),
            "R": row.get(f"{ch}R", np.nan),
            "CodeL": f"{ch}L",
            "CodeR": f"{ch}R",
        })
    return pd.DataFrame(data)