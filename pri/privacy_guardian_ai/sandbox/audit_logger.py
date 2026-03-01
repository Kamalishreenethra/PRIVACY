"""
AuditLogger — immutable tamper-evident audit trail.
Upgraded with epsilon history getter and login event filter.
"""
import os
import json
import datetime
import hashlib


class AuditLogger:
    def __init__(self, log_path="privacy_guardian_ai/logs/audit_trail.json"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if os.path.exists(self.log_path):
            with open(self.log_path, "r") as f:
                try:
                    self.logs = json.load(f)
                except Exception:
                    self.logs = []
        else:
            self.logs = []

    def log_event(self, user_id, role, action_type, reason, resource_id=None):
        """Create a transparency log entry."""
        entry = {
            "timestamp":    datetime.datetime.now().isoformat(),
            "user_id":      user_id,
            "role":         role,
            "action_type":  action_type,
            "reason":       reason,
            "resource_id":  resource_id,
            "ip_simulated": f"192.168.1.{hash(str(user_id)) % 255}",
        }
        prev_hash = self.logs[-1]["hash"] if self.logs else "0"
        entry_str = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256((entry_str + prev_hash).encode()).hexdigest()

        self.logs.append(entry)
        self._save()
        return entry

    def _save(self):
        with open(self.log_path, "w") as f:
            json.dump(self.logs, f, indent=4)

    def get_logs_for_student(self, student_id):
        return [l for l in self.logs if str(l.get("resource_id")) == str(student_id)]

    def get_all_logs(self):
        return self.logs

    def get_login_events(self, hours=24):
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return [
            l for l in self.logs
            if l.get("action_type") in ("LOGIN_SUCCESS", "LOGIN_FAILED")
            and self._parse_ts(l) >= cutoff
        ]

    def get_admin_logins(self, hours=72):
        """Return LOGIN_SUCCESS events from admin/security roles in last N hours."""
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return [
            l for l in self.logs
            if l.get("action_type") == "LOGIN_SUCCESS"
            and l.get("role", "").lower() in ("admin", "security_officer", "security")
            and self._parse_ts(l) >= cutoff
        ]

    def get_epsilon_history(self, last_n=30):
        """Pull from dedicated epsilon log if available."""
        eps_path = "privacy_guardian_ai/logs/epsilon_history.json"
        if os.path.exists(eps_path):
            with open(eps_path) as f:
                try:
                    data = json.load(f)
                    return data[-last_n:]
                except Exception:
                    pass
        return []

    def get_inspection_count(self, hours=1):
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return sum(
            1 for l in self.logs
            if l.get("action_type") == "MANUAL_INSPECTION"
            and self._parse_ts(l) >= cutoff
        )

    def _parse_ts(self, log_entry):
        try:
            return datetime.datetime.fromisoformat(log_entry.get("timestamp",""))
        except Exception:
            return datetime.datetime.min
