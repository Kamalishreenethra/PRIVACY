"""
ThreatScoreEngine — computes a dynamic weighted threat score.
Score = w1*attack_acc + w2*admin_freq + w3*eps_growth + w4*suspicious_logins
Classifies: SAFE (<35), ELEVATED (35-65), CRITICAL (>65)
"""
import json
import os
from datetime import datetime

WEIGHTS = {"attack_accuracy": 40, "admin_freq": 25, "eps_growth": 20, "suspicious_logins": 15}

class ThreatScoreEngine:
    HISTORY_PATH = "privacy_guardian_ai/logs/threat_history.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.HISTORY_PATH), exist_ok=True)
        self._history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.HISTORY_PATH):
            with open(self.HISTORY_PATH) as f:
                try:
                    return json.load(f)
                except Exception:
                    pass
        return []

    def _save(self):
        with open(self.HISTORY_PATH, "w") as f:
            json.dump(self._history[-200:], f, indent=2)  # keep last 200

    def compute(self,
                attack_accuracy: float,   # 0.0 – 1.0
                admin_access_count: int,  # raw count last hour
                epsilon_growth: float,    # delta epsilon since last round
                suspicious_logins: int    # failed/suspicious logins last hour
                ) -> dict:
        """Returns threat score dict with label and component breakdown."""
        # Normalise each component to 0-1
        atk_n   = min(attack_accuracy, 1.0)               # already 0-1
        adm_n   = min(admin_access_count / 10.0, 1.0)     # >10 = max contribution
        eps_n   = min(epsilon_growth / 5.0, 1.0)          # >5.0 growth = max
        sus_n   = min(suspicious_logins / 5.0, 1.0)       # >5 = max

        score = (
            WEIGHTS["attack_accuracy"]  * atk_n +
            WEIGHTS["admin_freq"]       * adm_n +
            WEIGHTS["eps_growth"]       * eps_n +
            WEIGHTS["suspicious_logins"]* sus_n
        )  # 0 – 100

        if score < 35:
            label, color = "SAFE",     "#22c55e"
        elif score < 65:
            label, color = "ELEVATED", "#eab308"
        else:
            label, color = "CRITICAL", "#ef4444"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "score": round(score, 2),
            "label": label,
            "components": {
                "attack_accuracy": round(atk_n * WEIGHTS["attack_accuracy"], 2),
                "admin_freq":      round(adm_n * WEIGHTS["admin_freq"], 2),
                "eps_growth":      round(eps_n * WEIGHTS["eps_growth"], 2),
                "suspicious_logins": round(sus_n * WEIGHTS["suspicious_logins"], 2),
            }
        }
        self._history.append(entry)
        self._save()

        return {"score": round(score, 2), "label": label, "color": color,
                "components": entry["components"]}

    def get_history(self, last_n=30):
        self._history = self._load_history()
        return self._history[-last_n:]
