from celery.result import AsyncResult

from task_queue.celery import app

# run the whole setup via docker compose first, then:
app.conf.broker_url = "amqp://guest:guest@localhost:5672//"
app.conf.result_backend = "redis://localhost:6379/0"

# check if task with some id has result, for example
task_id = "dummy-result"
result = AsyncResult(id=task_id, app=app)

if result.status == "SUCCESS":
    value = result.get()
    print(f"{task_id} result was {value}")
