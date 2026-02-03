from swiftclient.service import (
    SwiftService,
    SwiftUploadObject,
)
from pathlib import Path


def test_can_upload_object_to_openstack(
    swift_service: SwiftService, file_to_upload: Path
):
    uploadable_object = SwiftUploadObject(
        source=file_to_upload.as_posix(), object_name=file_to_upload.name
    )

    results = swift_service.upload(
        container="pg-service-blast", objects=[uploadable_object,]
    )
    next(results)

    for result in results:
        print(result)
