# PNI 2026 — DNG4/Takeda product-sensitive history model

## Purpose

This layer normalizes dengue vaccine history before implementation of
the position-20 Takeda decision engine.

It does not decide whether vaccination is due today.

## Product identity

The model recognizes three explicit product identities:

- `dengue_takeda`
- `dengue_butantan`
- `dengue_sanofi_legacy`

They are not collapsed into a generic dengue dose count.

## Takeda chronology

The ordinary position-20 product is Takeda.

A first Takeda event can be treated as valid product-series history when
it occurred within the supported Takeda label age and before the PNI
position-20 initiation ceiling at exact age 15.

A valid Takeda D1 received before age 10 can therefore remain relevant
historical series evidence even though it was not a PNI 10–14 initiation
event.

The first PNI decision core will separately determine current public
eligibility.

## D1 to D2 interval

The canonical series interval used by this model is 90 days.

Calendar-month clamping is not used.

A late D2 does not restart the series.

## Early Takeda D2

An early physical dose is preserved but is not counted as D2.

The next corrective Takeda date is the later of:

- D1 + 90 days; and
- the latest early physical dose + 30 days.

The history is not discarded merely because an early event exists.

## Takeda completion after age 15

Exact age 15 closes new position-20 Takeda initiation.

It does not erase a valid Takeda series already started before that
boundary. D2 may therefore occur after the fifteenth birthday.

## Butantan product firewall

Butantan is a separate single-dose strategy product and is not generally
interchangeable with Takeda.

One narrow 2026 error-management consequence is represented:

- valid Takeda D1;
- followed by a label-age-valid Butantan dose at least 30 days later;
- scheme considered complete.

The model records that outcome explicitly as an error-management
completion. It does not re-label the Butantan dose as Takeda D2 and does
not infer general interchangeability.

Other heterogeneous sequences fail closed.

## Sanofi legacy firewall

Documented Sanofi/Dengvaxia history is preserved and blocks automatic
position-20 Takeda interpretation.

The normalizer does not invent revaccination or heterologous completion.

## Dengue infection timing

Disease history is deliberately outside this history model.

Current 2026 error-management guidance means an already-administered
dengue vaccine dose is not invalidated solely because it was given less
than six months after prior dengue.

The current recommendation to wait six months after dengue before
starting vaccination belongs to the future decision engine.

Likewise, dengue after Takeda D1 affects the future D2 recommendation
date but does not change the vaccine-history chronology itself.

## Clinical context excluded from normalization

This model does not infer or consume:

- prior/recent dengue infection;
- other arboviral recovery dates;
- pregnancy;
- breastfeeding;
- immunodeficiency or immunosuppression;
- severe hypersensitivity;
- acute febrile illness;
- blood, plasma, or immunoglobulin exposure;
- live-vaccine interaction history;
- geography;
- occupational strategy eligibility.

## Safety behavior

Automatic routine interpretation fails closed for incomplete or undated
history, unsupported product identity, same-day multiple dengue vaccine
events, product-age conflicts, Sanofi history, or unsupported
cross-product sequences.

No due/not-due recommendation and no synthetic vaccination score are
produced by the normalizer.
