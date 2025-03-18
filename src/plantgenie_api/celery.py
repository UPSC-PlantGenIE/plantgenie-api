from celery import Celery

# Initialize Celery with the broker and backend URLs.
celery_app = Celery(
    "plantgenie_api",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="redis://redis:6379/0",
)

celery_app.conf.result_expires = 1800

# Optional: Configure task routes or other settings
celery_app.conf.task_routes = {
    "src.plantgenie_api.tasks.*": {"queue": "blast_tasks"},
}

# celery_app.conf.task_routes = {
#     "plantgenie_api.tasks.*": {"queue": "blast_tasks"},
# }


# If you want Celery to automatically discover tasks from a module
# celery_app.autodiscover_tasks(["src.plantgenie_api.tasks"])
celery_app.autodiscover_tasks(["plantgenie_api.tasks"])

if __name__ == '__main__':
    celery_app.start()