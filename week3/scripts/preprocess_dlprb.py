from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.project_paths import CLEAN_DATA, NORMALIZED_DATA, RAW_DATA, require_file


def main() -> None:
    raw = require_file(RAW_DATA)
    output_dir = CLEAN_DATA.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "preprocessing_summary.txt"

    df = pd.read_csv(raw)
    df = df.rename(columns={df.columns[0]: "time_index"})
    time_index = df["time_index"].copy()
    kpi = df.drop(columns=["time_index"]).apply(pd.to_numeric, errors="coerce")

    missing_before = int(kpi.isna().sum().sum())
    if missing_before:
        kpi = kpi.interpolate(method="linear", axis=0).ffill().bfill()

    combined = pd.concat([time_index, kpi], axis=1)
    duplicate_rows = int(combined.duplicated().sum())
    if duplicate_rows:
        combined = combined.drop_duplicates().reset_index(drop=True)
        time_index = combined["time_index"]
        kpi = combined.drop(columns=["time_index"])

    values = kpi.to_numpy(dtype=float)
    total_values = values.size
    zero_count = int((values == 0).sum())
    threshold = float(np.percentile(values, 99.99))
    extreme_count = int((values > threshold).sum())
    cleaned = kpi.clip(lower=0, upper=threshold)

    column_min = cleaned.min(axis=0)
    column_range = (cleaned.max(axis=0) - column_min).replace(0, 1)
    normalized = (cleaned - column_min) / column_range

    pd.concat([time_index.reset_index(drop=True), cleaned.reset_index(drop=True)], axis=1).to_csv(CLEAN_DATA, index=False)
    pd.concat([time_index.reset_index(drop=True), normalized.reset_index(drop=True)], axis=1).to_csv(NORMALIZED_DATA, index=False)

    summary = f"""5G DLPRB Dataset Preprocessing Summary
======================================

Input file: {raw}
Rows: {len(kpi)}
KPI columns: {kpi.shape[1]}
Total KPI values: {total_values}
Missing values before: {missing_before}
Missing values after: {int(kpi.isna().sum().sum())}
Duplicate rows: {duplicate_rows}
Zero values: {zero_count}
Zero percentage: {zero_count / total_values * 100:.4f}%
Original minimum: {values.min():.10f}
Original maximum: {values.max():.10f}
Original mean: {values.mean():.10f}
Clipping percentile: 99.99%
Upper threshold: {threshold:.10f}
Number of clipped values: {extreme_count}
Normalization: per-column Min-Max [0, 1]
"""
    report_file.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Saved: {CLEAN_DATA}")
    print(f"Saved: {NORMALIZED_DATA}")


if __name__ == "__main__":
    main()

