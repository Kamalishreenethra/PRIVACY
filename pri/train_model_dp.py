# ============================================
# Differentially Private Risk Prediction Model
# ============================================

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from opacus import PrivacyEngine
from torch.utils.data import DataLoader, TensorDataset

# -------------------------------
# Load Dataset
# -------------------------------

data = pd.read_csv("privacy_safe_student_lab_dataset_v2.csv")

X = data.drop("risk_label", axis=1).values
y = data["risk_label"].values

# Scale
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Convert to tensors
X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)

X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

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

model = RiskModel(X_train.shape[1])

criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# -------------------------------
# Attach Privacy Engine
# -------------------------------

privacy_engine = PrivacyEngine()

model, optimizer, train_loader = privacy_engine.make_private(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,
    noise_multiplier=1.0,
    max_grad_norm=1.0,
)

# -------------------------------
# Training Loop
# -------------------------------

epochs = 20

for epoch in range(epochs):
    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_x).squeeze()
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

    epsilon = privacy_engine.get_epsilon(delta=1e-5)
    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}, ε: {epsilon:.2f}")

# -------------------------------
# Evaluation
# -------------------------------

with torch.no_grad():
    outputs = model(X_test).squeeze()
    predictions = (outputs > 0.5).float()
    accuracy = (predictions == y_test).float().mean()

print("\nDifferentially Private Model Accuracy:", round(accuracy.item()*100, 2), "%")