# Kubernetes In-Cluster Auth

A small Python utility for creating an explicit Kubernetes in-cluster `ApiClient` using the ServiceAccount token, Kubernetes API server environment variables, and mounted CA certificate.

The goal is to provide a simple and defensive alternative to relying entirely on `kubernetes.config.load_incluster_config()` when applications need explicit control over how in-cluster authentication is configured.

## Why?

Kubernetes applications running inside a Pod normally use:

```python
from kubernetes import config

config.load_incluster_config()
```

This is the recommended and preferred approach for normal applications.

However, a client-library regression can cause the ServiceAccount token to be configured under a key that is not consumed by the generated authentication code.

This happened with the Kubernetes Python client v36.0.0, where `load_incluster_config()` populated:

```python
api_key["authorization"]
```

while the generated `auth_settings()` expected:

```python
api_key["BearerToken"]
```

As a result, the token could fail to appear in the HTTP `Authorization` header, causing authenticated Kubernetes API requests to fail with `401 Unauthorized`.

See the upstream discussion:

- Kubernetes Python client issue #2584:\
  [https://github.com/kubernetes-client/python/issues/2584](https://github.com/kubernetes-client/python/issues/2584)

## Approach

This project constructs the Kubernetes client configuration explicitly:

```text
Kubernetes Pod
     |
     +-- KUBERNETES_SERVICE_HOST
     |
     +-- KUBERNETES_SERVICE_PORT
     |
     +-- /var/run/secrets/kubernetes.io/serviceaccount/token
     |
     +-- /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
     |
     v
Explicit client.Configuration()
     |
     +-- API server
     +-- BearerToken
     +-- CA certificate
     +-- TLS verification enabled
     |
     v
Kubernetes ApiClient
```

## Features

- Explicit Kubernetes API server configuration
- Explicit ServiceAccount Bearer token configuration
- Explicit CA certificate configuration
- TLS certificate verification remains enabled
- Validation of required in-cluster files
- Validation of required Kubernetes environment variables
- No hard-coded credentials
- Suitable for Kubernetes Pods using ServiceAccounts
- Easy to test independently of a live Kubernetes cluster

## Installation

```bash
pip install kubernetes-incluster-auth
```

> The package name may change if this project is published to PyPI. For repository usage, the source package can be installed directly from GitHub.

## Usage

```python
from kubernetes import client

from kubernetes_incluster_auth import create_incluster_client


api_client = create_incluster_client()

core_api = client.CoreV1Api(api_client)

pods = core_api.list_pod_for_all_namespaces(limit=5)

for pod in pods.items:
    print(
        pod.metadata.namespace,
        pod.metadata.name,
    )
```

## Configuration

The implementation uses the standard Kubernetes in-cluster locations.

### API server

```text
KUBERNETES_SERVICE_HOST
KUBERNETES_SERVICE_PORT
```

The API server URL is constructed as:

```text
https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT
```

### ServiceAccount token

```text
/var/run/secrets/kubernetes.io/serviceaccount/token
```

### CA certificate

```text
/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## Security

This project does not disable TLS certificate verification.

The configuration explicitly enables:

```python
configuration.verify_ssl = True
```

and uses the Kubernetes ServiceAccount CA certificate:

```python
configuration.ssl_ca_cert = CA_CERT_PATH
```

The ServiceAccount token is read from the filesystem and is never logged or printed.

## Important: this is not a replacement for the upstream fix

**This** project is an application-level defensive configuration pattern.

It does not attempt to modify or replace the Kubernetes Python client's upstream implementation.

For standard applications, `load_incluster_config()` remains the preferred approach.

This project is useful when an application requires explicit control over authentication configuration or needs an additional defensive layer around client-library upgrades.

## When should you use this?

Use the standard approach when possible:

```python
from kubernetes import config

config.load_incluster_config()
```

Consider explicit configuration when:

- your application must control the authentication configuration directly;
- you need to validate the ServiceAccount credentials during application startup;
- you need deterministic configuration across client-library versions;
- you have experienced authentication regressions during Kubernetes client upgrades;
- you want automated tests around the in-cluster configuration.

## What this project does not do

This project does not:

- disable TLS verification;
- bypass Kubernetes RBAC;
- generate ServiceAccount tokens;
- modify Kubernetes API server configuration;
- grant additional permissions;
- replace Kubernetes authentication or authorization.

The ServiceAccount still needs appropriate RBAC permissions.

## Relationship to Kubernetes Python client issue #2584

The project was created after encountering the same class of in-cluster authentication failure documented in:

[https://github.com/kubernetes-client/python/issues/2584](https://github.com/kubernetes-client/python/issues/2584)

The issue describes a mismatch between the key populated by `load_incluster_config()` and the key expected by the generated authentication configuration.

The purpose of this repository is to document an application-level defensive approach and provide a reusable, testable implementation.

## Testing

Run:

```bash
pytest -v
```

The tests verify:

- API server configuration
- Bearer token configuration
- CA certificate configuration
- TLS verification
- missing token handling
- missing CA handling
- missing Kubernetes environment variables

## Kubernetes deployment example

A Pod using this library still requires a ServiceAccount.

Example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubernetes-incluster-auth-example
spec:
  serviceAccountName: example-service-account
  containers:
    - name: application
      image: your-image:latest
```

The ServiceAccount token and CA certificate are provided by Kubernetes according to the Pod's ServiceAccount configuration.

## Design principle

The primary design principle is:

> Make authentication configuration explicit and fail early when required credentials are unavailable.

Instead of discovering a configuration problem only after receiving:

```text
401 Unauthorized
```

or:

```text
403 Forbidden
```

the application validates the required configuration during client initialization.

## Disclaimer

This is an independent community project and is not affiliated with or endorsed by the Kubernetes project.

Kubernetes and the Kubernetes logo are trademarks of The Linux Foundation.
