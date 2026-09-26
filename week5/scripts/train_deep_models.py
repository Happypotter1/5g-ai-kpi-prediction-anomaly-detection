from pathlib import Path
import copy
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.project_paths import NORMALIZED_DATA, require_file

SEED, SEQ_LEN, BATCH_SIZE, EPOCHS, PATIENCE = 42, 6, 32, 80, 12
torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def prepare():
    df = pd.read_csv(require_file(NORMALIZED_DATA))
    kpi = df.drop(columns=["time_index"]).to_numpy(dtype=np.float32)
    target = kpi.mean(axis=1).astype(np.float32)
    X = np.asarray([kpi[i-SEQ_LEN:i] for i in range(SEQ_LEN, len(kpi))], dtype=np.float32)
    y = target[SEQ_LEN:]
    train_end, val_end = int(len(X) * .70), int(len(X) * .85)
    arrays = (X[:train_end], y[:train_end], X[train_end:val_end], y[train_end:val_end], X[val_end:], y[val_end:])
    out = ROOT / "week5/results"; out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "week5_sequences.npz", X_train=arrays[0], y_train=arrays[1], X_val=arrays[2], y_val=arrays[3], X_test=arrays[4], y_test=arrays[5])
    return arrays


class RNNRegressor(nn.Module):
    def __init__(self, input_dim, kind):
        super().__init__(); cls = nn.LSTM if kind == "LSTM" else nn.GRU
        self.rnn = cls(input_dim, 64, num_layers=2, batch_first=True, dropout=.1)
        self.head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(self, x):
        y, _ = self.rnn(x); return self.head(y[:, -1]).squeeze(-1)


class TransformerRegressor(nn.Module):
    def __init__(self, input_dim):
        super().__init__(); self.proj = nn.Linear(input_dim, 64); self.pos = nn.Parameter(torch.zeros(1, 32, 64))
        layer = nn.TransformerEncoderLayer(64, 4, 128, dropout=.1, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, 2); self.head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(self, x):
        x = self.proj(x); x = x + self.pos[:, :x.size(1)]; return self.head(self.encoder(x).mean(1)).squeeze(-1)


def train(name, model, arrays):
    Xtr, ytr, Xv, yv, Xte, yte = arrays
    train_loader = DataLoader(TensorDataset(torch.tensor(Xtr), torch.tensor(ytr)), BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.tensor(Xv), torch.tensor(yv)), BATCH_SIZE)
    model = model.to(DEVICE); opt = torch.optim.Adam(model.parameters(), lr=.001); loss_fn = nn.MSELoss()
    best, state, wait, train_hist, val_hist = float("inf"), None, 0, [], []
    for _ in range(EPOCHS):
        model.train(); batch = []
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE); opt.zero_grad(); loss = loss_fn(model(xb), yb); loss.backward(); opt.step(); batch.append(loss.item())
        model.eval(); vals = []
        with torch.no_grad():
            for xb, yb in val_loader: vals.append(loss_fn(model(xb.to(DEVICE)), yb.to(DEVICE)).item())
        train_hist.append(float(np.mean(batch))); val_hist.append(float(np.mean(vals)))
        if val_hist[-1] < best: best, state, wait = val_hist[-1], copy.deepcopy(model.state_dict()), 0
        else:
            wait += 1
            if wait >= PATIENCE: break
    model.load_state_dict(state); model.eval()
    with torch.no_grad(): pred = model(torch.tensor(Xte).to(DEVICE)).cpu().numpy()
    result = {"Model": name, "MAE": mean_absolute_error(yte, pred), "RMSE": np.sqrt(mean_squared_error(yte, pred)), "R2": r2_score(yte, pred)}
    torch.save(model.state_dict(), ROOT / "week5/models" / f"{name.lower()}_best.pt")
    return result, pred, train_hist, val_hist


def main():
    for d in (ROOT / "week5/models", ROOT / "week5/results", ROOT / "week5/figures"): d.mkdir(parents=True, exist_ok=True)
    arrays = prepare(); input_dim = arrays[0].shape[2]; rows = []
    for idx, (name, model) in enumerate((("LSTM", RNNRegressor(input_dim, "LSTM")), ("GRU", RNNRegressor(input_dim, "GRU")), ("Transformer", TransformerRegressor(input_dim))), 1):
        row, pred, tr, va = train(name, model, arrays); rows.append(row)
        plt.figure(figsize=(9, 5)); plt.plot(tr, label="Training Loss"); plt.plot(va, label="Validation Loss"); plt.legend(); plt.title(f"{name} Training and Validation Loss"); plt.tight_layout(); plt.savefig(ROOT / "week5/figures" / f"{idx*2-1:02d}_{name.lower()}_loss.png", dpi=200); plt.close()
        plt.figure(figsize=(11, 5)); plt.plot(arrays[5], label="Actual"); plt.plot(pred, label="Predicted"); plt.legend(); plt.title(f"{name}: Actual vs Predicted"); plt.tight_layout(); plt.savefig(ROOT / "week5/figures" / f"{idx*2:02d}_{name.lower()}_actual_vs_predicted.png", dpi=200); plt.close()
    table = pd.DataFrame(rows).sort_values("MAE"); table.to_csv(ROOT / "week5/results/deep_learning_metrics.csv", index=False); print(table.to_string(index=False))


if __name__ == "__main__": main()

