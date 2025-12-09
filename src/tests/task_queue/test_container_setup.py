import pika
import redis

from task_queue.tasks import add


def test_redis_container_running(redis_container):
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        password=redis_container.password,
        decode_responses=True,
    )

    client.set("ping", "pong")
    assert client.get("ping") == "pong"


def test_rabbitmq_container_running(rabbitmq_container):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_container.get_container_host_ip(),
            port=rabbitmq_container.get_exposed_port(5672),
            credentials=pika.PlainCredentials(
                username="guest", password="guest"
            ),
            virtual_host="celery_testing",
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue="healthcheck", durable=False)
    connection.close()


def test_celery_add_task(
    rabbitmq_container,
    redis_container,
    celery_container,
    configured_celery_test_app,
):
    async_result = add.delay(4, 6)
    result = async_result.get(timeout=10)

    assert result == 10
