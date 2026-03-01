"""
AdaptivePrivacyController — compliance-mode-aware noise adjustment.
Upgraded with epsilon history tracking and compliance mode hooks.
"""
import json
import os
from datetime import datetime


class AdaptivePrivacyController:
    HISTORY_PATH = "privacy_guardian_ai/logs/epsilon_history.json"

    def __init__(self, initial_noise=1.1, initial_lr=0.01):
        self.noise_multiplier = initial_noise
        self.learning_rate    = initial_lr
        self.epsilon          = 0.0
        self.round_num        = 0
        self.history          = []
        os.makedirs(os.path.dirname(self.HISTORY_PATH), exist_ok=True)
        self._persisted = self._load_history()

    def _load_history(self):
        if os.path.exists(self.HISTORY_PATH):
            with open(self.HISTORY_PATH) as f:
                try:
                    return json.load(f)
                except Exception:
                    pass
        return []

    def _save_history(self):
        with open(self.HISTORY_PATH, "w") as f:
            json.dump(self._persisted[-500:], f, indent=2)

    def set_compliance_mode(self, mode: str):
        """Adjust noise bounds based on compliance mode."""
        if mode == "STRICT":
            self.noise_multiplier = max(self.noise_multiplier, 1.5)
        elif mode == "AUDIT":
            self.noise_multiplier = max(self.noise_multiplier, 2.0)
        # STANDARD: no forced change

    def record_round(self, epsilon: float, noise: float, round_number: int):
        """Record epsilon + noise after each federated round."""
        self.epsilon   = epsilon
        self.round_num = round_number
        entry = {
            "timestamp":      datetime.now().isoformat(),
            "round":          round_number,
            "epsilon":        round(epsilon, 4),
            "noise_multiplier": round(noise, 4),
        }
        self._persisted.append(entry)
        self._save_history()
        return entry

    def update(self, attack_accuracy: float):
        """Adaptive noise adjustment based on attack accuracy."""
        status = "Normal"
        if attack_accuracy > 0.60:
            self.noise_multiplier += 0.2
            self.learning_rate    *= 0.8
            status = "Elevated Risk - Increasing Privacy"
        elif attack_accuracy < 0.52:
            self.noise_multiplier  = max(1.1, self.noise_multiplier - 0.1)
            status = "Safe - Optimizing Utility"

        self.history.append({
            "attack_accuracy":  attack_accuracy,
            "noise_multiplier": self.noise_multiplier,
            "learning_rate":    self.learning_rate,
            "status":           status,
        })
        return status, self.noise_multiplier, self.learning_rate

    def get_epsilon_history(self, last_n=30):
        self._persisted = self._load_history()
        return self._persisted[-last_n:]

    def get_epsilon_growth_rate(self) -> float:
        """Delta epsilon between last two recorded rounds."""
        data = self.get_epsilon_history(2)
        if len(data) < 2:
            return 0.0
        return abs(data[-1]["epsilon"] - data[-2]["epsilon"])
