from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.project_paths import NORMALIZED_DATA, require_file


def save_plot(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def main() -> None:
    df = pd.read_csv(require_file(NORMALIZED_DATA))
    time_index = df["time_index"].to_numpy()
    kpi = df.drop(columns=["time_index"])
    out = ROOT / "week3" / "analysis"
    out.mkdir(parents=True, exist_ok=True)

    stats = pd.DataFrame({
        "mean": kpi.mean(), "std": kpi.std(), "min": kpi.min(),
        "max": kpi.max(), "median": kpi.median(), "zero_ratio": (kpi == 0).mean(),
    })
    stats.to_csv(out / "beam_statistics.csv")
    stats.sort_values("mean", ascending=False).head(20).to_csv(out / "top20_beams.csv")

    values = kpi.to_numpy().ravel()
    plt.figure(figsize=(10, 6)); plt.hist(values, bins=80); plt.xlabel("Normalized DLPRB"); plt.ylabel("Frequency"); plt.title("Overall DLPRB Distribution"); save_plot(out / "01_overall_distribution.png")
    mean_series = kpi.mean(axis=1); plt.figure(figsize=(12, 6)); plt.plot(time_index, mean_series); plt.xlabel("Time Index"); plt.ylabel("Mean Normalized DLPRB"); plt.title("Mean DLPRB Over Time"); save_plot(out / "02_mean_over_time.png")
    active_ratio = (kpi > 0).mean(axis=1); plt.figure(figsize=(12, 6)); plt.plot(time_index, active_ratio); plt.xlabel("Time Index"); plt.ylabel("Active Beam Ratio"); plt.title("Active Beam Ratio Over Time"); save_plot(out / "03_active_ratio_over_time.png")
    plt.figure(figsize=(12, 7))
    for col in kpi.columns[:5]: plt.plot(time_index, kpi[col], label=col)
    plt.xlabel("Time Index"); plt.ylabel("Normalized DLPRB"); plt.title("Selected Beam DLPRB Time Series"); plt.legend(); save_plot(out / "04_selected_beams.png")
    plt.figure(figsize=(12, 6)); plt.plot(time_index, kpi.max(axis=1)); plt.xlabel("Time Index"); plt.ylabel("Maximum Normalized DLPRB"); plt.title("Maximum DLPRB Over Time"); save_plot(out / "05_max_over_time.png")

    summary = f"""DLPRB Dataset Analysis Summary
==============================
Rows: {df.shape[0]}
Beam features: {kpi.shape[1]}
Overall mean: {values.mean():.6f}
Overall minimum: {values.min():.6f}
Overall maximum: {values.max():.6f}
Overall zero ratio: {(values == 0).mean():.6f}
Mean active beam ratio: {active_ratio.mean():.6f}
"""
    (out / "analysis_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()

