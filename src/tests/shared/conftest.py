from swiftclient.service import SwiftDeleteObject, SwiftService
from pathlib import Path

import pytest

from shared.services.database import SafeDuckDbConnection
from shared.services.openstack import get_swift_service
from shared.config import backend_config


@pytest.fixture(scope="session")
def allowed_path():
    return Path(__file__).parent.resolve()


@pytest.fixture(scope="session")
def selectable_file(allowed_path: Path):
    file_to_write = allowed_path / "test_example.txt"
    file_to_write.write_text("id\tcontent\n1\tYou got it\n")
    yield file_to_write
    file_to_write.unlink()


@pytest.fixture(scope="session")
def safe_database_connection(allowed_path: Path):
    with SafeDuckDbConnection(
        ":memory:",
        read_only=False,
        allowed_directories=[allowed_path.resolve().as_posix()],
    ) as connection:
        yield connection


@pytest.fixture(scope="session")
def swift_service():
    return get_swift_service(env=backend_config)


@pytest.fixture(scope="session")
def file_to_upload(swift_service: SwiftService):
    path_to_file = Path(__file__).parent / "test_file.txt"
    path_to_file.write_text("This is some test text\n")

    yield path_to_file

    object_to_delete = SwiftDeleteObject(object_name=path_to_file.name)

    result = swift_service.delete(
        container="pg-testing-fixtures",
        objects=[
            object_to_delete,
        ],
    )

    for res in result:
        print(res)

    path_to_file.unlink()
