from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urljoin
import re
import unicodedata


REGISTRY_SCHEMA_VERSION = 1
ARCHIVE_MANIFEST_SCHEMA_VERSION = 1

REGISTRY_ID = "sus-pcdt-registry"

DOCUMENT_TYPE = "pcdt"

APPROVAL_STATES = {
    "approved_listed",
    "explicitly_superseded",
    "withdrawn_explicit",
    "unknown",
}

DEVELOPMENT_STATES = {
    "none_observed",
    "new_document_in_elaboration",
    "update_in_progress",
    "conitec_review",
}

DISCOVERY_STATES = {
    "not_assessed",
    "discovery_in_progress",
    "assessed_no_known_gaps",
    "assessed_with_known_gaps",
}

DOCUMENT_ROLES = {
    "protocol_text",
    "protocol_summary",
    "approval_act",
    "annex",
    "amendment",
    "rectification",
    "recommendation_report",
    "public_consultation_draft",
    "public_consultation_report",
    "ministry_publication",
    "supporting_official_document",
}

REVISION_EVENT_TYPES = {
    "annex_amended",
    "rectified",
    "approval_act_updated",
    "approval_act_republished",
    "official_content_amended",
    "other_official_revision",
}

GAP_REASONS = {
    "official_reference_without_recoverable_asset",
    "upstream_link_dead",
    "retrieval_failed",
    "ambiguous_document_identity",
    "ambiguous_document_role",
    "license_review_pending",
    "historical_source_not_yet_exhausted",
}

AVAILABILITY_STATES = {
    "archived",
    "known_upstream_unavailable",
    "metadata_only",
    "retrieval_failed",
}

REDISTRIBUTION_STATES = {
    "public_verified",
    "archive_only_pending_license_review",
    "not_publicly_redistributable",
    "unknown_requires_review",
}

LICENSE_EVIDENCE_TYPES = {
    "explicit_in_document",
    "inherited_from_official_page",
    "official_license_page",
    "manual_legal_review",
    "unknown",
}

ARCHIVE_OBJECT_RE = re.compile(
    r"^sha256:[0-9a-f]{64}$"
)

SEMANTIC_ID_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)

FORBIDDEN_CLINICAL_KEYS = {
    "patient_eligibility",
    "medication_eligibility",
    "diagnosis_criteria",
    "inclusion_criteria",
    "exclusion_criteria",
    "dosage_recommendation",
    "treatment_recommendation",
    "treatment_sequence",
    "monitoring_schedule",
    "stopping_criteria",
}

DATE_RE = re.compile(
    r"(?P<day>\d{1,2})(?:º|ª)?/"
    r"(?P<month>\d{1,2})/"
    r"(?P<year>\d{4})"
)

PORTARIA_RE = re.compile(
    r"\b"
    r"(?P<act_type>Portaria(?:\s+Conjunta)?)"
    r"\s+"
    r"(?P<units>[A-ZÀ-Ü]+(?:\s*(?:/|[-–—])\s*[A-ZÀ-Ü]+)*)"
    r"\s+n[ºo°.]?\s*"
    r"(?P<number>[\d.]+)"
    r"(?:/(?P<number_year>\d{4}))?",
    flags=re.IGNORECASE,
)

PUBLICATION_RE = re.compile(
    r"Publicad[ao]\s+em\s+"
    r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
    flags=re.IGNORECASE,
)

PAGE_MODIFIED_RE = re.compile(
    r"Modificado\s+em\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})"
    r"\s+"
    r"(?P<time>\d{2}:\d{2})",
    flags=re.IGNORECASE,
)

