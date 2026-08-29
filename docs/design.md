# Design and Rationale

## Problem

Applications running inside Kubernetes commonly initialize the Python Kubernetes client using:

```python
config.load_incluster_config()
```

This is convenient because the client automatically discovers:

* Kubernetes API server
* ServiceAccount token
* CA certificate

However, authentication configuration depends on the internal contract between the in-cluster configuration loader and the generated Kubernetes client's authentication implementation.

A mismatch between these components can result in a valid ServiceAccount token being present on disk but not being attached to outgoing API requests.

## Observed Failure

The failure pattern observed in Kubernetes Python client v36.0.0 was:

```text
ServiceAccount token exists
        |
        v
load_incluster_config()
        |
        v
api_key["authorization"]
        |
        X
auth_settings() expects
api_key["BearerToken"]
        |
        v
Authorization header not generated
        |
        v
Kubernetes API
        |
        v
401 Unauthorized
```

The upstream issue is documented in Kubernetes Python client issue #2584.

## Defensive Design

This project removes the dependency on implicit configuration for the authentication-critical values.

```text
Environment
    |
    +-- KUBERNETES_SERVICE_HOST
    +-- KUBERNETES_SERVICE_PORT
    |
    v
API server URL


Filesystem
    |
    +-- ServiceAccount token
    +-- CA certificate
    |
    v
Credential validation
    |
    v
client.Configuration()
    |
    +-- host
    +-- BearerToken
    +-- ssl_ca_cert
    +-- verify_ssl=True
    |
    v
client.ApiClient
```

## Security Model

The implementation does not weaken TLS verification.

The CA certificate mounted by Kubernetes is used to validate the API server certificate.

The ServiceAccount token is read only when constructing the client.

The token must never be written to application logs.

## Fail-Fast Behavior

The implementation validates:

1. `KUBERNETES_SERVICE_HOST`
2. `KUBERNETES_SERVICE_PORT`
3. ServiceAccount token
4. CA certificate

before returning the Kubernetes client.

This makes configuration failures visible during initialization rather than during a later Kubernetes API operation.

## Compatibility

The implementation intentionally uses public `kubernetes.client.Configuration` and `kubernetes.client.ApiClient` APIs rather than modifying Kubernetes client internals.

This keeps the implementation small and easier to test.

## Scope

This project focuses only on client-side in-cluster configuration.

It does not attempt to solve:

* Kubernetes RBAC configuration
* ServiceAccount provisioning
* token rotation
* Kubernetes API server authentication
* Kubernetes API server authorization
* TLS certificate generation
* cluster security configuration

## Future Improvements

Potential future work:

* integration tests running inside Kubernetes
* support for projected ServiceAccount tokens
* token refresh/rotation handling
* compatibility matrix across Kubernetes Python client versions
* optional health-check API
* packaging for PyPI
* CI testing against supported Python versions
