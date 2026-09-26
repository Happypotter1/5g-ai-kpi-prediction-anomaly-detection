from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ProjectFiles:
    root: Path

    @property
    def normalized_data(self) -> Path:
        return self.root / "week3" / "datasets" / "processed" / "DLPRB_normalized.csv"

    @property
    def model_metrics(self) -> Path:
        return self.root / "week5" / "results" / "all_models_metrics_with_scope.csv"

    @property
    def anomaly_results(self) -> Path:
        return self.root / "week6" / "results" / "ml_anomaly_results.csv"

    @property
    def anomaly_summary(self) -> Path:
        return self.root / "week6" / "results" / "week6_detection_summary.csv"

    @property
    def anomaly_ranking(self) -> Path:
        return self.root / "week6" / "results" / "anomaly_time_ranking.csv"

    @property
    def root_causes(self) -> Path:
        return self.root / "week6" / "results" / "root_cause_kpi_ranking.csv"

    @property
    def statistical_results(self) -> Path:
        return self.root / "week6" / "results" / "statistical_anomaly_results.csv"


PREDICTION_FILES = {
    "传统机器学习（单 Beam）": ("week4/results/original/baseline_predictions.csv", "actual"),
    "Boosting（全网平均 KPI）": ("week4/results/original/boosting_predictions.csv", "Actual"),
    "RNN（全网平均 KPI）": ("week5/results/rnn_predictions.csv", "Actual"),
    "Transformer（全网平均 KPI）": ("week5/results/transformer_predictions.csv", "Actual"),
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"缺少项目文件：{path}")
    return path


def load_model_metrics(files: ProjectFiles) -> pd.DataFrame:
    data = pd.read_csv(require_file(files.model_metrics))
    expected = {"Model", "MAE", "RMSE", "R2", "Task"}
    if not expected.issubset(data.columns):
        raise ValueError(f"模型指标字段不完整：{expected - set(data.columns)}")
    task_labels = {
        "mean_KPI_week5": "全网平均 KPI · Week 5",
        "mean_KPI_week4": "全网平均 KPI · Week 4",
        "beam_11_0_19_week4": "单 Beam 11_0_19 · Week 4",
    }
    data["任务范围"] = data["Task"].map(task_labels).fillna(data["Task"])
    return data.sort_values(["任务范围", "RMSE"], ignore_index=True)


def list_prediction_groups() -> list[str]:
    return list(PREDICTION_FILES)


def load_predictions(files: ProjectFiles, group: str) -> pd.DataFrame:
    if group not in PREDICTION_FILES:
        raise KeyError(f"未知预测结果组：{group}")
    relative, actual_column = PREDICTION_FILES[group]
    data = pd.read_csv(require_file(files.root / relative)).rename(columns={actual_column: "实际值"})
    if "time_index" not in data.columns:
        data.insert(0, "time_index", range(len(data)))
    return data


def load_anomaly_bundle(files: ProjectFiles) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    results = pd.read_csv(require_file(files.anomaly_results))
    summary = pd.read_csv(require_file(files.anomaly_summary))
    ranking = pd.read_csv(require_file(files.anomaly_ranking))
    root_causes = pd.read_csv(require_file(files.root_causes))
    return results, summary, ranking, root_causes


def load_network_characteristics(files: ProjectFiles) -> pd.DataFrame:
    return pd.read_csv(require_file(files.statistical_results))


def read_kpi_series(files: ProjectFiles, kpi: str) -> pd.DataFrame:
    header = pd.read_csv(require_file(files.normalized_data), nrows=0)
    if kpi not in header.columns or kpi == "time_index":
        raise KeyError(f"未知 KPI：{kpi}")
    return pd.read_csv(files.normalized_data, usecols=["time_index", kpi])


def list_kpis(files: ProjectFiles) -> list[str]:
    columns = pd.read_csv(require_file(files.normalized_data), nrows=0).columns.tolist()
    return [column for column in columns if column != "time_index"]


def data_health(files: ProjectFiles) -> dict[str, object]:
    required = {
        "归一化数据": files.normalized_data,
        "模型指标": files.model_metrics,
        "异常结果": files.anomaly_results,
        "异常摘要": files.anomaly_summary,
        "异常时刻排名": files.anomaly_ranking,
        "网络统计特征": files.statistical_results,
        "根因排名": files.root_causes,
    }
    required.update({f"预测结果 {name}": files.root / path for name, (path, _) in PREDICTION_FILES.items()})
    return {
        "ready": all(path.is_file() for path in required.values()),
        "files": {name: path.is_file() for name, path in required.items()},
    }
