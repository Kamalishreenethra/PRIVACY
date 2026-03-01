import torch
import pandas as pd
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

def load_federated_data(csv_path, num_clients=5, batch_size=32):
    data = pd.read_csv(csv_path)
    X = data.drop("risk_label", axis=1).values
    y = data["risk_label"].values
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)
    
    client_size = len(X) // num_clients
    client_loaders = []
    
    for i in range(num_clients):
        start = i * client_size
        end = (i + 1) * client_size
        
        client_x = X[start:end]
        client_y = y[start:end]
        
        dataset = TensorDataset(client_x, client_y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        client_loaders.append(loader)
        
    return client_loaders, X, y, scaler

if __name__ == "__main__":
    # Test loading
    loaders, X, y, scaler = load_federated_data("privacy_guardian_ai/dataset/student_data.csv")
    print(f"Loaded {len(loaders)} client loaders.")
