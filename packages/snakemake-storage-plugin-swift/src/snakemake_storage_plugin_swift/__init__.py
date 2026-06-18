from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, cast
from urllib.parse import urlparse

from shared.services.openstack import SwiftClient
from snakemake_interface_common.exceptions import WorkflowError  # noqa
from snakemake_interface_storage_plugins.io import (
    IOCacheStorageInterface,
    Mtime,
)
from snakemake_interface_storage_plugins.settings import (
    StorageProviderSettingsBase,
)
from snakemake_interface_storage_plugins.storage_object import (
    StorageObjectGlob,
    StorageObjectRead,
    StorageObjectWrite,
    retry_decorator,
)
from snakemake_interface_storage_plugins.storage_provider import (  # noqa
    ExampleQuery,
    Operation,
    QueryType,
    StorageProviderBase,
    StorageQueryValidationResult,
)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class StorageProviderSettings(StorageProviderSettingsBase):
    auth_url: Optional[str] = field(
        default=os.environ.get("OS_AUTH_URL"),
        metadata={
            "help": "OpenStack Keystone auth URL (e.g. https://north-1.cloud.snic.se:5000)",
            "env_var": True,
            "required": True,
        },
    )
    application_credential_id: Optional[str] = field(
        default=os.environ.get("OS_APPLICATION_CREDENTIAL_ID"),
        metadata={
            "help": "OpenStack application credential ID",
            "env_var": True,
            "required": True,
        },
    )
    application_credential_secret: Optional[str] = field(
        default=os.environ.get("OS_APPLICATION_CREDENTIAL_SECRET"),
        metadata={
            "help": "OpenStack application credential secret",
            "env_var": True,
            "required": True,
        },
    )
    auth_type: Optional[str] = field(
        default=os.environ.get("OS_AUTH_TYPE", "v3applicationcredential"),
        metadata={
            "help": "OpenStack auth type (default: v3applicationcredential)",
            "env_var": True,
            "required": False,
        },
    )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class StorageProvider(StorageProviderBase):
    @property
    def _settings(self) -> StorageProviderSettings:
        assert self.settings is not None
        return cast(StorageProviderSettings, self.settings)

    def __post_init__(self):
        self._client = SwiftClient(
            openstack_auth_type=self._settings.auth_type
            or "v3applicationcredential",
            openstack_auth_url=self._settings.auth_url,
            application_credential_id=self._settings.application_credential_id,
            application_credential_secret=self._settings.application_credential_secret,
        )

    @property
    def client(self) -> SwiftClient:
        return self._client

    @classmethod
    def example_queries(cls) -> List[ExampleQuery]:
        return [
            ExampleQuery(
                query="swift://my-container/path/to/file.txt",
                description="A file in an OpenStack Swift container",
                type=QueryType.INPUT,
            ),
            ExampleQuery(
                query="swift://my-container/path/to/output.txt",
                description="A file to write into an OpenStack Swift container",
                type=QueryType.OUTPUT,
            ),
        ]

    def rate_limiter_key(self, query: str, operation: Operation) -> Any:
        return self._settings.auth_url

    def default_max_requests_per_second(self) -> float:
        return 10.0

    def use_rate_limiter(self) -> bool:
        return True

    @classmethod
    def is_valid_query(cls, query: str) -> StorageQueryValidationResult:
        try:
            parsed = urlparse(query)
            if parsed.scheme != "swift":
                return StorageQueryValidationResult(
                    query=query,
                    valid=False,
                    reason="Query must start with swift://",
                )
            if not parsed.netloc:
                return StorageQueryValidationResult(
                    query=query,
                    valid=False,
                    reason="Query must include a container name (swift://<container>/...)",
                )
            return StorageQueryValidationResult(query=query, valid=True)
        except Exception as e:
            return StorageQueryValidationResult(
                query=query, valid=False, reason=str(e)
            )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _parse_query(query: str):
    """Return (container, object_name) from a swift://container/object query."""
    parsed = urlparse(query)
    container = parsed.netloc
    object_name = parsed.path.lstrip("/")
    return container, object_name


# ---------------------------------------------------------------------------
# Storage object
# ---------------------------------------------------------------------------


class StorageObject(
    StorageObjectRead, StorageObjectWrite, StorageObjectGlob
):
    def __post_init__(self):
        self._container, self._object_name = _parse_query(self.query)

    # @property
    # def _client(self) -> SwiftClient:
    #     return self.provider.client
    @property
    def _client(self) -> SwiftClient:
        return cast(StorageProvider, self.provider).client

    def _head(self) -> Optional[dict]:
        headers = self._client.head_object(
            self._container, self._object_name
        )
        if headers is None:
            return None
        return {
            "name": self._object_name,
            "mtime": float(headers.get("X-Timestamp", 0.0)),
            "bytes": int(headers.get("Content-Length", 0)),
        }

    async def inventory(self, cache: IOCacheStorageInterface):
        meta = self._head()
        if meta is None:
            cache.exists_in_storage[self.cache_key()] = False
            return
        cache.exists_in_storage[self.cache_key()] = True
        cache.mtime[self.cache_key()] = Mtime(storage=meta["mtime"])
        cache.size[self.cache_key()] = meta["bytes"]

    def get_inventory_parent(self) -> Optional[str]:
        return None

    def local_suffix(self) -> str:
        return f"{self._container}/{self._object_name}"

    def cleanup(self):
        pass

    @retry_decorator
    def exists(self) -> bool:
        return self._head() is not None

    @retry_decorator
    def mtime(self) -> float:
        meta = self._head()
        if meta is None:
            raise FileNotFoundError(
                f"swift://{self._container}/{self._object_name} does not exist"
            )
        return meta["mtime"]

    @retry_decorator
    def size(self) -> int:
        meta = self._head()
        if meta is None:
            raise FileNotFoundError(
                f"swift://{self._container}/{self._object_name} does not exist"
            )
        return meta["bytes"]

    @retry_decorator
    def local_footprint(self) -> int:
        return self.size()

    @retry_decorator
    def retrieve_object(self):
        self._client.download_object(
            container=self._container,
            object=self._object_name,
            output_path=self.local_path(),
        )

    @retry_decorator
    def store_object(self):
        self._client.upload(
            container=self._container,
            object_name=self._object_name,
            path=self.local_path(),
        )

    @retry_decorator
    def remove(self):
        self._client.delete_objects(
            container=self._container,
            objects=[self._object_name],
        )

    @retry_decorator
    def list_candidate_matches(self) -> Iterable[str]:
        from snakemake_interface_storage_plugins.io import (
            get_constant_prefix,
        )

        prefix = get_constant_prefix(self.query)
        _, obj_prefix = _parse_query(prefix)
        objects = self._client.list_objects(self._container)
        for obj in objects:
            name = obj.get("name", "")
            if name.startswith(obj_prefix):
                yield f"swift://{self._container}/{name}"
