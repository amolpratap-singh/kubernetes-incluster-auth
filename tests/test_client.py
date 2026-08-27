from logging import config

import pytest

from kubernetes_incluster_auth.client import (
    InClusterConfigurationError,
    create_incluster_client
)

def test_incluster_configuration(monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    ca_file = tmp_path / "ca.crt"

    token_file.write_text("test-token")
    ca_file.write_text("test-ca")

    monkeypatch.setenv(
        "KUBERNETES_SERVICE_HOST",
        "kubernetes.default.svc"
    )

    monkeypatch.setenv(
        "KUBERNETES_SERVICE_PORT",
        "443"
    )

    api_client = create_incluster_client(
        token_file=str(token_file),
        ca_file=str(ca_file)
    )

    configuration = api_client.configuration

    assert (
        configuration.host == "https://kubernetes.default.svc:443"
    )

    assert (
        configuration.api_key["authorization"] == "Bearer test-token"
    )

    assert configuration.ssl_ca_cert == str(ca_file)
    assert configuration.verify_ssl is True

def test_missing_token(monkeypatch, tmp_path):
    ca_file = tmp_path / "ca.crt"
    ca_file.write_text("test-ca")

    monkeypatch.setenv(
        "KUBERNETES_SERVICE_HOST",
        "kubernetes.default.svc"
    )

    monkeypatch.setenv(
        "KUBERNETES_SERVICE_PORT",
        "443"
    )

    with pytest.raises(InClusterConfigurationError):
        create_incluster_client(
            token_file=str(tmp_path / "missing_token"),
            ca_file=str(ca_file)
        )