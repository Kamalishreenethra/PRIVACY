import hashlib
import json
import os
from .rbac import Roles

class AuthSystem:
    def __init__(self, cred_path="privacy_guardian_ai/identity/credentials.json"):
        self.cred_path = cred_path
        if os.path.exists(cred_path):
            with open(cred_path, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}
            self._generate_default_credentials()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_default_credentials(self):
        """Generate default credentials for testing"""
        # Admin
        self.users["admin"] = {
            "password": self._hash_password("admin123"),
            "role": Roles.ADMIN,
            "display_name": "Senior Academic Admin"
        }
        # Security Officer
        self.users["security"] = {
            "password": self._hash_password("sec123"),
            "role": Roles.SECURITY_OFFICER,
            "display_name": "Privacy Compliance Officer"
        }
        # Students (0-9 for demo)
        for i in range(10):
            sid = str(i)
            self.users[sid] = {
                "password": self._hash_password(f"student{sid}"),
                "role": Roles.STUDENT,
                "display_name": f"Student {sid}"
            }
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.cred_path), exist_ok=True)
        with open(self.cred_path, "w") as f:
            json.dump(self.users, f, indent=4)

    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user["password"] == self._hash_password(password):
            return {
                "username": username,
                "role": user["role"],
                "display_name": user["display_name"]
            }
        return None
