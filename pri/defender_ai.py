# ============================================
# Defender AI - Membership Inference Attack
# ============================================

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from torch.utils.data import DataLoader, TensorDataset

# -------------------------------
# Load Dataset
# -------------------------------

data = pd.read_csv("privacy_safe_student_lab_dataset_v2.csv")

X = data.drop("risk_label", axis=1).values
y = data["risk_label"].values

scaler = StandardScaler()
X = scaler.fit_transform(X)

# Split dataset (simulate training vs unseen data)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.5, random_state=42
)

X_train = torch.tensor(X_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)

# -------------------------------
# Load Trained Federated+DP Model
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

model = RiskModel(X.shape[1])
model.load_state_dict(torch.load("federated_dp_model.pth"))
model.eval()

# -------------------------------
# Get Model Confidence Scores
# -------------------------------

with torch.no_grad():
    train_outputs = model(X_train).squeeze().numpy()
    test_outputs = model(X_test).squeeze().numpy()

# Build attack dataset
attack_features = np.concatenate([train_outputs, test_outputs])
attack_labels = np.concatenate([
    np.ones(len(train_outputs)),   # 1 = in training set
    np.zeros(len(test_outputs))    # 0 = not in training set
])

attack_features = attack_features.reshape(-1, 1)

# -------------------------------
# Train Simple Attack Model
# -------------------------------

from sklearn.linear_model import LogisticRegression

attack_model = LogisticRegression()
attack_model.fit(attack_features, attack_labels)

attack_preds = attack_model.predict(attack_features)
attack_accuracy = accuracy_score(attack_labels, attack_preds)

print("\nMembership Inference Attack Accuracy:",
      round(attack_accuracy * 100, 2), "%")

# -------------------------------
# Defender Decision
# -------------------------------

if attack_accuracy > 0.60:
    print("⚠ Privacy Risk Detected. Defender should increase noise.")
else:
    print("✅ Privacy Level Acceptable.")