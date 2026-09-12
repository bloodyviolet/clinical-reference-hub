# SUS PCDT Registry — metadata verification

## Scope

Roadmap Item 9 is implemented as the metadata/index layer of the
**SUS PCDT Registry & Public Document Repository**.

The registry is not a clinical decision engine.

It identifies official PCDTs, their approval instruments, source links,
revision annotations, provenance, archive relationships and discovery
state.

## Authority

The primary current-state source is the official Conitec approved-PCDT
catalogue.

SUS Open Data, Ministry publication pages, approval acts, DOU records and
other official sources may be used for cross-checking and historical
discovery.

## Stable identities

`pcdt_id` is an immutable semantic protocol identity.

`approval_version_id` is derived from the official approving act.

`document_id` identifies a logical official document relationship.

`archive_object_id` identifies exact PDF bytes by SHA-256.

These identities must not be conflated.

## Current catalogue snapshot

The first registry snapshot is generated deterministically from the
official approved-PCDT catalogue HTML.

Rows whose approval-act identity cannot safely be parsed are retained as
manual-review records rather than discarded or guessed.

## Revision events

Catalogue annotations are preserved as structured events, including:

- annex amended;
- rectified;
- approval act updated;
- approval act republished;
- other official amendments.

The original approval metadata remains intact.

## Development lifecycle

Development state is a separate axis from approval state.

The first approved-catalogue snapshot does not automatically join the
dynamic Conitec development table. Development joins require exact title,
known alias, or curated identity mapping.

## Clinical firewall

The registry does not encode:

- patient eligibility;
- diagnosis criteria;
- medication indication;
- dose selection;
- treatment sequencing;
- monitoring schedules;
- stopping rules.

The PNI/clinical decision-core count therefore remains unchanged.
