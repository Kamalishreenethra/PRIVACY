"""
ComplianceModeManager — manages STANDARD / STRICT / AUDIT privacy modes.
Each mode configures noise, access restrictions, and logging intensity.
"""
import json
import os
from datetime import datetime

MODES = {
    "STANDARD": {
        "noise_multiplier_min": 1.0,
        "noise_multiplier_max": 1.5,
        "admin_access_restricted": False,
        "log_all_access": False,
        "require_justification": True,
        "description": "Balanced noise. Normal access. Standard logging.",
        "color": "#38bdf8",
    },
    "STRICT": {
        "noise_multiplier_min": 1.5,
        "noise_multiplier_max": 2.5,
        "admin_access_restricted": True,
        "log_all_access": True,
        "require_justification": True,
        "description": "Higher noise. Reduced analytics. Admin access restricted.",
        "color": "#eab308",
    },
    "AUDIT": {
        "noise_multiplier_min": 2.0,
        "noise_multiplier_max": 3.5,
        "admin_access_restricted": True,
        "log_all_access": True,
        "require_justification": True,
        "description": "Maximum logging. Enhanced monitoring. All access justified.",
        "color": "#ef4444",
    },
}

class ComplianceModeManager:
    def __init__(self,
                 config_path="privacy_guardian_ai/configs/compliance_mode.json",
                 log_path="privacy_guardian_ai/logs/audit_trail.json"):
        self.config_path = config_path
        self.log_path    = log_path
        self._ensure_dirs()
        self._mode = self._load_mode()

    def _ensure_dirs(self):
        for p in [self.config_path, self.log_path]:
            os.makedirs(os.path.dirname(p), exist_ok=True)

    def _load_mode(self):
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                try:
                    return json.load(f).get("mode", "STANDARD")
                except Exception:
                    pass
        return "STANDARD"

    def _save(self):
        with open(self.config_path, "w") as f:
            json.dump({"mode": self._mode, "updated_at": datetime.now().isoformat()}, f, indent=2)

    def _log_switch(self, old_mode, new_mode):
        logs = []
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                try:
                    logs = json.load(f)
                except Exception:
                    pass
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": "system",
            "role": "security_officer",
            "action_type": "COMPLIANCE_MODE_CHANGE",
            "reason": f"Mode switched from {old_mode} to {new_mode}",
            "resource_id": None,
            "ip_simulated": "127.0.0.1",
            "hash": "mode_change_event"
        })
        with open(self.log_path, "w") as f:
            json.dump(logs, f, indent=4)

    def set_mode(self, mode: str):
        if mode not in MODES:
            raise ValueError(f"Unknown mode: {mode}. Choose from {list(MODES.keys())}")
        old = self._mode
        self._mode = mode
        self._save()
        if old != mode:
            self._log_switch(old, mode)

    def get_mode(self) -> str:
        self._mode = self._load_mode()
        return self._mode

    def get_config(self) -> dict:
        return {**MODES[self.get_mode()], "mode": self._mode}

    def all_modes(self) -> dict:
        return MODES
