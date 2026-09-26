from pathlib import Path
import sys

import pandas as pd


WEEK7 = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEEK7.parent
sys.path.insert(0, str(WEEK7))

from core.data_repository import (  # noqa: E402
    ProjectFiles,
    data_health,
    list_kpis,
    load_anomaly_bundle,
    load_model_metrics,
    load_predictions,
)


FILES = ProjectFiles(PROJECT_ROOT)


def test_required_project_data_is_ready():
    health = data_health(FILES)
    assert health["ready"], health["files"]


def test_metrics_cover_traditional_and_deep_models():
    metrics = load_model_metrics(FILES)
    assert len(metrics) == 8
    assert {"LightGBM", "Transformer", "LSTM"}.issubset(set(metrics["Model"]))
    assert metrics[["MAE", "RMSE", "R2"]].notna().all().all()


def test_prediction_groups_have_actual_values_and_models():
    for group in ("传统机器学习（单 Beam）", "Boosting（全网平均 KPI）", "RNN（全网平均 KPI）", "Transformer（全网平均 KPI）"):
        data = load_predictions(FILES, group)
        assert {"time_index", "实际值"}.issubset(data.columns)
        assert data.shape[1] >= 3
        assert len(data) > 100


def test_anomaly_outputs_are_consistent():
    results, summary, ranking, causes = load_anomaly_bundle(FILES)
    assert len(results) == 840
    assert int(results["ml_union_anomaly"].sum()) == 40
    assert int(summary.loc[summary.Method == "ML Union", "Anomaly_Count"].iloc[0]) == 40
    assert ranking["combined_anomaly_score"].is_monotonic_decreasing
    assert causes["rank"].is_monotonic_increasing


def test_kpi_catalog_matches_dataset_shape():
    kpis = list_kpis(FILES)
    assert len(kpis) == 2880
    assert "1_1_22" in kpis

