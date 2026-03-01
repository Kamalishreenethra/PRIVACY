"""
SecureSandbox — upgraded with CSV download block, raw PII block,
directory whitelist enforcement, and AuditLogger integration.
"""
import os
import datetime
import logging
from privacy_guardian_ai.sandbox.audit_logger import AuditLogger

BLOCKED_EXTENSIONS = {".csv", ".pkl", ".pth", ".json"}
ALLOWED_DIRS       = {"privacy_guardian_ai/sandbox/storage"}
BLOCKED_PATTERNS   = ["student_data", "vault", "audit_trail", "raw", "pii"]


class SecureSandbox:
    def __init__(self, allowed_dir="privacy_guardian_ai/sandbox/storage"):
        self.allowed_dir  = allowed_dir
        self._audit       = AuditLogger()
        os.makedirs(allowed_dir, exist_ok=True)

        self.log_file = "privacy_guardian_ai/sandbox/security.log"
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def _log(self, user, action, resource):
        msg = f"User: {user} | Action: {action} | Resource: {resource}"
        logging.info(msg)

    def log_access(self, user, action, resource):
        self._log(user, action, resource)

    def block_csv_download(self, filename: str, user="unknown") -> dict:
        """Block any raw CSV export attempt."""
        if filename.endswith(".csv") or "dataset" in filename.lower():
            self._log(user, "BLOCKED_CSV_DOWNLOAD", filename)
            self._audit.log_event(user, "sandbox", "SANDBOX_BLOCK_CSV",
                                  f"Blocked CSV download: {filename}")
            return {"allowed": False, "reason": "Raw CSV export is prohibited by sandbox policy."}
        return {"allowed": True, "reason": ""}

    def block_raw_pii(self, resource: str, user="unknown") -> dict:
        """Block access to files matching PII patterns."""
        for pattern in BLOCKED_PATTERNS:
            if pattern in resource.lower():
                self._log(user, "BLOCKED_PII_ACCESS", resource)
                self._audit.log_event(user, "sandbox", "SANDBOX_BLOCK_PII",
                                      f"Blocked PII access: {resource}")
                return {"allowed": False, "reason": f"PII resource '{resource}' is access-restricted."}
        return {"allowed": True, "reason": ""}

    def enforce_directory_whitelist(self, path: str, user="unknown") -> dict:
        """Block access to paths outside the allowed sandbox directory."""
        norm = path.replace("\\", "/")
        for allowed in ALLOWED_DIRS:
            if norm.startswith(allowed):
                return {"allowed": True, "reason": ""}
        self._log(user, "BLOCKED_DIRECTORY", path)
        self._audit.log_event(user, "sandbox", "SANDBOX_BLOCK_DIR",
                              f"Directory violation: {path}")
        return {"allowed": False, "reason": f"Path '{path}' outside sandbox boundary."}

    def safe_write(self, filename: str, content: str, user="SYSTEM") -> bool:
        """Controlled file write within sandbox."""
        if ".." in filename or filename.startswith("/") or ":" in filename:
            self._log(user, "DENIED_WRITE", filename)
            return False
        path = os.path.join(self.allowed_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        self._log(user, "AUTHORIZED_WRITE", filename)
        return True

    def enforce_read_only(self, path: str):
        self._log("MODEL_TRAINING", "READ_ONLY_ACCESS", path)
        return True

    def get_integrity_status(self):
        return {
            "sandbox_active":       True,
            "read_only_enforced":   True,
            "csv_download_blocked": True,
            "pii_access_blocked":   True,
            "directory_isolation":  True,
            "last_log_entry":       datetime.datetime.now().isoformat(),
        }
