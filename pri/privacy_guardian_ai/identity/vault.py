import json
import os

class IdentityVault:
    def __init__(self, vault_path="privacy_guardian_ai/identity/vault.json"):
        self.vault_path = vault_path
        if os.path.exists(vault_path):
            with open(vault_path, "r") as f:
                self.vault = json.load(f)
        else:
            self.vault = {}
            self._generate_mock_vault()

    def _generate_mock_vault(self):
        """Generate mock student names for IDs 0 to 1499"""
        first_names = ["John", "Jane", "Alex", "Emily", "Chris", "Katie", "Michael", "Sarah", "David", "Laura"]
        last_names = ["Smith", "Doe", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez"]
        
        for i in range(1500):
            name = f"{first_names[i % 10]} {last_names[(i // 10) % 10]}"
            self.vault[str(i)] = {
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}@university.edu"
            }
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        with open(self.vault_path, "w") as f:
            json.dump(self.vault, f, indent=4)

    def get_identity(self, user_id):
        return self.vault.get(str(user_id))

    def get_all_ids(self):
        return list(self.vault.keys())
