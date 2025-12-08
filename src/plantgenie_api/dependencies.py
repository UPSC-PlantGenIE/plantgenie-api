from typing import Dict
from dotenv import dotenv_values
from swiftclient.service import SwiftService

backend_config = {**dotenv_values(".env.shared")}


def get_swift_service(env: Dict[str, str | None]) -> SwiftService:
    return SwiftService(
        options={
            "auth_type": env.get("OS_AUTH_TYPE"),
            "auth_url": env.get("OS_AUTH_URL"),
            "identity_api_version": env.get("OS_IDENTITY_API_VERSION"),
            "region_name": env.get("OS_REGION_NAME"),
            "interface": env.get("OS_INTERFACE"),
            "application_credential_id": env.get(
                "OS_APPLICATION_CREDENTIAL_ID"
            ),
            "application_credential_secret": env.get(
                "OS_APPLICATION_CREDENTIAL_SECRET"
            ),
        }
    )


# swift_service = SwiftService(
#     options={
#         "auth_type": env.get("OS_AUTH_TYPE"),
#         "auth_url": env.get("OS_AUTH_URL"),
#         "identity_api_version": env.get("OS_IDENTITY_API_VERSION"),
#         "region_name": env.get("OS_REGION_NAME"),
#         "interface": env.get("OS_INTERFACE"),
#         "application_credential_id": env.get(
#             "OS_APPLICATION_CREDENTIAL_ID"
#         ),
#         "application_credential_secret": env.get(
#             "OS_APPLICATION_CREDENTIAL_SECRET"
#         ),
#     }
# )
