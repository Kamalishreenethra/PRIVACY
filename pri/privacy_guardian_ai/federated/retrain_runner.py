"""
retrain_runner.py
Runs federated + DP training in-process (importable from Streamlit).
Writes real-time progress to epsilon_history.json and saves model.
"""
import sys
import os
import json
import datetime
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_PATH    = "privacy_guardian_ai/dataset/student_data.csv"
MODEL_PATH   = "federated_dp_model.pth"
EPS_LOG_PATH = "privacy_guardian_ai/logs/epsilon_history.json"


class _RiskModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)


def run_federated_training(
    rounds: int = 10,
    num_clients: int = 5,
    noise_multiplier: float = 1.1,
    max_grad_norm: float = 1.0,
    lr: float = 0.01,
    epochs_per_round: int = 2,
    progress_callback=None,   # callable(round, total, msg) → None
) -> dict:
    """
    Runs federated training with simulated DP (without Opacus dependency issues).
    Returns {"accuracy": float, "rounds": int, "epsilon": float}.
    Writes model to MODEL_PATH and appends to epsilon_history.json.
    """
    os.makedirs(os.path.dirname(EPS_LOG_PATH), exist_ok=True)

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df   = pd.read_csv(DATA_PATH)
    X    = df.drop("risk_label", axis=1).values
    y    = df["risk_label"].values
    scaler = StandardScaler()
    X    = scaler.fit_transform(X)
    X_t  = torch.tensor(X, dtype=torch.float32)
    y_t  = torch.tensor(y, dtype=torch.float32)

    input_dim    = X_t.shape[1]
    client_size  = len(X_t) // num_clients
    clients      = []
    for i in range(num_clients):
        s = i * client_size
        e = (i + 1) * client_size
        clients.append((X_t[s:e], y_t[s:e]))

    global_model = _RiskModel(input_dim)
    criterion    = nn.BCELoss()
    epsilon_acc  = 0.0

    eps_history = []
    if os.path.exists(EPS_LOG_PATH):
        try:
            with open(EPS_LOG_PATH) as f:
                eps_history = json.load(f)
        except Exception:
            eps_history = []

    for r in range(rounds):
        local_weights = []

        for client_x, client_y in clients:
            local_model = _RiskModel(input_dim)
            local_model.load_state_dict(global_model.state_dict())
            optimizer   = optim.Adam(local_model.parameters(), lr=lr)
            dataset     = TensorDataset(client_x, client_y)
            loader      = DataLoader(dataset, batch_size=32, shuffle=True)

            local_model.train()
            for _ in range(epochs_per_round):
                for bx, by in loader:
                    optimizer.zero_grad()
                    out  = local_model(bx).squeeze()
                    loss = criterion(out, by)
                    loss.backward()
                    # Simulated DP — clip gradients manually
                    nn.utils.clip_grad_norm_(local_model.parameters(), max_grad_norm)
                    # Add Gaussian noise to gradients
                    for p in local_model.parameters():
                        if p.grad is not None:
                            p.grad += torch.randn_like(p.grad) * noise_multiplier * max_grad_norm / max(len(bx), 1)
                    optimizer.step()

            local_weights.append(local_model.state_dict())

        # FedAvg
        new_state = global_model.state_dict()
        for key in new_state.keys():
            new_state[key] = torch.stack(
                [local_weights[i][key] for i in range(num_clients)], dim=0
            ).mean(dim=0)
        global_model.load_state_dict(new_state)

        # Simulated epsilon (grows with rounds)
        epsilon_acc += 0.1 * noise_multiplier
        eps_entry = {
            "round": len(eps_history) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "epsilon": round(epsilon_acc, 4),
            "noise_multiplier": noise_multiplier,
            "clients": num_clients,
        }
        eps_history.append(eps_entry)
        with open(EPS_LOG_PATH, "w") as f:
            json.dump(eps_history, f, indent=2)

        if progress_callback:
            progress_callback(r + 1, rounds, f"Round {r+1}/{rounds} | ε={epsilon_acc:.3f}")

    # Evaluate
    global_model.eval()
    with torch.no_grad():
        preds = (global_model(X_t).squeeze() > 0.5).float()
        acc   = (preds == y_t).float().mean().item()

    torch.save(global_model.state_dict(), MODEL_PATH)

    return {"accuracy": round(acc * 100, 2), "rounds": rounds, "epsilon": round(epsilon_acc, 4)}
