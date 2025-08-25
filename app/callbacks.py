from __future__ import annotations

# -*- coding: utf-8 -*-
# Callback-и Dash приложения

from pathlib import Path
from typing import Dict, List, Tuple

import io
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, html, dcc, ctx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .data_loader import list_csv_files, load_many
from .metadata import make_default_metadata
from .computations import build_bar_dataframe, compute_all_metrics_for_row, compute_corridor
from .utils import CHANNEL_ORDER, CHANNELS_READABLE, POINT_CODES_24, COLOR_HIGH, COLOR_LOW, COLOR_SAFE


def register_callbacks(app: Dash, data_dir: Path, points_dir: Path) -> None:
    # Debug callback для вывода данных analysis-mode-chart
    @app.callback(
        Output("analysis-debug", "children"),
        Input("apply-filters", "n_clicks"),
        State("file-dropdown", "value"),
        State("date-dropdown", "value"),
        State("analysis-mode-point", "value"),
        State("analysis-mode-metric", "value"),
        State("recommendation-mode", "value"),
        State("store-data", "data"),
        prevent_initial_call=True,
    )
    def debug_analysis_chart(n_clicks, selected_file, selected_date, analysis_mode_point, analysis_mode_metric, recommendation_mode, data_json):
        import json
        debug = {}
        try:
            if not data_json:
                debug["error"] = "data_json is None"
                return json.dumps(debug, ensure_ascii=False, indent=2)
            if not selected_file:
                debug["error"] = "selected_file is None"
                return json.dumps(debug, ensure_ascii=False, indent=2)
            df = pd.read_json(io.StringIO(data_json), orient="split")
            debug["df_shape"] = str(df.shape)
            debug["df_columns"] = list(df.columns)
            debug["df_head"] = df.head(5).astype(str).to_dict()
            debug["selected_file"] = selected_file
            debug["selected_date"] = selected_date
            debug["analysis_mode_point"] = analysis_mode_point
            debug["analysis_mode_metric"] = analysis_mode_metric
            from .utils import POINT_CODES_24
            df_sorted = df.sort_values("Date")
            if analysis_mode_point and analysis_mode_point in POINT_CODES_24 and analysis_mode_point in df_sorted.columns:
                y_vals = pd.to_numeric(df_sorted[analysis_mode_point], errors="coerce")
                x_vals = df_sorted["Date"].astype(str)
                mask = ~pd.isna(y_vals)
                debug["dates"] = list(x_vals[mask])
                debug["values"] = list(y_vals[mask])
            elif analysis_mode_metric:
                y_vals = []
                for _, r in df_sorted.iterrows():
                    from .computations import compute_all_metrics_for_row
                    m = compute_all_metrics_for_row(r, recommendation_mode=recommendation_mode)
                    y_vals.append(m.get(analysis_mode_metric))
                x_vals = df_sorted["Date"].astype(str)
                debug["dates"] = list(x_vals)
                debug["values"] = y_vals
            return json.dumps(debug, ensure_ascii=False, indent=2)
        except Exception as e:
            import traceback
            debug["exception"] = str(e)
            debug["traceback"] = traceback.format_exc()
            return json.dumps(debug, ensure_ascii=False, indent=2)
    # Дропдаун для точек
    @app.callback(
        Output("analysis-mode-point", "options"),
        Input("project-title", "children"),
        prevent_initial_call=False,
    )
    def init_analysis_mode_point_options(_title: str):
        from .utils import POINT_CODES_24
        return [{"label": code, "value": code} for code in POINT_CODES_24]

    # Дропдаун для метрик
    @app.callback(
        Output("analysis-mode-metric", "options"),
        Input("project-title", "children"),
        prevent_initial_call=False,
    )
    def init_analysis_mode_metric_options(_title: str):
        metrics = [
            {"label": "Yin_L", "value": "Yin_L"},
            {"label": "Yin_R", "value": "Yin_R"},
            {"label": "Yang_L", "value": "Yang_L"},
            {"label": "Yang_R", "value": "Yang_R"},
            {"label": "Hands_L", "value": "Hands_L"},
            {"label": "Hands_R", "value": "Hands_R"},
            {"label": "Feet_L", "value": "Feet_L"},
            {"label": "Feet_R", "value": "Feet_R"},
            {"label": "Inner_L", "value": "Inner_L"},
            {"label": "Inner_R", "value": "Inner_R"},
            {"label": "Outer_L", "value": "Outer_L"},
            {"label": "Outer_R", "value": "Outer_R"},
            {"label": "MeanAll", "value": "MeanAll"},
        ]
        return metrics
    """Регистрирует все callback-и приложения."""

    @app.callback(
        Output("file-dropdown", "options"),
        Output("store-metadata", "data"),
        Input("project-title", "children"),
        prevent_initial_call=False,
    )
    def init_files_and_meta(_title: str):
        files = list_csv_files(data_dir)
        options = [{"label": f.name, "value": str(f)} for f in files]
        meta_dict = {m.code: m.__dict__ for m in make_default_metadata(points_dir).values()}
        return options, meta_dict


    @app.callback(
        Output("date-dropdown", "options"),
        Output("store-data", "data"),
        Input("file-dropdown", "value"),
        prevent_initial_call=True,
    )
    def load_data(selected_file: str | None):
        if not selected_file:
            return [], {}
        paths = [Path(selected_file)]
        df = load_many(paths)
        if df.empty:
            return [], {}
        dates = sorted(df["Date"].dropna().unique(), reverse=True)
        date_options = [{"label": pd.Timestamp(d).strftime("%d-%m-%Y"), "value": str(pd.Timestamp(d).date())} for d in dates]
        return date_options, df.to_json(date_format="iso", orient="split")

    # Восстановление предпочтений: значения переключателей и точек
    # Восстановление режима рекомендаций и выбранных точек

    # Восстановление выбора файлов после загрузки опций
    @app.callback(
        Output("file-dropdown", "value"),
        Input("file-dropdown", "options"),
        State("store-preferences", "data"),
        prevent_initial_call=False,
    )
    def restore_files(options: List[Dict] | None, pref: Dict | None):
        if not options or not pref:
            return None
        opt_values = {o["value"] for o in options}
        saved = pref.get("file") if isinstance(pref.get("file"), str) else None
        return saved if saved in opt_values else None

    # Восстановление выбора дат после загрузки опций дат
    @app.callback(
        Output("date-dropdown", "value"),
        Input("date-dropdown", "options"),
        State("store-preferences", "data"),
        prevent_initial_call=False,
    )
    def restore_dates(options: List[Dict] | None, pref: Dict | None):
        if not options or not pref:
            return None
        opt_values = {o["value"] for o in options}
        saved = pref.get("date") if isinstance(pref.get("date"), str) else None
        return saved if saved in opt_values else None

    # Сохранение предпочтений по кнопке (чтобы избежать циклов зависимостей)

    # Новый callback: обновление графиков только по кнопке "Применить"
    @app.callback(
        Output("bar-chart", "figure"),
        Output("metrics-table", "children"),
        Output("metrics-figure", "figure"),
        Output("analysis-mode-chart", "figure"),
        Output("meridian-network", "elements"),
        Input("apply-filters", "n_clicks"),
        State("file-dropdown", "value"),
        State("date-dropdown", "value"),
        State("analysis-mode-point", "value"),
        State("analysis-mode-metric", "value"),
        State("recommendation-mode", "value"),
        State("store-data", "data"),
        State("store-metadata", "data"),
        prevent_initial_call=True,
    )
    def update_outputs_apply(n_clicks,
                            selected_file,
                            selected_date,
                            analysis_mode_point,
                            analysis_mode_metric,
                            recommendation_mode,
                            data_json,
                            metadata):
        empty_fig = go.Figure()
        if not data_json or not selected_file or not selected_date:
            return empty_fig, html.Div("Нет данных"), empty_fig, empty_fig, []
        df = pd.read_json(io.StringIO(data_json), orient="split")
        want_date = pd.to_datetime(selected_date).date()
        df_date = df[df["Date"].dt.date.eq(want_date)]
        if df_date.empty:
            return empty_fig, html.Div("Нет данных"), empty_fig, empty_fig, []
        row = df_date.sort_values("Date", ascending=False).iloc[0]
        bar_df = build_bar_dataframe(row)
        corridor = compute_corridor(row)
        def title_for(code: str) -> str:
            if not metadata:
                return code
            m = metadata.get(code)
            return (m.get("title") if isinstance(m, dict) else None) or code
        bar_df["TitleL"] = bar_df["CodeL"].map(title_for)
        bar_df["TitleR"] = bar_df["CodeR"].map(title_for)
        # Bar Chart
        fig = go.Figure()
        fig.add_bar(x=bar_df["Channel"], y=bar_df["L"], name="Left",
                    customdata=bar_df[["CodeL", "TitleL"]],
                    hovertemplate=(
                        "Точка: %{customdata[1]}<br>Канал: %{x}<br>Сторона: Left\n"
                        "<br>Код: %{customdata[0]}<br>Значение: %{y:.1f}<extra></extra>"
                    ))
        fig.add_bar(x=bar_df["Channel"], y=bar_df["R"], name="Right",
                    customdata=bar_df[["CodeR", "TitleR"]],
                    hovertemplate=(
                        "Точка: %{customdata[1]}<br>Канал: %{x}<br>Сторона: Right\n"
                        "<br>Код: %{customdata[0]}<br>Значение: %{y:.1f}<extra></extra>"
                    ))
        fig.update_layout(barmode="group", xaxis_title="Каналы", yaxis_title="Значение")
        fig.update_yaxes(tickformat=".1f")
        if pd.notna(corridor.lower) and pd.notna(corridor.upper):
            fig.add_hline(y=corridor.lower, line=dict(color="#aaa", dash="dot"))
            fig.add_hline(y=corridor.upper, line=dict(color="#aaa", dash="dot"))
        # Сводная таблица
        metrics = compute_all_metrics_for_row(row, recommendation_mode=recommendation_mode)
        rounded_metrics: Dict[str, object] = {}
        for k, v in metrics.items():
            if isinstance(v, (int, float)) and pd.notna(v):
                rounded_metrics[k] = round(float(v), 1)
            else:
                rounded_metrics[k] = v
        rows = [{"metric": k, "value": rounded_metrics[k]} for k in rounded_metrics.keys()]
        table = dash_table.DataTable(
            columns=[{"name": "Показатель", "id": "metric"}, {"name": "Значение", "id": "value"}],
            data=rows,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "6px"},
        )
        # График вычисленных показателей
        metrics_fig = go.Figure()
        metrics_fig.add_bar(x=list(rounded_metrics.keys()), y=list(rounded_metrics.values()), name="Показатели")
        metrics_fig.update_layout(xaxis_title="Показатель", yaxis_title="Значение", barmode="group")
        metrics_fig.update_yaxes(tickformat=".1f")
        # График анализа по точкам/показателям
        analysis_fig = go.Figure()
        # Для графика точки или метрики по датам используем выбранный дропдаун
        df_all_sorted = df.sort_values("Date")
        from .utils import POINT_CODES_24
        # Если выбрана точка
        if analysis_mode_point and analysis_mode_point in POINT_CODES_24 and analysis_mode_point in df_all_sorted.columns:
            title = title_for(analysis_mode_point)
            y_vals = pd.to_numeric(df_all_sorted[analysis_mode_point], errors="coerce")
            x_vals = df_all_sorted["Date"]
            mask = ~pd.isna(y_vals)
            y_vals = y_vals[mask]
            x_vals = x_vals[mask]
            if len(y_vals) > 0:
                analysis_fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode="lines+markers",
                    name=title,
                    hovertemplate=("Точка: {title}<br>Дата: %{{x|%d-%m-%Y}}<br>Значение: %{{y:.1f}}<extra></extra>".format(title=title)),
                ))
                analysis_fig.update_yaxes(tickformat=".1f")
                analysis_fig.update_layout(xaxis_title="Дата", yaxis_title="Значение")
        # Если выбрана метрика
        if analysis_mode_metric and analysis_mode_metric in metrics:
            y_vals = []
            for _, r in df_all_sorted.iterrows():
                m = compute_all_metrics_for_row(r, recommendation_mode=recommendation_mode)
                y_vals.append(m.get(analysis_mode_metric))
            analysis_fig.add_trace(go.Scatter(
                x=df_all_sorted["Date"], y=y_vals, mode="lines+markers",
                name=analysis_mode_metric,
                hovertemplate=("Показатель: {name}<br>Дата: %{{x|%d-%m-%Y}}<br>Значение: %{{y:.1f}}<extra></extra>".format(name=analysis_mode_metric)),
            ))
            analysis_fig.update_yaxes(tickformat=".1f")
            analysis_fig.update_layout(xaxis_title="Дата", yaxis_title="Значение")
            # Если выбрана некорректная опция — не строить график
        # Меридианная сеть
        elements = []
        for ch in CHANNEL_ORDER:
            l_val = row.get(f"{ch}L")
            r_val = row.get(f"{ch}R")
            vals = [v for v in [l_val, r_val] if pd.notna(v)]
            mean_val = float(pd.Series(vals).mean()) if vals else None
            classes = ""
            if mean_val is not None:
                if mean_val > corridor.upper:
                    classes = "high"
                elif mean_val < corridor.lower:
                    classes = "low"
                else:
                    classes = "safe"
            elements.append({"data": {"id": ch, "label": CHANNELS_READABLE[ch]}, "classes": classes})
        for i in range(len(CHANNEL_ORDER) - 1):
            elements.append({"data": {"source": CHANNEL_ORDER[i], "target": CHANNEL_ORDER[i + 1]}})
        return fig, table, metrics_fig, analysis_fig, elements

    # Экспорт CSV
    @app.callback(
        Output("download-metrics", "data"),
        Input("export-csv", "n_clicks"),
        State("date-dropdown", "value"),
        State("recommendation-mode", "value"),
        State("store-data", "data"),
        prevent_initial_call=True,
    )
    def export_metrics_csv(n_clicks: int, selected_date: str | None, recommendation_mode: str, data_json: str | None):
        if not n_clicks or not data_json:
            return None
        df = pd.read_json(io.StringIO(data_json), orient="split")
        if selected_date:
            want_date = set([pd.to_datetime(selected_date).date()])
            df = df[df["Date"].dt.date.isin(want_date)]
        if df.empty:
            return None
        df = df.sort_values("Date")
        rows: List[Dict[str, object]] = []
        for _, r in df.iterrows():
            metrics = compute_all_metrics_for_row(r, recommendation_mode=recommendation_mode)
            out: Dict[str, object] = {"Date": r["Date"].strftime("%Y-%m-%d")}
            for k, v in metrics.items():
                out[k] = round(float(v), 1) if isinstance(v, (int, float)) and pd.notna(v) else v
            rows.append(out)
        export_df = pd.DataFrame(rows)
        return dcc.send_data_frame(export_df.to_csv, filename="metrics.csv", index=False)

    # Экспорт Excel
    @app.callback(
        Output("download-metrics-xlsx", "data"),
        Input("export-xlsx", "n_clicks"),
        State("date-dropdown", "value"),
        State("recommendation-mode", "value"),
        State("store-data", "data"),
        prevent_initial_call=True,
    )
    def export_metrics_xlsx(n_clicks: int, selected_date: str | None, recommendation_mode: str, data_json: str | None):
        if not n_clicks or not data_json:
            return None
        df = pd.read_json(io.StringIO(data_json), orient="split")
        if selected_date:
            want_date = set([pd.to_datetime(selected_date).date()])
            df = df[df["Date"].dt.date.isin(want_date)]
        if df.empty:
            return None
        df = df.sort_values("Date")
        rows: List[Dict[str, object]] = []
        for _, r in df.iterrows():
            metrics = compute_all_metrics_for_row(r, recommendation_mode=recommendation_mode)
            out: Dict[str, object] = {"Date": r["Date"].strftime("%Y-%m-%d")}
            for k, v in metrics.items():
                out[k] = round(float(v), 1) if isinstance(v, (int, float)) and pd.notna(v) else v
            rows.append(out)
        export_df = pd.DataFrame(rows)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name="Metrics", index=False)
        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), filename="metrics.xlsx")

    # Экспорт PDF (простой текстовый отчет)
    @app.callback(
        Output("download-metrics-pdf", "data"),
        Input("export-pdf", "n_clicks"),
        State("date-dropdown", "value"),
        State("recommendation-mode", "value"),
        State("store-data", "data"),
        prevent_initial_call=True,
    )
    def export_metrics_pdf(n_clicks: int, selected_date: str | None, recommendation_mode: str, data_json: str | None):
        if not n_clicks or not data_json:
            return None
        df = pd.read_json(io.StringIO(data_json), orient="split")
        if selected_date:
            want_date = set([pd.to_datetime(selected_date).date()])
            df = df[df["Date"].dt.date.isin(want_date)]
        if df.empty:
            return None
        df = df.sort_values("Date")
        # Подготовка строк
        rows: List[Dict[str, object]] = []
        for _, r in df.iterrows():
            metrics = compute_all_metrics_for_row(r, recommendation_mode=recommendation_mode)
            out: Dict[str, object] = {"Date": r["Date"].strftime("%Y-%m-%d")}
            for k, v in metrics.items():
                out[k] = round(float(v), 1) if isinstance(v, (int, float)) and pd.notna(v) else v
            rows.append(out)
        # Рендер PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Riodoraku Metrics Report")
        y -= 20
        c.setFont("Helvetica", 10)
        for row in rows:
            if y < 80:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, y, "Riodoraku Metrics Report (cont.)")
                y -= 20
                c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Дата: {row['Date']}")
            y -= 14
            for k, v in row.items():
                if k == "Date":
                    continue
                c.drawString(60, y, f"{k}: {v}")
                y -= 12
            y -= 8
        c.save()
        buf.seek(0)
        return dcc.send_bytes(buf.getvalue(), filename="metrics.pdf")