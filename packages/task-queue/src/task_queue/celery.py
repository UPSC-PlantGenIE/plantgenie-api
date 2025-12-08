from celery import Celery

app = Celery(
    "task-queue",
    broker="amqp://guest:guest@localhost:5672/celery_testing",
    backend="redis://localhost:6379/0",
)

app.autodiscover_tasks(
    ["task_queue", "task_queue.blast", "task_queue.enrichment"]
)
