from pathlib import Path
import copy
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "week5/results/week5_sequences.npz"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class AblationTransformer(nn.Module):
    def __init__(self, input_dim, nhead=4, positional=True, ffn=128):
        super().__init__(); self.positional = positional; self.proj = nn.Linear(input_dim, 64); self.pos = nn.Parameter(torch.zeros(1, 32, 64))
        layer = nn.TransformerEncoderLayer(64, nhead, ffn, dropout=.1, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, 2); self.head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(self, x):
        x = self.proj(x)
        if self.positional: x = x + self.pos[:, :x.size(1)]
        return self.head(self.encoder(x).mean(1)).squeeze(-1)


def run(name, cfg, d):
    # Reset all random generators so each architecture starts reproducibly.
    random.seed(42); np.random.seed(42); torch.manual_seed(42)
    model = AblationTransformer(d["X_train"].shape[2], **cfg).to(DEVICE); opt = torch.optim.Adam(model.parameters(), lr=.001); loss_fn = nn.MSELoss()
    tr = DataLoader(TensorDataset(torch.tensor(d["X_train"]), torch.tensor(d["y_train"])), 32, shuffle=True)
    va = DataLoader(TensorDataset(torch.tensor(d["X_val"]), torch.tensor(d["y_val"])), 32)
    best, state, wait = float("inf"), None, 0
    for _ in range(80):
        model.train()
        for xb, yb in tr: xb, yb = xb.to(DEVICE), yb.to(DEVICE); opt.zero_grad(); loss = loss_fn(model(xb), yb); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad(): score = np.mean([loss_fn(model(x.to(DEVICE)), y.to(DEVICE)).item() for x, y in va])
        if score < best: best, state, wait = score, copy.deepcopy(model.state_dict()), 0
        else:
            wait += 1
            if wait >= 12: break
    model.load_state_dict(state); model.eval()
    with torch.no_grad(): pred = model(torch.tensor(d["X_test"]).to(DEVICE)).cpu().numpy()
    y = d["y_test"]
    return {"Model": name, "MAE": mean_absolute_error(y, pred), "RMSE": np.sqrt(mean_squared_error(y, pred)), "R2": r2_score(y, pred)}


def main():
    if not DATA.exists(): raise FileNotFoundError("请先运行 train_deep_models.py 生成 week5_sequences.npz")
    d = np.load(DATA); configs = [("Full Transformer", {}), ("No Positional Encoding", {"positional": False}), ("Single Head Attention", {"nhead": 1}), ("Reduced FFN", {"ffn": 64})]
    table = pd.DataFrame([run(name, cfg, d) for name, cfg in configs]).sort_values("MAE")
    table.to_csv(ROOT / "week5/results/transformer_ablation_metrics.csv", index=False); print(table.to_string(index=False))


if __name__ == "__main__": main()
