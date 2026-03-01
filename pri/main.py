import sys
import os
import torch
import pandas as pd
from sklearn.model_selection import train_test_split

# Add current dir to sys.path for local imports
sys.path.append(os.getcwd())

from privacy_guardian_ai.dataset.generator import generate_synthetic_data
from privacy_guardian_ai.dataset.loader import load_federated_data
from privacy_guardian_ai.federated.server import FederatedServer
from privacy_guardian_ai.federated.client import FederatedClient
from privacy_guardian_ai.privacy.controller import AdaptivePrivacyController
from privacy_guardian_ai.defender.mia_attack import MIADefender
from privacy_guardian_ai.sandbox.runtime import SecureSandbox
from privacy_guardian_ai.sandbox.access_controller import AccessController
from privacy_guardian_ai.identity.rbac import Roles

def run_simulation(rounds=5, num_clients=5):
    print("🚀 Starting Privacy Guardian AI Simulation...")
    
    # 1. Setup Sandbox & Access Controller
    sandbox = SecureSandbox()
    access_ctrl = AccessController()
    
    access_ctrl.request_access("SYSTEM", Roles.SECURITY_OFFICER, "view_security_logs", reason="Initializing Privacy Guardian Engine")
    
    # 2. Generate Data (Simulate secure data vault)
    data_path = "privacy_guardian_ai/dataset/student_data.csv"
    access_ctrl.request_access("SYSTEM", Roles.SECURITY_OFFICER, "view_security_logs", reason=f"Generating synthetic academic data at {data_path}")
    generate_synthetic_data(num_samples=1500, output_path=data_path)
    
    # 3. Load Data
    sandbox.enforce_read_only(data_path)
    client_loaders, X, y, scaler = load_federated_data(data_path, num_clients=num_clients)
    
    # Split for MIA simulation (Train/Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Initialize Federated Server & Clients
    input_dim = X.shape[1]
    server = FederatedServer(input_dim)
    clients = [FederatedClient(i, client_loaders[i], input_dim) for i in range(num_clients)]
    
    # 5. Initialize Privacy Controller
    controller = AdaptivePrivacyController(initial_noise=1.1, initial_lr=0.01)
    
    metrics_history = []
    
    # 6. Training Loop
    global_weights = server.global_model.state_dict()
    
    for r in range(rounds):
        access_ctrl.request_access("SYSTEM", Roles.SECURITY_OFFICER, "view_mia_metrics", reason=f"Starting Federated Training Round {r+1}")
        print(f"\n--- Round {r+1} ---")
        
        # Setup clients with current privacy params
        for client in clients:
            client.setup_privacy(noise_multiplier=controller.noise_multiplier)
            
        # Local training
        local_weights_list = []
        epsilons = []
        for client in clients:
            weights, epsilon = client.train(global_weights, epochs=2)
            local_weights_list.append(weights)
            epsilons.append(epsilon)
            
        # Aggregation
        global_weights = server.aggregate(local_weights_list)
        
        # Evaluation
        accuracy = server.evaluate(X, y)
        avg_epsilon = sum(epsilons) / len(epsilons)
        
        # 7. Defender Attack Simulation
        defender = MIADefender(server.global_model)
        attack_accuracy = defender.simulate_attack(X_train, X_test)
        
        # 8. Adaptive Response
        status, new_noise, new_lr = controller.update(attack_accuracy)
        
        print(f"Accuracy: {accuracy:.4f} | Avg ε: {avg_epsilon:.2f} | Attack Acc: {attack_accuracy:.4f}")
        print(f"Defender Status: {status}")
        
        metrics_history.append({
            'round': r + 1,
            'accuracy': accuracy,
            'epsilon': avg_epsilon,
            'attack_accuracy': attack_accuracy,
            'status': status,
            'noise': new_noise
        })
        
        # Save metrics to sandbox for dashboard
        metrics_df = pd.DataFrame(metrics_history)
        sandbox.safe_write("metrics.csv", metrics_df.to_csv(index=False))

    # Save final model for explainer
    torch.save(server.global_model.state_dict(), "federated_dp_model.pth")
    print(f"Final model saved as federated_dp_model.pth")

    print("\n✅ Simulation Completed.")
    return metrics_history

if __name__ == "__main__":
    run_simulation()
