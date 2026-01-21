from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import Dict, List, Literal, Optional

import pendulum
import requests
from pendulum import DateTime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from swiftclient.service import SwiftService


class SwiftClientBaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Domain(SwiftClientBaseModel):
    id: str
    name: str


class Role(SwiftClientBaseModel):
    id: str
    name: str


class Endpoint(SwiftClientBaseModel):
    id: str
    interface: str
    region_id: str
    url: str
    region: str


class Service(SwiftClientBaseModel):
    id: str
    type: str
    name: str
    endpoints: List[Endpoint]


class User(SwiftClientBaseModel):
    id: str
    name: str
    domain: Domain
    password_expires_at: Optional[DateTime]

    @field_validator("password_expires_at", mode="before")
    def parse_pendulum(cls, v):
        if isinstance(v, str):
            return pendulum.parse(v)
        return v


class Project(SwiftClientBaseModel):
    id: str
    name: str
    domain: Domain


class ApplicationCredential(SwiftClientBaseModel):
    id: str
    name: str
    restricted: bool


class Token(SwiftClientBaseModel):
    methods: List[str]
    user: User
    audit_ids: List[str]
    expires_at: DateTime
    issued_at: DateTime
    project: Project
    is_domain: bool
    roles: List[Role]
    catalog: List[Service]
    application_credential: ApplicationCredential

    @field_validator("expires_at", "issued_at", mode="before")
    def parse_pendulum(cls, v):
        if isinstance(v, str):
            return pendulum.parse(v)
        return v


class KeystoneTokenResponse(SwiftClientBaseModel):
    token: Token


class SwiftUploadableObject(BaseModel):
    local_path: str
    object_name: str
    content_type: Optional[str] = Field(default="application/octet-stream")
    upload_status: Literal["FAIL", "SUCCESS", "PENDING", "EXISTS"] = Field(
        default="PENDING"
    )
    metadata: Optional[Dict[str, str]] = Field(default={})

    @field_validator("local_path")
    @classmethod
    def ensure_is_path(cls, v: str):
        Path(v).resolve(True)
        return v


class SwiftDeletedObject(BaseModel):
    object_name: str
    status_code: int
    response_content: str


class DownloadedObject(BaseModel):
    object_name: str


class NoAuthException(Exception):
    pass


class SwiftNotFoundException(Exception):
    pass


class TokenExpiredException(Exception):
    pass


def authenticated(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if (
            not getattr(self, "token_expiration_time", None)
            or self.token_expiration_time < pendulum.now()
        ):
            self.authenticate()

        if getattr(self, "is_authenticated", False):
            return method(self, *args, **kwargs)

        raise NoAuthException("This client is not authenticated!")

    return wrapper


class SwiftClient:
    def __init__(
        self,
        openstack_auth_type: Optional[str] = os.environ.get(
            "OS_AUTH_TYPE"
        ),
        openstack_auth_url: Optional[str] = os.environ.get("OS_AUTH_URL"),
        application_credential_id: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_ID"
        ),
        application_credential_secret: Optional[str] = os.environ.get(
            "OS_APPLICATION_CREDENTIAL_SECRET"
        ),
    ):
        if not (
            openstack_auth_type
            and openstack_auth_url
            and application_credential_id
            and application_credential_secret
        ):
            raise NoAuthException(
                "openstack_auth_url, application_credential_id and application_credential_secret must be provided"
            )

        self.openstack_auth_type = openstack_auth_type
        self.openstack_auth_url = openstack_auth_url
        self.application_credential_id = application_credential_id
        self.application_credential_secret = application_credential_secret

        self.auth_body = {
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

        response = requests.post(
            f"{openstack_auth_url}/v3/auth/tokens",
            json=self.auth_body,
            headers={"Content-Type": "application/json"},
        )

        self.token_response = KeystoneTokenResponse(**response.json())

        self.token = response.headers.get("x-subject-token")
        self.token_expiration_time = self.token_response.token.expires_at

        self.is_authenticated = self.token is not None

        self.storage_service: Optional[Service] = None

        for service in self.token_response.token.catalog:
            if service.type == "object-store":
                self.storage_service = service

        if self.storage_service is None:
            raise SwiftNotFoundException(
                "An object storage service was not found"
            )

    def authenticate(self):
        auth_body = {
            "auth": {
                "identity": {
                    "methods": ["application_credential"],
                    "application_credential": {
                        "id": self.application_credential_id,
                        "secret": self.application_credential_secret,
                    },
                }
            }
        }

        response = requests.post(
            f"{self.openstack_auth_url}/v3/auth/tokens",
            json=auth_body,
            headers={"Content-Type": "application/json"},
        )

        self.token_response = KeystoneTokenResponse(**response.json())

        self.token = response.headers.get("x-subject-token")
        self.token_expiration_time = self.token_response.token.expires_at
        self.is_authenticated = self.token is not None

        for service in self.token_response.token.catalog:
            if service.type == "object-store":
                self.storage_service = service

        if self.storage_service is None:
            raise SwiftNotFoundException(
                "An object storage service was not found"
            )

    @property
    def storage_service_url(self) -> Optional[str]:
        if self.storage_service is None:
            return None
        for endpoint in self.storage_service.endpoints:
            if endpoint.interface == "public":
                return endpoint.url

    @authenticated
    def create_container(self, container: str) -> requests.Response | None:
        url = f"{self.storage_service_url}/{container}"
        resp = requests.put(
            url,
            headers={"X-Auth-Token": self.token},
        )

        if resp.status_code in (201, 202, 409):
            # 201 - created
            # 202 - exists but no objects inside
            # 409 - exists with objects inside
            return resp

        if resp.status_code == 404:
            # Should not happen because this method requires authentication
            raise SwiftNotFoundException("Account not found.")

        resp.raise_for_status()

    @authenticated
    def upload_objects(
        self, container, objects: List[SwiftUploadableObject]
    ) -> List[SwiftUploadableObject]:
        """
        objects: list of (local_path, object_name)
        """
        self.create_container(container)

        for obj in objects:
            url = (
                f"{self.storage_service_url}/{container}/{obj.object_name}"
            )
            obj_path = Path(obj.local_path)

            response = requests.put(
                url,
                headers={
                    "X-Auth-Token": self.token,
                    "Content-Type": obj.content_type,
                    "X-Object-Meta-pipeline": "blast",
                },
                data=obj_path.read_bytes(),
            )

            if response.status_code in (201, 202):
                obj.upload_status = (
                    "SUCCESS" if response.status_code == 201 else "EXISTS"
                )

            else:
                obj.upload_status = "FAIL"

        return objects

    @authenticated
    def download_object(
        self, container: str, object: str | List[str], output_path: Path
    ) -> Optional[requests.Response]:
        response = requests.get(
            f"{self.storage_service_url}/{container}/{object}",
            headers={"X-Auth-Token": self.token},
            stream=True,
        )

        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            return response

        response.raise_for_status()

    @authenticated
    def delete_objects(
        self, container: str, objects: List[str]
    ) -> List[SwiftDeletedObject]:
        responses: List[SwiftDeletedObject] = []

        for obj in objects:
            response = requests.delete(
                f"{self.storage_service_url}/{container}/{obj}"
            )

            responses.append(
                SwiftDeletedObject(
                    object_name=obj,
                    status_code=response.status_code,
                    response_content=response.text,
                )
            )

        return responses


def get_swift_service(env: Dict[str, str]) -> SwiftService:
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
