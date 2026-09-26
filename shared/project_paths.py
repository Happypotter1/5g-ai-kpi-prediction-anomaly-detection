from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = PROJECT_ROOT / "week3" / "datasets" / "raw" / "DLPRB_train_0w-5w.csv"
CLEAN_DATA = PROJECT_ROOT / "week3" / "datasets" / "processed" / "DLPRB_cleaned.csv"
NORMALIZED_DATA = PROJECT_ROOT / "week3" / "datasets" / "processed" / "DLPRB_normalized.csv"


def require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            f"缺少文件：{path}\n请先把原始数据放到 week3/datasets/raw，或运行前一阶段脚本。"
        )
    return path

