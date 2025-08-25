from __future__ import annotations

# -*- coding: utf-8 -*-
# Layout Dash-приложения

from typing import List

from dash import dcc, html
import dash_cytoscape as cyto


def build_layout(project_title: str) -> html.Div:
    """Формирует основной layout приложения."""
    return html.Div([
        # Заголовок проекта
        html.Div([
            html.H2(project_title, id="project-title"),
            html.Div(id="status-text"),
        ], style={"marginBottom": "12px"}),

        # Панель управления
        html.Div([
            html.Div([
                html.Label("Файлы измерений"),
                dcc.Dropdown(id="file-dropdown", options=[], multi=False, placeholder="Выберите файл"),
            ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}),
            html.Div([
                html.Label("Даты"),
                dcc.Dropdown(id="date-dropdown", options=[], multi=False, placeholder="Выберите дату"),
            ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}),
                html.Div([
                    html.Label("Режим анализа точек"),
                    dcc.Dropdown(id="analysis-mode-point", options=[], multi=False, placeholder="Выберите точку"),
                    html.Label("Режим анализа показателей", style={"marginTop": "12px"}),
                    dcc.Dropdown(id="analysis-mode-metric", options=[], multi=False, placeholder="Выберите показатель"),
                ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}),
                html.Div([
                    html.Button("Применить", id="apply-filters", n_clicks=0, style={"marginTop": "28px", "marginRight": "6px"}),
                ], style={"width": "26%", "display": "inline-block", "verticalAlign": "top"}),
        ], style={"marginBottom": "12px"}),

        # Графики: bar, радар и временной ряд
        # Графики ниже дропдаунов
        html.Div([
            html.Div([
                dcc.Graph(id="bar-chart", config={"displayModeBar": False}),
            ], style={"width": "49%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}),
            html.Div([
                dcc.Graph(id="analysis-mode-chart", config={"displayModeBar": False}),
                # html.Pre(id="analysis-debug", style={"fontSize": "12px", "color": "#444"}),  # Debug panel hidden
            ], style={"width": "49%", "display": "inline-block", "verticalAlign": "top"}),
        ], style={"marginBottom": "12px"}),

        # Рекомендации и таблица
        html.Div([
            html.Div([
                html.Label("Режим рекомендаций"),
                dcc.RadioItems(
                    id="recommendation-mode",
                    options=[
                        {"label": "Простой", "value": "simple"},
                        {"label": "Пять элементов", "value": "five_elements"},
                    ],
                    value="simple",
                    labelStyle={"display": "block"},
                ),
            ], style={"width": "24%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}),
            html.Div([
                dcc.Graph(id="metrics-figure", config={"displayModeBar": False}),
                html.H4("Сводная таблица вычисленных показателей"),
                html.Div(id="metrics-table"),
                html.Button("Экспорт CSV (метрики)", id="export-csv", n_clicks=0, style={"marginTop": "12px", "marginRight": "6px"}),
                html.Button("Экспорт Excel (метрики)", id="export-xlsx", n_clicks=0, style={"marginTop": "12px", "marginRight": "6px"}),
                html.Button("Экспорт PDF (метрики)", id="export-pdf", n_clicks=0, style={"marginTop": "12px", "marginRight": "12px"}),
                html.Button("Сохранить фильтры", id="save-preferences", n_clicks=0, style={"marginTop": "12px"}),
                dcc.Download(id="download-metrics"),
                dcc.Download(id="download-metrics-xlsx"),
                dcc.Download(id="download-metrics-pdf"),
            ], style={"width": "75%", "display": "inline-block", "verticalAlign": "top"}),
        ], style={"marginBottom": "12px"}),

        # Cytoscape сеть меридианов
        html.Div([
            html.H4("Сеть меридианов и точек"),
            cyto.Cytoscape(
                id="meridian-network",
                layout={"name": "cose"},
                style={"width": "100%", "height": "480px", "border": "1px solid #ddd"},
                elements=[],
                stylesheet=[
                    {"selector": "node", "style": {"content": "data(label)"}},
                    {"selector": ".high", "style": {"background-color": "#d62728"}},
                    {"selector": ".low", "style": {"background-color": "#1f77b4"}},
                    {"selector": ".safe", "style": {"background-color": "#2ca02c"}},
                ],
            ),
        ]),

        # Хранилище данных и предпочтений
        dcc.Store(id="store-data"),
        dcc.Store(id="store-metadata"),
        dcc.Store(id="store-preferences", storage_type="local"),
    ], style={"padding": "16px"})