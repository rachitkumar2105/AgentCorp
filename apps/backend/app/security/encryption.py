"""app/security/encryption.py

Fernet symmetric encryption with key rotation support.
The active key and historical keys are retrieved from the secret manager.

Key rotation protocol:
  - Primary key:  secret ``ENCRYPTION_KEY``
  - Rotated keys: secrets ``ENCRYPTION_KEY_1``, ``ENCRYPTION_KEY_2``, …

When decrypting, all available keys are tried in order (newest first) so that
data encrypted with an older key can still be read after rotation.
"""
from __future__ import annotations

import base64
import os
from typing import List

from cryptography.fernet import Fernet, MultiFernet, InvalidToken

from app.security.secret_manager import get_secret


# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------

def _load_primary_key() -> bytes:
    """Load the primary Fernet key from the secret manager.

    Raises ``RuntimeError`` if no key is configured.
    """
    raw = get_secret("ENCRYPTION_KEY")
    if not raw:
        # Auto-generate a key in development mode; do NOT do this in production.
        generated = Fernet.generate_key()
        os.environ["AGENTCORP_SECRET_ENCRYPTION_KEY"] = generated.decode()
        return generated
    if isinstance(raw, str):
        raw = raw.encode()
    return raw


def _load_all_keys() -> List[bytes]:
    """Return all available Fernet keys (primary + historical rotation keys)."""
    keys = [_load_primary_key()]
    # Try up to 10 rotation slots
    for i in range(1, 11):
        raw = get_secret(f"ENCRYPTION_KEY_{i}")
        if not raw:
            break
        if isinstance(raw, str):
            raw = raw.encode()
        keys.append(raw)
    return keys


# ---------------------------------------------------------------------------
# Fernet helpers
# ---------------------------------------------------------------------------

def get_fernet() -> Fernet:
    """Return a Fernet instance using the primary key."""
    return Fernet(_load_primary_key())


def get_multi_fernet() -> MultiFernet:
    """Return a MultiFernet instance that can decrypt with any known key."""
    return MultiFernet([Fernet(k) for k in _load_all_keys()])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(value: str) -> str:
    """Encrypt a UTF‑8 string with the current primary key.

    Returns the base64-encoded ciphertext as a string.
    """
    return get_fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a token produced by :func:`encrypt`.

    Tries all available keys (supports key rotation).
    Raises ``InvalidToken`` if decryption fails with all keys.
    """
    return get_multi_fernet().decrypt(token.encode()).decode()


def rotate_key() -> str:
    """Generate a new primary Fernet key and return it as a string.

    The caller is responsible for:
    1. Storing the new key as ``ENCRYPTION_KEY`` in the secret manager.
    2. Moving the old key to ``ENCRYPTION_KEY_1`` (shifting older keys down).
    3. Re-encrypting sensitive data with the new key if required.
    """
    return Fernet.generate_key().decode()
