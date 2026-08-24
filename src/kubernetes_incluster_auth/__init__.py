"""Explicit Kubernetes in-cluster authentication."""

from .client import (
    InClusterConfigurationError,
    create_incluster_client,
)

__all__ = [
    "InClusterConfigurationError",
    "create_incluster_client",
]