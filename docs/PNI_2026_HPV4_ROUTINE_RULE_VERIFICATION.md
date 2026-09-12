# Brazil 2026 PNI — HPV4 routine 9–14 rule verification

Review date: 2026-09-11

## Implemented scope

BH8E5A implements only the routine HPV4 layer for people from age 9
through 14 years, 11 months and 29 days.

The 2026 national schedule defines a one-dose basic routine schedule for
girls and boys who have not previously been vaccinated.

The agenda is age 9, with vaccination as early as possible throughout
the routine window when missed.

## History

Within the routine age window:

- one valid documented routine-age HPV4 dose -> `not_due_now`;
- documented zero-dose history -> proceed to context and safety gates;
- unknown history -> `history_required`;
- partial history -> `history_required`.

Unknown history is not silently converted into documented zero-dose
history in this routine evaluator.

## Dose before age 9

A documented HPV4 administration before age 9 is not automatically
treated as completion of the routine one-dose schedule.

The national programme contains special-priority HPV indications with
different dose schedules and younger eligible ages.

Such a record therefore returns `special_pathway_review` rather than
having the routine engine infer why the early dose was given.

## Pregnancy

HPV4 is contraindicated during pregnancy.

For a person who is otherwise calendar-due:

- pregnancy status `unknown` -> `context_required`;
- `pregnant` -> `special_pathway_review`;
- `not_pregnant` or pregnancy `not_applicable` -> routine evaluation
  may continue.

The source states that inadvertent HPV4 administration during pregnancy
does not require an additional intervention beyond prenatal follow-up;
the routine engine does not itself manage that follow-up.

Breastfeeding is not a contraindication.

## Fifteenth-birthday boundary

At the 15th birthday the routine layer ends.

A `not_applicable` result from this routine evaluator must not be
interpreted as absence of all HPV vaccination indications.

The 15–19 rescue strategy is a distinct recommendation layer.

## 2026 rescue strategy

The national 15–19 rescue strategy is separate from routine HPV4 and,
as of this review, has been extended through 31 December 2026.

It covers eligible adolescents and young people who were not vaccinated
in the recommended age range, including the official no-record pathway.

BH8E5A does not implement this rescue layer.

## Special-priority HPV pathways

The 2026 PNI also contains selective priority pathways, including
multi-dose schedules for specific clinical groups.

Those pathways are not implemented by BH8E5A and must remain separate
from the routine one-dose rule.

## Simultaneous administration

HPV4 may be administered simultaneously with the other vaccines in the
current national calendar without a required interval.

The routine evaluator therefore does not invent an inter-vaccine spacing
rule.

## PT-BR / EN-GB

Every result contains:

- canonical PT-BR `interpretation_pt`;
- complete secondary EN-GB `interpretation_en`.

The clinical decision remains language-neutral.
