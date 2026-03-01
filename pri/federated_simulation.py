# ============================================
# Federated Learning Simulation (With DP Ready Model)
# ============================================

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

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
        super(RiskModel, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

# -------------------------------
# Split into Clients
# -------------------------------

num_clients = 5
client_data_size = len(X) // num_clients

clients = []

for i in range(num_clients):
    start = i * client_data_size
    end = (i + 1) * client_data_size
    clients.append((X[start:end], y[start:end]))

print(f"Simulated {num_clients} federated clients.")

# -------------------------------
# Federated Training
# -------------------------------

global_model = RiskModel(X.shape[1])
criterion = nn.BCELoss()

rounds = 5

for round_num in range(rounds):

    local_weights = []

    print(f"\nFederated Round {round_num+1}")

    for client_idx, (client_x, client_y) in enumerate(clients):

        local_model = RiskModel(X.shape[1])
        local_model.load_state_dict(global_model.state_dict())

        optimizer = optim.Adam(local_model.parameters(), lr=0.01)

        dataset = TensorDataset(client_x, client_y)
        loader = DataLoader(dataset, batch_size=64, shuffle=True)

        # Local training
        for epoch in range(3):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                outputs = local_model(batch_x).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

        print(f"Client {client_idx+1} trained.")

        local_weights.append(local_model.state_dict())

    # -------------------------------
    # Aggregate Weights (FedAvg)
    # -------------------------------

    new_state_dict = global_model.state_dict()

    for key in new_state_dict.keys():
        new_state_dict[key] = torch.stack(
            [local_weights[i][key] for i in range(num_clients)],
            dim=0
        ).mean(dim=0)

    global_model.load_state_dict(new_state_dict)

print("\nFederated Training Completed.")

# -------------------------------
# Evaluate Global Model
# -------------------------------

with torch.no_grad():
    outputs = global_model(X).squeeze()
    predictions = (outputs > 0.5).float()
    accuracy = (predictions == y).float().mean()

print("\nFederated Model Accuracy:", round(accuracy.item()*100, 2), "%")