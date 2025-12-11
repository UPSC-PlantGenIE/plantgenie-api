enable_utc = True
timezone = 'Europe/Stockholm'
task_serializer = "json"
broker_url = "amqp://guest:guest@localhost:5672/celery_testing"
result_backend = "redis://localhost:6379/0"
task_compression = "zlib"