REVISION_PATTERNS = (
    (
        "annex_amended",
        re.compile(
            r"Anexo\s+alterad[oa]\s+em\s+"
            r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "rectified",
        re.compile(
            r"Retificad[oa]\s+em\s+"
            r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "approval_act_updated",
        re.compile(
            r"Portaria\s+atualizada\s+em\s+"
            r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "approval_act_republished",
        re.compile(
            r"Republicad[oa]\s+em\s+"
            r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
            flags=re.IGNORECASE,
        ),
    ),
    (
        "official_content_amended",
        re.compile(
            r"(?<!Anexo\s)"
            r"Alterad[oa]\s+em\s+"
            r"(?P<date>\d{1,2}(?:º|ª)?/\d{1,2}/\d{4})",
            flags=re.IGNORECASE,
        ),
    ),
)


def _normspace(
    value: str,
) -> str:
    return " ".join(
        value.split()
    )


def _ascii(
    value: str,
) -> str:
    return unicodedata.normalize(
        "NFKD",
        value,
    ).encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii"
    )


def slugify_pt(
    value: str,
) -> str:
    value = _ascii(
        value
    ).lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    ).strip(
        "-"
    )

    if not value:
        raise ValueError(
            "cannot derive semantic slug from empty title"
        )

    return value


def _parse_date(
    value: str,
) -> str:
    match = DATE_RE.search(
        value
    )

    if not match:
        raise ValueError(
            f"invalid Brazilian date: {value!r}"
        )

    return (
        f"{int(match.group('year')):04d}-"
        f"{int(match.group('month')):02d}-"
        f"{int(match.group('day')):02d}"
    )


def _approval_atom(
    value: str,
) -> str:
    value = slugify_pt(
        value
    )

    return value


def build_approval_version_id(
    *,
    act_type: str,
    issuing_units: list[str],
    act_number: str,
    act_year: int,
) -> str:
    number = re.sub(
        r"\D",
        "",
        str(
            act_number
        ),
    )

    if not number:
        raise ValueError(
            "approval act number has no digits"
        )

    number = str(
        int(
            number
        )
    )

    parts = [
        _approval_atom(
            act_type
        ),
        *[
            _approval_atom(
                unit
            )
            for unit in issuing_units
        ],
        number,
        str(
            int(
                act_year
            )
        ),
    ]

    value = "-".join(
        parts
    )

    if not SEMANTIC_ID_RE.fullmatch(
        value
    ):
        raise ValueError(
            f"invalid approval_version_id: {value}"
        )

    return value


@dataclass
class _Link:
    href: str
    text: str


@dataclass
class _Cell:
    text: str
    links: list[_Link]


class _CatalogTableParser(
    HTMLParser
):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            convert_charrefs=True
        )

        self.rows: list[list[_Cell]] = []
        self.all_text: list[str] = []

        self._row: list[_Cell] | None = None
        self._cell_text: list[str] | None = None
        self._cell_links: list[_Link] | None = None

        self._anchor_href: str | None = None
        self._anchor_text: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()

        if tag == "tr":
            self._row = []

        elif (
            tag in {
                "td",
                "th",
            }
            and self._row is not None
        ):
            self._cell_text = []
            self._cell_links = []

        elif (
            tag == "a"
            and self._cell_text is not None
        ):
            attr_map = dict(
                attrs
            )

            href = attr_map.get(
                "href"
            )

            if href:
                self._anchor_href = href
                self._anchor_text = []

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        tag = tag.lower()

        if (
            tag == "a"
            and self._anchor_href is not None
            and self._cell_links is not None
        ):
            self._cell_links.append(
                _Link(
                    href=self._anchor_href,
                    text=_normspace(
                        " ".join(
                            self._anchor_text
                            or []
                        )
                    ),
                )
            )

            self._anchor_href = None
            self._anchor_text = None

        elif (
            tag in {
                "td",
                "th",
            }
            and self._row is not None
            and self._cell_text is not None
            and self._cell_links is not None
        ):
            self._row.append(
                _Cell(
                    text=_normspace(
                        " ".join(
                            self._cell_text
                        )
                    ),
                    links=self._cell_links,
                )
            )

            self._cell_text = None
            self._cell_links = None

        elif (
            tag == "tr"
            and self._row is not None
        ):
            if self._row:
                self.rows.append(
                    self._row
                )

            self._row = None
            self._cell_text = None
            self._cell_links = None

    def handle_data(
        self,
        data: str,
    ) -> None:
        cleaned = _normspace(
            data
        )

        if cleaned:
            self.all_text.append(
                cleaned
            )

            if self._cell_text is not None:
                self._cell_text.append(
                    cleaned
                )

            if self._anchor_text is not None:
                self._anchor_text.append(
                    cleaned
                )


