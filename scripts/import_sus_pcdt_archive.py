#!/usr/bin/env python3

from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json

from clinical_tools.pcdt_metadata import (
    build_discovery_plan,
    parse_conitec_catalog_html,
    validate_manifest,
    validate_registry,
)


def load_json(
    path: Path,
):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def main() -> int:
    parser = ArgumentParser(
        description=(
            "Validate the SUS PCDT registry/archive manifest and "
            "produce a deterministic discovery-only import plan."
        )
    )

    parser.add_argument(
        "--registry",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--discover-only",
        action="store_true",
        required=True,
        help=(
            "Required safety flag. This implementation does not "
            "download or archive PDFs."
        ),
    )

    parser.add_argument(
        "--catalog-html",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--catalog-url",
        default=None,
    )

    parser.add_argument(
        "--development-url",
        default=None,
    )

    parser.add_argument(
        "--snapshot-date",
        default=None,
    )

    parser.add_argument(
        "--sample",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    registry = load_json(
        args.registry
    )

    manifest = load_json(
        args.manifest
    )

    registry_summary = validate_registry(
        registry,
        manifest=manifest,
    )

    manifest_summary = validate_manifest(
        manifest
    )

    source_compare = None

    if args.catalog_html is not None:
        if not args.catalog_url:
            parser.error(
                "--catalog-url is required with --catalog-html"
            )

        if not args.snapshot_date:
            parser.error(
                "--snapshot-date is required with --catalog-html"
            )

        raw_bytes = args.catalog_html.read_bytes()

        parsed = parse_conitec_catalog_html(
            raw_bytes.decode(
                "utf-8",
                errors="replace",
            ),
            source_url=args.catalog_url,
            source_snapshot_date=args.snapshot_date,
            source_html_sha256=sha256(
                raw_bytes
            ).hexdigest(),
            development_source_url=args.development_url,
        )

        parsed_ids = {
            item[
                "pcdt_id"
            ]
            for item in parsed[
                "pcdts"
            ]
        }

        registry_ids = {
            item[
                "pcdt_id"
            ]
            for item in registry[
                "pcdts"
            ]
        }

        source_compare = {
            "same_pcdt_id_set":
                parsed_ids
                == registry_ids,

            "parsed_count":
                len(
                    parsed_ids
                ),

            "registry_count":
                len(
                    registry_ids
                ),

            "source_html_sha256_matches":
                (
                    parsed[
                        "source_snapshot"
                    ][
                        "source_html_sha256"
                    ]
                    == registry[
                        "source_snapshot"
                    ][
                        "source_html_sha256"
                    ]
                ),
        }

        if not all(
            source_compare.values()
        ):
            raise SystemExit(
                "registry does not reproduce supplied catalogue snapshot: "
                + json.dumps(
                    source_compare,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

    plan = build_discovery_plan(
        registry
    )

    sample_size = max(
        0,
        min(
            args.sample,
            50,
        ),
    )

    output = {
        "mode":
            "discover_only",

        "persistent_archive_mutation":
            False,

        "pdf_download_performed":
            False,

        "registry":
            registry_summary,

        "manifest":
            {
                "object_count":
                    manifest_summary[
                        "object_count"
                    ],
            },

        "discovery_candidate_count":
            len(
                plan
            ),

        "sample":
            plan[
                :sample_size
            ],

        "source_compare":
            source_compare,
    }

    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
