"""app/security/secret_manager.py

Abstract secret accessor with multiple backend adapters.

Default backend: environment variables prefixed with AGENTCORP_SECRET_.
Stub adapters for Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager are
provided so that the interfaces exist; switching backends requires only setting
SECRET_BACKEND env var and configuring the appropriate credentials.
"""
from __future__ import annotations

import os
from typing import Optional


# ---------------------------------------------------------------------------
# Backend: Environment Variables (default)
# ---------------------------------------------------------------------------

class _EnvBackend:
    PREFIX = "AGENTCORP_SECRET_"

    def get(self, name: str) -> Optional[str]:
        return os.getenv(f"{self.PREFIX}{name.upper()}")

    def set(self, name: str, value: str) -> None:  # noqa: A003
        # Environment variables cannot be persisted across processes.
        # This is a no-op for the env backend (useful only for tests).
        os.environ[f"{self.PREFIX}{name.upper()}"] = value


# ---------------------------------------------------------------------------
# Stub Backend: HashiCorp Vault
# ---------------------------------------------------------------------------

class _VaultBackend:
    """Stub – real implementation requires hvac client + Vault URL/token."""

    def get(self, name: str) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError(
            "VaultBackend requires hvac client and VAULT_ADDR/VAULT_TOKEN configuration."
        )

    def set(self, name: str, value: str) -> None:  # pragma: no cover  # noqa: A003
        raise NotImplementedError(
            "VaultBackend requires hvac client and VAULT_ADDR/VAULT_TOKEN configuration."
        )


# ---------------------------------------------------------------------------
# Stub Backend: AWS Secrets Manager
# ---------------------------------------------------------------------------

class _AWSBackend:
    """Stub – real implementation requires boto3 + AWS credentials."""

    def get(self, name: str) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError(
            "AWSBackend requires boto3 and AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY configuration."
        )

    def set(self, name: str, value: str) -> None:  # pragma: no cover  # noqa: A003
        raise NotImplementedError(
            "AWSBackend requires boto3 and AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY configuration."
        )


# ---------------------------------------------------------------------------
# Stub Backend: Azure Key Vault
# ---------------------------------------------------------------------------

class _AzureBackend:
    """Stub – real implementation requires azure-keyvault-secrets + credentials."""

    def get(self, name: str) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError(
            "AzureBackend requires azure-keyvault-secrets and AZURE_KEY_VAULT_URL configuration."
        )

    def set(self, name: str, value: str) -> None:  # pragma: no cover  # noqa: A003
        raise NotImplementedError(
            "AzureBackend requires azure-keyvault-secrets and AZURE_KEY_VAULT_URL configuration."
        )


# ---------------------------------------------------------------------------
# Stub Backend: GCP Secret Manager
# ---------------------------------------------------------------------------

class _GCPBackend:
    """Stub – real implementation requires google-cloud-secret-manager + credentials."""

    def get(self, name: str) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError(
            "GCPBackend requires google-cloud-secret-manager and GCP_PROJECT_ID configuration."
        )

    def set(self, name: str, value: str) -> None:  # pragma: no cover  # noqa: A003
        raise NotImplementedError(
            "GCPBackend requires google-cloud-secret-manager and GCP_PROJECT_ID configuration."
        )


# ---------------------------------------------------------------------------
# Backend registry & public API
# ---------------------------------------------------------------------------

_BACKENDS = {
    "env": _EnvBackend,
    "vault": _VaultBackend,
    "aws": _AWSBackend,
    "azure": _AzureBackend,
    "gcp": _GCPBackend,
}


def _get_backend():
    backend_name = os.getenv("SECRET_BACKEND", "env").lower()
    backend_cls = _BACKENDS.get(backend_name, _EnvBackend)
    return backend_cls()


def get_secret(name: str) -> Optional[str]:
    """Retrieve a secret value from the configured backend.

    Args:
        name: Logical name of the secret (e.g., ``"ENCRYPTION_KEY"``).

    Returns:
        The secret value as a string, or ``None`` if not found.
    """
    return _get_backend().get(name)


class SecretManager:
    """Simple wrapper class for secret access.

    Provides an instance-based API compatible with the test's MockSecretManager
    subclass which expects a ``get_secret`` method.
    """

    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret using the module-level ``get_secret`` function.

        Args:
            name: The secret identifier.
        Returns:
            The secret value or ``None`` if not found.
        """
        return get_secret(name)

    def set_secret(self, name: str, value: str) -> None:
        """Store a secret using the module-level ``set_secret`` function.

        Args:
            name: The secret identifier.
            value: The secret value to store.
        """
        set_secret(name, value)


def set_secret(name: str, value: str) -> None:
    """Store a secret value in the configured backend.

    Args:
        name: Logical name of the secret.
        value: Secret value to store.
    """
    _get_backend().set(name, value)
