# ============================================
# Federated Learning + Differential Privacy
# Corrected Version (Opacus Compatible)
# ============================================

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
from opacus import PrivacyEngine

# -------------------------------
# Load Dataset
# -------------------------------

data = pd.read_csv("privacy_safe_student_lab_dataset_v2.csv")

X = data.drop("risk_label", axis=1).values
y = data["risk_label"].values

scaler = StandardScaler()
X = scaler.fit_transform(X)

X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.float32)

# -------------------------------
# Define Model
# -------------------------------

class RiskModel(nn.Module):
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

# -------------------------------
# Federated Setup
# -------------------------------

num_clients = 5
client_size = len(X) // num_clients
clients = []

for i in range(num_clients):
    start = i * client_size
    end = (i + 1) * client_size
    clients.append((X[start:end], y[start:end]))

print(f"Simulated {num_clients} federated clients.")

global_model = RiskModel(X.shape[1])
criterion = nn.BCELoss()

rounds = 3

# -------------------------------
# Federated Training Loop
# -------------------------------

for r in range(rounds):
    print(f"\nFederated Round {r+1}")

    local_weights = []

    for idx, (client_x, client_y) in enumerate(clients):

        # Create local model copy
        local_model = RiskModel(X.shape[1])
        local_model.load_state_dict(global_model.state_dict())

        optimizer = optim.Adam(local_model.parameters(), lr=0.01)

        dataset = TensorDataset(client_x, client_y)
        loader = DataLoader(dataset, batch_size=64, shuffle=True)

        # Attach Differential Privacy
        privacy_engine = PrivacyEngine()

        local_model, optimizer, loader = privacy_engine.make_private(
            module=local_model,
            optimizer=optimizer,
            data_loader=loader,
            noise_multiplier=1.0,
            max_grad_norm=1.0,
        )

        # Local Training
        for epoch in range(2):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                outputs = local_model(batch_x).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

        epsilon = privacy_engine.get_epsilon(delta=1e-5)
        print(f"Client {idx+1} ε: {epsilon:.2f}")

        # IMPORTANT FIX:
        # Extract underlying model from Opacus wrapper
        local_weights.append(local_model._module.state_dict())

    # -------------------------------
    # Federated Averaging (FedAvg)
    # -------------------------------

    new_state = global_model.state_dict()

    for key in new_state.keys():
        new_state[key] = torch.stack(
            [local_weights[i][key] for i in range(num_clients)],
            dim=0
        ).mean(dim=0)

    global_model.load_state_dict(new_state)

print("\nFederated + DP Training Completed.")

# -------------------------------
# Evaluate Global Model
# -------------------------------

with torch.no_grad():
    outputs = global_model(X).squeeze()
    predictions = (outputs > 0.5).float()
    accuracy = (predictions == y).float().mean()

print("Federated + DP Accuracy:", round(accuracy.item() * 100, 2), "%")
torch.save(global_model.state_dict(), "federated_dp_model.pth")