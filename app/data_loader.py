from __future__ import annotations

# -*- coding: utf-8 -*-
# Загрузка и валидация данных CSV Riodoraku

from pathlib import Path
from typing import List

import pandas as pd
from dateutil import parser as dateparser

from .utils import POINT_CODES_24


def list_csv_files(data_dir: Path) -> List[Path]:
    """Сканирует каталог и возвращает список CSV-файлов."""
    if not data_dir.exists():
        return []
    return sorted([p for p in data_dir.glob("*.csv") if p.is_file()])


def parse_date(value: str) -> pd.Timestamp:
    """Гибкий парсинг даты с приведением к дате без времени."""
    dt = dateparser.parse(value, dayfirst=True)
    return pd.Timestamp(dt.date())


def load_csv_file(path: Path) -> pd.DataFrame:
    """Загружает один CSV с нормализацией колонок и дат."""
    df = pd.read_csv(path)
    # Приводим имена колонок к единообразию
    df.columns = [c.strip() for c in df.columns]
    # Проверяем наличие требуемых колонок
    required = {"Date", *POINT_CODES_24}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В файле {path} отсутствуют колонки: {sorted(missing)}")
    # Парсим дату
    df["Date"] = df["Date"].map(parse_date)
    # Приводим числовые значения
    for col in POINT_CODES_24:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Добавляем источник
    df["SourceFile"] = path.name
    return df


def load_many(files: List[Path]) -> pd.DataFrame:
    """Загружает несколько CSV и объединяет их по строкам."""
    frames: List[pd.DataFrame] = []
    for f in files:
        try:
            frames.append(load_csv_file(f))
        except Exception as exc:
            # Не прерываем загрузку всех файлов; проблемный файл пропускаем
            print(f"[WARN] Пропуск файла {f}: {exc}")
    if not frames:
        return pd.DataFrame(columns=["Date", *POINT_CODES_24, "SourceFile"])  # пустой каркас
    df_all = pd.concat(frames, ignore_index=True)
    # Удаляем полностью пустые строки по точкам
    if not df_all.empty:
        df_all = df_all.dropna(subset=POINT_CODES_24, how="all").reset_index(drop=True)
    return df_all