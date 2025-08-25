from __future__ import annotations

# -*- coding: utf-8 -*-
# Точка входа Dash приложения

import os
from pathlib import Path

from dash import Dash
from flask_caching import Cache
from dotenv import load_dotenv

from .layout import build_layout
from .callbacks import register_callbacks


load_dotenv()

PROJECT_TITLE = "Riodoraku Analytics"
DATA_DIR = Path(os.getenv("DATA_DIR", "./data/measurements")).resolve()
POINTS_DIR = Path(os.getenv("POINTS_DIR", "./data/points")).resolve()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8050"))


def create_app() -> Dash:
    app = Dash(__name__, suppress_callback_exceptions=True)
    # Кэш можно использовать для тяжелых операций, пока оставим конфиг по умолчанию
    Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

    app.title = PROJECT_TITLE
    app.layout = build_layout(PROJECT_TITLE)

    register_callbacks(app, DATA_DIR, POINTS_DIR)
    return app


def main() -> None:
    app = create_app()
    # Убедимся, что каталоги существуют
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    POINTS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host=HOST, port=PORT, debug=True)


if __name__ == "__main__":
    main()