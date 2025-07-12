from __future__ import annotations

import aiohttp
import os
import requests

from typing import Optional


class NoAuthException(Exception):
    pass


class SwiftNotFoundException(Exception):
    pass


class SwiftClient:
    def __init__(
        self,
        openstack_auth_url: Optional[str] = os.environ.get("OS_AUTH_URL"),
        application_credential_id: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_ID"
        ),
        application_credential_secret: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_SECRET"
        ),
    ):
        if not (
            openstack_auth_url
            and application_credential_id
            and application_credential_secret
        ):
            raise NoAuthException(
                "openstack_auth_url, application_credential_id and application_credential_secret must be provided"
            )

        auth_body = {
            "auth": {
                "identity": {
                    "methods": ["application_credential"],
                    "application_credential": {
                        "id": application_credential_id,
                        "secret": application_credential_secret,
                    },
                }
            }
        }

        token_response = requests.post(
            f"{openstack_auth_url}/v3/auth/tokens",
            json=auth_body,
            headers={"Content-Type": "application/json"},
        )


class AsyncSwiftClient:
    def __init__(
        self, auth_token: str, session: aiohttp.ClientSession, swift_public_url: str
    ) -> None:
        self.auth_token = auth_token
        self.session = session
        self.public_url = swift_public_url

    @classmethod
    async def create(
        cls,
        openstack_auth_url: Optional[str] = os.environ.get("OS_AUTH_URL"),
        application_credential_id: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_ID"
        ),
        application_credential_secret: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_SECRET"
        ),
    ) -> AsyncSwiftClient:
        if not (
            openstack_auth_url
            and application_credential_id
            and application_credential_secret
        ):
            raise NoAuthException(
                "openstack_auth_url, application_credential_id and application_credential_secret must be provided"
            )

        auth_body = {
            "auth": {
                "identity": {
                    "methods": ["application_credential"],
                    "application_credential": {
                        "id": application_credential_id,
                        "secret": application_credential_secret,
                    },
                }
            }
        }

        async with aiohttp.ClientSession() as temp_session:
            async with temp_session.post(
                f"{openstack_auth_url}/v3/auth/tokens",
                json=auth_body,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status != 201:
                    raise NoAuthException(
                        f"Authentication failed: {resp.status} - {await resp.text()}"
                    )
                token = resp.headers.get("X-Subject-Token")

                json_response = await resp.json()

                try:
                    swift_service = [
                        service
                        for service in json_response["token"]["catalog"]
                        if service["type"] == "object-store"
                    ][0]
                except (IndexError, KeyError) as _error:
                    raise SwiftNotFoundException(
                        "object-store service was not found in the catalog"
                    )

                try:
                    public_endpoint = [
                        endpoint
                        for endpoint in swift_service["endpoints"]
                        if endpoint["interface"] == "public"
                    ][0]

                    swift_service_url = public_endpoint["url"]
                    print(swift_service_url)

                except (IndexError, KeyError):
                    raise SwiftNotFoundException(
                        "public endpoint was not found for object-store service"
                    )

        # Return a fully initialized instance with a new session
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=100)
        session = aiohttp.ClientSession(
            timeout=timeout, connector=connector, headers={"X-Auth-Token": token}
        )
        return cls(
            auth_token=token, session=session, swift_public_url=swift_service_url
        )

    async def close(self):
        await self.session.close()

    async def container_exists(self, container_name: str) -> bool:
        async with self.session.head(f"{self.public_url}/{container_name}") as response:
            if response.status == 204:
                return True
            elif response.status == 404:
                return False
            else:
                text = await response.text()
                raise Exception(f"Unexpected response: {response.status} - {text}")