def _parse_page_modified(
    visible_text: str,
) -> str | None:
    match = PAGE_MODIFIED_RE.search(
        visible_text
    )

    if not match:
        return None

    day, month, year = [
        int(
            value
        )
        for value in match.group(
            "date"
        ).split(
            "/"
        )
    ]

    hour, minute = [
        int(
            value
        )
        for value in match.group(
            "time"
        ).split(
            ":"
        )
    ]

    return datetime(
        year,
        month,
        day,
        hour,
        minute,
    ).isoformat()


def _parse_approval(
    raw_text: str,
) -> dict[str, Any] | None:
    match = PORTARIA_RE.search(
        raw_text
    )

    if not match:
        return None

    act_type = _normspace(
        match.group(
            "act_type"
        )
    )

    units = [
        value.upper()
        for value in re.split(
            r"\s*(?:/|[-–—])\s*",
            match.group(
                "units"
            ),
        )
        if value
    ]

    act_number_raw = match.group(
        "number"
    )

    number_digits = re.sub(
        r"\D",
        "",
        act_number_raw,
    )

    act_number = str(
        int(
            number_digits
        )
    )

    remainder = raw_text[
        match.end():
    ]

    dates = [
        _parse_date(
            item.group(
                0
            )
        )
        for item in DATE_RE.finditer(
            remainder
        )
    ]

    act_date = (
        dates[
            0
        ]
        if dates
        else None
    )

    explicit_year = match.group(
        "number_year"
    )

    if explicit_year:
        act_year = int(
            explicit_year
        )

    elif act_date:
        act_year = int(
            act_date[
                :4
            ]
        )

    else:
        return None

    publication_match = PUBLICATION_RE.search(
        raw_text
    )

    dou_publication_date = (
        _parse_date(
            publication_match.group(
                "date"
            )
        )
        if publication_match
        else None
    )

    approval_version_id = build_approval_version_id(
        act_type=act_type,
        issuing_units=units,
        act_number=act_number,
        act_year=act_year,
    )

    return {
        "approval_version_id":
            approval_version_id,

        "act_type":
            act_type,

        "act_number":
            act_number,

        "act_number_raw":
            act_number_raw,

        "act_year":
            act_year,

        "issuing_units":
            units,

        "act_date":
            act_date,

        "dou_publication_date":
            dou_publication_date,

        "raw_approval_citation":
            raw_text,
    }


