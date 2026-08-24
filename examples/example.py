from kubernetes_incluster_auth import create_incluster_client
from kubernetes import client


def main() -> None:
    api_client = create_incluster_client()

    core_api = client.CoreV1Api(api_client)

    pods = core_api.list_pod_for_all_namespaces(limit=5)

    for pod in pods.items:
        print(pod.metadata.namespace, pod.metadata.name)

    services = core_api.list_service_for_all_namespaces(limit=5)
    for service in services.items:
        print(service.metadata.namespace, service.metadata.name)


if __name__ == "__main__":
    main()