from privacy_guardian_ai.identity.rbac import RBAC, Roles
from privacy_guardian_ai.sandbox.audit_logger import AuditLogger

class AccessController:
    """Centralized interceptor for all data and model access"""
    def __init__(self):
        self.logger = AuditLogger()

    def request_access(self, user_id, role, permission, resource_id=None, reason="No reason provided"):
        """Enforce RBAC and log the attempt"""
        if RBAC.has_permission(role, permission):
            # Log successful access
            self.logger.log_event(user_id, role, f"AUTHORIZED_{permission.upper()}", reason, resource_id)
            return True, "Access Authorized"
        else:
            # Log denied access
            self.logger.log_event(user_id, role, f"DENIED_{permission.upper()}", "Insufficient privileges", resource_id)
            return False, "Access Denied: Insufficient roles/permissions."

    def log_sandbox_violation(self, user_id, action, resource):
        """Specifically log suspicious activity within the sandbox"""
        self.logger.log_event(user_id, "SYSTEM", f"SANDBOX_VIOLATION_{action.upper()}", f"Illegal access to {resource}")