def _extract_revision_events(
    row_text: str,
    *,
    catalog_url: str,
    approval_version_id: str,
) -> list[dict[str, Any]]:
    events = []

    seen = set()

    for event_type, pattern in REVISION_PATTERNS:
        for match in pattern.finditer(
            row_text
        ):
            event_date = _parse_date(
                match.group(
                    "date"
                )
            )

            key = (
                event_type,
                event_date,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            event_id = (
                f"{approval_version_id}--"
                f"{event_type.replace('_', '-')}--"
                f"{event_date}"
            )

            events.append(
                {
                    "event_id":
                        event_id,

                    "event_type":
                        event_type,

                    "event_date":
                        event_date,

                    "raw_source_note":
                        _normspace(
                            match.group(
                                0
                            )
                        ),

                    "source_url":
                        catalog_url,

                    "affected_approval_version_id":
                        approval_version_id,

                    "associated_document_ids":
                        [],
                }
            )

    events.sort(
        key=lambda item: (
            item[
                "event_date"
            ],
            item[
                "event_type"
            ],
        )
    )

    return events


def _documents_from_row(
    *,
    pcdt_id: str,
    approval_version_id: str,
    row: list[_Cell],
    catalog_url: str,
) -> list[dict[str, Any]]:
    role_by_cell = {
        0:
            "protocol_text",

        1:
            "approval_act",

        2:
            "ministry_publication",

        3:
            "protocol_summary",
    }

    role_counts: dict[str, int] = {}

    seen_urls = set()

    documents = []

    for index, cell in enumerate(
        row
    ):
        role = role_by_cell.get(
            index,
            "supporting_official_document",
        )

        for link in cell.links:
            absolute = urljoin(
                catalog_url,
                link.href,
            )

            if absolute in seen_urls:
                continue

            seen_urls.add(
                absolute
            )

            role_counts[
                role
            ] = (
                role_counts.get(
                    role,
                    0,
                )
                + 1
            )

            sequence = role_counts[
                role
            ]

            document_id = (
                f"{pcdt_id}--"
                f"{approval_version_id}--"
                f"{role.replace('_', '-')}--"
                f"{sequence:03d}"
            )

            documents.append(
                {
                    "document_id":
                        document_id,

                    "document_role":
                        role,

                    "source_link_text":
                        link.text
                        or None,

                    "canonical_source_url":
                        absolute,

                    "archive_object_id":
                        None,

                    "self_hosted_public_url":
                        None,

                    "availability_state":
                        "metadata_only",

                    "redistribution_state":
                        "unknown_requires_review",

                    "license_evidence":
                        None,
                }
            )

    documents.sort(
        key=lambda item: item[
            "document_id"
        ]
    )

    return documents


def parse_conitec_catalog_html(
    html_text: str,
    *,
    source_url: str,
    source_snapshot_date: str,
    source_html_sha256: str | None = None,
    development_source_url: str | None = None,
) -> dict[str, Any]:
    parser = _CatalogTableParser()

    parser.feed(
        html_text
    )

    visible_text = "\n".join(
        parser.all_text
    )

    if source_html_sha256 is None:
        source_html_sha256 = sha256(
            html_text.encode(
                "utf-8"
            )
        ).hexdigest()

    page_modified_at = _parse_page_modified(
        visible_text
    )

    entries = []

    unresolved_rows = []

    seen_pcdt_ids = set()

    for row in parser.rows:
        if len(
            row
        ) < 2:
            continue

        first_cell = row[
            0
        ]

        title = None

        for link in first_cell.links:
            if link.text:
                title = link.text
                break

        if not title:
            title = first_cell.text

        title = _normspace(
            title
        )

        if not title:
            continue

        if title.casefold() in {
            "pcdt",
            "tabela de pcdt",
        }:
            continue

        approval_text = _normspace(
            row[
                1
            ].text
        )

        row_text = _normspace(
            " ".join(
                cell.text
                for cell in row
            )
        )

        # A catalogue row is retained if it has an approval
        # citation OR a source link in its title cell.
        if (
            "portaria"
            not in _ascii(
                approval_text
            ).lower()
            and not first_cell.links
        ):
            continue

        pcdt_id = slugify_pt(
            title
        )

        if pcdt_id in seen_pcdt_ids:
            raise ValueError(
                f"duplicate derived pcdt_id: {pcdt_id}"
            )

        seen_pcdt_ids.add(
            pcdt_id
        )

        approval = _parse_approval(
            approval_text
        )

        known_gaps = []

        manual_review_required = False

        approval_versions = []

        unresolved_documents = []

        if approval is not None:
            approval_version_id = approval[
                "approval_version_id"
            ]

            documents = _documents_from_row(
                pcdt_id=pcdt_id,
                approval_version_id=approval_version_id,
                row=row,
                catalog_url=source_url,
            )

            revision_events = _extract_revision_events(
                row_text,
                catalog_url=source_url,
                approval_version_id=approval_version_id,
            )

            approval_versions.append(
                {
                    **approval,

                    "dou_url":
                        next(
                            (
                                document[
                                    "canonical_source_url"
                                ]
                                for document in documents
                                if (
                                    document[
                                        "document_role"
                                    ]
                                    == "approval_act"
                                )
                            ),
                            None,
                        ),

                    "documents":
                        documents,

                    "revision_events":
                        revision_events,

                    "supersedes":
                        [],

                    "superseded_by":
                        None,
                }
            )

        else:
            manual_review_required = True

            known_gaps.append(
                {
                    "gap_id":
                        f"{pcdt_id}--approval-identity",

                    "pcdt_id":
                        pcdt_id,

                    "approval_version_id":
                        None,

                    "document_role":
                        None,

                    "gap_reason":
                        "ambiguous_document_identity",

                    "official_reference":
                        row_text,

                    "source_url":
                        source_url,

                    "first_observed_at":
                        source_snapshot_date,

                    "last_checked_at":
                        source_snapshot_date,

                    "resolution_state":
                        "open",

                    "resolution_note":
                        None,
                }
            )

            unresolved_documents = [
                {
                    "candidate_role":
                        (
                            "protocol_text"
                            if index == 0
                            else "supporting_official_document"
                        ),

                    "canonical_source_url":
                        urljoin(
                            source_url,
                            link.href,
                        ),

                    "source_link_text":
                        link.text
                        or None,
                }
                for index, cell in enumerate(
                    row
                )
                for link in cell.links
            ]

            unresolved_rows.append(
                {
                    "pcdt_id":
                        pcdt_id,

                    "canonical_title_pt":
                        title,

                    "raw_row_text":
                        row_text,
                }
            )

        entries.append(
            {
                "pcdt_id":
                    pcdt_id,

                "document_type":
                    DOCUMENT_TYPE,

                "canonical_title_pt":
                    title,

                "aliases_pt":
                    [],

                "historical_titles_pt":
                    [],

                "title_en":
                    None,

                "approval_state":
                    "approved_listed",

                # The development-page join is intentionally not
                # performed by this first catalogue snapshot.
                "development_state":
                    None,

                "development_observations":
                    [],

                "approval_versions":
                    approval_versions,

                "unresolved_documents":
                    unresolved_documents,

                "source_observation": {
                    "official_catalog_url":
                        source_url,

                    "source_snapshot_date":
                        source_snapshot_date,
                },

                "discovery_state":
                    "discovery_in_progress",

                "known_gaps":
                    known_gaps,

                "manual_review_required":
                    manual_review_required,
            }
        )

    if not entries:
        raise ValueError(
            "no PCDT catalogue rows parsed"
        )

    entries.sort(
        key=lambda item: (
            _ascii(
                item[
                    "canonical_title_pt"
                ]
            ).casefold(),
            item[
                "pcdt_id"
            ],
        )
    )

    parsed_approval_count = sum(
        1
        for item in entries
        if item[
            "approval_versions"
        ]
    )

    return {
        "schema_version":
            REGISTRY_SCHEMA_VERSION,

        "registry_id":
            REGISTRY_ID,

        "document_type":
            DOCUMENT_TYPE,

        "source_snapshot": {
            "authority":
                "Ministério da Saúde / Conitec",

            "official_catalog_url":
                source_url,

            "source_snapshot_date":
                source_snapshot_date,

            "source_html_sha256":
                source_html_sha256,

            "official_catalog_page_modified_at":
                page_modified_at,

            "development_source_url":
                development_source_url,

            "development_join_state":
                "deferred_after_catalog_seed",

            "license_page_observation": {
                "label":
                    (
                        "Creative Commons "
                        "Atribuição-SemDerivações 3.0 Não Adaptada"
                    ),

                "evidence_scope":
                    "official_catalog_page",

                "redistribution_inference_for_linked_pdfs":
                    False,
            },
        },

        "catalog_summary": {
            "pcdt_record_count":
                len(
                    entries
                ),

            "parsed_approval_record_count":
                parsed_approval_count,

            "manual_review_record_count":
                len(
                    entries
                )
                - parsed_approval_count,
        },

        "pcdts":
            entries,

        "unresolved_catalog_rows":
            unresolved_rows,

        "clinical_logic_included":
            False,
    }


def _walk_keys(
    value: Any,
):
    if isinstance(
        value,
        dict,
    ):
        for key, child in value.items():
            yield key

            yield from _walk_keys(
                child
            )

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            yield from _walk_keys(
                child
            )


def validate_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(
        manifest,
        dict,
    ):
        raise ValueError(
            "manifest must be an object"
        )

    if (
        manifest.get(
            "schema_version"
        )
        != ARCHIVE_MANIFEST_SCHEMA_VERSION
    ):
        raise ValueError(
            "unsupported archive manifest schema_version"
        )

    archive_root = manifest.get(
        "archive_root"
    )

    public_prefix = manifest.get(
        "public_prefix"
    )

    if not isinstance(
        archive_root,
        str,
    ) or not archive_root.startswith(
        "/"
    ):
        raise ValueError(
            "archive_root must be absolute"
        )

    if not isinstance(
        public_prefix,
        str,
    ) or not public_prefix.startswith(
        "/"
    ):
        raise ValueError(
            "public_prefix must be an absolute URL path"
        )

    objects = manifest.get(
        "objects"
    )

    if not isinstance(
        objects,
        list,
    ):
        raise ValueError(
            "manifest objects must be a list"
        )

    seen = set()

    for obj in objects:
        if not isinstance(
            obj,
            dict,
        ):
            raise ValueError(
                "archive object must be an object"
            )

        object_id = obj.get(
            "archive_object_id"
        )

        digest = obj.get(
            "sha256"
        )

        if not isinstance(
            object_id,
            str,
        ) or not ARCHIVE_OBJECT_RE.fullmatch(
            object_id
        ):
            raise ValueError(
                f"invalid archive_object_id: {object_id!r}"
            )

        if object_id in seen:
            raise ValueError(
                f"duplicate archive object: {object_id}"
            )

        seen.add(
            object_id
        )

        if digest != object_id.split(
            ":",
            1,
        )[
            1
        ]:
            raise ValueError(
                "archive_object_id does not match sha256"
            )

        if not isinstance(
            obj.get(
                "size_bytes"
            ),
            int,
        ) or obj[
            "size_bytes"
        ] <= 0:
            raise ValueError(
                "archive size_bytes must be positive"
            )

        if (
            obj.get(
                "availability_state"
            )
            not in AVAILABILITY_STATES
        ):
            raise ValueError(
                "invalid archive availability_state"
            )

        redistribution_state = obj.get(
            "redistribution_state"
        )

        if (
            redistribution_state
            not in REDISTRIBUTION_STATES
        ):
            raise ValueError(
                "invalid redistribution_state"
            )

        relative = obj.get(
            "local_relative_path"
        )

        expected_relative = (
            "objects/sha256/"
            f"{digest[:2]}/"
            f"{digest}.pdf"
        )

        if relative != expected_relative:
            raise ValueError(
                "archive relative path does not match content address"
            )

        public_url = obj.get(
            "public_url"
        )

        if public_url is not None:
            if (
                obj[
                    "availability_state"
                ]
                != "archived"
                or redistribution_state
                != "public_verified"
            ):
                raise ValueError(
                    "public URL requires archived/public_verified object"
                )

    return {
        "object_count":
            len(
                objects
            ),

        "object_ids":
            seen,
    }


def _iter_documents(
    registry: dict[str, Any],
):
    for pcdt in registry.get(
        "pcdts",
        []
    ):
        for version in pcdt.get(
            "approval_versions",
            []
        ):
            for document in version.get(
                "documents",
                []
            ):
                yield (
                    pcdt,
                    version,
                    document,
                )


def validate_registry(
    registry: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(
        registry,
        dict,
    ):
        raise ValueError(
            "registry must be an object"
        )

    if (
        registry.get(
            "schema_version"
        )
        != REGISTRY_SCHEMA_VERSION
    ):
        raise ValueError(
            "unsupported registry schema_version"
        )

    if registry.get(
        "registry_id"
    ) != REGISTRY_ID:
        raise ValueError(
            "unexpected registry_id"
        )

    if registry.get(
        "document_type"
    ) != DOCUMENT_TYPE:
        raise ValueError(
            "registry document_type must be pcdt"
        )

    if (
        registry.get(
            "clinical_logic_included"
        )
        is not False
    ):
        raise ValueError(
            "PCDT metadata registry must not include clinical logic"
        )

    forbidden_found = sorted(
        {
            key
            for key in _walk_keys(
                registry
            )
            if key in FORBIDDEN_CLINICAL_KEYS
        }
    )

    if forbidden_found:
        raise ValueError(
            "forbidden clinical fields found: "
            + ", ".join(
                forbidden_found
            )
        )

    pcdts = registry.get(
        "pcdts"
    )

    if not isinstance(
        pcdts,
        list,
    ):
        raise ValueError(
            "pcdts must be a list"
        )

    seen_pcdt_ids = set()
    seen_document_ids = set()
    seen_approval_ids = set()

    document_count = 0
    revision_count = 0

    for pcdt in pcdts:
        pcdt_id = pcdt.get(
            "pcdt_id"
        )

        if not isinstance(
            pcdt_id,
            str,
        ) or not SEMANTIC_ID_RE.fullmatch(
            pcdt_id
        ):
            raise ValueError(
                f"invalid pcdt_id: {pcdt_id!r}"
            )

        if pcdt_id in seen_pcdt_ids:
            raise ValueError(
                f"duplicate pcdt_id: {pcdt_id}"
            )

        seen_pcdt_ids.add(
            pcdt_id
        )

        if pcdt.get(
            "document_type"
        ) != DOCUMENT_TYPE:
            raise ValueError(
                f"{pcdt_id}: document_type must be pcdt"
            )

        if not str(
            pcdt.get(
                "canonical_title_pt",
                "",
            )
        ).strip():
            raise ValueError(
                f"{pcdt_id}: missing canonical_title_pt"
            )

        if (
            pcdt.get(
                "approval_state"
            )
            not in APPROVAL_STATES
        ):
            raise ValueError(
                f"{pcdt_id}: invalid approval_state"
            )

        development_state = pcdt.get(
            "development_state"
        )

        if (
            development_state is not None
            and development_state
            not in DEVELOPMENT_STATES
        ):
            raise ValueError(
                f"{pcdt_id}: invalid development_state"
            )

        if (
            pcdt.get(
                "discovery_state"
            )
            not in DISCOVERY_STATES
        ):
            raise ValueError(
                f"{pcdt_id}: invalid discovery_state"
            )

        if not isinstance(
            pcdt.get(
                "manual_review_required"
            ),
            bool,
        ):
            raise ValueError(
                f"{pcdt_id}: manual_review_required must be bool"
            )

        for gap in pcdt.get(
            "known_gaps",
            []
        ):
            if (
                gap.get(
                    "gap_reason"
                )
                not in GAP_REASONS
            ):
                raise ValueError(
                    f"{pcdt_id}: invalid gap_reason"
                )

        for version in pcdt.get(
            "approval_versions",
            []
        ):
            approval_id = version.get(
                "approval_version_id"
            )

            if not isinstance(
                approval_id,
                str,
            ) or not SEMANTIC_ID_RE.fullmatch(
                approval_id
            ):
                raise ValueError(
                    f"{pcdt_id}: invalid approval_version_id"
                )

            global_approval_key = (
                pcdt_id,
                approval_id,
            )

            if global_approval_key in seen_approval_ids:
                raise ValueError(
                    f"duplicate approval version: {global_approval_key}"
                )

            seen_approval_ids.add(
                global_approval_key
            )

            for event in version.get(
                "revision_events",
                []
            ):
                if (
                    event.get(
                        "event_type"
                    )
                    not in REVISION_EVENT_TYPES
                ):
                    raise ValueError(
                        f"{pcdt_id}: invalid revision event"
                    )

                revision_count += 1

            for document in version.get(
                "documents",
                []
            ):
                document_id = document.get(
                    "document_id"
                )

                if not isinstance(
                    document_id,
                    str,
                ) or not document_id:
                    raise ValueError(
                        f"{pcdt_id}: missing document_id"
                    )

                if document_id in seen_document_ids:
                    raise ValueError(
                        f"duplicate document_id: {document_id}"
                    )

                seen_document_ids.add(
                    document_id
                )

                if (
                    document.get(
                        "document_role"
                    )
                    not in DOCUMENT_ROLES
                ):
                    raise ValueError(
                        f"{document_id}: invalid document_role"
                    )

                if not str(
                    document.get(
                        "canonical_source_url",
                        "",
                    )
                ).startswith(
                    (
                        "https://",
                        "http://",
                    )
                ):
                    raise ValueError(
                        f"{document_id}: invalid source URL"
                    )

                if (
                    document.get(
                        "availability_state"
                    )
                    not in AVAILABILITY_STATES
                ):
                    raise ValueError(
                        f"{document_id}: invalid availability_state"
                    )

                if (
                    document.get(
                        "redistribution_state"
                    )
                    not in REDISTRIBUTION_STATES
                ):
                    raise ValueError(
                        f"{document_id}: invalid redistribution_state"
                    )

                archive_object_id = document.get(
                    "archive_object_id"
                )

                public_url = document.get(
                    "self_hosted_public_url"
                )

                if public_url is not None and archive_object_id is None:
                    raise ValueError(
                        f"{document_id}: public URL requires archive object"
                    )

                document_count += 1

    manifest_summary = None

    if manifest is not None:
        manifest_summary = validate_manifest(
            manifest
        )

        object_ids = manifest_summary[
            "object_ids"
        ]

        object_map = {
            obj[
                "archive_object_id"
            ]:
                obj
            for obj in manifest.get(
                "objects",
                []
            )
        }

        for _, _, document in _iter_documents(
            registry
        ):
            archive_object_id = document.get(
                "archive_object_id"
            )

            if archive_object_id is None:
                continue

            if archive_object_id not in object_ids:
                raise ValueError(
                    "dangling document archive_object_id: "
                    f"{archive_object_id}"
                )

            if document.get(
                "self_hosted_public_url"
            ):
                obj = object_map[
                    archive_object_id
                ]

                if (
                    obj[
                        "availability_state"
                    ]
                    != "archived"
                    or obj[
                        "redistribution_state"
                    ]
                    != "public_verified"
                ):
                    raise ValueError(
                        "document public URL points to non-public archive object"
                    )

    summary = registry.get(
        "catalog_summary",
        {}
    )

    if (
        summary.get(
            "pcdt_record_count"
        )
        != len(
            pcdts
        )
    ):
        raise ValueError(
            "catalog summary PCDT count mismatch"
        )

    return {
        "pcdt_count":
            len(
                pcdts
            ),

        "approval_version_count":
            len(
                seen_approval_ids
            ),

        "document_count":
            document_count,

        "revision_event_count":
            revision_count,

        "manual_review_count":
            sum(
                1
                for item in pcdts
                if item[
                    "manual_review_required"
                ]
            ),

        "manifest_object_count":
            (
                manifest_summary[
                    "object_count"
                ]
                if manifest_summary is not None
                else None
            ),
    }


def build_discovery_plan(
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    validate_registry(
        registry
    )

    plan = []

    for pcdt, version, document in _iter_documents(
        registry
    ):
        if document.get(
            "archive_object_id"
        ) is not None:
            continue

        plan.append(
            {
                "pcdt_id":
                    pcdt[
                        "pcdt_id"
                    ],

                "approval_version_id":
                    version[
                        "approval_version_id"
                    ],

                "document_id":
                    document[
                        "document_id"
                    ],

                "document_role":
                    document[
                        "document_role"
                    ],

                "canonical_source_url":
                    document[
                        "canonical_source_url"
                    ],

                "availability_state":
                    document[
                        "availability_state"
                    ],

                "redistribution_state":
                    document[
                        "redistribution_state"
                    ],

                "action":
                    "review_before_fetch",
            }
        )

    plan.sort(
        key=lambda item: item[
            "document_id"
        ]
    )

    return plan


def manifest_object_relative_path(
    digest: str,
) -> str:
    if not re.fullmatch(
        r"[0-9a-f]{64}",
        digest,
    ):
        raise ValueError(
            "digest must be 64 lowercase hex characters"
        )

    return str(
        PurePosixPath(
            "objects",
            "sha256",
            digest[
                :2
            ],
            f"{digest}.pdf",
        )
    )
