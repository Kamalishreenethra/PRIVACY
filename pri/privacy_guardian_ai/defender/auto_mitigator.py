"""
AutoMitigator — automatically escalates privacy defenses when thresholds are breached.
Conditions checked:
  - attack_accuracy > 0.60
  - epsilon > 8.0
  - admin_access_count >= 5 in last hour (admin spike)
"""
import json
import os
from datetime import datetime

class AutoMitigator:
    THRESHOLDS = {
        "attack_accuracy": 0.60,
        "epsilon_limit":   8.0,
        "admin_spike":     5,
    }
    LOG_PATH = "privacy_guardian_ai/logs/mitigation_log.json"

    def __init__(self, noise_multiplier=1.1):
        self.noise_multiplier = noise_multiplier
        self.status = "STANDBY"
        self.last_action = None
        os.makedirs(os.path.dirname(self.LOG_PATH), exist_ok=True)
        self._log = self._load_log()

    def _load_log(self):
        if os.path.exists(self.LOG_PATH):
            with open(self.LOG_PATH) as f:
                try:
                    return json.load(f)
                except Exception:
                    pass
        return []

    def _append_log(self, entry):
        self._log.append(entry)
        with open(self.LOG_PATH, "w") as f:
            json.dump(self._log[-200:], f, indent=2)

    def evaluate(self,
                 attack_accuracy: float,
                 epsilon: float,
                 admin_access_count: int) -> dict:
        """
        Returns mitigation result dict.
        Side effects: bumps noise_multiplier if conditions met.
        """
        triggers = []
        actions  = []

        if attack_accuracy > self.THRESHOLDS["attack_accuracy"]:
            triggers.append(f"Attack accuracy {attack_accuracy:.1%} > {self.THRESHOLDS['attack_accuracy']:.0%}")
            self.noise_multiplier = round(self.noise_multiplier + 0.2, 2)
            actions.append(f"Noise multiplier increased to {self.noise_multiplier}")

        if epsilon > self.THRESHOLDS["epsilon_limit"]:
            triggers.append(f"Epsilon {epsilon:.2f} > safety limit {self.THRESHOLDS['epsilon_limit']}")
            actions.append("Prediction granularity reduced")
            actions.append("Admin detailed access restricted")

        if admin_access_count >= self.THRESHOLDS["admin_spike"]:
            triggers.append(f"Admin access spike: {admin_access_count} accesses in last hour")
            actions.append("Admin access rate-limited")

        if triggers:
            self.status = "ACTIVATED"
            entry = {
                "timestamp": datetime.now().isoformat(),
                "status": "ACTIVATED",
                "triggers": triggers,
                "actions": actions,
                "noise_multiplier": self.noise_multiplier,
                "epsilon": epsilon,
            }
            self._append_log(entry)
            self.last_action = entry
        else:
            self.status = "STANDBY"

        return {
            "status": self.status,
            "triggers": triggers,
            "actions": actions,
            "noise_multiplier": self.noise_multiplier,
        }

    def get_log(self, last_n=10):
        self._log = self._load_log()
        return self._log[-last_n:]
