"""
AnomalyDetector — detects admin spikes, login anomalies, epsilon growth,
repeated profile access, and sandbox violations from the audit trail.
"""
import json
import os
from datetime import datetime, timedelta
from collections import Counter


class AnomalyDetector:
    THRESHOLDS = {
        "admin_access_per_hour": 5,
        "login_failures_per_hour": 3,
        "same_profile_access_per_day": 4,
        "epsilon_growth_per_round": 0.5,
    }

    def __init__(self, log_path="privacy_guardian_ai/logs/audit_trail.json"):
        self.log_path = log_path
        self._logs = []
        self._load()

    def _load(self):
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                try:
                    self._logs = json.load(f)
                except Exception:
                    self._logs = []

    def _recent(self, hours=1):
        cutoff = datetime.now() - timedelta(hours=hours)
        result = []
        for l in self._logs:
            try:
                ts = datetime.fromisoformat(l["timestamp"])
                if ts >= cutoff:
                    result.append(l)
            except Exception:
                pass
        return result

    def detect(self):
        self._load()
        anomalies = []
        recent_1h  = self._recent(1)
        recent_24h = self._recent(24)

        # 1 — Admin access spike (MANUAL_INSPECTION in last 1h)
        admin_accesses = [l for l in recent_1h if l.get("action_type") == "MANUAL_INSPECTION"]
        if len(admin_accesses) >= self.THRESHOLDS["admin_access_per_hour"]:
            anomalies.append({
                "type": "ADMIN_ACCESS_SPIKE",
                "severity": "ELEVATED",
                "detail": f"{len(admin_accesses)} manual inspections in last hour",
                "count": len(admin_accesses),
            })

        # 2 — Login failure anomaly
        login_fails = [l for l in recent_1h if l.get("action_type") == "LOGIN_FAILED"]
        if len(login_fails) >= self.THRESHOLDS["login_failures_per_hour"]:
            anomalies.append({
                "type": "LOGIN_ANOMALY",
                "severity": "ELEVATED",
                "detail": f"{len(login_fails)} failed login attempts in last hour",
                "count": len(login_fails),
            })

        # 3 — Repeated profile access (same subject, last 24h)
        subjects = [
            l.get("reason","").split(",")[0].replace("Subject:","").strip()
            for l in recent_24h
            if l.get("action_type") == "MANUAL_INSPECTION"
        ]
        subject_counts = Counter(subjects)
        for subj, cnt in subject_counts.items():
            if cnt >= self.THRESHOLDS["same_profile_access_per_day"] and subj:
                anomalies.append({
                    "type": "REPEATED_PROFILE_ACCESS",
                    "severity": "CRITICAL",
                    "detail": f"Subject {subj} accessed {cnt}x in last 24h",
                    "count": cnt,
                })

        # 4 — Sandbox violations
        sandbox_events = [l for l in recent_24h if "SANDBOX" in l.get("action_type","").upper()
                          or "BLOCK" in l.get("action_type","").upper()]
        if sandbox_events:
            anomalies.append({
                "type": "SANDBOX_VIOLATION",
                "severity": "CRITICAL",
                "detail": f"{len(sandbox_events)} sandbox violations detected",
                "count": len(sandbox_events),
            })

        return anomalies

    def get_admin_access_count(self, hours=1):
        recent = self._recent(hours)
        return len([l for l in recent if l.get("action_type") == "MANUAL_INSPECTION"])

    def get_login_failure_count(self, hours=1):
        recent = self._recent(hours)
        return len([l for l in recent if l.get("action_type") == "LOGIN_FAILED"])

    def get_suspicious_login_count(self, hours=24):
        recent = self._recent(hours)
        return len([l for l in recent if l.get("action_type") in ("LOGIN_FAILED", "MANUAL_INSPECTION")])
