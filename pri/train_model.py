# ============================================
# Privacy-Preserving Student Risk Prediction
# Version 2 - Enhanced Dataset
# ============================================

import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib


# -------------------------------
# 1. Load Dataset
# -------------------------------

DATA_FILE = "privacy_safe_student_lab_dataset_v2.csv"

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"{DATA_FILE} not found in project folder.")

data = pd.read_csv(DATA_FILE)

print("\nDataset Loaded Successfully.")
print("Shape:", data.shape)
print(data.head())


# -------------------------------
# 2. Check Class Balance
# -------------------------------

print("\nClass Distribution:")
print(data["risk_label"].value_counts())


# -------------------------------
# 3. Separate Features and Label
# -------------------------------

X = data.drop("risk_label", axis=1)
y = data["risk_label"]

print("\nFeatures Used:")
print(list(X.columns))


# -------------------------------
# 4. Train-Test Split
# -------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("\nTraining samples:", X_train.shape[0])
print("Testing samples:", X_test.shape[0])


# -------------------------------
# 5. Feature Scaling
# -------------------------------

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# -------------------------------
# 6. Train Model
# -------------------------------

model = LogisticRegression(max_iter=2000)
model.fit(X_train_scaled, y_train)

print("\nModel Training Completed.")


# -------------------------------
# 7. Evaluate Model
# -------------------------------

y_pred = model.predict(X_test_scaled)

accuracy = accuracy_score(y_test, y_pred)

print("\n==============================")
print("MODEL PERFORMANCE (V2)")
print("==============================")
print("Accuracy:", round(accuracy * 100, 2), "%\n")
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))


# -------------------------------
# 8. Save Model & Scaler
# -------------------------------

joblib.dump(model, "risk_model_v2.pkl")
joblib.dump(scaler, "scaler_v2.pkl")

print("\nModel and Scaler saved successfully as:")
print(" - risk_model_v2.pkl")
print(" - scaler_v2.pkl")

print("\nEnhanced Model Setup Complete.")