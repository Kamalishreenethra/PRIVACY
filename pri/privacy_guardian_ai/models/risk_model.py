import torch.nn as nn

class RiskModel(nn.Module):
    def __init__(self, input_dim):
        super(RiskModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)

if __name__ == "__main__":
    # Test model
    import torch
    model = RiskModel(5)
    print(model)
    x = torch.randn(10, 5)
    y = model(x)
    print(f"Output shape: {y.shape}")
