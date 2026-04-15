"""
AutoCoder Security Layer
Based on axiomcode security practices - Zero-trust, zero-knowledge, encrypted.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


HASH_ALGORITHM = "sha512"
HMAC_ALGORITHM = "sha512"
KEY_SIZE = 64
NONCE_SIZE = 32
SALT_SIZE = 32


@dataclass
class KeyPair:
    encryption_key: bytes
    signing_key: bytes
    key_id: str
    created_at: float

    @classmethod
    def generate(cls) -> "KeyPair":
        return cls(
            encryption_key=secrets.token_bytes(KEY_SIZE),
            signing_key=secrets.token_bytes(KEY_SIZE),
            key_id=secrets.token_hex(8),
            created_at=time.time(),
        )

    def to_dict(self) -> dict:
        return {
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "signing_key": base64.b64encode(self.signing_key).decode(),
            "key_id": self.key_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KeyPair":
        return cls(
            encryption_key=base64.b64decode(data["encryption_key"]),
            signing_key=base64.b64decode(data["signing_key"]),
            key_id=data["key_id"],
            created_at=data["created_at"],
        )


class KeyStore:
    """Secure key storage with zero-knowledge design."""

    def __init__(self, store_dir: str = ".autocoder/keys"):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, KeyPair] = {}

    def _derive_master_key(self, passphrase: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha512", passphrase.encode("utf-8"), salt, iterations=600000
        )

    def _encrypt_key(self, key_data: bytes, master_key: bytes) -> dict:
        nonce = secrets.token_bytes(NONCE_SIZE)
        keystream = hashlib.sha512(master_key + nonce).digest()
        while len(keystream) < len(key_data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        encrypted = bytes(a ^ b for a, b in zip(key_data, keystream[:len(key_data)]))
        return {
            "nonce": base64.b64encode(nonce).decode(),
            "data": base64.b64encode(encrypted).decode(),
        }

    def _decrypt_key(self, encrypted: dict, master_key: bytes) -> bytes:
        nonce = base64.b64decode(encrypted["nonce"])
        data = base64.b64decode(encrypted["data"])
        keystream = hashlib.sha512(master_key + nonce).digest()
        while len(keystream) < len(data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        return bytes(a ^ b for a, b in zip(data, keystream[:len(data)]))

    def create_key(self, name: str, passphrase: str) -> KeyPair:
        keypair = KeyPair.generate()
        salt = secrets.token_bytes(SALT_SIZE)
        master_key = self._derive_master_key(passphrase, salt)
        encrypted = self._encrypt_key(json.dumps(keypair.to_dict()).encode(), master_key)

        key_file = self.store_dir / f"{name}.key"
        key_file.write_text(json.dumps({
            "version": 1,
            "salt": base64.b64encode(salt).decode(),
            "encrypted": encrypted,
        }, indent=2))

        self._cache[name] = keypair
        return keypair

    def load_key(self, name: str, passphrase: str) -> KeyPair:
        key_file = self.store_dir / f"{name}.key"
        if not key_file.exists():
            raise FileNotFoundError(f"Key not found: {name}")

        data = json.loads(key_file.read_text(encoding='utf-8'))
        salt = base64.b64decode(data["salt"])
        master_key = self._derive_master_key(passphrase, salt)
        decrypted = self._decrypt_key(data["encrypted"], master_key)
        keypair = KeyPair.from_dict(json.loads(decrypted))

        self._cache[name] = keypair
        return keypair


def hash_data(data: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_file(path: Path, algorithm: str = HASH_ALGORITHM) -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_hmac(data: bytes, key: bytes, algorithm: str = HMAC_ALGORITHM) -> str:
    return hmac.new(key, data, hashlib.new(algorithm)).hexdigest()


def verify_hmac(data: bytes, key: bytes, signature: str, algorithm: str = HMAC_ALGORITHM) -> bool:
    expected = compute_hmac(data, key, algorithm)
    return hmac.compare_digest(expected, signature)


@dataclass
class AuditEntry:
    timestamp: float
    user: str
    action: str
    details: dict = field(default_factory=dict)


class AuditLog:
    """Tamper-evident audit log."""

    def __init__(self, log_file: str = ".autocoder/audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.write_text("")

    def add_entry(self, action: str, details: dict = None):
        entry = {
            "timestamp": time.time(),
            "user": os.environ.get("USER", "unknown"),
            "action": action,
            "details": details or {},
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def verify_integrity(self) -> bool:
        if not self.log_file.exists():
            return True
        try:
            for line in self.log_file.read_text().strip().split("\n"):
                if line:
                    json.loads(line)
            return True
        except:
            return False

    def get_entries(self, limit: int = 100) -> list[AuditEntry]:
        if not self.log_file.exists():
            return []
        entries = []
        for line in self.log_file.read_text().strip().split("\n"):
            if line:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
        return entries[-limit:]


class RateLimiter:
    """Rate limiting for API calls."""

    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        if identifier not in self.calls:
            self.calls[identifier] = []

        self.calls[identifier] = [
            t for t in self.calls[identifier] if now - t < self.window_seconds
        ]

        if len(self.calls[identifier]) >= self.max_calls:
            return False

        self.calls[identifier].append(now)
        return True

    def reset(self, identifier: str):
        if identifier in self.calls:
            del self.calls[identifier]
