from celery import Celery

app = Celery("task-queue")

app.config_from_object("task_queue.config")

app.autodiscover_tasks(
    ["task_queue", "task_queue.blast", "task_queue.enrichment"]
)
