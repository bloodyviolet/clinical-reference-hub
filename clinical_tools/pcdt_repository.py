from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import re
import unicodedata

from clinical_tools.pcdt_metadata import (
    validate_manifest,
    validate_registry,
)


_SHA256_RE = re.compile(
    r"^[0-9a-f]{64}$"
)


def _normalise(
    value: object,
) -> str:
    text = unicodedata.normalize(
        "NFD",
        str(
            value
            or ""
        ),
    )

    return "".join(
        character
        for character in text
        if unicodedata.category(
            character
        )
        != "Mn"
    ).casefold()


def _is_current_version(
    version: dict[str, Any],
) -> bool:
    return not bool(
        version.get(
            "superseded_by"
        )
    )


class PCDTRepository:
    """
    Read-only PCDT metadata and immutable-document repository.

    Deliberate clinical firewall:
    this component does not determine diagnosis, eligibility,
    treatment selection, medication dosing, treatment sequencing,
    monitoring schedules, or stopping rules.
    """

    def __init__(
        self,
        registry: dict[str, Any],
        manifest: dict[str, Any],
    ) -> None:
        manifest_summary = validate_manifest(
            manifest
        )

        registry_summary = validate_registry(
            registry,
            manifest=manifest,
        )

        self._registry = registry
        self._manifest = manifest

        self._pcdts = tuple(
            registry[
                "pcdts"
            ]
        )

        self._pcdt_by_id = {
            pcdt[
                "pcdt_id"
            ]:
            pcdt
            for pcdt
            in self._pcdts
        }

        self._objects = tuple(
            manifest[
                "objects"
            ]
        )

        self._object_by_id = {
            obj[
                "archive_object_id"
            ]:
            obj
            for obj
            in self._objects
        }

        self._object_by_digest = {
            obj[
                "sha256"
            ]:
            obj
            for obj
            in self._objects
        }

        self._servable_object_ids: set[str] = set()

        for pcdt in self._pcdts:
            for version in pcdt[
                "approval_versions"
            ]:
                for document in version[
                    "documents"
                ]:
                    object_id = document.get(
                        "archive_object_id"
                    )

                    if (
                        object_id
                        and document.get(
                            "availability_state"
                        )
                        == "archived"
                        and document.get(
                            "redistribution_state"
                        )
                        == "public_verified"
                    ):
                        archive_object = (
                            self._object_by_id.get(
                                object_id
                            )
                        )

                        if (
                            archive_object
                            and archive_object.get(
                                "availability_state"
                            )
                            == "archived"
                            and archive_object.get(
                                "redistribution_state"
                            )
                            == "public_verified"
                        ):
                            self._servable_object_ids.add(
                                object_id
                            )

        self._summary = {
            "pcdt_count":
                registry_summary[
                    "pcdt_count"
                ],

            "approval_version_count":
                registry_summary[
                    "approval_version_count"
                ],

            "logical_document_count":
                registry_summary[
                    "document_count"
                ],

            "archive_object_count":
                manifest_summary[
                    "object_count"
                ],

            "servable_archive_object_count":
                len(
                    self._servable_object_ids
                ),
        }


    @classmethod
    def from_files(
        cls,
        registry_path: Path,
        manifest_path: Path,
    ) -> "PCDTRepository":
        registry = json.loads(
            registry_path.read_text(
                encoding="utf-8"
            )
        )

        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

        return cls(
            registry,
            manifest,
        )


    def summary(
        self,
    ) -> dict[str, int]:
        return dict(
            self._summary
        )


    def _search_values(
        self,
        pcdt: dict[str, Any],
    ) -> tuple[object, ...]:
        values: list[object] = [
            pcdt.get(
                "pcdt_id"
            ),

            pcdt.get(
                "canonical_title_pt"
            ),

            pcdt.get(
                "title_en"
            ),

            *pcdt.get(
                "aliases_pt",
                [],
            ),

            *pcdt.get(
                "historical_titles_pt",
                [],
            ),
        ]

        for version in pcdt[
            "approval_versions"
        ]:
            values.extend(
                (
                    version.get(
                        "approval_version_id"
                    ),

                    version.get(
                        "act_type"
                    ),

                    version.get(
                        "act_number"
                    ),

                    version.get(
                        "act_year"
                    ),

                    version.get(
                        "raw_approval_citation"
                    ),
                )
            )

            for document in version[
                "documents"
            ]:
                values.extend(
                    (
                        document.get(
                            "document_id"
                        ),

                        document.get(
                            "document_role"
                        ),

                        document.get(
                            "source_link_text"
                        ),
                    )
                )

        return tuple(
            values
        )


    def _index_item(
        self,
        pcdt: dict[str, Any],
    ) -> dict[str, Any]:
        versions = pcdt[
            "approval_versions"
        ]

        current_versions = [
            version
            for version in versions
            if _is_current_version(
                version
            )
        ]

        documents = [
            document
            for version in versions
            for document in version[
                "documents"
            ]
        ]

        current_protocols = [
            document
            for version in current_versions
            for document in version[
                "documents"
            ]
            if document.get(
                "document_role"
            )
            == "protocol_text"
        ]

        return {
            "pcdt_id":
                pcdt[
                    "pcdt_id"
                ],

            "canonical_title_pt":
                pcdt[
                    "canonical_title_pt"
                ],

            "title_en":
                pcdt.get(
                    "title_en"
                ),

            "aliases_pt":
                list(
                    pcdt.get(
                        "aliases_pt",
                        [],
                    )
                ),

            "historical_titles_pt":
                list(
                    pcdt.get(
                        "historical_titles_pt",
                        [],
                    )
                ),

            "approval_state":
                pcdt[
                    "approval_state"
                ],

            "discovery_state":
                pcdt[
                    "discovery_state"
                ],

            "approval_version_count":
                len(
                    versions
                ),

            "current_approval_version_ids":
                [
                    version[
                        "approval_version_id"
                    ]
                    for version
                    in current_versions
                ],

            "document_count":
                len(
                    documents
                ),

            "current_protocol_document_count":
                len(
                    current_protocols
                ),
        }


    def search(
        self,
        *,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        if (
            limit < 1
            or limit > 100
        ):
            raise ValueError(
                "limit must be between 1 and 100."
            )

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        query = str(
            q
            or ""
        ).strip()

        if len(
            query
        ) > 120:
            raise ValueError(
                "Search query cannot exceed 120 characters."
            )

        needle = _normalise(
            query
        )

        if needle:
            selected = [
                pcdt
                for pcdt
                in self._pcdts
                if any(
                    needle
                    in _normalise(
                        value
                    )
                    for value
                    in self._search_values(
                        pcdt
                    )
                )
            ]

        else:
            selected = list(
                self._pcdts
            )

        selected.sort(
            key=lambda item:
                _normalise(
                    item[
                        "canonical_title_pt"
                    ]
                )
        )

        page = selected[
            offset:
            offset + limit
        ]

        return {
            "query":
                query
                or None,

            "total":
                len(
                    selected
                ),

            "limit":
                limit,

            "offset":
                offset,

            "returned":
                len(
                    page
                ),

            "items":
                [
                    self._index_item(
                        item
                    )
                    for item
                    in page
                ],
        }


    def _require_pcdt(
        self,
        pcdt_id: str,
    ) -> dict[str, Any]:
        key = str(
            pcdt_id
            or ""
        ).strip()

        if (
            not key
            or len(
                key
            )
            > 200
        ):
            raise KeyError(
                key
            )

        pcdt = self._pcdt_by_id.get(
            key
        )

        if pcdt is None:
            raise KeyError(
                key
            )

        return pcdt


    def detail(
        self,
        pcdt_id: str,
    ) -> dict[str, Any]:
        pcdt = self._require_pcdt(
            pcdt_id
        )

        metadata = {
            key:
                value
            for key, value
            in pcdt.items()
            if key
            != "approval_versions"
        }

        versions = []

        for version in pcdt[
            "approval_versions"
        ]:
            payload = {
                key:
                    value
                for key, value
                in version.items()
                if key
                != "documents"
            }

            payload[
                "current_version"
            ] = _is_current_version(
                version
            )

            payload[
                "document_count"
            ] = len(
                version[
                    "documents"
                ]
            )

            payload[
                "document_roles"
            ] = sorted(
                {
                    document[
                        "document_role"
                    ]
                    for document
                    in version[
                        "documents"
                    ]
                }
            )

            versions.append(
                payload
            )

        return {
            "pcdt":
                metadata,

            "approval_versions":
                versions,
        }


    def _document_payload(
        self,
        *,
        version: dict[str, Any],
        document: dict[str, Any],
    ) -> dict[str, Any]:
        object_id = document.get(
            "archive_object_id"
        )

        archive_object = (
            self._object_by_id.get(
                object_id
            )
            if object_id
            else None
        )

        digest = (
            archive_object.get(
                "sha256"
            )
            if archive_object
            else None
        )

        qualified = bool(
            object_id
            and object_id
            in self._servable_object_ids
            and isinstance(
                digest,
                str,
            )
            and _SHA256_RE.fullmatch(
                digest
            )
        )

        payload = dict(
            document
        )

        payload.update(
            {
                "approval_version_id":
                    version[
                        "approval_version_id"
                    ],

                "current_version":
                    _is_current_version(
                        version
                    ),

                "archive_sha256":
                    digest,

                "self_hosted_url":
                    (
                        f"/documents/pcdt/{digest}.pdf"
                        if qualified
                        else None
                    ),

                "archive_mime_type":
                    (
                        archive_object.get(
                            "mime_type"
                        )
                        if archive_object
                        else None
                    ),

                "archive_size_bytes":
                    (
                        archive_object.get(
                            "size_bytes"
                        )
                        if archive_object
                        else None
                    ),

                "archive_first_retrieved_at":
                    (
                        archive_object.get(
                            "first_retrieved_at"
                        )
                        if archive_object
                        else None
                    ),

                "archive_last_verified_at":
                    (
                        archive_object.get(
                            "last_verified_at"
                        )
                        if archive_object
                        else None
                    ),

                "archive_license":
                    (
                        archive_object.get(
                            "license"
                        )
                        if archive_object
                        else None
                    ),
            }
        )

        return payload


    def documents(
        self,
        pcdt_id: str,
    ) -> dict[str, Any]:
        pcdt = self._require_pcdt(
            pcdt_id
        )

        items = [
            self._document_payload(
                version=version,
                document=document,
            )
            for version
            in pcdt[
                "approval_versions"
            ]
            for document
            in version[
                "documents"
            ]
        ]

        items.sort(
            key=lambda item: (
                not bool(
                    item[
                        "current_version"
                    ]
                ),

                str(
                    item.get(
                        "document_role",
                        "",
                    )
                ),

                str(
                    item.get(
                        "document_id",
                        "",
                    )
                ),
            )
        )

        return {
            "pcdt_id":
                pcdt[
                    "pcdt_id"
                ],

            "returned":
                len(
                    items
                ),

            "items":
                items,
        }


    def _manifest_object(
        self,
        digest: str,
    ) -> dict[str, Any]:
        value = str(
            digest
            or ""
        )

        if not _SHA256_RE.fullmatch(
            value
        ):
            raise ValueError(
                "Invalid PCDT archive SHA-256."
            )

        archive_object = (
            self._object_by_digest.get(
                value
            )
        )

        if archive_object is None:
            raise KeyError(
                value
            )

        if (
            archive_object.get(
                "availability_state"
            )
            != "archived"
            or archive_object.get(
                "redistribution_state"
            )
            != "public_verified"
        ):
            raise KeyError(
                value
            )

        expected_relative = (
            "objects/sha256/"
            + value[:2]
            + "/"
            + value
            + ".pdf"
        )

        if (
            archive_object.get(
                "local_relative_path"
            )
            != expected_relative
        ):
            raise RuntimeError(
                "PCDT archive manifest path is not canonical."
            )

        return archive_object


    def _servable_object(
        self,
        digest: str,
    ) -> dict[str, Any]:
        archive_object = self._manifest_object(
            digest
        )

        if (
            archive_object[
                "archive_object_id"
            ]
            not in self._servable_object_ids
        ):
            raise KeyError(
                digest
            )

        return archive_object


    def _safe_archive_path(
        self,
        *,
        archive_root: Path,
        archive_object: dict[str, Any],
    ) -> Path:
        resolved_root = archive_root.resolve(
            strict=True
        )

        if not resolved_root.is_dir():
            raise FileNotFoundError(
                str(
                    resolved_root
                )
            )

        candidate = (
            resolved_root
            / archive_object[
                "local_relative_path"
            ]
        ).resolve(
            strict=True
        )

        if resolved_root not in candidate.parents:
            raise RuntimeError(
                "PCDT archive path escaped the configured root."
            )

        if not candidate.is_file():
            raise FileNotFoundError(
                str(
                    candidate
                )
            )

        return candidate


    def resolve_document(
        self,
        digest: str,
        archive_root: Path,
    ) -> tuple[
        Path,
        dict[str, Any],
    ]:
        archive_object = self._servable_object(
            digest
        )

        path = self._safe_archive_path(
            archive_root=archive_root,
            archive_object=archive_object,
        )

        stat_result = path.stat()

        if (
            stat_result.st_size
            != archive_object[
                "size_bytes"
            ]
        ):
            raise RuntimeError(
                "PCDT archive object size does not match manifest."
            )

        hasher = sha256()

        with path.open(
            "rb"
        ) as handle:
            signature = handle.read(
                5
            )

            if signature != b"%PDF-":
                raise RuntimeError(
                    "PCDT archive object is not a valid PDF."
                )

            hasher.update(
                signature
            )

            while True:
                block = handle.read(
                    1024 * 1024
                )

                if not block:
                    break

                hasher.update(
                    block
                )

        if (
            hasher.hexdigest()
            != archive_object[
                "sha256"
            ]
        ):
            raise RuntimeError(
                "PCDT archive object SHA-256 does not match manifest."
            )

        return (
            path,
            archive_object,
        )


    def validate_archive_root(
        self,
        archive_root: Path,
        *,
        verify_hashes: bool,
    ) -> dict[str, int]:
        resolved_root = archive_root.resolve(
            strict=True
        )

        if not resolved_root.is_dir():
            raise RuntimeError(
                "Configured PCDT archive root is not a directory."
            )

        checked = 0

        for archive_object in self._objects:
            digest = archive_object[
                "sha256"
            ]

            archive_object = self._manifest_object(
                digest
            )

            path = self._safe_archive_path(
                archive_root=resolved_root,
                archive_object=archive_object,
            )

            stat_result = path.stat()

            if (
                stat_result.st_size
                != archive_object[
                    "size_bytes"
                ]
            ):
                raise RuntimeError(
                    "PCDT archive object size mismatch: "
                    + digest
                )

            with path.open(
                "rb"
            ) as handle:
                if handle.read(
                    5
                ) != b"%PDF-":
                    raise RuntimeError(
                        "PCDT archive object is not a PDF: "
                        + digest
                    )

            if verify_hashes:
                hasher = sha256()

                with path.open(
                    "rb"
                ) as handle:
                    while True:
                        block = handle.read(
                            1024 * 1024
                        )

                        if not block:
                            break

                        hasher.update(
                            block
                        )

                if (
                    hasher.hexdigest()
                    != digest
                ):
                    raise RuntimeError(
                        "PCDT archive object hash mismatch: "
                        + digest
                    )

            checked += 1

        return {
            "object_count":
                checked,
        }
