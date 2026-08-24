"""
Explicit kubernetes in-cluster client configuration.
"""

from __future__ import annotations

import os
from pathlib import Path
from kubernetes import client

DEFAULT_TOKEN_PATH = (
    "/var/run/secrets/kubernetes.io/serviceaccount/token"
)

DEFAULT_CA_CERT_PATH = (
    "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
)


class InClusterConfigurationError(RuntimeError):
    """Raised when the required in-cluster configuration is missing."""

def create_incluster_client(
    token_path: str = DEFAULT_TOKEN_PATH,
    ca_cert_path: str = DEFAULT_CA_CERT_PATH,
) -> client.ApiClient:
    """
    Create a Kubernetes ApiClient using explicit in-cluster configuration.

    The configuration is constructed directly from Kubernetes
    ServiceAccount credentials instead of relying on
    kubernetes.config.load_incluster_config().

    Args:
        token_path: Path to the mounted ServiceAccount token.
        ca_cert_path: Path to the mounted Kubernetes CA certificate.

    Returns:
        Configured kubernetes.client.ApiClient.

    Raises:
        InClusterConfigurationError:
            If required environment variables or ServiceAccount
            files are missing or invalid.
    """

    host = _get_api_server()

    token = _read_required_file(token_path, "ServiceAccount token")

    _validate_required_file(ca_cert_path, "Kubernetes CA certificate")

    configuration = client.Configuration()

    configuration.host = host

    # Explicity configruation the authentication mechanism expected by
    # the generated Kubernetes client.
    configuration.api_key = {"authorization": f"Bearer {token}"}

    # Keep TLS certificate verification enabled for security.
    configuration.ssl_ca_cert = ca_cert_path
    configuration.verify_ssl = True

    return client.ApiClient(configuration)

def _get_api_server() -> str:
    """
    Get the Kubernetes API server URL from the environment.

    Returns:
        The Kubernetes API server URL.
    """

    host = os.environ.get("KUBERNETES_SERVICE_HOST")
    port = os.environ.get("KUBERNETES_SERVICE_PORT")

    if not host:
        raise InClusterConfigurationError(
            "Missing required environment variable: KUBERNETES_SERVICE_HOST"
        )

    if not port:
        raise InClusterConfigurationError(
            "Missing required environment variable: KUBERNETES_SERVICE_PORT"
        )

    return f"https://{host}:{port}"

def _read_required_file(path: str, description: str) -> str:
    """
    Read the contents of a required file.

    Args:
        path: Path to the file.
        description: Description of the file for error messages.

    Returns:
        The contents of the file as a string.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise InClusterConfigurationError(
            f"{description} not found: {path}"
        )

    if not file_path.is_file():
        raise InClusterConfigurationError(
            f"{description} is not a regular file: {path}"
        )

    value = file_path.read_text(encoding="utf-8").strip()

    if not value:
        raise InClusterConfigurationError(
            f"{description} is empty: {path}"
        )

    return value

def _validate_required_file(path: str, description: str) -> None:
    """
    Validate that a required file exists and is a regular file.

    Args:
        path: Path to the file.
        description: Description of the file for error messages.

    Raises:
        InClusterConfigurationError:
            If the file does not exist or is not a regular file.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise InClusterConfigurationError(
            f"{description} not found: {path}"
        )

    if not file_path.is_file():
        raise InClusterConfigurationError(
            f"{description} is not a regular file: {path}"
        )