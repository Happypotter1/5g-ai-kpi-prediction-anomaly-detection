from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.project_paths import NORMALIZED_DATA, require_file


def metrics(name, y, pred):
    return {"Model": name, "MAE": mean_absolute_error(y, pred), "RMSE": np.sqrt(mean_squared_error(y, pred)), "R2": r2_score(y, pred)}


def main() -> None:
    df = pd.read_csv(require_file(NORMALIZED_DATA))
    kpi = df.drop(columns=["time_index"])
    X = kpi.iloc[:-1].reset_index(drop=True)
    y = kpi.iloc[1:].mean(axis=1).reset_index(drop=True)
    times = df["time_index"].iloc[1:].reset_index(drop=True)
    split = int(len(X) * 0.8)
    X_train, X_test, y_train, y_test = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]

    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTree": DecisionTreeRegressor(max_depth=8, min_samples_leaf=5, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1),
        "LightGBM": LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1, verbosity=-1),
    }
    result_dir, fig_dir, model_dir = ROOT / "week4/results", ROOT / "week4/figures", ROOT / "week4/models"
    for d in (result_dir, fig_dir, model_dir): d.mkdir(parents=True, exist_ok=True)
    rows, preds = [], pd.DataFrame({"time_index": times.iloc[split:].values, "Actual": y_test.values})
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rows.append(metrics(name, y_test, pred)); preds[name] = pred
        joblib.dump(model, model_dir / f"{name}.joblib")
    table = pd.DataFrame(rows).sort_values("R2", ascending=False).reset_index(drop=True)
    table.to_csv(result_dir / "all_models_metrics.csv", index=False); preds.to_csv(result_dir / "all_models_predictions.csv", index=False)
    for metric_name, filename in [("MAE", "06_all_models_mae.png"), ("RMSE", "07_all_models_rmse.png"), ("R2", "08_all_models_r2.png")]:
        plt.figure(figsize=(10, 6)); plt.bar(table["Model"], table[metric_name]); plt.ylabel(metric_name); plt.title(f"{metric_name} Comparison of KPI Prediction Models"); plt.xticks(rotation=25, ha="right"); plt.tight_layout(); plt.savefig(fig_dir / filename, dpi=200); plt.close()
    best = table.iloc[0]["Model"]
    plt.figure(figsize=(12, 6)); plt.plot(preds["Actual"].values, label="Actual", linewidth=2); plt.plot(preds[best].values, label=f"{best} Prediction"); plt.legend(); plt.xlabel("Test Sample"); plt.ylabel("Normalized KPI"); plt.title(f"{best}: Actual vs Predicted KPI"); plt.tight_layout(); plt.savefig(fig_dir / "09_best_actual_vs_predicted.png", dpi=200); plt.close()
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()

