import time

from swiftclient.service import SwiftService, ClientException


def download_object_from_object_store(
    service: SwiftService,
    container: str,
    object_path: str,
    output_directory: str,
    number_of_attempts: int = 5,
):

    for attempt in range(number_of_attempts):
        result = next(
            service.download(
                container=container,
                objects=[object_path],
                options={"out_directory": output_directory},
            )
        )

        if result["success"]:
            print(f"[blast_execute_task] downloaded file {result["path"]}")
            break

        if "error" in result and isinstance(result["error"], ClientException):
            time.sleep(2)
            continue

    return {
        "output_path": result["path"] if "path" in result else None,
        "error": result["error"] if "error" in result else None,
    }
