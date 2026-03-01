import torch
import torch.optim as optim
import torch.nn as nn
from opacus import PrivacyEngine
from ..models.risk_model import RiskModel

class FederatedClient:
    def __init__(self, client_id, loader, input_dim):
        self.client_id = client_id
        self.loader = loader
        self.input_dim = input_dim
        self.local_model = RiskModel(input_dim)
        self.optimizer = None
        self.privacy_engine = None
        self.epsilon = 0.0

    def setup_privacy(self, noise_multiplier=1.1, max_grad_norm=1.0):
        self.optimizer = optim.Adam(self.local_model.parameters(), lr=0.01)
        self.privacy_engine = PrivacyEngine()
        
        # Opacus make_private
        self.local_model, self.optimizer, self.loader = self.privacy_engine.make_private(
            module=self.local_model,
            optimizer=self.optimizer,
            data_loader=self.loader,
            noise_multiplier=noise_multiplier,
            max_grad_norm=max_grad_norm,
        )

    def train(self, global_state_dict, epochs=2):
        # Load global model state
        self.local_model._module.load_state_dict(global_state_dict)
        self.local_model.train()
        
        criterion = nn.BCELoss()
        
        for _ in range(epochs):
            for batch_x, batch_y in self.loader:
                self.optimizer.zero_grad()
                outputs = self.local_model(batch_x).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                
        # Track epsilon
        self.epsilon = self.privacy_engine.get_epsilon(delta=1e-5)
        return self.local_model._module.state_dict(), self.epsilon
