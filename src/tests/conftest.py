from pathlib import Path

import pytest

from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage
from testcontainers.core.network import Network
from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.redis import RedisContainer

from task_queue.celery import app


@pytest.fixture(scope="package")
def host_data_directory() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="package")
def network():
    network = Network()
    network.create()

    yield network

    network.remove()


@pytest.fixture(scope="package")
def redis_container(network: Network):
    container = RedisContainer(image="redis:8.4-alpine")
    container.with_network(network)
    container.with_network_aliases("redis-service")
    container.start()

    yield container

    container.stop()


@pytest.fixture(scope="package")
def rabbitmq_container(network: Network):
    container = RabbitMqContainer(
        image="rabbitmq:4.2-alpine",
        vhost="celery_testing",
        username="guest",
        password="guest",
        port=5672,
    )
    container.with_network(network)
    container.with_network_aliases("rabbitmq-service")
    container.start()

    yield container

    container.stop()


@pytest.fixture(scope="package")
def celery_image():
    image = DockerImage(
        path=Path(__file__).parent.parent.parent,
        dockerfile_path=(
            Path(__file__).parent.parent.parent
            / "packages"
            / "task-queue"
            / "Dockerfile"
        ),
        tag="celery-worker:testing",
        clean_up=False,
    )
    image.build()

    yield image

    image.remove(force=True)


@pytest.fixture(scope="package")
def celery_container(
    network: Network,
    celery_image: DockerImage,
    host_data_directory: Path,
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer
):
    container = DockerContainer(str(celery_image))
    container.with_network(network)
    container.with_env(
        "CELERY_BROKER_URL",
        "amqp://guest:guest@rabbitmq-service:5672/celery_testing",
    )
    container.with_env(
        "CELERY_RESULT_BACKEND",
        "redis://redis-service:6379/0",
    )
    container.with_volume_mapping(
        host=host_data_directory, container="/tests", mode="rw"
    )

    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="package")
def configured_celery_test_app(
    rabbitmq_container: RabbitMqContainer, redis_container: RedisContainer
):
    rmq_host = rabbitmq_container.get_container_host_ip()
    rmq_port = rabbitmq_container.get_exposed_port(5672)

    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)

    message_broker_url = (
        f"amqp://guest:guest@{rmq_host}:{rmq_port}/celery_testing"
    )
    result_backend_url = f"redis://{redis_host}:{redis_port}/0"

    app.conf.update(
        broker_url=message_broker_url,
        result_backend=result_backend_url,
    )

    yield app

    app.conf.clear()
    app.control.shutdown()
