from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataAsset:
    id: str
    bucket_uri: str
    kind: str | None = None
    source_url: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class BuildStep:
    id: str
    command: str
    reads: dict[str, DataAsset]
    writes: dict[str, DataAsset]
    body_path: str | None = None


@dataclass(frozen=True)
class AnnotationLink:
    annotation_id: str
    role: str
    asset_id: str


@dataclass(frozen=True)
class Catalog:
    assets: dict[str, DataAsset]
    steps: dict[str, BuildStep]
    annotation_links: list[AnnotationLink]


class CatalogBuilder:
    def __init__(self) -> None:
        self.assets: dict[str, DataAsset] = {}
        self.steps: dict[str, BuildStep] = {}
        self.annotation_links: list[AnnotationLink] = []

    def static_asset(
        self,
        *,
        id: str,
        bucket_uri: str,
        kind: str | None = None,
        source_url: str | None = None,
        description: str | None = None,
    ) -> DataAsset:
        if id in self.assets:
            raise ValueError(f"Duplicate asset id: {id}")
        asset = DataAsset(
            id=id,
            bucket_uri=bucket_uri,
            kind=kind,
            source_url=source_url,
            description=description,
        )
        self.assets[id] = asset
        return asset

    def derived_asset(
        self,
        *,
        id: str,
        bucket_uri: str,
        kind: str | None = None,
        description: str | None = None,
    ) -> DataAsset:
        if id in self.assets:
            raise ValueError(f"Duplicate asset id: {id}")
        asset = DataAsset(
            id=id,
            bucket_uri=bucket_uri,
            kind=kind,
            description=description,
        )
        self.assets[id] = asset
        return asset

    def step(
        self,
        *,
        id: str,
        command: str,
        reads: dict[str, DataAsset],
        writes: dict[str, DataAsset],
        body_path: str | None = None,
    ) -> BuildStep:
        if id in self.steps:
            raise ValueError(f"Duplicate step id: {id}")
        bs = BuildStep(
            id=id,
            command=command,
            reads=reads,
            writes=writes,
            body_path=body_path,
        )
        self.steps[id] = bs
        return bs

    def annotation_link(
        self,
        *,
        annotation_id: str,
        role: str,
        asset: DataAsset,
    ) -> None:
        self.annotation_links.append(
            AnnotationLink(
                annotation_id=annotation_id,
                role=role,
                asset_id=asset.id,
            )
        )

    def build(self) -> Catalog:
        for step in self.steps.values():
            for role, asset in (
                *step.reads.items(),
                *step.writes.items(),
            ):
                if asset.id not in self.assets:
                    raise ValueError(
                        f"Step {step.id!r} references unknown "
                        f"asset {asset.id!r} in role {role!r}"
                    )
        for link in self.annotation_links:
            if link.asset_id not in self.assets:
                raise ValueError(
                    f"Annotation link for "
                    f"{link.annotation_id!r} references "
                    f"unknown asset {link.asset_id!r}"
                )
        return Catalog(
            assets=dict(self.assets),
            steps=dict(self.steps),
            annotation_links=list(self.annotation_links),
        )
