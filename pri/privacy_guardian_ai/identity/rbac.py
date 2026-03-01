class Roles:
    STUDENT = "student"
    ADMIN = "admin"
    SECURITY_OFFICER = "security_officer"

class RBAC:
    PERMISSIONS = {
        Roles.STUDENT: ["view_own_risk", "view_own_logs"],
        Roles.ADMIN: ["view_aggregated_risk", "request_individual_access", "trigger_retrain"],
        Roles.SECURITY_OFFICER: ["view_security_logs", "adjust_privacy_params", "view_mia_metrics"]
    }

    @staticmethod
    def has_permission(role, permission):
        return permission in RBAC.PERMISSIONS.get(role, [])
