# Brazil 2026 PNI — maternal VVSR rule verification

Review date: 2026-09-11

## National rule

The national 2026 PNI recommendation for maternal respiratory syncytial
virus vaccination is:

- pregnancy is required;
- one VVSR dose is recommended in each pregnancy;
- administration begins from the 28th gestational week;
- there is no maternal-age restriction.

A dose documented in the current pregnancy satisfies the one-dose
current-pregnancy rule.

The Ministry also states that a dose inadvertently administered before
the recommended gestational age should not be repeated solely because
of that timing error.

## Fail-closed history semantics

At or after week 28:

- documented zero-dose history can support `recommend_now`;
- unknown history produces `history_required`;
- partial history without proof about the current pregnancy produces
  `history_required`;
- a documented dose from a previous pregnancy does not satisfy the
  current pregnancy;
- a documented dose linked to the current pregnancy produces
  `not_due_now`.

Before week 28, the routine recommendation is `not_due_now`.

The engine does not fabricate an exact future administration date from
integer-only gestational-week input.

## dTpa intentionally deferred

dTpa is not implemented in BH8E1.

The 2026 national dTpa recommendation requires consideration of the
interval between vaccines containing diphtheria and tetanus toxoids,
including history-dependent basic-series branches.

That is an antigen-family history problem rather than a single
`vaccine_key = dtpa` history problem.

Automating dTpa before adding a cross-vaccine toxoid/antigen history
contract could misclassify recent dT, DTP, pentavalent or other relevant
toxoid-containing doses.

BH8E1 therefore implements VVSR only.
