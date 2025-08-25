# -*- coding: utf-8 -*-
# Минимальный тест расчетов

import pandas as pd

from app.computations import compute_all_metrics_for_row


def test_compute_all_metrics_for_row_basic():
    row = pd.Series({
        "H1L": 160, "H2L": 150, "H3L": 160, "H4L": 130, "H5L": 150, "H6L": 160,
        "H1R": 150, "H2R": 140, "H3R": 140, "H4R": 125, "H5R": 145, "H6R": 150,
        "F1L": 150, "F2L": 160, "F3L": 160, "F4L": 135, "F5L": 145, "F6L": 150,
        "F1R": 125, "F2R": 155, "F3R": 160, "F4R": 135, "F5R": 150, "F6R": 160,
    })
    metrics = compute_all_metrics_for_row(row)
    assert set([
        "Yin_L","Yin_R","Yang_L","Yang_R","Hands_L","Hands_R","Feet_L","Feet_R",
        "Inner_L","Inner_R","Outer_L","Outer_R","MeanAll","CorridorLower","CorridorUpper",
        "MaxCode","MaxValue","MaxMeridian","MaxAction","MinCode","MinValue","MinMeridian","MinAction"
    ]).issubset(metrics.keys())