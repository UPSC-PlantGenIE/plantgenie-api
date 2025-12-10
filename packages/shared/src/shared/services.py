from typing import Dict, Optional

from swiftclient.service import SwiftService


def get_swift_service(env: Dict[str, Optional[str]]) -> SwiftService:
    return SwiftService(
        options={
            "os_auth_type": env.get("OS_AUTH_TYPE"),
            "os_auth_url": env.get("OS_AUTH_URL"),
            "os_application_credential_id": env.get(
                "OS_APPLICATION_CREDENTIAL_ID"
            ),
            "os_application_credential_secret": env.get(
                "OS_APPLICATION_CREDENTIAL_SECRET"
            ),
        }
    )
