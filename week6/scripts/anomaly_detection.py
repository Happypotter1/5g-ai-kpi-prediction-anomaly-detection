"""Recompute Week 6 statistics, unsupervised anomalies and KPI candidates.

Inputs are normalized Week 3 Beam values. Labels are anomaly candidates, and
the contribution score measures association across the anomaly set, not cause.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.project_paths import NORMALIZED_DATA, require_file  # noqa: E402


def minmax(values):
    """Scale one statistic across all KPI columns to [0, 1]."""
    values = np.asarray(values, dtype=float)
    low, high = np.nanmin(values), np.nanmax(values)
    return np.zeros_like(values) if high - low < 1e-12 else (values - low) / (high - low)


def statistical_detection(time, kpi):
    """Apply 3σ and IQR to the mean of all Beam columns at each time."""
    network_mean = kpi.mean(axis=1)
    mean, std = network_mean.mean(), network_mean.std(ddof=1)
    q1, q3 = network_mean.quantile([0.25, 0.75])
    sigma_bounds = (mean - 3 * std, mean + 3 * std)
    iqr_bounds = (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
    sigma = (~network_mean.between(*sigma_bounds)).astype(int)
    iqr = (~network_mean.between(*iqr_bounds)).astype(int)
    frame = pd.DataFrame({
        "time_index": time, "mean_kpi": network_mean,
        "max_kpi": kpi.max(axis=1), "std_kpi": kpi.std(axis=1),
        "active_ratio": (kpi > 0).mean(axis=1),
        "sigma_anomaly": sigma, "iqr_anomaly": iqr,
        "statistical_anomaly": sigma | iqr,
    })
    return frame, sigma_bounds, iqr_bounds


def machine_learning_detection(time, kpi, stat):
    """Project the full KPI state and apply two unsupervised detectors."""
    scaled = StandardScaler().fit_transform(kpi.to_numpy())
    features = PCA(n_components=min(20, *scaled.shape), random_state=42).fit_transform(scaled)
    forest = IsolationForest(n_estimators=300, contamination=.03, random_state=42, n_jobs=-1)
    svm = OneClassSVM(kernel="rbf", gamma="scale", nu=.03)
    iso = (forest.fit_predict(features) == -1).astype(int)
    ocsvm = (svm.fit_predict(features) == -1).astype(int)
    return pd.DataFrame({
        "time_index": time,
        "sigma_anomaly": stat.sigma_anomaly,
        "iqr_anomaly": stat.iqr_anomaly,
        "isolation_forest_anomaly": iso,
        "isolation_forest_score": -forest.score_samples(features),
        "ocsvm_anomaly": ocsvm,
        "ocsvm_score": -svm.decision_function(features),
        "ml_common_anomaly": iso & ocsvm,
        "ml_union_anomaly": iso | ocsvm,
    })


def rank_candidates(time, kpi, ml):
    """Rank KPIs for all union anomalies, then rank anomalous times."""
    label = ml.ml_union_anomaly.to_numpy(dtype=int)
    values = kpi.to_numpy(dtype=float)
    normal, abnormal = values[label == 0], values[label == 1]
    normal_mean, anomaly_mean = normal.mean(axis=0), abnormal.mean(axis=0)
    normal_std, anomaly_std = normal.std(axis=0), abnormal.std(axis=0)
    mean_diff, std_diff = anomaly_mean - normal_mean, anomaly_std - normal_std
    corr = np.array([
        0.0 if kpi[name].std() == 0 else kpi[name].corr(pd.Series(label))
        for name in kpi.columns
    ])
    corr = np.nan_to_num(corr)
    score = .5 * minmax(abs(mean_diff)) + .2 * minmax(abs(std_diff)) + .3 * minmax(abs(corr))
    causes = pd.DataFrame({
        "kpi": kpi.columns,
        "normal_mean": normal_mean, "anomaly_mean": anomaly_mean,
        "mean_difference": mean_diff, "abs_mean_difference": abs(mean_diff),
        "normal_std": normal_std, "anomaly_std": anomaly_std,
        "std_difference": std_diff,
        "correlation_with_anomaly": corr, "abs_correlation": abs(corr),
        "contribution_score": score,
    }).sort_values("contribution_score", ascending=False, ignore_index=True)
    causes["rank"] = np.arange(1, len(causes) + 1)

    time_score = .5 * minmax(ml.isolation_forest_score) + .5 * minmax(ml.ocsvm_score)
    times = pd.DataFrame({
        "time_index": time,
        "isolation_forest_score": ml.isolation_forest_score,
        "ocsvm_score": ml.ocsvm_score,
        "combined_anomaly_score": time_score,
        "isolation_forest_anomaly": ml.isolation_forest_anomaly,
        "ocsvm_anomaly": ml.ocsvm_anomaly,
        "common_anomaly": ml.ml_common_anomaly,
        "union_anomaly": ml.ml_union_anomaly,
    }).sort_values("combined_anomaly_score", ascending=False, ignore_index=True)
    return causes, times


def main():
    data = pd.read_csv(require_file(NORMALIZED_DATA))
    time, kpi = data.time_index, data.drop(columns="time_index")
    results, figures = ROOT / "week6/results", ROOT / "week6/figures"
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    stat, sigma_bounds, iqr_bounds = statistical_detection(time, kpi)
    ml = machine_learning_detection(time, kpi, stat)
    causes, times = rank_candidates(time, kpi, ml)
    counts = [int(stat.sigma_anomaly.sum()), int(stat.iqr_anomaly.sum()),
              int(ml.isolation_forest_anomaly.sum()), int(ml.ocsvm_anomaly.sum()),
              int(ml.ml_common_anomaly.sum()), int(ml.ml_union_anomaly.sum())]
    summary = pd.DataFrame({
        "Method": ["3-Sigma", "IQR", "Isolation Forest", "One-Class SVM", "ML Common", "ML Union"],
        "Anomaly_Count": counts, "Anomaly_Ratio": np.array(counts) / len(data),
    })
    for name, frame in {
        "statistical_anomaly_results.csv": stat,
        "ml_anomaly_results.csv": ml,
        "root_cause_kpi_ranking.csv": causes,
        "anomaly_time_ranking.csv": times,
        "week6_detection_summary.csv": summary,
    }.items():
        frame.to_csv(results / name, index=False)

    # Three presentation figures; older exploratory images remain archived separately.
    plt.figure(figsize=(10, 5))
    plt.plot(time, stat.mean_kpi, label="Network mean")
    plt.axhline(sigma_bounds[1], color="orange", linestyle="--", label="3σ upper")
    plt.axhline(iqr_bounds[1], color="red", linestyle=":", label="IQR upper")
    plt.legend(); plt.tight_layout(); plt.savefig(figures / "01_statistical_thresholds.png", dpi=180); plt.close()
    plt.figure(figsize=(10, 5))
    plt.bar(summary.Method, summary.Anomaly_Count)
    plt.xticks(rotation=25); plt.tight_layout(); plt.savefig(figures / "15_week6_detection_summary.png", dpi=180); plt.close()
    plt.figure(figsize=(10, 6))
    top = causes.head(10).iloc[::-1]
    plt.barh(top.kpi, top.contribution_score)
    plt.tight_layout(); plt.savefig(figures / "17_week6_top10_root_causes.png", dpi=180); plt.close()
    print(summary.to_string(index=False))
    print(f"3σ bounds: {sigma_bounds}; IQR bounds: {iqr_bounds}")


if __name__ == "__main__":
    main()
