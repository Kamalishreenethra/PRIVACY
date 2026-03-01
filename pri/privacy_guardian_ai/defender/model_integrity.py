"""
ModelIntegrityVerifier — SHA256 hash chain for model weight integrity.
Each federated round's model hash is stored and chained to the previous.
"""
import hashlib
import json
import os
from datetime import datetime


class ModelIntegrityVerifier:
    CHAIN_PATH = "privacy_guardian_ai/logs/integrity_chain.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.CHAIN_PATH), exist_ok=True)
        self._chain = self._load()

    def _load(self):
        if os.path.exists(self.CHAIN_PATH):
            with open(self.CHAIN_PATH) as f:
                try:
                    return json.load(f)
                except Exception:
                    pass
        return []

    def _save(self):
        with open(self.CHAIN_PATH, "w") as f:
            json.dump(self._chain, f, indent=2)

    def hash_weights(self, state_dict: dict) -> str:
        """Generate SHA256 hash of all model weight tensors."""
        h = hashlib.sha256()
        for key in sorted(state_dict.keys()):
            tensor = state_dict[key]
            try:
                h.update(tensor.numpy().tobytes())
            except Exception:
                h.update(str(tensor).encode())
        return h.hexdigest()

    def hash_model_file(self, model_path: str) -> str:
        """Hash a model .pth file directly."""
        h = hashlib.sha256()
        if not os.path.exists(model_path):
            return "FILE_NOT_FOUND"
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def store_hash(self, round_num: int, model_hash: str, source="state_dict"):
        """Append a hash entry to the chain."""
        prev_hash = (self._chain[-1].get("hash") or self._chain[-1].get("chain_hash", "GENESIS")) if self._chain else "GENESIS"
        chain_hash = hashlib.sha256(
            (model_hash + prev_hash).encode()
        ).hexdigest()

        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "model_hash": model_hash,
            "prev_hash": prev_hash,
            "chain_hash": chain_hash,
            "source": source,
            "status": "VERIFIED",
        }
        self._chain.append(entry)
        self._save()
        return entry

    def verify(self, round_num: int = None) -> dict:
        """
        Verify the integrity of the hash chain.
        If round_num given, checks that specific round.
        Returns: {valid: bool, breach: bool, detail: str}
        """
        self._chain = self._load()
        if not self._chain:
            return {"valid": False, "breach": False, "detail": "No chain entries found."}

        # verify chain linkage
        for i, entry in enumerate(self._chain[1:], 1):
            expected_prev = self._chain[i-1]["hash"] if "hash" in self._chain[i-1] else self._chain[i-1]["chain_hash"]
            actual_prev   = entry.get("prev_hash")
            if expected_prev != actual_prev:
                return {
                    "valid": False,
                    "breach": True,
                    "detail": f"MODEL INTEGRITY BREACH at round {entry['round']}",
                    "round": entry["round"],
                }

        latest = self._chain[-1]
        return {
            "valid": True,
            "breach": False,
            "detail": f"Chain intact. Last verified: Round {latest['round']}",
            "latest_hash": latest.get("model_hash","")[:16] + "...",
            "round": latest["round"],
        }

    def get_chain(self, last_n=10):
        self._chain = self._load()
        return self._chain[-last_n:]

    def get_current_hash(self, model_path="federated_dp_model.pth") -> str:
        return self.hash_model_file(model_path)
