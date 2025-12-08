import os
from pathlib import Path

DATABASE_FILENAME = "plantgenie-backend.db"
ENV_DATA_PATH = os.environ.get("DATA_PATH")
DATA_PATH = Path(ENV_DATA_PATH) if ENV_DATA_PATH else None

OS_AUTH_TYPE = os.environ.get("OS_AUTH_TYPE")
OS_AUTH_URL = os.environ.get("OS_AUTH_URL")
OS_IDENTITY_API_VERSION = os.environ.get("OS_IDENTITY_API_VERSION")
OS_REGION_NAME = os.environ.get("OS_REGION_NAME")
OS_INTERFACE = os.environ.get("OS_INTERFACE")
OS_APPLICATION_CREDENTIAL_ID = os.environ.get("OS_APPLICATION_CREDENTIAL_ID")
OS_APPLICATION_CREDENTIAL_SECRET = os.environ.get("OS_APPLICATION_CREDENTIAL_SECRET")
