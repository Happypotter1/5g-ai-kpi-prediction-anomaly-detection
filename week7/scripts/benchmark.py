from __future__ import annotations

import json
import sys
import time
import tracemalloc
from pathlib import Path


WEEK7 = Path(__file__).resolve().parents[1]
ROOT = WEEK7.parent
sys.path.insert(0, str(WEEK7))

from core.data_repository import (  # noqa: E402
    ProjectFiles,
    list_kpis,
    load_anomaly_bundle,
    load_model_metrics,
    read_kpi_series,
)


def measure(name, operation):
    tracemalloc.start()
    start = time.perf_counter()
    value = operation()
    duration = (time.perf_counter() - start) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"operation": name, "elapsed_ms": round(duration, 2), "peak_memory_mb": round(peak / 1024 / 1024, 2)}, value


def main() -> None:
    files = ProjectFiles(ROOT)
    records = []
    record, _ = measure("加载模型指标", lambda: load_model_metrics(files))
    records.append(record)
    record, _ = measure("加载异常检测全套结果", lambda: load_anomaly_bundle(files))
    records.append(record)
    record, kpis = measure("读取 2880 个 KPI 名称", lambda: list_kpis(files))
    records.append(record)
    record, _ = measure("按需读取单个 KPI 时序", lambda: read_kpi_series(files, kpis[0]))
    records.append(record)
    output = WEEK7 / "results" / "performance_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"generated_by": "week7 benchmark", "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

