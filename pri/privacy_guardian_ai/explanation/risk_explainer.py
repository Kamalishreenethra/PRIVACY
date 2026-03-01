import torch
import numpy as np

class RiskExplainer:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names

    def explain_instance(self, x):
        """Simple perturbation-based feature importance for explanation"""
        self.model.eval()
        x_tensor = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            base_prob = self.model(x_tensor).item()
            
        importances = {}
        # Perturb each feature slightly to see contribution
        for i, name in enumerate(self.feature_names):
            x_perturbed = x.copy()
            x_perturbed[i] *= 1.1 # 10% increase
            x_p_tensor = torch.tensor(x_perturbed, dtype=torch.float32).unsqueeze(0)
            
            with torch.no_grad():
                perturbed_prob = self.model(x_p_tensor).item()
                
            # Contribution is the change in probability
            importances[name] = perturbed_prob - base_prob
            
        return importances, base_prob
