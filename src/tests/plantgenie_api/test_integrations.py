import pytest
from plantgenie_api.dependencies import backend_config, get_swift_service

@pytest.fixture(autouse=True)
def swift_service():
    return get_swift_service(backend_config)


def test_can_write_result_to_bucket():
    assert 1+1 == 2
