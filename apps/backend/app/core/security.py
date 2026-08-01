import hashlib
import secrets


def generate_secret_key(length: int = 64) -> str:
    return secrets.token_hex(length)


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()