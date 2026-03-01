import torch
from ..models.risk_model import RiskModel

class FederatedServer:
    def __init__(self, input_dim):
        self.global_model = RiskModel(input_dim)
        
    def aggregate(self, client_weights):
        """Perform Federated Averaging (FedAvg)"""
        new_state = self.global_model.state_dict()
        
        for key in new_state.keys():
            new_state[key] = torch.stack(
                [weights[key] for weights in client_weights],
                dim=0
            ).mean(dim=0)
            
        self.global_model.load_state_dict(new_state)
        return self.global_model.state_dict()
    
    def evaluate(self, X_val, y_val):
        self.global_model.eval()
        with torch.no_grad():
            outputs = self.global_model(X_val).squeeze()
            predictions = (outputs > 0.5).float()
            accuracy = (predictions == y_val).float().mean()
            return accuracy.item()
