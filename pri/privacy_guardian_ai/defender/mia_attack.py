import torch
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

class MIADefender:
    def __init__(self, model):
        self.model = model
        
    def simulate_attack(self, X_train, X_test):
        """Simulate a Membership Inference Attack using confidence scores"""
        self.model.eval()
        
        with torch.no_grad():
            # Get confidence scores (outputs) for training data
            train_outputs = self.model(X_train).squeeze().numpy()
            # Get confidence scores for unseen data
            test_outputs = self.model(X_test).squeeze().numpy()
            
        # Build attack dataset
        # 1 = Member, 0 = Non-member
        attack_features = np.concatenate([train_outputs, test_outputs]).reshape(-1, 1)
        attack_labels = np.concatenate([
            np.ones(len(train_outputs)),
            np.zeros(len(test_outputs))
        ])
        
        # Train a simple shadow/attack model (Logistic Regression)
        # In a real scenario, this would be more complex, but this simulates the concept
        X_a_train, X_a_test, y_a_train, y_a_test = train_test_split(
            attack_features, attack_labels, test_size=0.3, random_state=42
        )
        
        attack_clf = LogisticRegression()
        attack_clf.fit(X_a_train, y_a_train)
        
        preds = attack_clf.predict(X_a_test)
        accuracy = accuracy_score(y_a_test, preds)
        
        return accuracy
