from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Any


VVSR_RULE_ID = (
    "PNI26-VVSR-PREG-ROUTINE-001"
)

VVSR_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

VVSR_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/composicao/"
    "svsa/pni/calendario-tecnico/"
    "instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026"
)


def _as_plain_dict(
    value: Any,
) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(
        value,
        dict,
    ):
        return value

    model_dump = getattr(
        value,
        "model_dump",
        None,
    )

    if model_dump is not None:
        return model_dump()

    raise ValueError(
        "history must be a mapping or Pydantic model"
    )


def _as_date(
    value: Any,
) -> date:
    if isinstance(
        value,
        date,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        return date.fromisoformat(
            value
        )

    raise ValueError(
        "invalid administration date"
    )


def _result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "vaccine_key":
            "vvsr",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                VVSR_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                VVSR_SOURCE_URL,

            "source_snapshot_date":
                VVSR_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_vvsr_history(
    history: Any,
    *,
    assessment_date: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "vvsr"
    ):
        raise ValueError(
            "VVSR rule requires vaccine_key=vvsr"
        )

    allowed_states = {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }

    state = value.get(
        "history_state"
    )

    if state not in allowed_states:
        raise ValueError(
            "invalid VVSR history_state"
        )

    doses = value.get(
        "doses"
    ) or []

    normalised_doses = []

    for raw_dose in doses:
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "VVSR administration_date cannot follow assessment_date"
            )

        normalised_doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    value = {
        **value,
        "doses":
            normalised_doses,
    }

    return value


def evaluate_pni_vvsr_routine(
    *,
    assessment_date: date,
    pregnancy_status: str,
    gestational_age_weeks: int | None,
    pregnancy_episode_key: str | None,
    history: Any = None,
) -> dict[str, Any]:
    """
    Evaluate only the 2026 national routine maternal VVSR rule.

    This function deliberately does not implement dTpa or any other
    PNI vaccine family.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    allowed_pregnancy_statuses = {
        "pregnant",
        "not_pregnant",
        "unknown",
        "not_applicable",
    }

    if (
        pregnancy_status
        not in allowed_pregnancy_statuses
    ):
        raise ValueError(
            "invalid pregnancy_status"
        )

    if pregnancy_status in {
        "not_pregnant",
        "not_applicable",
    }:
        return _result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A recomendação nacional de VVSR materna "
                "avaliada por esta regra aplica-se à gestação."
            ),
            interpretation_en=(
                "The national maternal RSV vaccine recommendation "
                "evaluated by this rule applies during pregnancy."
            ),
        )

    if (
        pregnancy_status
        == "unknown"
    ):
        return _result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "É necessário confirmar se há gestação antes "
                "de aplicar a regra materna de VVSR."
            ),
            interpretation_en=(
                "Pregnancy status must be confirmed before "
                "applying the maternal RSV vaccine rule."
            ),
        )

    if (
        gestational_age_weeks
        is None
    ):
        return _result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "gestational_age_weeks",
            ],
            interpretation_pt=(
                "A idade gestacional é necessária para aplicar "
                "a recomendação nacional de VVSR."
            ),
            interpretation_en=(
                "Gestational age is required to apply the "
                "national maternal RSV vaccine recommendation."
            ),
        )

    if (
        not isinstance(
            gestational_age_weeks,
            int,
        )
        or gestational_age_weeks < 0
        or gestational_age_weeks > 45
    ):
        raise ValueError(
            "gestational_age_weeks must be an integer from 0 to 45"
        )

    normalised_history = (
        _normalise_vvsr_history(
            history,
            assessment_date=assessment_date,
        )
    )

    # A documented dose linked to the current pregnancy satisfies the
    # one-dose-each-pregnancy rule even if it was inadvertently given
    # before week 28; the Ministry advises against repeating solely for
    # that timing error.
    if (
        normalised_history is not None
        and pregnancy_episode_key is not None
    ):
        for dose in normalised_history[
            "doses"
        ]:
            if (
                dose.get(
                    "pregnancy_episode_key"
                )
                == pregnancy_episode_key
            ):
                return _result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    interpretation_pt=(
                        "Há dose de VVSR documentada na gestação "
                        "atual. Não indicar nova dose apenas por "
                        "eventual administração antes da 28ª semana."
                    ),
                    interpretation_en=(
                        "An RSV vaccine dose is documented in the "
                        "current pregnancy. Do not recommend another "
                        "dose solely because it may have been given "
                        "before gestational week 28."
                    ),
                )

    if (
        gestational_age_weeks
        < 28
    ):
        return _result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A recomendação rotineira de VVSR inicia a partir "
                "da 28ª semana gestacional. Com a idade gestacional "
                "informada, a dose não é indicada agora."
            ),
            interpretation_en=(
                "Routine maternal RSV vaccination begins from "
                "gestational week 28. At the supplied gestational "
                "age, the dose is not due now."
            ),
        )

    if (
        normalised_history
        is None
    ):
        return _result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "A gestação está na faixa recomendada, mas é "
                "necessário verificar o histórico de VVSR desta "
                "gestação antes de recomendar outra dose."
            ),
            interpretation_en=(
                "The pregnancy is within the recommended gestational "
                "window, but RSV vaccination history for the current "
                "pregnancy must be checked before recommending a dose."
            ),
        )

    state = normalised_history[
        "history_state"
    ]

    if (
        state
        == "unknown"
    ):
        return _result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de VVSR é desconhecido. Não tratar "
                "histórico desconhecido como ausência documentada "
                "de vacinação."
            ),
            interpretation_en=(
                "RSV vaccination history is unknown. Do not treat "
                "unknown history as documented zero-dose history."
            ),
        )

    if (
        state
        == "documented_zero_dose"
    ):
        return _result(
            assessment_date=assessment_date,
            decision="recommend_now",
            interpretation_pt=(
                "Gestante com 28 semanas ou mais e histórico "
                "documentado sem dose de VVSR: recomendar 1 dose "
                "na gestação atual."
            ),
            interpretation_en=(
                "Pregnant person at or beyond 28 weeks with "
                "documented zero-dose RSV vaccine history: recommend "
                "one dose in the current pregnancy."
            ),
        )

    if (
        state
        == "partial_record"
    ):
        return _result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro de VVSR é parcial e não comprova uma "
                "dose na gestação atual. É necessário reconciliar "
                "o histórico antes de recomendar nova dose."
            ),
            interpretation_en=(
                "The RSV vaccine record is partial and does not "
                "establish a dose in the current pregnancy. History "
                "reconciliation is required before recommending "
                "another dose."
            ),
        )

    # documented_doses
    doses = normalised_history[
        "doses"
    ]

    if (
        pregnancy_episode_key
        is None
    ):
        return _result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_episode_key",
            ],
            interpretation_pt=(
                "Existem doses documentadas de VVSR, mas é "
                "necessário identificar a gestação atual para "
                "distinguir doses de gestações anteriores."
            ),
            interpretation_en=(
                "RSV vaccine doses are documented, but the current "
                "pregnancy episode must be identified to distinguish "
                "previous-pregnancy doses."
            ),
        )

    if any(
        dose.get(
            "pregnancy_episode_key"
        )
        is None
        for dose in doses
    ):
        return _result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Há dose documentada de VVSR sem identificação da "
                "gestação correspondente. Não é seguro assumir que "
                "ela pertence ou não à gestação atual."
            ),
            interpretation_en=(
                "A documented RSV vaccine dose lacks pregnancy-episode "
                "identity. It is unsafe to assume whether it belongs "
                "to the current pregnancy."
            ),
        )

    # All documented doses are linked to other pregnancy episodes.
    return _result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "As doses documentadas pertencem a outras gestações. "
            "Como a recomendação é de 1 dose em cada gestação e "
            "a idade gestacional atual é de pelo menos 28 semanas, "
            "recomendar 1 dose de VVSR agora."
        ),
        interpretation_en=(
            "Documented doses belong to previous pregnancies. "
            "Because one dose is recommended in every pregnancy "
            "and the current gestational age is at least 28 weeks, "
            "recommend one RSV vaccine dose now."
        ),
    )



DTPA_MATERNAL_RULE_ID = (
    "PNI26-DTPA-MATERNAL-ROUTINE-001"
)

DTPA_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

DTPA_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

DTPA_SAFETY_SCREEN_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}

DTPA_REQUIRED_ANTIGENS = {
    "diphtheria_toxoid",
    "tetanus_toxoid",
}


def _dtpa_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "dtpa",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                DTPA_MATERNAL_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                DTPA_SOURCE_URL,

            "source_snapshot_date":
                DTPA_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_dtpa_antigen_history(
    value: Any,
    *,
    assessment_date: date,
) -> dict[str, Any] | None:
    if value is None:
        return None

    summary = _as_plain_dict(
        value
    )

    target_antigens = set(
        summary.get(
            "target_antigens"
        )
        or []
    )

    if not DTPA_REQUIRED_ANTIGENS.issubset(
        target_antigens
    ):
        raise ValueError(
            "maternal dTpa requires diphtheria/tetanus antigen history"
        )

    raw_exposures = (
        summary.get(
            "exposures"
        )
        or []
    )

    exposures = []

    for raw in raw_exposures:
        exposure = _as_plain_dict(
            raw
        )

        administration_date = _as_date(
            exposure.get(
                "administration_date"
            )
        )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "dTpa antigen exposure cannot follow assessment_date"
            )

        components = set(
            exposure.get(
                "antigen_components"
            )
            or []
        )

        if not DTPA_REQUIRED_ANTIGENS.issubset(
            components
        ):
            raise ValueError(
                "normalized D/T exposure lacks required toxoid components"
            )

        gestational_age = exposure.get(
            "gestational_age_weeks_at_administration"
        )

        if (
            gestational_age is not None
            and (
                not isinstance(
                    gestational_age,
                    int,
                )
                or gestational_age < 0
                or gestational_age > 45
            )
        ):
            raise ValueError(
                "invalid gestational age at dTpa administration"
            )

        exposures.append({
            **exposure,
            "administration_date":
                administration_date,

            "antigen_components":
                list(
                    exposure.get(
                        "antigen_components"
                    )
                    or []
                ),
        })

    exposures.sort(
        key=lambda item: (
            item[
                "administration_date"
            ],
            item.get(
                "source_vaccine_key"
            )
            or "",
            item.get(
                "source_product_key"
            )
            or "",
        )
    )

    exposure_count = summary.get(
        "exposure_event_count"
    )

    if (
        exposure_count
        != len(
            exposures
        )
    ):
        raise ValueError(
            "antigen-history exposure count mismatch"
        )

    reported_last = summary.get(
        "last_exposure_date"
    )

    if (
        reported_last is not None
    ):
        reported_last = _as_date(
            reported_last
        )

    calculated_last = (
        exposures[
            -1
        ][
            "administration_date"
        ]
        if exposures
        else None
    )

    if (
        reported_last
        != calculated_last
    ):
        raise ValueError(
            "antigen-history last exposure mismatch"
        )

    dates = [
        item[
            "administration_date"
        ]
        for item
        in exposures
    ]

    duplicate_dates = {
        value
        for value in dates
        if dates.count(
            value
        ) > 1
    }

    safe = (
        summary.get(
            "history_scope"
        )
        == "complete"
        and summary.get(
            "history_state"
        )
        in {
            "documented_zero_exposure",
            "documented_exposures",
        }
        and summary.get(
            "safe_for_interval_evaluation"
        )
        is True
        and summary.get(
            "safe_for_basic_series_count"
        )
        is True
        and summary.get(
            "source_history_incomplete"
        )
        is False
        and not (
            summary.get(
                "unmapped_vaccine_keys"
            )
            or []
        )
        and not (
            summary.get(
                "ambiguous_same_day_exposure_dates"
            )
            or []
        )
        and not duplicate_dates
    )

    return {
        **summary,
        "exposures":
            exposures,

        "last_exposure_date":
            calculated_last,

        "_safe":
            safe,
    }


def _dtpa_exposures(
    antigen_history: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        exposure
        for exposure
        in antigen_history[
            "exposures"
        ]
        if exposure.get(
            "source_vaccine_key"
        )
        == "dtpa"
    ]


def _dtpa_episode_state(
    exposures: list[dict[str, Any]],
    episode_key: str,
) -> str:
    matching = [
        exposure
        for exposure
        in exposures
        if exposure.get(
            "pregnancy_episode_key"
        )
        == episode_key
    ]

    if not matching:
        return "none"

    if any(
        exposure.get(
            "gestational_age_weeks_at_administration"
        )
        is not None
        and exposure[
            "gestational_age_weeks_at_administration"
        ]
        >= 20
        for exposure
        in matching
    ):
        return "satisfied"

    if any(
        exposure.get(
            "gestational_age_weeks_at_administration"
        )
        is None
        for exposure
        in matching
    ):
        return "timing_unknown"

    return "early_only"


def _dtpa_series_note(
    exposure_count: int,
) -> tuple[str, str]:
    if exposure_count == 0:
        return (
            (
                "Após esta dTpa, o esquema básico contra difteria "
                "e tétano permanece incompleto e deverá ser "
                "completado com duas doses de dT conforme o PNI."
            ),
            (
                "After this dTpa dose, the basic diphtheria/tetanus "
                "series remains incomplete and should be completed "
                "with two dT doses according to the PNI."
            ),
        )

    if exposure_count == 1:
        return (
            (
                "Após esta dTpa, resta uma dose de dT para "
                "totalizar três doses contendo toxoides "
                "diftérico e tetânico."
            ),
            (
                "After this dTpa dose, one further dT dose remains "
                "to total three doses containing diphtheria and "
                "tetanus toxoids."
            ),
        )

    if exposure_count == 2:
        return (
            (
                "Esta dTpa pode compor a terceira dose do esquema "
                "básico contra difteria e tétano."
            ),
            (
                "This dTpa dose can form the third dose of the "
                "basic diphtheria/tetanus series."
            ),
        )

    return (
        (
            "O esquema básico contra difteria e tétano já possui "
            "pelo menos três exposições documentadas; a dTpa "
            "permanece indicada como dose específica desta "
            "gestação ou do puerpério correspondente."
        ),
        (
            "The basic diphtheria/tetanus series already contains "
            "at least three documented exposures; dTpa remains "
            "indicated as the pregnancy-specific dose or the "
            "corresponding postpartum dose."
        ),
    )


def evaluate_pni_dtpa_maternal_routine(
    *,
    assessment_date: date,
    pregnancy_status: str,
    gestational_age_weeks: int | None,
    pregnancy_episode_key: str | None,
    postpartum_days: int | None,
    postpartum_pregnancy_episode_key: str | None,
    antigen_history: Any,
    administration_safety_screen_state: str,
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate the national 2026 maternal dTpa schedule only.

    PT-BR is the canonical clinical interpretation and EN-GB is the
    required informational secondary interpretation.

    This evaluator does not diagnose contraindications and does not
    infer authorization for the exceptional 30-day minimum interval.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if (
        pregnancy_status
        not in {
            "pregnant",
            "not_pregnant",
            "unknown",
            "not_applicable",
        }
    ):
        raise ValueError(
            "invalid pregnancy_status"
        )

    if (
        administration_safety_screen_state
        not in DTPA_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized must be boolean"
        )

    if (
        postpartum_days is not None
        and (
            not isinstance(
                postpartum_days,
                int,
            )
            or postpartum_days < 0
            or postpartum_days > 365
        )
    ):
        raise ValueError(
            "postpartum_days must be an integer from 0 to 365"
        )

    if (
        pregnancy_status
        == "pregnant"
        and postpartum_days is not None
    ):
        raise ValueError(
            "pregnancy and postpartum context cannot coexist"
        )

    maternal_mode = None

    if pregnancy_status == "pregnant":
        maternal_mode = "pregnancy"

        if gestational_age_weeks is None:
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "gestational_age_weeks",
                ],
                interpretation_pt=(
                    "A idade gestacional é necessária para aplicar "
                    "a regra materna de dTpa."
                ),
                interpretation_en=(
                    "Gestational age is required to apply the "
                    "maternal dTpa rule."
                ),
            )

        if (
            not isinstance(
                gestational_age_weeks,
                int,
            )
            or gestational_age_weeks < 0
            or gestational_age_weeks > 45
        ):
            raise ValueError(
                "gestational_age_weeks must be an integer from 0 to 45"
            )

        if gestational_age_weeks < 20:
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "A dTpa materna de rotina é indicada a partir "
                    "da 20ª semana de gestação. Com a idade "
                    "gestacional informada, a dose não é indicada agora."
                ),
                interpretation_en=(
                    "Routine maternal dTpa is recommended from "
                    "gestational week 20. At the supplied gestational "
                    "age, the dose is not due now."
                ),
            )

    elif postpartum_days is not None:
        maternal_mode = "postpartum"

        if postpartum_days > 45:
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="not_applicable",
                interpretation_pt=(
                    "Esta regra materna de dTpa contempla o "
                    "puerpério somente até 45 dias após o parto."
                ),
                interpretation_en=(
                    "This maternal dTpa rule covers the postpartum "
                    "period only through 45 days after delivery."
                ),
            )

        if postpartum_pregnancy_episode_key is None:
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "postpartum_pregnancy_episode_key",
                ],
                interpretation_pt=(
                    "É necessário identificar a gestação que terminou "
                    "recentemente para confirmar se a dTpa foi perdida "
                    "durante essa gestação."
                ),
                interpretation_en=(
                    "The recently completed pregnancy must be "
                    "identified to confirm whether dTpa was missed "
                    "during that pregnancy."
                ),
            )

    elif pregnancy_status == "unknown":
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "É necessário confirmar se existe gestação ou "
                "puerpério elegível antes de aplicar a regra "
                "materna de dTpa."
            ),
            interpretation_en=(
                "Pregnancy or an eligible postpartum state must "
                "be confirmed before applying the maternal dTpa rule."
            ),
        )

    else:
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "Esta função avalia apenas a recomendação materna "
                "de dTpa durante a gestação ou até 45 dias pós-parto."
            ),
            interpretation_en=(
                "This function evaluates only the maternal dTpa "
                "recommendation during pregnancy or through "
                "45 days postpartum."
            ),
        )

    history = _normalise_dtpa_antigen_history(
        antigen_history,
        assessment_date=assessment_date,
    )

    if history is None:
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "É necessário reconciliar o histórico de vacinas "
                "contendo toxoides diftérico e tetânico antes de "
                "avaliar a dTpa materna."
            ),
            interpretation_en=(
                "History of vaccines containing diphtheria and "
                "tetanus toxoids must be reconciled before maternal "
                "dTpa can be evaluated."
            ),
        )

    dtpa_history = _dtpa_exposures(
        history
    )

    # --------------------------------------------------------
    # Exact pregnancy/postpartum dose suppression comes before
    # global history-safety gating to avoid recommending a
    # duplicate dose when a qualifying dose is already known.
    # --------------------------------------------------------

    if maternal_mode == "pregnancy":
        if pregnancy_episode_key is not None:
            episode_state = _dtpa_episode_state(
                dtpa_history,
                pregnancy_episode_key,
            )

            if episode_state == "satisfied":
                return _dtpa_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    interpretation_pt=(
                        "Há dTpa documentada nesta gestação, "
                        "administrada a partir da 20ª semana. "
                        "Não recomendar outra dose materna nesta gestação."
                    ),
                    interpretation_en=(
                        "A dTpa dose is documented in this pregnancy "
                        "at or after gestational week 20. Do not "
                        "recommend another maternal dose in this pregnancy."
                    ),
                )

            if episode_state == "timing_unknown":
                return _dtpa_result(
                    assessment_date=assessment_date,
                    decision="context_required",
                    missing_context=[
                        "gestational_age_weeks_at_prior_dtpa_administration",
                    ],
                    interpretation_pt=(
                        "Há dTpa vinculada à gestação atual, mas a "
                        "idade gestacional no momento da aplicação "
                        "não está documentada. Não é seguro decidir "
                        "revacinação automaticamente."
                    ),
                    interpretation_en=(
                        "A dTpa dose is linked to the current pregnancy, "
                        "but gestational age at administration is not "
                        "documented. Automatic revaccination cannot be "
                        "decided safely."
                    ),
                )

            if episode_state == "early_only":
                return _dtpa_result(
                    assessment_date=assessment_date,
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "Existe dTpa documentada nesta gestação antes "
                        "da 20ª semana. A fonte nacional revisada não "
                        "estabelece uma regra automática geral de "
                        "repetição para esse cenário; encaminhar para "
                        "avaliação da equipe de vacinação."
                    ),
                    interpretation_en=(
                        "A dTpa dose is documented in this pregnancy "
                        "before gestational week 20. The reviewed "
                        "national source does not establish a general "
                        "automatic repeat rule for this scenario; "
                        "refer for vaccination-team review."
                    ),
                )

        elif dtpa_history:
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "pregnancy_episode_key",
                ],
                interpretation_pt=(
                    "Existem doses de dTpa documentadas, mas falta "
                    "identificar a gestação atual para diferenciar "
                    "doses desta gestação das anteriores."
                ),
                interpretation_en=(
                    "dTpa doses are documented, but the current "
                    "pregnancy episode is not identified, so current "
                    "and previous pregnancy doses cannot be distinguished."
                ),
            )

        if any(
            exposure.get(
                "pregnancy_episode_key"
            )
            is None
            for exposure
            in dtpa_history
        ):
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "dtpa_pregnancy_episode_attribution",
                ],
                interpretation_pt=(
                    "Há dose de dTpa sem identificação da gestação "
                    "correspondente. É necessário reconciliar essa "
                    "atribuição antes de recomendar outra dose."
                ),
                interpretation_en=(
                    "A dTpa dose lacks pregnancy-episode attribution. "
                    "That attribution must be reconciled before another "
                    "dose can be recommended."
                ),
            )

    else:
        delivery_date = (
            assessment_date
            - timedelta(
                days=postpartum_days,
            )
        )

        # Any documented postpartum dTpa since the delivery
        # satisfies the missed-pregnancy postpartum opportunity.
        if any(
            exposure[
                "administration_date"
            ]
            >= delivery_date
            for exposure
            in dtpa_history
        ):
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "Há dTpa documentada após o parto atual. "
                    "Não recomendar outra dose por esta indicação "
                    "materna no mesmo puerpério."
                ),
                interpretation_en=(
                    "A dTpa dose is documented after the current "
                    "delivery. Do not recommend another dose for this "
                    "maternal indication in the same postpartum period."
                ),
            )

        episode_state = _dtpa_episode_state(
            dtpa_history,
            postpartum_pregnancy_episode_key,
        )

        if episode_state == "satisfied":
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "A dTpa foi documentada na gestação que terminou "
                    "recentemente, a partir da 20ª semana. A indicação "
                    "puerperal por dose perdida não se aplica."
                ),
                interpretation_en=(
                    "dTpa is documented in the recently completed "
                    "pregnancy at or after gestational week 20. "
                    "The postpartum missed-dose indication does not apply."
                ),
            )

        if episode_state == "timing_unknown":
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "gestational_age_weeks_at_prior_dtpa_administration",
                ],
                interpretation_pt=(
                    "Há dTpa vinculada à gestação recém-encerrada, "
                    "mas sem idade gestacional documentada na aplicação. "
                    "Não é seguro classificá-la automaticamente como "
                    "dose materna válida ou perdida."
                ),
                interpretation_en=(
                    "A dTpa dose is linked to the recently completed "
                    "pregnancy, but gestational age at administration "
                    "is undocumented. It cannot safely be classified "
                    "automatically as a valid or missed maternal dose."
                ),
            )

        if episode_state == "early_only":
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A única dTpa vinculada à gestação recém-encerrada "
                    "foi administrada antes da 20ª semana. A fonte "
                    "revisada não define regra automática geral de "
                    "repetição; encaminhar para avaliação."
                ),
                interpretation_en=(
                    "The only dTpa dose linked to the recently completed "
                    "pregnancy was administered before gestational "
                    "week 20. The reviewed source does not define a "
                    "general automatic repeat rule; refer for review."
                ),
            )

        if any(
            exposure.get(
                "pregnancy_episode_key"
            )
            is None
            and exposure[
                "administration_date"
            ]
            < delivery_date
            for exposure
            in dtpa_history
        ):
            return _dtpa_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "dtpa_pregnancy_episode_attribution",
                ],
                interpretation_pt=(
                    "Existe dTpa anterior ao parto sem identificação "
                    "da gestação correspondente. É necessário reconciliar "
                    "o registro antes de concluir que a dose foi perdida "
                    "na gestação recente."
                ),
                interpretation_en=(
                    "A pre-delivery dTpa dose lacks pregnancy-episode "
                    "attribution. The record must be reconciled before "
                    "concluding that the dose was missed in the recent "
                    "pregnancy."
                ),
            )

    # --------------------------------------------------------
    # No qualifying current/recent maternal dTpa is documented.
    # Definitive scheduling now requires safe cross-vaccine D/T
    # history.
    # --------------------------------------------------------

    if history[
        "_safe"
    ] is not True:
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico cruzado de vacinas com toxoides "
                "diftérico e tetânico está incompleto ou ambíguo. "
                "Não é seguro calcular série ou intervalo de dTpa."
            ),
            interpretation_en=(
                "Cross-vaccine diphtheria/tetanus toxoid history "
                "is incomplete or ambiguous. dTpa series status or "
                "interval cannot be calculated safely."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança registrou uma preocupação "
                "clínica. A situação do calendário não substitui a "
                "avaliação de precauções ou contraindicações; "
                "encaminhar para avaliação da equipe de vacinação."
            ),
            interpretation_en=(
                "The administration-safety screen identified a "
                "clinical concern. Calendar status does not replace "
                "assessment of precautions or contraindications; "
                "refer for vaccination-team review."
            ),
        )

    exposure_count = history[
        "exposure_event_count"
    ]

    series_pt, series_en = (
        _dtpa_series_note(
            exposure_count
        )
    )

    last_exposure_date = history[
        "last_exposure_date"
    ]

    recommended_interval_days = None
    minimum_interval_days = None
    minimum_interval_applied = False
    next_date = None
    due_now = False

    if last_exposure_date is None:
        due_now = True

    else:
        days_since_last = (
            assessment_date
            - last_exposure_date
        ).days

        recommended_interval_days = 60
        minimum_interval_days = 30

        if days_since_last >= 60:
            due_now = True

        elif (
            days_since_last >= 30
            and exceptional_minimum_interval_authorized
        ):
            due_now = True
            minimum_interval_applied = True

        else:
            interval_to_use = (
                30
                if exceptional_minimum_interval_authorized
                else 60
            )

            next_date = (
                last_exposure_date
                + timedelta(
                    days=interval_to_use,
                )
            )

            minimum_interval_applied = (
                exceptional_minimum_interval_authorized
            )

    if not due_now:
        if maternal_mode == "postpartum":
            postpartum_end = (
                delivery_date
                + timedelta(
                    days=45,
                )
            )

            if (
                next_date
                > postpartum_end
            ):
                return _dtpa_result(
                    assessment_date=assessment_date,
                    decision="special_pathway_review",
                    recommended_interval_days=60,
                    minimum_interval_days=30,
                    minimum_interval_applied=(
                        minimum_interval_applied
                    ),
                    interpretation_pt=(
                        "O próximo intervalo calculável ultrapassa "
                        "a janela materna de até 45 dias pós-parto. "
                        "A fonte não autoriza o software a extrapolar "
                        "automaticamente esta indicação; encaminhar "
                        "para avaliação da equipe de vacinação."
                    ),
                    interpretation_en=(
                        "The next calculable interval falls beyond "
                        "the maternal window of 45 days postpartum. "
                        "The source does not authorise the software "
                        "to extend this indication automatically; "
                        "refer for vaccination-team review."
                    ),
                )

        if (
            exceptional_minimum_interval_authorized
        ):
            interval_pt = (
                "Foi autorizada, após avaliação de risco-benefício, "
                "a utilização do intervalo mínimo excepcional de "
                "30 dias; esse intervalo ainda não foi alcançado."
            )

            interval_en = (
                "Use of the exceptional 30-day minimum interval "
                "has been explicitly authorised following risk-benefit "
                "assessment; that interval has not yet been reached."
            )

        else:
            interval_pt = (
                "O intervalo recomendado de 60 dias desde a última "
                "dose contendo toxoides diftérico e tetânico ainda "
                "não foi alcançado."
            )

            interval_en = (
                "The recommended 60-day interval since the last dose "
                "containing diphtheria and tetanus toxoids has not "
                "yet been reached."
            )

        safety_pt = (
            ""
            if administration_safety_screen_state
            == "screened_no_concern"
            else (
                " Antes da administração futura, ainda será "
                "necessário registrar a triagem de segurança."
            )
        )

        safety_en = (
            ""
            if administration_safety_screen_state
            == "screened_no_concern"
            else (
                " Administration-safety screening must still be "
                "documented before the future dose is given."
            )
        )

        return _dtpa_result(
            assessment_date=assessment_date,
            decision="future_recommendation",
            recommended_date=next_date,
            recommended_interval_days=60,
            minimum_interval_days=30,
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                f"{interval_pt} "
                f"Próxima data calculada: "
                f"{next_date.isoformat()}. "
                f"{series_pt}"
                f"{safety_pt}"
            ),
            interpretation_en=(
                f"{interval_en} "
                f"Next calculated date: "
                f"{next_date.isoformat()}. "
                f"{series_en}"
                f"{safety_en}"
            ),
        )

    # At this point the calendar indicates a dose now.
    # Safety clearance is deliberately separate.
    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _dtpa_result(
            assessment_date=assessment_date,
            decision="context_required",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Pelo calendário, a dTpa pode estar indicada agora, "
                "mas a triagem de segurança para administração ainda "
                "não foi registrada. O calendário não substitui a "
                "avaliação de precauções e contraindicações."
            ),
            interpretation_en=(
                "By the vaccination schedule, dTpa may be due now, "
                "but administration-safety screening has not yet been "
                "documented. Calendar status does not replace assessment "
                "of precautions and contraindications."
            ),
        )

    if maternal_mode == "pregnancy":
        context_pt = (
            "Gestante a partir da 20ª semana, sem dTpa materna "
            "válida documentada nesta gestação: recomendar dTpa agora."
        )

        context_en = (
            "Pregnant person at or beyond gestational week 20, "
            "without a documented valid maternal dTpa dose in this "
            "pregnancy: recommend dTpa now."
        )

    else:
        context_pt = (
            "Puérpera dentro de 45 dias pós-parto, sem dTpa materna "
            "válida documentada na gestação recente ou no puerpério: "
            "recomendar dTpa agora."
        )

        context_en = (
            "Postpartum person within 45 days of delivery, without "
            "a documented valid maternal dTpa dose in the recent "
            "pregnancy or postpartum period: recommend dTpa now."
        )

    if minimum_interval_applied:
        interval_pt = (
            " Foi utilizada autorização explícita para o intervalo "
            "mínimo excepcional de 30 dias após avaliação "
            "de risco-benefício."
        )

        interval_en = (
            " Explicit authorisation for the exceptional 30-day "
            "minimum interval was used following risk-benefit assessment."
        )

    else:
        interval_pt = ""
        interval_en = ""

    return _dtpa_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_interval_days=(
            recommended_interval_days
        ),
        minimum_interval_days=(
            minimum_interval_days
        ),
        minimum_interval_applied=(
            minimum_interval_applied
        ),
        interpretation_pt=(
            f"{context_pt}"
            f"{interval_pt} "
            f"{series_pt}"
        ),
        interpretation_en=(
            f"{context_en}"
            f"{interval_en} "
            f"{series_en}"
        ),
    )



HEPATITIS_A_CHILD_RULE_ID = (
    "PNI26-HA-CHILD-ROUTINE-001"
)

HEPATITIS_A_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

HEPATITIS_A_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

PNI_ADMINISTRATION_SAFETY_SCREEN_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}


def _add_months_clamped(
    value: date,
    months: int,
) -> date:
    total_month = (
        value.year * 12
        + value.month - 1
        + months
    )

    year = (
        total_month
        // 12
    )

    month = (
        total_month
        % 12
        + 1
    )

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def _hepatitis_a_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "hepatitis_a",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                HEPATITIS_A_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                HEPATITIS_A_SOURCE_URL,

            "source_snapshot_date":
                HEPATITIS_A_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_hepatitis_a_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "hepatitis_a"
    ):
        raise ValueError(
            "hepatitis A rule requires vaccine_key=hepatitis_a"
        )

    allowed_states = {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }

    state = value.get(
        "history_state"
    )

    if state not in allowed_states:
        raise ValueError(
            "invalid hepatitis A history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "hepatitis A administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "hepatitis A administration_date cannot follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_hepatitis_a_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    history: Any = None,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate only the 2026 national routine childhood hepatitis A rule.

    PT-BR is primary and EN-GB is the complete secondary
    interpretation.

    RIE/CRIE special-condition hepatitis A schedules are deliberately
    outside this routine-layer evaluator.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    twelve_month_date = (
        _add_months_clamped(
            date_of_birth,
            12,
        )
    )

    routine_due_date = (
        _add_months_clamped(
            date_of_birth,
            15,
        )
    )

    fifth_birthday = (
        _add_months_clamped(
            date_of_birth,
            60,
        )
    )

    normalised_history = (
        _normalise_hepatitis_a_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    doses = (
        normalised_history[
            "doses"
        ]
        if normalised_history
        is not None
        else []
    )

    valid_child_doses = [
        dose
        for dose
        in doses
        if (
            dose[
                "administration_date"
            ]
            >= twelve_month_date
            and dose[
                "administration_date"
            ]
            < fifth_birthday
        )
    ]

    pre_12_month_doses = [
        dose
        for dose
        in doses
        if (
            dose[
                "administration_date"
            ]
            < twelve_month_date
        )
    ]

    if valid_child_doses:
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há uma dose de vacina hepatite A documentada "
                "em idade válida para o esquema infantil. "
                "A regra rotineira de dose única está satisfeita."
            ),
            interpretation_en=(
                "One hepatitis A vaccine dose is documented at "
                "a valid age for the childhood schedule. "
                "The routine one-dose requirement is satisfied."
            ),
        )

    if pre_12_month_doses:
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há dose de hepatite A documentada antes dos "
                "12 meses de idade. A fonte nacional contraindica "
                "a vacina nessa faixa etária e não foi identificada "
                "regra automática geral de repetição; encaminhar "
                "para avaliação da equipe de vacinação."
            ),
            interpretation_en=(
                "A hepatitis A dose is documented before "
                "12 months of age. The national source "
                "contraindicates vaccination at that age and no "
                "general automatic repeat rule was identified; "
                "refer for vaccination-team review."
            ),
        )

    if (
        assessment_date
        < twelve_month_date
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A criança ainda não atingiu 12 meses. "
                "A fonte nacional contraindica a vacina hepatite A "
                "antes dessa idade; a agenda rotineira é aos 15 meses."
            ),
            interpretation_en=(
                "The child is younger than 12 months. "
                "The national source contraindicates hepatitis A "
                "vaccination before this age; the routine schedule "
                "dose is at 15 months."
            ),
        )

    if (
        assessment_date
        < routine_due_date
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A agenda rotineira nacional prevê uma dose de "
                "hepatite A aos 15 meses. Com a idade atual, "
                "a dose de rotina ainda não está vencida."
            ),
            interpretation_en=(
                "The national routine schedule gives one "
                "hepatitis A dose at 15 months. At the current age, "
                "the routine dose is not yet due."
            ),
        )

    if (
        assessment_date
        >= fifth_birthday
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A janela rotineira infantil do PNI para hepatite A "
                "termina antes do quinto aniversário. Esta avaliação "
                "não inclui os esquemas especiais da RIE/CRIE."
            ),
            interpretation_en=(
                "The PNI routine childhood hepatitis A window ends "
                "before the fifth birthday. This assessment does not "
                "include special RIE/CRIE schedules."
            ),
        )

    if normalised_history is None:
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "A criança está na janela rotineira para hepatite A, "
                "mas é necessário verificar o histórico vacinal antes "
                "de recomendar a dose."
            ),
            interpretation_en=(
                "The child is within the routine hepatitis A window, "
                "but vaccination history must be checked before "
                "recommending the dose."
            ),
        )

    state = normalised_history[
        "history_state"
    ]

    if state in {
        "unknown",
        "partial_record",
    }:
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de hepatite A é desconhecido ou parcial. "
                "Não tratar ausência de comprovação como zero dose "
                "documentado."
            ),
            interpretation_en=(
                "Hepatitis A history is unknown or partial. "
                "Do not treat lack of proof as documented "
                "zero-dose history."
            ),
        )

    if (
        state
        != "documented_zero_dose"
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro não permite confirmar de forma segura "
                "a situação rotineira da vacina hepatite A."
            ),
            interpretation_en=(
                "The record does not safely establish routine "
                "hepatitis A vaccination status."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Pelo calendário, a dose de hepatite A está indicada, "
                "mas a triagem de segurança para administração ainda "
                "não foi registrada. Elegibilidade no calendário não "
                "substitui a avaliação de contraindicações."
            ),
            interpretation_en=(
                "By the schedule, the hepatitis A dose is indicated, "
                "but administration-safety screening has not yet been "
                "documented. Schedule eligibility does not replace "
                "contraindication screening."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _hepatitis_a_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "clínica. Encaminhar para avaliação antes da "
                "administração da vacina hepatite A."
            ),
            interpretation_en=(
                "The administration-safety screen identified a "
                "clinical concern. Refer for review before "
                "hepatitis A vaccination."
            ),
        )

    return _hepatitis_a_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "Criança na janela rotineira do PNI, sem dose "
            "documentada de hepatite A e com triagem de segurança "
            "sem preocupação registrada: recomendar 1 dose agora. "
            "Não é necessário intervalo em relação às demais vacinas "
            "do Calendário Nacional de Vacinação."
        ),
        interpretation_en=(
            "The child is within the PNI routine window, has no "
            "documented hepatitis A dose, and administration-safety "
            "screening records no concern: recommend one dose now. "
            "No interval is required from other vaccines in the "
            "National Vaccination Schedule."
        ),
    )



HPV4_ROUTINE_RULE_ID = (
    "PNI26-HPV4-ROUTINE-9-14-001"
)

HPV4_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

HPV4_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)


def _hpv4_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "hpv4",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                HPV4_ROUTINE_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                HPV4_SOURCE_URL,

            "source_snapshot_date":
                HPV4_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_hpv4_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "hpv4"
    ):
        raise ValueError(
            "HPV4 routine rule requires vaccine_key=hpv4"
        )

    allowed_states = {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }

    state = value.get(
        "history_state"
    )

    if state not in allowed_states:
        raise ValueError(
            "invalid HPV4 history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "HPV4 administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "HPV4 administration_date cannot follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_hpv4_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    pregnancy_status: str,
    history: Any = None,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate only the 2026 national HPV4 routine layer for ages 9-14.

    The 15-19 rescue strategy and special-priority HPV pathways are
    deliberately outside this evaluator.

    PT-BR is primary and EN-GB is the required secondary
    interpretation.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        pregnancy_status
        not in {
            "pregnant",
            "not_pregnant",
            "unknown",
            "not_applicable",
        }
    ):
        raise ValueError(
            "invalid pregnancy_status"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    ninth_birthday = (
        _add_months_clamped(
            date_of_birth,
            108,
        )
    )

    fifteenth_birthday = (
        _add_months_clamped(
            date_of_birth,
            180,
        )
    )

    normalised_history = (
        _normalise_hpv4_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    doses = (
        normalised_history[
            "doses"
        ]
        if normalised_history
        is not None
        else []
    )

    routine_window_doses = [
        dose
        for dose
        in doses
        if (
            dose[
                "administration_date"
            ]
            >= ninth_birthday
            and dose[
                "administration_date"
            ]
            < fifteenth_birthday
        )
    ]

    pre_routine_doses = [
        dose
        for dose
        in doses
        if (
            dose[
                "administration_date"
            ]
            < ninth_birthday
        )
    ]

    if routine_window_doses:
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há pelo menos uma dose de HPV4 documentada na "
                "faixa etária rotineira de 9 a 14 anos. "
                "O esquema básico rotineiro de dose única está satisfeito."
            ),
            interpretation_en=(
                "At least one HPV4 dose is documented within the "
                "routine 9-to-14-year age range. "
                "The routine one-dose schedule is satisfied."
            ),
        )

    if pre_routine_doses:
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há dose de HPV4 documentada antes dos 9 anos, fora "
                "da faixa rotineira avaliada por esta regra. "
                "Existem indicações especiais com esquemas próprios; "
                "não inferir automaticamente a situação do esquema."
            ),
            interpretation_en=(
                "An HPV4 dose is documented before age 9, outside "
                "the routine age range evaluated by this rule. "
                "Special indications have their own schedules; "
                "do not infer routine-series status automatically."
            ),
        )

    if (
        assessment_date
        < ninth_birthday
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A vacinação rotineira contra HPV inicia aos 9 anos. "
                "Com a idade atual, a dose rotineira ainda não está indicada."
            ),
            interpretation_en=(
                "Routine HPV vaccination begins at age 9. "
                "At the current age, the routine dose is not yet due."
            ),
        )

    if (
        assessment_date
        >= fifteenth_birthday
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A faixa rotineira de HPV4 termina antes do "
                "15º aniversário. Pessoas de 15 a 19 anos podem "
                "ter indicação por estratégia de resgate vigente, "
                "que é uma camada separada desta regra."
            ),
            interpretation_en=(
                "The routine HPV4 age range ends before the "
                "15th birthday. People aged 15 to 19 may be eligible "
                "under a current rescue strategy, which is separate "
                "from this routine rule."
            ),
        )

    if normalised_history is None:
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "A pessoa está na faixa etária rotineira do HPV4, "
                "mas o histórico vacinal precisa ser verificado "
                "antes de recomendar a dose."
            ),
            interpretation_en=(
                "The person is within the routine HPV4 age range, "
                "but vaccination history must be checked before "
                "recommending the dose."
            ),
        )

    state = normalised_history[
        "history_state"
    ]

    if state in {
        "unknown",
        "partial_record",
    }:
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de HPV4 é desconhecido ou parcial. "
                "Não tratar histórico desconhecido como zero dose "
                "documentado nesta regra rotineira."
            ),
            interpretation_en=(
                "HPV4 history is unknown or partial. "
                "Do not treat unknown history as documented "
                "zero-dose history in this routine rule."
            ),
        )

    if (
        state
        != "documented_zero_dose"
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não permite confirmar "
                "com segurança a situação rotineira do HPV4."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "routine HPV4 vaccination status."
            ),
        )

    if (
        pregnancy_status
        == "unknown"
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "É necessário esclarecer o status gestacional antes "
                "da administração do HPV4, pois a vacina é "
                "contraindicada durante a gestação."
            ),
            interpretation_en=(
                "Pregnancy status must be clarified before HPV4 "
                "administration because the vaccine is contraindicated "
                "during pregnancy."
            ),
        )

    if (
        pregnancy_status
        == "pregnant"
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A vacina HPV4 é contraindicada durante a gestação. "
                "Não administrar pela regra rotineira; seguir a "
                "orientação clínica correspondente e retomar a "
                "avaliação vacinal após a gestação quando aplicável."
            ),
            interpretation_en=(
                "HPV4 is contraindicated during pregnancy. "
                "Do not administer it under the routine rule; follow "
                "the appropriate clinical guidance and reassess "
                "vaccination after pregnancy when applicable."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Pelo calendário, a dose de HPV4 está indicada, "
                "mas a triagem de segurança ainda não foi registrada. "
                "Elegibilidade no calendário não substitui a avaliação "
                "de contraindicações."
            ),
            interpretation_en=(
                "By the schedule, the HPV4 dose is indicated, "
                "but administration-safety screening has not yet been "
                "documented. Schedule eligibility does not replace "
                "contraindication screening."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _hpv4_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "clínica. Encaminhar para avaliação antes da "
                "administração da vacina HPV4."
            ),
            interpretation_en=(
                "The administration-safety screen identified a "
                "clinical concern. Refer for review before HPV4 "
                "vaccination."
            ),
        )

    return _hpv4_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "Pessoa na faixa rotineira de 9 a 14 anos, sem dose "
            "documentada de HPV4, sem gestação e com triagem de "
            "segurança sem preocupação registrada: recomendar "
            "1 dose agora. Não é necessário intervalo em relação "
            "às demais vacinas do Calendário Nacional de Vacinação."
        ),
        interpretation_en=(
            "The person is within the routine 9-to-14-year age range, "
            "has no documented HPV4 dose, is not pregnant, and "
            "administration-safety screening records no concern: "
            "recommend one dose now. No interval is required from "
            "other vaccines in the National Vaccination Schedule."
        ),
    )



BCG_CHILD_ROUTINE_RULE_ID = (
    "PNI26-BCG-CHILD-ROUTINE-001"
)

BCG_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

BCG_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

BCG_NEONATAL_MAX_AGE_DAYS = 27
BCG_WEIGHT_THRESHOLD_GRAMS = 2000


def _bcg_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "bcg",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                BCG_CHILD_ROUTINE_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                BCG_SOURCE_URL,

            "source_snapshot_date":
                BCG_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_bcg_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "bcg"
    ):
        raise ValueError(
            "BCG routine rule requires vaccine_key=bcg"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid BCG history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "BCG administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "BCG administration_date cannot follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    if (
        state
        == "documented_zero_dose"
        and doses
    ):
        raise ValueError(
            "documented_zero_dose cannot contain BCG doses"
        )

    return {
        **value,
        "doses":
            doses,
    }


def _normalise_bcg_evidence(
    evidence: Any,
) -> dict[str, bool | None] | None:
    if evidence is None:
        return None

    value = _as_plain_dict(
        evidence
    )

    keys = (
        "vaccination_record_present",
        "scar_present",
        "palpable_nodule_present",
    )

    result = {
        key:
            value.get(
                key
            )
        for key
        in keys
    }

    for key, item in result.items():
        if (
            item is not None
            and not isinstance(
                item,
                bool,
            )
        ):
            raise ValueError(
                f"{key} must be boolean or null"
            )

    if all(
        item is None
        for item in result.values()
    ):
        raise ValueError(
            "BCG evidence requires at least one assessed field"
        )

    return result


def evaluate_pni_bcg_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    history: Any = None,
    current_weight_grams: int | None = None,
    bcg_vaccination_evidence: Any = None,
    special_condition_codes: list[str] | None = None,
    epidemiologic_context_codes: list[str] | None = None,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate only routine childhood BCG for tuberculosis protection.

    Separate BCG pathways such as hanseniasis-contact immunoprophylaxis,
    HIV/immunodeficiency, newborn tuberculosis contact and exceptional
    invalid-dose revaccination are deliberately not evaluated here.

    PT-BR is primary and EN-GB is the required secondary
    interpretation.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        current_weight_grams is not None
        and (
            not isinstance(
                current_weight_grams,
                int,
            )
            or isinstance(
                current_weight_grams,
                bool,
            )
            or current_weight_grams < 1
        )
    ):
        raise ValueError(
            "current_weight_grams must be a positive integer"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    special_condition_codes = list(
        special_condition_codes
        or []
    )

    epidemiologic_context_codes = list(
        epidemiologic_context_codes
        or []
    )

    for collection_name, values in (
        (
            "special_condition_codes",
            special_condition_codes,
        ),
        (
            "epidemiologic_context_codes",
            epidemiologic_context_codes,
        ),
    ):
        if any(
            not isinstance(
                item,
                str,
            )
            or not item.strip()
            for item
            in values
        ):
            raise ValueError(
                f"{collection_name} must contain non-empty strings"
            )

    fifth_birthday = (
        _add_months_clamped(
            date_of_birth,
            60,
        )
    )

    age_days = (
        assessment_date
        - date_of_birth
    ).days

    history_value = (
        _normalise_bcg_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    evidence = (
        _normalise_bcg_evidence(
            bcg_vaccination_evidence
        )
    )

    history_state = (
        history_value.get(
            "history_state"
        )
        if history_value
        is not None
        else None
    )

    doses = (
        history_value.get(
            "doses"
        )
        or []
        if history_value
        is not None
        else []
    )

    positive_evidence = (
        evidence is not None
        and any(
            value is True
            for value
            in evidence.values()
        )
    )

    # --------------------------------------------------------
    # Explicit special/epidemiologic context must not be
    # swallowed by the routine one-dose branch. BCG has
    # separate national pathways where additional or different
    # logic may apply.
    # --------------------------------------------------------

    if (
        special_condition_codes
        or epidemiologic_context_codes
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há contexto clínico especial ou epidemiológico "
                "registrado. A regra rotineira de BCG para proteção "
                "contra formas graves de tuberculose não deve substituir "
                "os ramos específicos do PNI, como hanseníase, HIV, "
                "imunodeficiência ou contato com tuberculose."
            ),
            interpretation_en=(
                "A special clinical or epidemiological context is "
                "recorded. The routine BCG rule for protection against "
                "severe tuberculosis must not replace specific PNI "
                "pathways such as hanseniasis, HIV, immunodeficiency "
                "or tuberculosis-contact management."
            ),
        )

    # --------------------------------------------------------
    # The routine child layer ends before the fifth birthday.
    # Separate hanseniasis pathways may extend beyond this age,
    # but are not inferred here.
    # --------------------------------------------------------

    if (
        assessment_date
        >= fifth_birthday
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A rotina de BCG para proteção infantil contra formas "
                "graves de tuberculose termina antes do quinto "
                "aniversário. Este resultado não exclui indicações "
                "especiais, como imunoprofilaxia de contatos de hanseníase."
            ),
            interpretation_en=(
                "The routine childhood BCG layer for protection against "
                "severe tuberculosis ends before the fifth birthday. "
                "This result does not exclude separate indications such "
                "as hanseniasis-contact immunoprophylaxis."
            ),
        )

    # --------------------------------------------------------
    # Positive BCG evidence can establish prior vaccination:
    # card/record, scar, or palpable nodule.
    #
    # Explicit zero-dose history conflicting with positive
    # evidence is reconciled rather than silently choosing one.
    # --------------------------------------------------------

    if (
        history_state
        == "documented_zero_dose"
        and positive_evidence
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico registra zero dose, mas há evidência "
                "positiva de vacinação BCG por registro, cicatriz ou "
                "nódulo palpável. É necessário reconciliar os registros "
                "antes de decidir sobre nova dose."
            ),
            interpretation_en=(
                "History records zero doses, but positive BCG "
                "vaccination evidence exists through a record, scar or "
                "palpable nodule. The records must be reconciled before "
                "deciding on another dose."
            ),
        )

    if (
        doses
        or positive_evidence
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há comprovação de vacinação BCG por dose documentada, "
                "registro, cicatriz vacinal ou nódulo palpável. "
                "A rotina de dose única está satisfeita. A ausência "
                "isolada de cicatriz não constitui indicação rotineira "
                "de revacinação."
            ),
            interpretation_en=(
                "BCG vaccination is evidenced by a documented dose, "
                "record, vaccination scar or palpable nodule. "
                "The routine one-dose schedule is satisfied. "
                "Absence of a scar alone is not a routine indication "
                "for revaccination."
            ),
        )

    # --------------------------------------------------------
    # Assessed absence of record/scar/nodule does NOT prove
    # documented zero-dose history because some vaccinated
    # children do not develop a scar.
    # --------------------------------------------------------

    if (
        history_value is None
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Não há histórico vacinal reconciliado de BCG. "
                "Ausência de registro, cicatriz ou nódulo por si só "
                "não deve ser convertida automaticamente em zero dose."
            ),
            interpretation_en=(
                "No reconciled BCG vaccination history is available. "
                "Absence of a record, scar or nodule alone must not "
                "be converted automatically into documented zero-dose "
                "history."
            ),
        )

    if (
        history_state
        in {
            "unknown",
            "partial_record",
        }
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de BCG é desconhecido ou parcial e não "
                "há evidência positiva suficiente para confirmar "
                "vacinação. É necessário reconciliar o histórico; "
                "cicatriz ausente não equivale a zero dose."
            ),
            interpretation_en=(
                "BCG history is unknown or partial and there is no "
                "sufficient positive evidence to confirm vaccination. "
                "History must be reconciled; an absent scar does not "
                "equal documented zero-dose history."
            ),
        )

    if (
        history_state
        != "documented_zero_dose"
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não estabelece com segurança "
                "a situação vacinal rotineira da BCG."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "routine BCG vaccination status."
            ),
        )

    # --------------------------------------------------------
    # Newborn weight gate:
    # Ministry sources define the neonatal period as the first
    # 28 days. For an unvaccinated newborn, current weight is
    # required because the PNI defers BCG below 2,000 g until
    # that current weight is reached.
    # --------------------------------------------------------

    if (
        age_days
        <= BCG_NEONATAL_MAX_AGE_DAYS
    ):
        if (
            current_weight_grams
            is None
        ):
            return _bcg_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "current_weight_grams",
                ],
                interpretation_pt=(
                    "Para recém-nascido sem vacinação BCG documentada, "
                    "é necessário informar o peso atual. O PNI orienta "
                    "adiar a BCG abaixo de 2.000 g até que o recém-nascido "
                    "atinja esse peso. Peso ao nascer não substitui "
                    "o peso atual."
                ),
                interpretation_en=(
                    "For an unvaccinated newborn, current weight is "
                    "required. The PNI advises deferring BCG below "
                    "2,000 g until the newborn reaches that weight. "
                    "Birth weight does not substitute for current weight."
                ),
            )

        if (
            current_weight_grams
            < BCG_WEIGHT_THRESHOLD_GRAMS
        ):
            return _bcg_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "Recém-nascido com peso atual inferior a 2.000 g: "
                    "adiar a BCG até atingir 2.000 g. O peso utilizado "
                    "nesta decisão é o peso atual, não o peso ao nascer."
                ),
                interpretation_en=(
                    "The newborn's current weight is below 2,000 g: "
                    "defer BCG until 2,000 g is reached. This decision "
                    "uses current weight, not birth weight."
                ),
            )

    elif (
        current_weight_grams is not None
        and current_weight_grams
        < BCG_WEIGHT_THRESHOLD_GRAMS
    ):
        # The automatic source wording is specifically for
        # newborns. An extremely low current weight outside the
        # neonatal period is not promoted into an invented
        # routine rule.
        return _bcg_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Foi informado peso atual inferior a 2.000 g fora do "
                "período neonatal. A orientação automática de adiamento "
                "por peso na fonte revisada é formulada para "
                "recém-nascidos; não extrapolar essa regra. Encaminhar "
                "para avaliação da equipe de vacinação."
            ),
            interpretation_en=(
                "A current weight below 2,000 g is reported outside "
                "the neonatal period. The reviewed source expresses "
                "the automatic weight-deferral rule for newborns; "
                "do not extrapolate that rule automatically. Refer "
                "for vaccination-team review."
            ),
        )

    # --------------------------------------------------------
    # Calendar eligibility is deliberately separate from
    # administration-safety clearance.
    # --------------------------------------------------------

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Pelo calendário rotineiro, a BCG pode estar indicada, "
                "mas a triagem de segurança para administração ainda "
                "não foi registrada. A regra de calendário não substitui "
                "a avaliação de precauções, contraindicações ou "
                "imunodeficiência."
            ),
            interpretation_en=(
                "Under the routine schedule, BCG may be indicated, "
                "but administration-safety screening has not yet been "
                "documented. Schedule status does not replace assessment "
                "of precautions, contraindications or immunodeficiency."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _bcg_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "clínica. A BCG é uma vacina viva e possui precauções "
                "e contraindicações específicas; encaminhar para "
                "avaliação antes da administração."
            ),
            interpretation_en=(
                "The administration-safety screen identified a "
                "clinical concern. BCG is a live vaccine with specific "
                "precautions and contraindications; refer for review "
                "before administration."
            ),
        )

    return _bcg_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "Criança na faixa rotineira do PNI, com zero dose "
            "documentado de BCG, sem contexto especial registrado e "
            "com triagem de segurança sem preocupação: recomendar "
            "1 dose agora. Para recém-nascidos, o limiar de 2.000 g "
            "foi aplicado usando peso atual. Não é necessário intervalo "
            "em relação às demais vacinas do Calendário Nacional."
        ),
        interpretation_en=(
            "The child is within the PNI routine age range, has "
            "documented zero-dose BCG history, no recorded special "
            "context, and administration-safety screening records no "
            "concern: recommend one dose now. For newborns, the "
            "2,000 g threshold was applied using current weight. "
            "No interval is required from other vaccines in the "
            "National Vaccination Schedule."
        ),
    )



HEPATITIS_B_BIRTH_RULE_ID = (
    "PNI26-HB-BIRTH-ROUTINE-001"
)

HEPATITIS_B_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

HEPATITIS_B_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)


def _hepatitis_b_birth_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "hepatitis_b",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                HEPATITIS_B_BIRTH_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                2,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                HEPATITIS_B_SOURCE_URL,

            "source_snapshot_date":
                HEPATITIS_B_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_hepatitis_b_birth_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "hepatitis_b"
    ):
        raise ValueError(
            "hepatitis-B birth-dose rule requires "
            "vaccine_key=hepatitis_b"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid hepatitis-B history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "hepatitis-B administration_date cannot "
                "precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "hepatitis-B administration_date cannot "
                "follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    if (
        state
        == "documented_zero_dose"
        and doses
    ):
        raise ValueError(
            "documented_zero_dose cannot contain hepatitis-B doses"
        )

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_hepatitis_b_birth_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    maternal_hbsag_status: str | None,
    history: Any = None,
    special_condition_codes: list[str] | None = None,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate only the monovalent hepatitis-B birth-dose opportunity.

    The later pentavalent infant schedule and maternal/perinatal
    immunoprophylaxis pathways are deliberately separate.

    PT-BR is primary and EN-GB is required on every result.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    allowed_hbsag = {
        None,
        "positive",
        "negative",
        "unknown_or_unavailable",
    }

    if (
        maternal_hbsag_status
        not in allowed_hbsag
    ):
        raise ValueError(
            "invalid maternal_hbsag_status"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    special_condition_codes = list(
        special_condition_codes
        or []
    )

    if any(
        not isinstance(
            item,
            str,
        )
        or not item.strip()
        for item
        in special_condition_codes
    ):
        raise ValueError(
            "special_condition_codes must contain "
            "non-empty strings"
        )

    one_month_birthday = (
        _add_months_clamped(
            date_of_birth,
            1,
        )
    )

    active_birth_window = (
        assessment_date
        <= one_month_birthday
    )

    history_value = (
        _normalise_hepatitis_b_birth_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    history_state = (
        history_value.get(
            "history_state"
        )
        if history_value
        is not None
        else None
    )

    doses = []

    if history_value is not None:
        doses = list(
            history_value.get(
                "doses"
            )
            or []
        )

    birth_window_doses = [
        dose
        for dose
        in doses
        if (
            dose[
                "administration_date"
            ]
            <= one_month_birthday
        )
    ]

    # --------------------------------------------------------
    # Explicit maternal/perinatal context must not be swallowed
    # by an ordinary routine-birth-dose completion result.
    # --------------------------------------------------------

    if (
        maternal_hbsag_status
        == "positive"
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A mãe possui HBsAg positivo. O recém-nascido pertence "
                "à via específica de prevenção da transmissão vertical, "
                "que inclui vacina hepatite B monovalente e "
                "imunoglobulina humana anti-hepatite B em sítios "
                "distintos. Esta regra rotineira de dose ao nascer não "
                "substitui esse protocolo perinatal."
            ),
            interpretation_en=(
                "Maternal HBsAg is positive. The newborn belongs to "
                "the specific vertical-transmission prevention pathway, "
                "which includes monovalent hepatitis-B vaccine and "
                "hepatitis-B immune globulin at separate sites. "
                "This routine birth-dose rule does not replace that "
                "perinatal protocol."
            ),
        )

    if (
        maternal_hbsag_status
        == "unknown_or_unavailable"
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O estado materno para HBsAg é desconhecido ou "
                "indisponível. A Instrução Normativa direciona esse "
                "cenário para avaliação da via de imunoprofilaxia "
                "perinatal. Não tratar estado materno desconhecido como "
                "resultado negativo e não inferir automaticamente a "
                "indicação de imunoglobulina nesta regra."
            ),
            interpretation_en=(
                "Maternal HBsAg status is unknown or unavailable. "
                "The national instruction directs this scenario for "
                "assessment under the perinatal immunoprophylaxis "
                "pathway. Do not treat unknown maternal status as "
                "negative and do not automatically infer an immune-"
                "globulin indication in this rule."
            ),
        )

    if special_condition_codes:
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há condição clínica especial registrada. A avaliação "
                "de hepatite B deve seguir o ramo específico aplicável; "
                "esta regra implementa somente a dose monovalente "
                "rotineira ao nascer."
            ),
            interpretation_en=(
                "A special clinical condition is recorded. "
                "Hepatitis-B vaccination must follow the applicable "
                "specific pathway; this rule implements only the "
                "routine monovalent birth-dose layer."
            ),
        )

    # Maternal status not supplied is relevant while the
    # perinatal/birth-dose opportunity is still active.
    if (
        maternal_hbsag_status
        is None
        and active_birth_window
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O estado materno para HBsAg não foi informado durante "
                "a janela ativa da dose ao nascer. A vacinação contra "
                "hepatite B permanece tempo-dependente e não deve ser "
                "atrasada apenas por essa ausência de informação, mas "
                "esta regra rotineira não pode excluir uma via perinatal "
                "concomitante sem esclarecer o contexto materno."
            ),
            interpretation_en=(
                "Maternal HBsAg status was not supplied during the "
                "active birth-dose window. Hepatitis-B vaccination "
                "remains time-sensitive and should not be delayed solely "
                "because that information is missing, but this routine "
                "rule cannot exclude a concurrent perinatal pathway "
                "without clarifying maternal context."
            ),
        )

    # --------------------------------------------------------
    # A documented hepatitis-B dose administered inside the
    # birth-dose opportunity satisfies this narrow layer.
    #
    # A later pentavalent history is a different vaccine key
    # and is not consumed or inferred here.
    # --------------------------------------------------------

    if birth_window_doses:
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há dose de vacina hepatite B documentada dentro da "
                "janela da dose ao nascer. Esta camada rotineira está "
                "satisfeita. As doses infantis posteriores com a vacina "
                "pentavalente aos 2, 4 e 6 meses pertencem a outra "
                "etapa do esquema."
            ),
            interpretation_en=(
                "A hepatitis-B vaccine dose is documented within the "
                "birth-dose opportunity window. This routine layer is "
                "satisfied. Later infant doses using pentavalent vaccine "
                "at 2, 4 and 6 months belong to a separate schedule layer."
            ),
        )

    # --------------------------------------------------------
    # Once the one-month opportunity has passed, this specific
    # monovalent birth dose must not be invented later.
    # --------------------------------------------------------

    if not active_birth_window:
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A oportunidade específica da dose monovalente de "
                "hepatite B ao nascer terminou após 1 mês de vida. "
                "Não administrar uma dose tardia fingindo tratar-se "
                "da dose ao nascer. Para lactentes que perderam essa "
                "oportunidade, o PNI orienta o esquema com vacina "
                "pentavalente aos 2, 4 e 6 meses."
            ),
            interpretation_en=(
                "The specific monovalent hepatitis-B birth-dose "
                "opportunity has ended after 1 month of life. "
                "Do not create a delayed dose and classify it as the "
                "birth dose. For infants who missed that opportunity, "
                "the PNI directs the pentavalent schedule at "
                "2, 4 and 6 months."
            ),
        )

    # --------------------------------------------------------
    # Active window: unknown/partial history is not zero dose.
    # --------------------------------------------------------

    if history_value is None:
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "A criança ainda está na janela da dose ao nascer, mas "
                "não há histórico vacinal reconciliado de hepatite B. "
                "É necessário verificar o registro antes de tratar o "
                "histórico como zero dose."
            ),
            interpretation_en=(
                "The child is still within the birth-dose window, "
                "but no reconciled hepatitis-B vaccination history is "
                "available. The record must be checked before treating "
                "the history as documented zero dose."
            ),
        )

    if (
        history_state
        in {
            "unknown",
            "partial_record",
        }
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de hepatite B é desconhecido ou parcial. "
                "Não converter histórico desconhecido em zero dose "
                "documentado durante a janela da dose ao nascer."
            ),
            interpretation_en=(
                "Hepatitis-B vaccination history is unknown or partial. "
                "Do not convert unknown history into documented zero "
                "doses during the birth-dose window."
            ),
        )

    if (
        history_state
        != "documented_zero_dose"
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não estabelece com segurança "
                "a situação da dose de hepatite B ao nascer."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "hepatitis-B birth-dose status."
            ),
        )

    # --------------------------------------------------------
    # Calendar eligibility remains separate from administration
    # safety clearance.
    # --------------------------------------------------------

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A dose monovalente de hepatite B ao nascer está dentro "
                "da janela do calendário, mas a triagem de segurança "
                "ainda não foi registrada. Elegibilidade no calendário "
                "não substitui a avaliação antes da administração."
            ),
            interpretation_en=(
                "The monovalent hepatitis-B birth dose is within its "
                "schedule window, but administration-safety screening "
                "has not yet been documented. Schedule eligibility "
                "does not replace pre-administration assessment."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _hepatitis_b_birth_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "clínica. Encaminhar para avaliação antes da "
                "administração da vacina hepatite B."
            ),
            interpretation_en=(
                "The administration-safety screen identified a "
                "clinical concern. Refer for review before "
                "hepatitis-B vaccination."
            ),
        )

    return _hepatitis_b_birth_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "Criança dentro da janela da dose monovalente de hepatite B "
            "ao nascer, com zero dose documentado, estado materno HBsAg "
            "negativo e triagem de segurança sem preocupação: recomendar "
            "1 dose agora. A agenda oportuna prioriza a sala de parto ou "
            "as primeiras 12 horas; esta implementação baseada em datas "
            "não inventa horário de nascimento ou de avaliação."
        ),
        interpretation_en=(
            "The child is within the monovalent hepatitis-B birth-dose "
            "window, has documented zero-dose history, maternal HBsAg "
            "is negative, and administration-safety screening records "
            "no concern: recommend one dose now. The preferred agenda "
            "is the delivery room or first 12 hours; this date-based "
            "implementation does not invent birth or assessment times."
        ),
    )



ROTAVIRUS_ROUTINE_RULE_ID = (
    "PNI26-ROTAVIRUS-ROUTINE-001"
)

ROTAVIRUS_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

ROTAVIRUS_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "vacinacao/calendario"
)

ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS = 60
ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS = 30


def _rotavirus_age_boundary(
    date_of_birth: date,
    *,
    months: int,
    days: int,
) -> date:
    from datetime import timedelta

    return (
        _add_months_clamped(
            date_of_birth,
            months,
        )
        + timedelta(
            days=days,
        )
    )


def _rotavirus_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "rotavirus",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                ROTAVIRUS_ROUTINE_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title":
                "Calendário Nacional de Vacinação 2026",

            "source_url":
                ROTAVIRUS_SOURCE_URL,

            "source_snapshot_date":
                ROTAVIRUS_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_rotavirus_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "rotavirus"
    ):
        raise ValueError(
            "rotavirus routine rule requires vaccine_key=rotavirus"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid rotavirus history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "rotavirus administration_date cannot "
                "precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "rotavirus administration_date cannot "
                "follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    doses.sort(
        key=lambda item:
            item[
                "administration_date"
            ]
    )

    if (
        state
        == "documented_zero_dose"
        and doses
    ):
        raise ValueError(
            "documented_zero_dose cannot contain rotavirus doses"
        )

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_rotavirus_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    history: Any = None,
    administration_safety_screen_state: str = "not_screened",
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate the 2026 routine two-dose rotavirus schedule.

    The schedule engine consumes only age, vaccination history,
    administration-safety state and explicit authorization for the
    exceptional 30-day minimum interval.

    It does not infer contraindications or exceptional circumstances.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized must be boolean"
        )

    d1_earliest = _rotavirus_age_boundary(
        date_of_birth,
        months=1,
        days=15,
    )

    d1_latest = _rotavirus_age_boundary(
        date_of_birth,
        months=11,
        days=29,
    )

    d2_earliest = _rotavirus_age_boundary(
        date_of_birth,
        months=3,
        days=15,
    )

    d2_latest = _rotavirus_age_boundary(
        date_of_birth,
        months=23,
        days=29,
    )

    history_value = (
        _normalise_rotavirus_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    if history_value is None:
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Não há histórico vacinal reconciliado para rotavírus. "
                "Como cada dose possui limites etários específicos, "
                "é necessário confirmar o histórico antes de definir "
                "a próxima oportunidade."
            ),
            interpretation_en=(
                "No reconciled rotavirus vaccination history is "
                "available. Because each dose has specific age limits, "
                "history must be confirmed before determining the next "
                "opportunity."
            ),
        )

    history_state = history_value.get(
        "history_state"
    )

    doses = list(
        history_value.get(
            "doses"
        )
        or []
    )

    if (
        history_state
        in {
            "unknown",
            "partial_record",
        }
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de rotavírus é desconhecido ou parcial. "
                "Não converter esse estado em zero dose, pois a "
                "elegibilidade para D1 e D2 depende da idade e da "
                "data da dose anterior."
            ),
            interpretation_en=(
                "Rotavirus history is unknown or partial. Do not "
                "convert that state into documented zero doses because "
                "eligibility for dose 1 and dose 2 depends on age and "
                "the date of the previous dose."
            ),
        )

    if (
        history_state
        == "documented_doses"
        and not doses
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico informa doses documentadas de rotavírus, "
                "mas nenhuma data de dose está disponível. É necessário "
                "reconciliar o registro."
            ),
            interpretation_en=(
                "History indicates documented rotavirus doses, but no "
                "dose date is available. The record must be reconciled."
            ),
        )

    if len(
        doses
    ) > 2:
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de duas doses de rotavírus registradas. "
                "A rotina nacional implementada aqui possui duas doses; "
                "revisar o histórico antes de emitir nova recomendação."
            ),
            interpretation_en=(
                "More than two rotavirus doses are recorded. "
                "The national routine implemented here contains two "
                "doses; review the history before issuing another "
                "recommendation."
            ),
        )

    # --------------------------------------------------------
    # TWO DOCUMENTED DOSES
    # --------------------------------------------------------

    if len(
        doses
    ) == 2:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        d2_date = doses[
            1
        ][
            "administration_date"
        ]

        if not (
            d1_earliest
            <= d1_date
            <= d1_latest
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A primeira dose documentada está fora da janela "
                    "etária nacional permitida para D1. Não validar "
                    "automaticamente o esquema."
                ),
                interpretation_en=(
                    "The documented first dose is outside the national "
                    "permitted age window for dose 1. Do not "
                    "automatically validate the series."
                ),
            )

        if not (
            d2_earliest
            <= d2_date
            <= d2_latest
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A segunda dose documentada está fora da janela "
                    "etária nacional permitida para D2. É necessária "
                    "revisão do registro."
                ),
                interpretation_en=(
                    "The documented second dose is outside the national "
                    "permitted age window for dose 2. The record "
                    "requires review."
                ),
            )

        interval_days = (
            d2_date
            - d1_date
        ).days

        if (
            interval_days
            < ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre D1 e D2 é inferior "
                    "ao mínimo excepcional de 30 dias. Não considerar "
                    "automaticamente o esquema como concluído."
                ),
                interpretation_en=(
                    "The documented interval between dose 1 and dose 2 "
                    "is shorter than the exceptional 30-day minimum. "
                    "Do not automatically consider the series complete."
                ),
            )

        if (
            interval_days
            < ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre D1 e D2 está entre "
                    "30 e 59 dias. O PNI admite 30 dias apenas em "
                    "situação excepcional; como essa justificativa "
                    "histórica não está estruturada neste registro, "
                    "é necessário revisar antes de declarar o esquema "
                    "rotineiro concluído."
                ),
                interpretation_en=(
                    "The documented interval between dose 1 and dose 2 "
                    "is 30 to 59 days. The PNI permits 30 days only in "
                    "exceptional circumstances; because that historical "
                    "justification is not structured in this record, "
                    "review is required before declaring the routine "
                    "series complete."
                ),
            )

        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_interval_days=(
                ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            interpretation_pt=(
                "D1 e D2 de rotavírus estão documentadas dentro das "
                "janelas etárias permitidas e com intervalo de pelo "
                "menos 60 dias. O esquema rotineiro de duas doses "
                "está concluído."
            ),
            interpretation_en=(
                "Rotavirus dose 1 and dose 2 are documented within "
                "their permitted age windows and at least 60 days apart. "
                "The routine two-dose series is complete."
            ),
        )

    # --------------------------------------------------------
    # ONE DOCUMENTED DOSE => evaluate D2.
    # --------------------------------------------------------

    if len(
        doses
    ) == 1:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        if not (
            d1_earliest
            <= d1_date
            <= d1_latest
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A única dose documentada de rotavírus está fora "
                    "da janela permitida para D1. Não inferir "
                    "automaticamente elegibilidade para D2."
                ),
                interpretation_en=(
                    "The only documented rotavirus dose is outside "
                    "the permitted dose-1 window. Do not automatically "
                    "infer eligibility for dose 2."
                ),
            )

        if (
            assessment_date
            > d2_latest
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="not_applicable",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "Há D1 válida documentada, mas a criança já "
                    "ultrapassou a idade máxima permitida para D2 "
                    "(23 meses e 29 dias). Não criar uma D2 tardia "
                    "fora da janela nacional."
                ),
                interpretation_en=(
                    "A valid dose 1 is documented, but the child has "
                    "already passed the maximum permitted age for "
                    "dose 2 (23 months and 29 days). Do not create a "
                    "late dose 2 outside the national window."
                ),
            )

        interval_days = (
            assessment_date
            - d1_date
        ).days

        if (
            assessment_date
            < d2_earliest
            or interval_days
            < ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D1 está documentada, mas D2 ainda não atingiu "
                    "simultaneamente a idade mínima de 3 meses e "
                    "15 dias e o intervalo mínimo aplicável desde D1."
                ),
                interpretation_en=(
                    "Dose 1 is documented, but dose 2 has not yet "
                    "simultaneously reached the minimum age of "
                    "3 months and 15 days and the applicable minimum "
                    "interval from dose 1."
                ),
            )

        if (
            interval_days
            < ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
            and not exceptional_minimum_interval_authorized
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D2 está dentro da janela etária e já ultrapassou "
                    "30 dias desde D1, porém o intervalo recomendado "
                    "é de 60 dias. O mínimo de 30 dias somente deve ser "
                    "usado quando a situação excepcional estiver "
                    "explicitamente autorizada."
                ),
                interpretation_en=(
                    "Dose 2 is within its age window and more than "
                    "30 days have elapsed since dose 1, but the "
                    "recommended interval is 60 days. The 30-day "
                    "minimum should only be used when the exceptional "
                    "circumstance is explicitly authorized."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    interval_days
                    < ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D2 está elegível pelo calendário, mas a triagem "
                    "de segurança para administração ainda não foi "
                    "registrada. O mecanismo de calendário não infere "
                    "contraindicações."
                ),
                interpretation_en=(
                    "Dose 2 is schedule-eligible, but administration-"
                    "safety screening has not been documented. "
                    "The schedule engine does not infer "
                    "contraindications."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _rotavirus_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    interval_days
                    < ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A triagem de segurança identificou preocupação "
                    "antes de D2. Encaminhar para avaliação; não "
                    "inferir automaticamente contraindicação ou "
                    "conduta a partir desta regra de calendário."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    "concern before dose 2. Refer for review; do not "
                    "automatically infer a contraindication or action "
                    "from this schedule rule."
                ),
            )

        use_exception = (
            interval_days
            < ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
        )

        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_interval_days=(
                ROTAVIRUS_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                ROTAVIRUS_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    "D1 está documentada, D2 está dentro da janela "
                    "etária permitida e o intervalo recomendado de "
                    "60 dias foi atingido: recomendar D2 agora."
                )
                if not use_exception
                else
                (
                    "D1 está documentada, D2 está dentro da janela "
                    "etária e há autorização explícita para usar o "
                    "intervalo mínimo excepcional de 30 dias: "
                    "recomendar D2 agora."
                )
            ),
            interpretation_en=(
                (
                    "Dose 1 is documented, dose 2 is within its "
                    "permitted age window, and the recommended "
                    "60-day interval has been reached: recommend "
                    "dose 2 now."
                )
                if not use_exception
                else
                (
                    "Dose 1 is documented, dose 2 is within its "
                    "age window, and use of the exceptional 30-day "
                    "minimum interval is explicitly authorized: "
                    "recommend dose 2 now."
                )
            ),
        )

    # --------------------------------------------------------
    # ZERO DOCUMENTED DOSES => evaluate D1.
    # --------------------------------------------------------

    if (
        history_state
        != "documented_zero_dose"
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não estabelece com segurança "
                "a situação do esquema rotineiro de rotavírus."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "routine rotavirus-series status."
            ),
        )

    if (
        assessment_date
        < d1_earliest
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A criança ainda não atingiu a idade mínima permitida "
                "para D1 de rotavírus: 1 mês e 15 dias."
            ),
            interpretation_en=(
                "The child has not yet reached the minimum permitted "
                "age for rotavirus dose 1: 1 month and 15 days."
            ),
        )

    if (
        assessment_date
        > d1_latest
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A criança ultrapassou a idade máxima permitida para "
                "D1 de rotavírus (11 meses e 29 dias) sem dose "
                "documentada. Conforme o calendário nacional, perde-se "
                "também a oportunidade de D2; não iniciar o esquema "
                "fora dessa janela."
            ),
            interpretation_en=(
                "The child has passed the maximum permitted age for "
                "rotavirus dose 1 (11 months and 29 days) with no "
                "documented dose. Under the national schedule, the "
                "dose-2 opportunity is also lost; do not start the "
                "series outside this window."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "D1 está dentro da janela etária permitida, mas a "
                "triagem de segurança para administração ainda não "
                "foi registrada. A regra de calendário não infere "
                "contraindicações."
            ),
            interpretation_en=(
                "Dose 1 is within its permitted age window, but "
                "administration-safety screening has not been "
                "documented. The schedule rule does not infer "
                "contraindications."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _rotavirus_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "antes de D1. Encaminhar para avaliação antes da "
                "administração."
            ),
            interpretation_en=(
                "Administration-safety screening identified a concern "
                "before dose 1. Refer for review before administration."
            ),
        )

    return _rotavirus_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "A criança está dentro da janela permitida para D1 de "
            "rotavírus, de 1 mês e 15 dias a 11 meses e 29 dias, "
            "possui zero dose documentado e a triagem de segurança "
            "não registrou preocupação: recomendar D1 agora."
        ),
        interpretation_en=(
            "The child is within the permitted rotavirus dose-1 "
            "window of 1 month and 15 days through 11 months and "
            "29 days, has documented zero-dose history, and the "
            "administration-safety screen records no concern: "
            "recommend dose 1 now."
        ),
    )



MENINGOCOCCAL_C_INFANT_RULE_ID = (
    "PNI26-MENC-INFANT-ROUTINE-001"
)

MENINGOCOCCAL_C_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

MENINGOCOCCAL_C_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS = 60
MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS = 30


def _meningococcal_c_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "meningococcal_c",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                MENINGOCOCCAL_C_INFANT_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                MENINGOCOCCAL_C_SOURCE_URL,

            "source_snapshot_date":
                MENINGOCOCCAL_C_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_meningococcal_c_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "meningococcal_c"
    ):
        raise ValueError(
            "MenC infant rule requires "
            "vaccine_key=meningococcal_c"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid MenC history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "MenC administration_date cannot "
                "precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "MenC administration_date cannot "
                "follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    doses.sort(
        key=lambda item:
            item[
                "administration_date"
            ]
    )

    if (
        state
        == "documented_zero_dose"
        and doses
    ):
        raise ValueError(
            "documented_zero_dose cannot contain MenC doses"
        )

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_meningococcal_c_infant_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    history: Any = None,
    administration_safety_screen_state: str = "not_screened",
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate only the infant MenC primary/catch-up layer before
    12 months of age.

    MenACWY reinforcement/catch-up from 12 months onward is a separate
    rule family and is deliberately not evaluated here.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized "
            "must be boolean"
        )

    three_months = _add_months_clamped(
        date_of_birth,
        3,
    )

    eleven_months = _add_months_clamped(
        date_of_birth,
        11,
    )

    first_birthday = _add_months_clamped(
        date_of_birth,
        12,
    )

    history_value = (
        _normalise_meningococcal_c_history(
            history,
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
        )
    )

    history_state = (
        history_value.get(
            "history_state"
        )
        if history_value is not None
        else None
    )

    doses = (
        list(
            history_value.get(
                "doses"
            )
            or []
        )
        if history_value is not None
        else []
    )

    # Validate any documented MenC dose before deciding that the
    # current infant layer is complete or no longer applicable.
    for dose in doses:
        if (
            dose[
                "administration_date"
            ]
            < three_months
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há dose de meningocócica C documentada antes "
                    "da idade mínima da rotina infantil de 3 meses. "
                    "Não validar automaticamente esse histórico."
                ),
                interpretation_en=(
                    "A meningococcal-C dose is documented before "
                    "the routine infant minimum age of 3 months. "
                    "Do not automatically validate this history."
                ),
            )

    if len(
        doses
    ) > 2:
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de duas doses de meningocócica C registradas "
                "na camada infantil. Revisar o histórico antes de "
                "emitir nova recomendação."
            ),
            interpretation_en=(
                "More than two meningococcal-C doses are recorded "
                "in the infant layer. Review the history before "
                "issuing another recommendation."
            ),
        )

    # The MenC infant layer stops before the first birthday.
    # From 12 months the national routine transitions to MenACWY
    # reinforcement/catch-up.
    if (
        assessment_date
        >= first_birthday
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A camada infantil de meningocócica C termina antes "
                "dos 12 meses. A partir de 12 meses, reforço e "
                "atualização pertencem à regra separada da vacina "
                "meningocócica ACWY; não inventar nova dose de MenC "
                "nesta camada."
            ),
            interpretation_en=(
                "The infant meningococcal-C layer ends before "
                "12 months. From 12 months onward, reinforcement and "
                "catch-up belong to the separate meningococcal-ACWY "
                "rule; do not invent another MenC dose in this layer."
            ),
        )

    if history_value is None:
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Não há histórico reconciliado de meningocócica C. "
                "A atualização infantil depende do número e das datas "
                "das doses anteriores."
            ),
            interpretation_en=(
                "No reconciled meningococcal-C history is available. "
                "Infant catch-up depends on the number and dates of "
                "previous doses."
            ),
        )

    if (
        history_state
        in {
            "unknown",
            "partial_record",
        }
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de meningocócica C é desconhecido ou "
                "parcial. Não converter esse estado em zero dose."
            ),
            interpretation_en=(
                "Meningococcal-C history is unknown or partial. "
                "Do not convert that state into documented zero doses."
            ),
        )

    if (
        history_state
        == "documented_doses"
        and not doses
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico informa doses de meningocócica C, "
                "mas não contém datas documentadas. É necessário "
                "reconciliar o registro."
            ),
            interpretation_en=(
                "History reports meningococcal-C doses but contains "
                "no documented dates. The record must be reconciled."
            ),
        )

    # --------------------------------------------------------
    # TWO DOCUMENTED MENC DOSES
    # --------------------------------------------------------

    if len(
        doses
    ) == 2:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        d2_date = doses[
            1
        ][
            "administration_date"
        ]

        if (
            d2_date
            >= first_birthday
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A segunda dose registrada de meningocócica C "
                    "ocorreu a partir de 12 meses, quando a rotina "
                    "infantil já transiciona para MenACWY. Revisar "
                    "o histórico sem validar automaticamente essa dose "
                    "como parte da camada infantil."
                ),
                interpretation_en=(
                    "The recorded second meningococcal-C dose occurred "
                    "at or after 12 months, when the infant routine "
                    "transitions to MenACWY. Review the history rather "
                    "than automatically validating that dose in the "
                    "infant layer."
                ),
            )

        interval_days = (
            d2_date
            - d1_date
        ).days

        if (
            interval_days
            < MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre as duas doses de "
                    "MenC é inferior ao mínimo excepcional de 30 dias. "
                    "Não considerar automaticamente o esquema infantil "
                    "como válido."
                ),
                interpretation_en=(
                    "The documented interval between the two MenC "
                    "doses is shorter than the exceptional 30-day "
                    "minimum. Do not automatically consider the infant "
                    "series valid."
                ),
            )

        if (
            interval_days
            < MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre as doses de MenC "
                    "está entre 30 e 59 dias. O PNI admite 30 dias "
                    "somente em situação excepcional; como a "
                    "justificativa histórica não está estruturada "
                    "neste registro, revisar antes de declarar o "
                    "esquema infantil concluído."
                ),
                interpretation_en=(
                    "The documented MenC interval is 30 to 59 days. "
                    "The PNI permits 30 days only in exceptional "
                    "circumstances; because the historical justification "
                    "is not structured in this record, review is "
                    "required before declaring the infant series "
                    "complete."
                ),
            )

        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_interval_days=(
                MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            interpretation_pt=(
                "Duas doses válidas de meningocócica C estão "
                "documentadas com intervalo rotineiro de pelo menos "
                "60 dias. A série infantil MenC está concluída. "
                "O reforço posterior pertence à camada MenACWY, "
                "preferencialmente aos 12 meses."
            ),
            interpretation_en=(
                "Two valid meningococcal-C doses are documented with "
                "the routine interval of at least 60 days. The infant "
                "MenC primary series is complete. The later booster "
                "belongs to the MenACWY layer, preferably at 12 months."
            ),
        )

    # --------------------------------------------------------
    # ONE DOCUMENTED MENC DOSE
    # --------------------------------------------------------

    if len(
        doses
    ) == 1:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        interval_days = (
            assessment_date
            - d1_date
        ).days

        if (
            interval_days
            < MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "Há uma dose de MenC documentada, mas ainda não "
                    "foram completados 30 dias desde essa dose."
                ),
                interpretation_en=(
                    "One MenC dose is documented, but 30 days have "
                    "not yet elapsed since that dose."
                ),
            )

        if (
            interval_days
            < MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
            and not exceptional_minimum_interval_authorized
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "Já transcorreram pelo menos 30 dias desde a dose "
                    "anterior, mas o intervalo recomendado entre doses "
                    "de MenC é 60 dias. O mínimo de 30 dias somente "
                    "deve ser aplicado com autorização explícita para "
                    "situação excepcional."
                ),
                interpretation_en=(
                    "At least 30 days have elapsed since the previous "
                    "dose, but the recommended MenC interval is "
                    "60 days. The 30-day minimum should be used only "
                    "with explicit authorization for an exceptional "
                    "circumstance."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    interval_days
                    < MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A próxima dose de MenC está elegível pelo "
                    "calendário, mas a triagem de segurança ainda não "
                    "foi registrada."
                ),
                interpretation_en=(
                    "The next MenC dose is schedule-eligible, but "
                    "administration-safety screening has not yet "
                    "been documented."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _meningococcal_c_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    interval_days
                    < MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A triagem de segurança identificou preocupação "
                    "antes da próxima dose de MenC. Encaminhar para "
                    "avaliação antes da administração."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    "concern before the next MenC dose. Refer for "
                    "review before administration."
                ),
            )

        use_exception = (
            interval_days
            < MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
        )

        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_interval_days=(
                MENINGOCOCCAL_C_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                MENINGOCOCCAL_C_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    "Há uma dose válida de MenC documentada e o "
                    "intervalo recomendado de 60 dias foi atingido: "
                    "recomendar mais 1 dose de MenC agora. O reforço "
                    "MenACWY permanece em camada separada."
                )
                if not use_exception
                else
                (
                    "Há uma dose válida de MenC documentada e existe "
                    "autorização explícita para usar o intervalo mínimo "
                    "excepcional de 30 dias: recomendar mais 1 dose de "
                    "MenC agora. O reforço MenACWY permanece separado."
                )
            ),
            interpretation_en=(
                (
                    "One valid MenC dose is documented and the "
                    "recommended 60-day interval has been reached: "
                    "recommend one additional MenC dose now. "
                    "The MenACWY booster remains a separate layer."
                )
                if not use_exception
                else
                (
                    "One valid MenC dose is documented and use of the "
                    "exceptional 30-day minimum interval is explicitly "
                    "authorized: recommend one additional MenC dose "
                    "now. The MenACWY booster remains separate."
                )
            ),
        )

    # --------------------------------------------------------
    # DOCUMENTED ZERO DOSES
    # --------------------------------------------------------

    if (
        history_state
        != "documented_zero_dose"
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não estabelece com segurança "
                "a situação do esquema infantil de MenC."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "infant MenC-series status."
            ),
        )

    if (
        assessment_date
        < three_months
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A criança ainda não atingiu a idade inicial da "
                "rotina de meningocócica C, aos 3 meses."
            ),
            interpretation_en=(
                "The child has not yet reached the starting age "
                "for routine meningococcal-C vaccination at 3 months."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A dose de MenC está indicada pela atualização do "
                "calendário infantil, mas a triagem de segurança ainda "
                "não foi registrada."
            ),
            interpretation_en=(
                "A MenC dose is indicated by the infant catch-up "
                "schedule, but administration-safety screening has "
                "not yet been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou preocupação antes "
                "da vacinação MenC. Encaminhar para avaliação."
            ),
            interpretation_en=(
                "Administration-safety screening identified a concern "
                "before MenC vaccination. Refer for review."
            ),
        )

    if (
        assessment_date
        >= eleven_months
    ):
        return _meningococcal_c_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            interpretation_pt=(
                "A criança está aos 11 meses, sem dose documentada de "
                "MenC. A atualização nacional orienta 1 dose de MenC "
                "nesta idade. Não inventar uma segunda dose MenC após "
                "a transição de 12 meses; o reforço/atualização seguinte "
                "pertence à vacina MenACWY."
            ),
            interpretation_en=(
                "The child is 11 months old with no documented MenC "
                "dose. National catch-up guidance calls for one MenC "
                "dose at this age. Do not invent a second MenC dose "
                "after the 12-month transition; the next booster/"
                "catch-up step belongs to MenACWY."
            ),
        )

    return _meningococcal_c_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            "A criança tem pelo menos 3 meses e menos de 11 meses, "
            "com zero dose documentado de MenC: recomendar 1 dose "
            "agora. Entre 6 e 10 meses, ausência de histórico ainda "
            "mantém a atualização com duas doses de MenC, respeitando "
            "60 dias entre elas ou 30 dias somente em situação "
            "excepcional explicitamente autorizada."
        ),
        interpretation_en=(
            "The child is at least 3 months and younger than 11 months "
            "with documented zero-dose MenC history: recommend one dose "
            "now. From 6 through 10 months, no prior history still "
            "requires catch-up with two MenC doses, using a 60-day "
            "interval or 30 days only when an exceptional circumstance "
            "is explicitly authorized."
        ),
    )



MENINGOCOCCAL_ACWY_CHILD_RULE_ID = (
    "PNI26-MENACWY-CHILD-ROUTINE-001"
)

MENINGOCOCCAL_ACWY_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

MENINGOCOCCAL_ACWY_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/composicao/"
    "svsa/pni/calendario-tecnico/"
    "instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026"
)

MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS = 60


def _meningococcal_acwy_child_age_boundary(
    date_of_birth: date,
    *,
    months: int,
    days: int = 0,
) -> date:
    from datetime import timedelta

    return (
        _add_months_clamped(
            date_of_birth,
            months,
        )
        + timedelta(
            days=days,
        )
    )


def _meningococcal_acwy_child_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    minimum_interval_days: int | None = None,
) -> dict[str, Any]:
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "meningococcal_acwy",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                MENINGOCOCCAL_ACWY_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                MENINGOCOCCAL_ACWY_SOURCE_URL,

            "source_snapshot_date":
                MENINGOCOCCAL_ACWY_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_meningococcal_child_history(
    history: Any,
    *,
    required_vaccine_key: str,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != required_vaccine_key
    ):
        raise ValueError(
            "meningococcal child rule requires "
            f"vaccine_key={required_vaccine_key}"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid meningococcal history_state"
        )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                f"{required_vaccine_key} administration_date "
                "cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                f"{required_vaccine_key} administration_date "
                "cannot follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    doses.sort(
        key=lambda item:
            item[
                "administration_date"
            ]
    )

    if (
        state
        == "documented_zero_dose"
        and (
            doses
            or value.get(
                "reported_prior_doses_without_exact_dates",
                0,
            )
        )
    ):
        raise ValueError(
            "documented_zero_dose cannot contain prior doses"
        )

    return {
        **value,
        "doses":
            doses,
    }


def evaluate_pni_meningococcal_acwy_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    menc_history: Any = None,
    menacwy_history: Any = None,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate only the routine MenACWY child booster/catch-up layer
    from 12 months through 4 years, 11 months and 29 days.

    MenC and MenACWY histories remain explicit separate inputs.
    The adolescent 11-14-year layer is deliberately excluded.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    child_start = (
        _meningococcal_acwy_child_age_boundary(
            date_of_birth,
            months=12,
        )
    )

    child_end = (
        _meningococcal_acwy_child_age_boundary(
            date_of_birth,
            months=59,
            days=29,
        )
    )

    menc = _normalise_meningococcal_child_history(
        menc_history,
        required_vaccine_key="meningococcal_c",
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
    )

    menacwy = _normalise_meningococcal_child_history(
        menacwy_history,
        required_vaccine_key="meningococcal_acwy",
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
    )

    # --------------------------------------------------------
    # STRICT CHILD-LAYER AGE BOUNDARY
    # --------------------------------------------------------

    if (
        assessment_date
        < child_start
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A camada infantil de reforço/atualização com MenACWY "
                "inicia aos 12 meses. Antes dessa idade, o esquema "
                "infantil pertence à camada MenC."
            ),
            interpretation_en=(
                "The child MenACWY booster/catch-up layer begins "
                "at 12 months. Before that age, the infant schedule "
                "belongs to the MenC layer."
            ),
        )

    if (
        assessment_date
        > child_end
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A criança ultrapassou o limite desta camada MenACWY, "
                "de 4 anos, 11 meses e 29 dias. Não extrapolar esta "
                "regra para a recomendação de adolescentes de "
                "11 a 14 anos."
            ),
            interpretation_en=(
                "The child has passed this MenACWY layer's upper "
                "age limit of 4 years, 11 months and 29 days. "
                "Do not extrapolate this rule to the separate "
                "11-to-14-year adolescent recommendation."
            ),
        )

    menc_state = (
        menc.get(
            "history_state"
        )
        if menc is not None
        else None
    )

    menc_doses = (
        list(
            menc.get(
                "doses"
            )
            or []
        )
        if menc is not None
        else []
    )

    menc_undated = (
        int(
            menc.get(
                "reported_prior_doses_without_exact_dates",
                0,
            )
        )
        if menc is not None
        else 0
    )

    acwy_state = (
        menacwy.get(
            "history_state"
        )
        if menacwy is not None
        else None
    )

    acwy_doses = (
        list(
            menacwy.get(
                "doses"
            )
            or []
        )
        if menacwy is not None
        else []
    )

    acwy_undated = (
        int(
            menacwy.get(
                "reported_prior_doses_without_exact_dates",
                0,
            )
        )
        if menacwy is not None
        else 0
    )

    # --------------------------------------------------------
    # A DOCUMENTED VALID CHILD MENACWY DOSE IS SUFFICIENT TO
    # SUPPRESS A DUPLICATE ROUTINE CHILD DOSE.
    # --------------------------------------------------------

    child_acwy_doses = [
        dose
        for dose
        in acwy_doses
        if (
            child_start
            <= dose[
                "administration_date"
            ]
            <= child_end
        )
    ]

    pre_child_acwy_doses = [
        dose
        for dose
        in acwy_doses
        if (
            dose[
                "administration_date"
            ]
            < child_start
        )
    ]

    if (
        len(
            child_acwy_doses
        )
        > 1
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de uma dose MenACWY documentada dentro da "
                "faixa infantil desta regra. Revisar o histórico; "
                "não inferir automaticamente que se trata apenas "
                "da rotina infantil."
            ),
            interpretation_en=(
                "More than one MenACWY dose is documented within "
                "this child-rule age range. Review the history rather "
                "than assuming it represents only the routine child "
                "schedule."
            ),
        )

    if child_acwy_doses:
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há uma dose MenACWY documentada dentro da faixa "
                "infantil de 12 meses a 4 anos, 11 meses e 29 dias. "
                "A camada rotineira infantil está satisfeita; não "
                "repetir automaticamente a dose."
            ),
            interpretation_en=(
                "A MenACWY dose is documented within the child "
                "12-month through 4-year-11-month-29-day range. "
                "The routine child layer is satisfied; do not "
                "automatically repeat the dose."
            ),
        )

    if pre_child_acwy_doses:
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há dose MenACWY documentada antes dos 12 meses. "
                "Essa situação não deve ser automaticamente usada "
                "para satisfazer a camada rotineira infantil de "
                "12 meses; revisar a indicação original."
            ),
            interpretation_en=(
                "A MenACWY dose is documented before 12 months. "
                "Do not automatically use that dose to satisfy the "
                "routine child layer beginning at 12 months; review "
                "the original indication."
            ),
        )

    # --------------------------------------------------------
    # LEGACY MEN C BOOSTER:
    # complete MenC basic series + MenC booster is explicitly
    # considered vaccinated by the 2026 instruction.
    #
    # We only auto-suppress when exact history is unambiguous.
    # --------------------------------------------------------

    if (
        menc_state
        == "documented_doses"
        and menc_undated == 0
        and len(
            menc_doses
        )
        == 3
    ):
        pre_12 = [
            dose
            for dose
            in menc_doses
            if (
                dose[
                    "administration_date"
                ]
                < child_start
            )
        ]

        post_12 = [
            dose
            for dose
            in menc_doses
            if (
                dose[
                    "administration_date"
                ]
                >= child_start
            )
        ]

        if (
            len(
                pre_12
            )
            == 2
            and len(
                post_12
            )
            == 1
        ):
            first = pre_12[
                0
            ][
                "administration_date"
            ]

            second = pre_12[
                1
            ][
                "administration_date"
            ]

            booster = post_12[
                0
            ][
                "administration_date"
            ]

            basic_interval = (
                second
                - first
            ).days

            booster_interval = (
                booster
                - second
            ).days

            if (
                basic_interval
                >= 60
                and booster_interval
                >= 60
            ):
                return _meningococcal_acwy_child_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    interpretation_pt=(
                        "O histórico documenta esquema básico MenC "
                        "com duas doses e reforço MenC posterior aos "
                        "12 meses, com intervalos rotineiros verificáveis. "
                        "A Instrução Normativa 2026 considera essa "
                        "situação vacinada; não acrescentar MenACWY "
                        "apenas para substituir retrospectivamente "
                        "o produto do reforço."
                    ),
                    interpretation_en=(
                        "History documents a two-dose MenC basic "
                        "series and a MenC booster after 12 months "
                        "with verifiable routine intervals. The 2026 "
                        "national instruction considers this state "
                        "vaccinated; do not add MenACWY solely to "
                        "retroactively replace the booster product."
                    ),
                )

            return _meningococcal_acwy_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há padrão compatível com esquema básico MenC "
                    "mais reforço MenC, porém os intervalos documentados "
                    "não permitem validar automaticamente o estado "
                    "como esquema rotineiro completo."
                ),
                interpretation_en=(
                    "The history resembles a MenC basic series plus "
                    "MenC booster, but documented intervals do not "
                    "allow automatic validation as a complete routine "
                    "series."
                ),
            )

    # Any other MenC dose given at or after 12 months is not silently
    # re-labelled as the legacy valid booster state.
    post_12_menc = [
        dose
        for dose
        in menc_doses
        if (
            dose[
                "administration_date"
            ]
            >= child_start
        )
    ]

    if post_12_menc:
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há dose MenC documentada a partir de 12 meses, mas "
                "o histórico não demonstra de forma inequívoca o "
                "padrão legado de duas doses básicas mais reforço MenC. "
                "Revisar antes de definir a atualização com MenACWY."
            ),
            interpretation_en=(
                "A MenC dose is documented at or after 12 months, "
                "but the history does not unambiguously establish the "
                "legacy two-dose basic series plus MenC booster pattern. "
                "Review before determining MenACWY catch-up."
            ),
        )

    # --------------------------------------------------------
    # HISTORY COMPLETENESS
    # --------------------------------------------------------

    if (
        menacwy is None
        or acwy_state
        in {
            "unknown",
            "partial_record",
        }
        or acwy_undated
        > 0
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico MenACWY não estabelece com segurança "
                "se a dose infantil já foi administrada. Confirmar "
                "o registro antes de recomendar uma duplicata."
            ),
            interpretation_en=(
                "MenACWY history does not safely establish whether "
                "the child dose has already been given. Confirm the "
                "record before recommending a duplicate."
            ),
        )

    if (
        menc is None
        or menc_state
        in {
            "unknown",
            "partial_record",
        }
        or menc_undated
        > 0
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico MenC é ausente, desconhecido ou parcial. "
                "Embora a atualização infantil use MenACWY mesmo com "
                "esquema básico incompleto, é necessário excluir uma "
                "dose MenC recente que ainda imponha o intervalo de "
                "60 dias ou um reforço MenC já realizado."
            ),
            interpretation_en=(
                "MenC history is missing, unknown or partial. "
                "Although child catch-up uses MenACWY even when the "
                "basic series is incomplete, a recent MenC dose that "
                "still requires the 60-day interval—or a prior MenC "
                "booster—must first be excluded."
            ),
        )

    if (
        acwy_state
        not in {
            "documented_zero_dose",
            "documented_doses",
        }
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico MenACWY não está em estado documental "
                "seguro para a decisão."
            ),
            interpretation_en=(
                "MenACWY history is not in a documented state safe "
                "for this decision."
            ),
        )

    if (
        menc_state
        not in {
            "documented_zero_dose",
            "documented_doses",
        }
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico MenC não está em estado documental "
                "seguro para a decisão."
            ),
            interpretation_en=(
                "MenC history is not in a documented state safe "
                "for this decision."
            ),
        )

    # --------------------------------------------------------
    # RECENT MENC HANDOFF INTERVAL
    #
    # The child MenACWY recommendation does not require the engine
    # to decide whether the old MenC basic series was complete.
    # It only must not violate the explicit 60-day handoff after
    # a recent MenC dose.
    # --------------------------------------------------------

    if menc_doses:
        latest_menc = menc_doses[
            -1
        ][
            "administration_date"
        ]

        if (
            latest_menc
            < _add_months_clamped(
                date_of_birth,
                3,
            )
        ):
            return _meningococcal_acwy_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há dose MenC documentada antes dos 3 meses. "
                    "Não usar automaticamente esse histórico para "
                    "calcular a atualização MenACWY de rotina."
                ),
                interpretation_en=(
                    "A MenC dose is documented before 3 months. "
                    "Do not automatically use that history to calculate "
                    "routine MenACWY catch-up."
                ),
            )

        days_since_menc = (
            assessment_date
            - latest_menc
        ).days

        if (
            days_since_menc
            < MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS
        ):
            return _meningococcal_acwy_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                minimum_interval_days=(
                    MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS
                ),
                interpretation_pt=(
                    "A atualização infantil será realizada com MenACWY, "
                    "porém ainda não transcorreram 60 dias desde a "
                    "dose MenC mais recente. Aguardar completar o "
                    "intervalo de 60 dias."
                ),
                interpretation_en=(
                    "Child catch-up will use MenACWY, but 60 days "
                    "have not yet elapsed since the most recent MenC "
                    "dose. Wait until the 60-day interval is complete."
                ),
            )

    # --------------------------------------------------------
    # ADMINISTRATION SAFETY
    # --------------------------------------------------------

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            minimum_interval_days=(
                MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS
                if menc_doses
                else None
            ),
            interpretation_pt=(
                "A dose infantil MenACWY está indicada pelo calendário, "
                "mas a triagem de segurança antes da administração "
                "ainda não foi registrada."
            ),
            interpretation_en=(
                "The child MenACWY dose is indicated by the schedule, "
                "but administration-safety screening has not yet "
                "been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _meningococcal_acwy_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            minimum_interval_days=(
                MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS
                if menc_doses
                else None
            ),
            interpretation_pt=(
                "A triagem de segurança identificou preocupação antes "
                "da dose MenACWY. Encaminhar para avaliação antes "
                "da administração."
            ),
            interpretation_en=(
                "Administration-safety screening identified a concern "
                "before the MenACWY dose. Refer for review before "
                "administration."
            ),
        )

    return _meningococcal_acwy_child_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        minimum_interval_days=(
            MENINGOCOCCAL_ACWY_CHILD_MENC_HANDOFF_DAYS
            if menc_doses
            else None
        ),
        interpretation_pt=(
            "A criança está entre 12 meses e 4 anos, 11 meses e "
            "29 dias, não possui dose infantil MenACWY documentada "
            "e não há reforço MenC previamente validado que satisfaça "
            "esta camada. Conforme a situação vacinal encontrada, "
            "administrar 1 dose de MenACWY agora."
        ),
        interpretation_en=(
            "The child is 12 months through 4 years, 11 months and "
            "29 days old, has no documented child MenACWY dose, "
            "and no previously validated MenC booster already "
            "satisfies this layer. According to the vaccination "
            "history found, administer one MenACWY dose now."
        ),
    )



PENTAVALENT_CHILD_RULE_ID = (
    "PNI26-PENTAVALENT-CHILD-ROUTINE-001"
)

PENTAVALENT_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

PENTAVALENT_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

PENTAVALENT_RECOMMENDED_INTERVAL_DAYS = 60
PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS = 30


def _pentavalent_age_boundary(
    date_of_birth: date,
    *,
    months: int,
    days: int = 0,
) -> date:
    from datetime import timedelta

    return (
        _add_months_clamped(
            date_of_birth,
            months,
        )
        + timedelta(
            days=days,
        )
    )


def _pentavalent_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "pentavalent",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            None,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                PENTAVALENT_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title":
                (
                    "Instrução Normativa do Calendário "
                    "Nacional de Vacinação 2026"
                ),

            "source_url":
                PENTAVALENT_SOURCE_URL,

            "source_snapshot_date":
                PENTAVALENT_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _normalise_pentavalent_history(
    history: Any,
    *,
    assessment_date: date,
    date_of_birth: date,
) -> dict[str, Any] | None:
    if history is None:
        return None

    value = _as_plain_dict(
        history
    )

    if (
        value.get(
            "vaccine_key"
        )
        != "pentavalent"
    ):
        raise ValueError(
            "pentavalent child rule requires "
            "vaccine_key=pentavalent"
        )

    state = value.get(
        "history_state"
    )

    if state not in {
        "documented_zero_dose",
        "documented_doses",
        "partial_record",
        "unknown",
    }:
        raise ValueError(
            "invalid pentavalent history_state"
        )

    undated = int(
        value.get(
            "reported_prior_doses_without_exact_dates",
            0,
        )
        or 0
    )

    doses = []

    for raw_dose in (
        value.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "pentavalent administration_date cannot "
                "precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "pentavalent administration_date cannot "
                "follow assessment_date"
            )

        doses.append({
            **dose,
            "administration_date":
                administration_date,
        })

    doses.sort(
        key=lambda item:
            item[
                "administration_date"
            ]
    )

    if (
        state
        == "documented_zero_dose"
        and (
            doses
            or undated
        )
    ):
        raise ValueError(
            "documented_zero_dose cannot contain "
            "pentavalent prior doses"
        )

    return {
        **value,
        "doses":
            doses,
        "reported_prior_doses_without_exact_dates":
            undated,
    }


def evaluate_pni_pentavalent_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    history: Any = None,
    administration_safety_screen_state: str = "not_screened",
    exceptional_early_start_authorized: bool = False,
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate the homologous pentavalent basic series in children.

    This rule counts only history normalized as vaccine_key=pentavalent.
    Monovalent HB, DTP, RIE hexavalent and any unmodeled Hib history
    are not silently converted into pentavalent doses.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_early_start_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_early_start_authorized must be boolean"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized "
            "must be boolean"
        )

    earliest_d1 = _pentavalent_age_boundary(
        date_of_birth,
        months=1,
        days=15,
    )

    routine_start = _add_months_clamped(
        date_of_birth,
        2,
    )

    six_months = _add_months_clamped(
        date_of_birth,
        6,
    )

    child_end = _pentavalent_age_boundary(
        date_of_birth,
        months=83,
        days=29,
    )

    history_value = _normalise_pentavalent_history(
        history,
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
    )

    # --------------------------------------------------------
    # AGE SCOPE
    # --------------------------------------------------------

    if (
        assessment_date
        > child_end
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A criança ultrapassou a faixa etária desta regra "
                "de pentavalente, até 6 anos, 11 meses e 29 dias. "
                "A partir dessa faixa, a atualização dos componentes "
                "difteria/tétano e hepatite B utiliza regras e vacinas "
                "separadas; não criar nova dose de penta."
            ),
            interpretation_en=(
                "The child has passed this pentavalent rule's upper "
                "age range of 6 years, 11 months and 29 days. "
                "Beyond this range, diphtheria/tetanus and hepatitis-B "
                "catch-up use separate vaccine rules; do not create "
                "another pentavalent dose."
            ),
        )

    # --------------------------------------------------------
    # HISTORY COMPLETENESS
    # --------------------------------------------------------

    if history_value is None:
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Não há histórico reconciliado de pentavalente. "
                "Como a atualização depende do número e das datas "
                "das doses anteriores, é necessário confirmar o "
                "registro antes de definir a próxima dose."
            ),
            interpretation_en=(
                "No reconciled pentavalent history is available. "
                "Because catch-up depends on the number and dates "
                "of previous doses, the record must be confirmed "
                "before determining the next dose."
            ),
        )

    history_state = history_value.get(
        "history_state"
    )

    doses = list(
        history_value.get(
            "doses"
        )
        or []
    )

    undated = int(
        history_value.get(
            "reported_prior_doses_without_exact_dates",
            0,
        )
        or 0
    )

    if (
        history_state
        in {
            "unknown",
            "partial_record",
        }
        or undated
        > 0
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de pentavalente é desconhecido, parcial "
                "ou contém doses sem data exata. Não converter esse "
                "estado em zero dose, pois os intervalos e a idade da "
                "terceira dose são determinantes."
            ),
            interpretation_en=(
                "Pentavalent history is unknown, partial or contains "
                "doses without exact dates. Do not convert this state "
                "into documented zero doses because intervals and "
                "the age of dose 3 are determinative."
            ),
        )

    if (
        history_state
        == "documented_doses"
        and not doses
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico informa doses de pentavalente, porém "
                "nenhuma data está documentada. É necessário "
                "reconciliar o registro."
            ),
            interpretation_en=(
                "History reports pentavalent doses but contains "
                "no documented dates. The record must be reconciled."
            ),
        )

    if len(
        doses
    ) > 3:
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de três doses de pentavalente registradas. "
                "Esta regra implementa apenas o esquema básico "
                "rotineiro de três doses; revisar possíveis reforços, "
                "substituições ou contextos especiais."
            ),
            interpretation_en=(
                "More than three pentavalent doses are recorded. "
                "This rule implements only the routine three-dose "
                "basic series; review possible boosters, substitutions "
                "or special contexts."
            ),
        )

    # --------------------------------------------------------
    # VALIDATE DOCUMENTED D1 AGE.
    # An early D1 from 1m15d to before 2m is accepted only when
    # the caller explicitly confirms the exceptional early start.
    # --------------------------------------------------------

    if doses:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        if (
            d1_date
            < earliest_d1
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A primeira dose documentada de pentavalente "
                    "ocorreu antes da idade mínima de 1 mês e 15 dias. "
                    "Não validar automaticamente essa dose."
                ),
                interpretation_en=(
                    "The documented first pentavalent dose occurred "
                    "before the minimum age of 1 month and 15 days. "
                    "Do not automatically validate that dose."
                ),
            )

        if (
            d1_date
            < routine_start
            and not exceptional_early_start_authorized
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A primeira dose foi administrada entre 1 mês "
                    "e 15 dias e antes dos 2 meses. Essa antecipação "
                    "é reservada a situação excepcional; é necessária "
                    "confirmação explícita dessa autorização antes de "
                    "usar a dose automaticamente na série."
                ),
                interpretation_en=(
                    "The first dose was administered from 1 month "
                    "and 15 days but before 2 months. Such early "
                    "administration is reserved for exceptional "
                    "circumstances; explicit confirmation is required "
                    "before automatically using the dose in the series."
                ),
            )

    # --------------------------------------------------------
    # VALIDATE ALREADY-DOCUMENTED INTERVALS.
    #
    # We do not infer that a past 30-59-day interval had an
    # exceptional justification simply because the current caller
    # requests acceleration prospectively.
    # --------------------------------------------------------

    if len(
        doses
    ) >= 2:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        d2_date = doses[
            1
        ][
            "administration_date"
        ]

        interval_12 = (
            d2_date
            - d1_date
        ).days

        if (
            interval_12
            < PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre D1 e D2 é inferior "
                    "ao mínimo excepcional de 30 dias. Não validar "
                    "automaticamente a série."
                ),
                interpretation_en=(
                    "The documented interval between dose 1 and dose 2 "
                    "is shorter than the exceptional 30-day minimum. "
                    "Do not automatically validate the series."
                ),
            )

        if (
            interval_12
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D1 e D2 está entre "
                    "30 e 59 dias. O PNI admite esse mínimo somente em "
                    "situação excepcional e essa justificativa "
                    "histórica não está estruturada no registro; "
                    "revisar antes de validar."
                ),
                interpretation_en=(
                    "The historical interval between dose 1 and dose 2 "
                    "is 30 to 59 days. The PNI permits that minimum "
                    "only in exceptional circumstances, and the "
                    "historical justification is not structured in "
                    "this record; review before validating it."
                ),
            )

    if len(
        doses
    ) >= 3:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        d2_date = doses[
            1
        ][
            "administration_date"
        ]

        d3_date = doses[
            2
        ][
            "administration_date"
        ]

        interval_23 = (
            d3_date
            - d2_date
        ).days

        if (
            interval_23
            < PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo documentado entre D2 e D3 é inferior "
                    "ao mínimo excepcional de 30 dias. Não validar "
                    "automaticamente a série."
                ),
                interpretation_en=(
                    "The documented interval between dose 2 and dose 3 "
                    "is shorter than the exceptional 30-day minimum. "
                    "Do not automatically validate the series."
                ),
            )

        if (
            interval_23
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D2 e D3 está entre "
                    "30 e 59 dias sem comprovação estruturada da "
                    "situação excepcional. Revisar antes de validar."
                ),
                interpretation_en=(
                    "The historical interval between dose 2 and dose 3 "
                    "is 30 to 59 days without structured evidence of "
                    "the exceptional circumstance. Review before "
                    "validating it."
                ),
            )

        d1_to_d3_minimum = _add_months_clamped(
            d1_date,
            4,
        )

        if (
            d3_date
            < d1_to_d3_minimum
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A terceira dose documentada ocorreu antes de "
                    "completar o intervalo mínimo de 4 meses entre "
                    "D1 e D3, exigido pelo componente hepatite B."
                ),
                interpretation_en=(
                    "The documented third dose occurred before the "
                    "required minimum 4-calendar-month interval "
                    "between dose 1 and dose 3, which is required "
                    "because of the hepatitis-B component."
                ),
            )

        if (
            d3_date
            < six_months
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A terceira dose documentada foi administrada "
                    "antes dos 6 meses de idade. O PNI determina que "
                    "D3 não seja administrada antes dessa idade."
                ),
                interpretation_en=(
                    "The documented third dose was administered "
                    "before 6 months of age. The PNI specifies that "
                    "dose 3 must not be administered before that age."
                ),
            )

        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_interval_days=(
                PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            interpretation_pt=(
                "Três doses válidas de pentavalente estão "
                "documentadas e o esquema básico desta camada está "
                "concluído. Os reforços de 15 meses e 4 anos pertencem "
                "à regra separada da vacina DTP."
            ),
            interpretation_en=(
                "Three valid pentavalent doses are documented and "
                "the basic series in this layer is complete. "
                "The 15-month and 4-year boosters belong to the "
                "separate DTP rule."
            ),
        )

    # --------------------------------------------------------
    # TWO DOCUMENTED DOSES -> prospective D3.
    # Must satisfy:
    #   - 60 days routinely, or 30 with explicit exception;
    #   - 4 calendar months from D1;
    #   - at least 6 months of age.
    # --------------------------------------------------------

    if len(
        doses
    ) == 2:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        d2_date = doses[
            1
        ][
            "administration_date"
        ]

        days_since_d2 = (
            assessment_date
            - d2_date
        ).days

        d1_to_d3_minimum = _add_months_clamped(
            d1_date,
            4,
        )

        if (
            days_since_d2
            < PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D1 e D2 estão documentadas, porém ainda não "
                    "foram completados 30 dias desde D2."
                ),
                interpretation_en=(
                    "Dose 1 and dose 2 are documented, but 30 days "
                    "have not yet elapsed since dose 2."
                ),
            )

        if (
            days_since_d2
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
            and not exceptional_minimum_interval_authorized
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D1 e D2 estão documentadas. O intervalo "
                    "recomendado até D3 é de 60 dias; o mínimo de "
                    "30 dias somente pode ser usado quando a "
                    "antecipação excepcional estiver explicitamente "
                    "autorizada."
                ),
                interpretation_en=(
                    "Dose 1 and dose 2 are documented. The recommended "
                    "interval to dose 3 is 60 days; the 30-day minimum "
                    "may be used only when exceptional acceleration "
                    "is explicitly authorized."
                ),
            )

        if (
            assessment_date
            < d1_to_d3_minimum
            or assessment_date
            < six_months
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo desde D2 pode estar satisfeito, "
                    "mas D3 também exige pelo menos 4 meses desde D1 "
                    "e idade mínima de 6 meses. Uma ou ambas as "
                    "condições ainda não foram atingidas."
                ),
                interpretation_en=(
                    "The interval from dose 2 may be satisfied, "
                    "but dose 3 also requires at least 4 calendar "
                    "months from dose 1 and a minimum age of 6 months. "
                    "One or both conditions have not yet been reached."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    days_since_d2
                    < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D3 está elegível pelo calendário, mas a triagem "
                    "de segurança antes da administração ainda não "
                    "foi registrada."
                ),
                interpretation_en=(
                    "Dose 3 is schedule-eligible, but administration-"
                    "safety screening has not yet been documented."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    days_since_d2
                    < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A triagem de segurança identificou preocupação "
                    "antes de D3. Encaminhar para avaliação; não "
                    "inferir automaticamente produto alternativo."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    "concern before dose 3. Refer for review; do not "
                    "automatically infer an alternative product."
                ),
            )

        use_exception = (
            days_since_d2
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
        )

        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_interval_days=(
                PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    "D1 e D2 estão válidas; transcorreram pelo menos "
                    "60 dias desde D2, pelo menos 4 meses desde D1 "
                    "e a criança tem pelo menos 6 meses: recomendar "
                    "D3 de pentavalente agora."
                )
                if not use_exception
                else
                (
                    "D1 e D2 estão válidas e há autorização explícita "
                    "para o intervalo mínimo excepcional desde D2; "
                    "também foram cumpridos 4 meses desde D1 e idade "
                    "mínima de 6 meses: recomendar D3 agora."
                )
            ),
            interpretation_en=(
                (
                    "Dose 1 and dose 2 are valid; at least 60 days "
                    "have elapsed since dose 2, at least 4 calendar "
                    "months since dose 1, and the child is at least "
                    "6 months old: recommend pentavalent dose 3 now."
                )
                if not use_exception
                else
                (
                    "Dose 1 and dose 2 are valid and use of the "
                    "exceptional minimum interval from dose 2 is "
                    "explicitly authorized; at least 4 calendar months "
                    "from dose 1 and the minimum age of 6 months are "
                    "also satisfied: recommend dose 3 now."
                )
            ),
        )

    # --------------------------------------------------------
    # ONE DOCUMENTED DOSE -> prospective D2.
    # --------------------------------------------------------

    if len(
        doses
    ) == 1:
        d1_date = doses[
            0
        ][
            "administration_date"
        ]

        days_since_d1 = (
            assessment_date
            - d1_date
        ).days

        if (
            days_since_d1
            < PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "Há uma dose de pentavalente documentada, mas "
                    "ainda não transcorreram 30 dias desde D1."
                ),
                interpretation_en=(
                    "One pentavalent dose is documented, but 30 days "
                    "have not yet elapsed since dose 1."
                ),
            )

        if (
            days_since_d1
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
            and not exceptional_minimum_interval_authorized
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "Há uma dose válida documentada. O intervalo "
                    "recomendado até D2 é de 60 dias; usar 30 dias "
                    "somente quando a antecipação excepcional estiver "
                    "explicitamente autorizada."
                ),
                interpretation_en=(
                    "One valid dose is documented. The recommended "
                    "interval to dose 2 is 60 days; use the 30-day "
                    "minimum only when exceptional acceleration is "
                    "explicitly authorized."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    days_since_d1
                    < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D2 está elegível pelo calendário, mas a triagem "
                    "de segurança ainda não foi registrada."
                ),
                interpretation_en=(
                    "Dose 2 is schedule-eligible, but administration-"
                    "safety screening has not yet been documented."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _pentavalent_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=(
                    days_since_d1
                    < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A triagem de segurança identificou preocupação "
                    "antes de D2. Encaminhar para avaliação."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    "concern before dose 2. Refer for review."
                ),
            )

        use_exception = (
            days_since_d1
            < PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
        )

        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_interval_days=(
                PENTAVALENT_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                PENTAVALENT_EXCEPTIONAL_MINIMUM_INTERVAL_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    "D1 está válida e o intervalo recomendado de "
                    "60 dias foi atingido: recomendar D2 de "
                    "pentavalente agora."
                )
                if not use_exception
                else
                (
                    "D1 está válida e há autorização explícita para "
                    "usar o intervalo mínimo excepcional de 30 dias: "
                    "recomendar D2 de pentavalente agora."
                )
            ),
            interpretation_en=(
                (
                    "Dose 1 is valid and the recommended 60-day "
                    "interval has been reached: recommend pentavalent "
                    "dose 2 now."
                )
                if not use_exception
                else
                (
                    "Dose 1 is valid and use of the exceptional "
                    "30-day minimum interval is explicitly authorized: "
                    "recommend pentavalent dose 2 now."
                )
            ),
        )

    # --------------------------------------------------------
    # DOCUMENTED ZERO DOSES -> prospective D1.
    # --------------------------------------------------------

    if (
        history_state
        != "documented_zero_dose"
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O registro disponível não estabelece com segurança "
                "a situação do esquema básico de pentavalente."
            ),
            interpretation_en=(
                "The available record does not safely establish "
                "pentavalent basic-series status."
            ),
        )

    if (
        assessment_date
        < earliest_d1
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A criança ainda não atingiu a idade mínima absoluta "
                "para início excepcional da pentavalente: "
                "1 mês e 15 dias."
            ),
            interpretation_en=(
                "The child has not yet reached the absolute minimum "
                "age for exceptional pentavalent initiation: "
                "1 month and 15 days."
            ),
        )

    early_window = (
        assessment_date
        < routine_start
    )

    if (
        early_window
        and not exceptional_early_start_authorized
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A criança já atingiu 1 mês e 15 dias, porém ainda "
                "não chegou à agenda rotineira de 2 meses. O início "
                "nesta janela é reservado a situação excepcional e "
                "exige autorização explícita."
            ),
            interpretation_en=(
                "The child has reached 1 month and 15 days but has "
                "not yet reached the routine 2-month schedule. "
                "Starting in this window is reserved for exceptional "
                "circumstances and requires explicit authorization."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "D1 está elegível pela agenda aplicável, mas a triagem "
                "de segurança antes da administração ainda não foi "
                "registrada."
            ),
            interpretation_en=(
                "Dose 1 is eligible under the applicable schedule, "
                "but administration-safety screening has not yet "
                "been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _pentavalent_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou preocupação "
                "antes de D1 de pentavalente. Encaminhar para "
                "avaliação sem inferir automaticamente produto "
                "alternativo ou via CRIE."
            ),
            interpretation_en=(
                "Administration-safety screening identified a concern "
                "before pentavalent dose 1. Refer for review without "
                "automatically inferring an alternative product or "
                "CRIE pathway."
            ),
        )

    return _pentavalent_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        interpretation_pt=(
            (
                "A criança atingiu a agenda rotineira de pentavalente "
                "e possui zero dose documentado: recomendar D1 agora."
            )
            if not early_window
            else
            (
                "A criança tem pelo menos 1 mês e 15 dias e há "
                "autorização explícita para início excepcional "
                "antecipado: recomendar D1 de pentavalente agora."
            )
        ),
        interpretation_en=(
            (
                "The child has reached the routine pentavalent "
                "schedule and has documented zero-dose history: "
                "recommend dose 1 now."
            )
            if not early_window
            else
            (
                "The child is at least 1 month and 15 days old and "
                "exceptional early initiation is explicitly "
                "authorized: recommend pentavalent dose 1 now."
            )
        ),
    )



IPV_CHILD_RULE_ID = (
    "PNI26-IPV-CHILD-ROUTINE-001"
)

IPV_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

IPV_TECHNICAL_CALENDAR_URL = (
    "https://www.gov.br/saude/pt-br/composicao/"
    "svsa/pni/calendario-tecnico/"
    "calendario-tecnico-nacional-de-vacinacao-crianca"
)

IPV_TRANSITION_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/informes/"
    "retirada-da-vacina-poliomielite-1-e-3-atenuada-"
    "e-adocao-do-esquema-exclusivo-com-vacina-"
    "poliomielite-1-2-e-3-inativada.pdf"
)

IPV_EXCLUSIVE_SCHEDULE_FROM = date(
    2024,
    11,
    4,
)

IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS = 60
IPV_PRIMARY_MINIMUM_INTERVAL_DAYS = 30
IPV_BOOSTER_RECOMMENDED_MONTHS_AFTER_D3 = 9
IPV_BOOSTER_MINIMUM_MONTHS_AFTER_D3 = 6
IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS = 30


def _ipv_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "ipv",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                IPV_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title":
                (
                    "Calendário Técnico Nacional de "
                    "Vacinação da Criança 2026"
                ),

            "source_url":
                IPV_TECHNICAL_CALENDAR_URL,

            "source_snapshot_date":
                IPV_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _validate_ipv_normalized_history(
    value: Any,
) -> dict[str, Any]:
    history = _as_plain_dict(
        value
    )

    required = {
        "history_scope",
        "history_state",
        "present_history_keys",
        "ipv_history_supplied",
        "legacy_vopb_history_supplied",
        "combination_history_keys_supplied",
        "exposures",
        "ipv_equivalent_exposure_count",
        "legacy_vopb_exposure_count",
        "ambiguous_same_day_exposure_dates",
        "unmapped_vaccine_keys",
        "source_history_incomplete",
        "special_pathway_exposure_present",
        "safe_for_interval_evaluation",
        "safe_for_primary_series_count",
        "safe_for_transition_evaluation",
    }

    missing = sorted(
        required
        - set(
            history
        )
    )

    if missing:
        raise ValueError(
            "normalized polio history missing fields: "
            + ", ".join(
                missing
            )
        )

    return history


def evaluate_pni_ipv_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    polio_history: Any,
    administration_safety_screen_state: str = "not_screened",
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate the current Brazilian routine VIP child schedule.

    Input is the output of normalize_polio_history().  This evaluator
    does not reconstruct cross-product vaccine history itself.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized "
            "must be boolean"
        )

    history = _validate_ipv_normalized_history(
        polio_history
    )

    routine_start = _add_months_clamped(
        date_of_birth,
        2,
    )

    booster_age = _add_months_clamped(
        date_of_birth,
        15,
    )

    child_end = (
        _add_months_clamped(
            date_of_birth,
            60,
        )
        - timedelta(
            days=1,
        )
    )

    legacy_reconciliation_relevant = (
        booster_age
        < IPV_EXCLUSIVE_SCHEDULE_FROM
    )

    # --------------------------------------------------------
    # MODEL/HISTORY SAFETY
    # --------------------------------------------------------

    if history[
        "special_pathway_exposure_present"
    ]:
        return _ipv_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico de poliomielite contém produto de via "
                "especial/RIE. Esta regra de rotina preserva a "
                "exposição, mas não infere indicação CRIE nem "
                "reclassifica automaticamente a dose."
            ),
            interpretation_en=(
                "Polio history contains a special-pathway/RIE product. "
                "This routine rule preserves the exposure but does not "
                "infer CRIE eligibility or automatically reclassify "
                "the dose."
            ),
        )

    if (
        history[
            "source_history_incomplete"
        ]
        or history[
            "unmapped_vaccine_keys"
        ]
        or history[
            "ambiguous_same_day_exposure_dates"
        ]
        or not history[
            "safe_for_primary_series_count"
        ]
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de poliomielite está parcial, "
                "desconhecido, contém produto não mapeado ou "
                "exposição possivelmente duplicada. É necessário "
                "reconciliar o registro antes de classificar doses "
                "do esquema básico ou reforço."
            ),
            interpretation_en=(
                "Polio history is partial or unknown, contains an "
                "unmapped product, or has a possible duplicate "
                "exposure. Reconcile the record before classifying "
                "primary-series or booster doses."
            ),
        )

    exposures = list(
        history[
            "exposures"
        ]
    )

    ipv_exposures = [
        exposure
        for exposure in exposures
        if exposure[
            "contains_ipv"
        ]
    ]

    vop_exposures = [
        exposure
        for exposure in exposures
        if exposure[
            "legacy_oral"
        ]
    ]

    ipv_count = len(
        ipv_exposures
    )

    vop_count = len(
        vop_exposures
    )

    if (
        ipv_count
        != history[
            "ipv_equivalent_exposure_count"
        ]
        or vop_count
        != history[
            "legacy_vopb_exposure_count"
        ]
    ):
        raise ValueError(
            "normalized polio history count mismatch"
        )

    if vop_count > 2:
        return _ipv_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de dois registros históricos de VOPb. "
                "A regra implementada cobre a transição documentada "
                "de zero, um ou dois reforços orais; revisar o "
                "histórico antes de definir a conduta."
            ),
            interpretation_en=(
                "More than two historical VOPb records are present. "
                "This implementation covers the documented transition "
                "states of zero, one or two oral boosters; review the "
                "history before determining conduct."
            ),
        )

    if ipv_count > 4:
        return _ipv_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de quatro exposições equivalentes a VIP. "
                "O calendário atual contém três doses básicas e "
                "apenas um reforço de rotina; revisar o registro."
            ),
            interpretation_en=(
                "More than four IPV-equivalent exposures are present. "
                "The current schedule contains three primary doses "
                "and only one routine booster; review the record."
            ),
        )

    # --------------------------------------------------------
    # AGE SCOPE
    # --------------------------------------------------------

    if (
        assessment_date
        > child_end
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A criança ultrapassou a faixa desta regra rotineira "
                "de VIP, que termina em 4 anos, 11 meses e 29 dias. "
                "Não inferir vacinação de viajante, bloqueio ou "
                "outra estratégia a partir desta camada."
            ),
            interpretation_en=(
                "The child is beyond this routine IPV rule's upper "
                "age limit of 4 years, 11 months and 29 days. "
                "Do not infer traveler, outbreak/blocking or another "
                "strategy from this layer."
            ),
        )

    # --------------------------------------------------------
    # VALIDATE PRIMARY CANDIDATES ALREADY PRESENT
    # --------------------------------------------------------

    primary = ipv_exposures[
        :min(
            ipv_count,
            3,
        )
    ]

    if primary:
        d1 = primary[
            0
        ][
            "administration_date"
        ]

        if d1 < routine_start:
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A primeira exposição equivalente a VIP ocorreu "
                    "antes dos 2 meses de idade. Esta regra não "
                    "possui autorização para validar automaticamente "
                    "uma dose anterior à idade inicial do calendário."
                ),
                interpretation_en=(
                    "The first IPV-equivalent exposure occurred before "
                    "2 months of age. This rule has no authority to "
                    "automatically validate a dose before the schedule's "
                    "starting age."
                ),
            )

    if len(
        primary
    ) >= 2:
        d1 = primary[
            0
        ][
            "administration_date"
        ]

        d2 = primary[
            1
        ][
            "administration_date"
        ]

        interval_12 = (
            d2
            - d1
        ).days

        if (
            interval_12
            < IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D1 e D2 é inferior "
                    "ao mínimo de 30 dias. Não validar "
                    "automaticamente o esquema."
                ),
                interpretation_en=(
                    "The historical interval between dose 1 and dose 2 "
                    "is shorter than the 30-day minimum. Do not "
                    "automatically validate the series."
                ),
            )

        if (
            interval_12
            < IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D1 e D2 está entre "
                    "30 e 59 dias. O PNI reserva o intervalo mínimo "
                    "a situações excepcionais, e essa justificativa "
                    "histórica não está estruturada no registro."
                ),
                interpretation_en=(
                    "The historical interval between dose 1 and dose 2 "
                    "is 30 to 59 days. The PNI reserves the minimum "
                    "interval for exceptional situations, and that "
                    "historical justification is not structured in "
                    "the record."
                ),
            )

    if len(
        primary
    ) >= 3:
        d2 = primary[
            1
        ][
            "administration_date"
        ]

        d3 = primary[
            2
        ][
            "administration_date"
        ]

        interval_23 = (
            d3
            - d2
        ).days

        if (
            interval_23
            < IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D2 e D3 é inferior "
                    "ao mínimo de 30 dias. Não validar "
                    "automaticamente o esquema."
                ),
                interpretation_en=(
                    "The historical interval between dose 2 and dose 3 "
                    "is shorter than the 30-day minimum. Do not "
                    "automatically validate the series."
                ),
            )

        if (
            interval_23
            < IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O intervalo histórico entre D2 e D3 está entre "
                    "30 e 59 dias sem justificativa excepcional "
                    "estruturada. Revisar antes de validar."
                ),
                interpretation_en=(
                    "The historical interval between dose 2 and dose 3 "
                    "is 30 to 59 days without structured evidence of "
                    "the exceptional circumstance. Review before "
                    "validation."
                ),
            )

    # A VOPb booster cannot be silently used to repair an incomplete
    # three-dose IPV-equivalent primary series.
    if (
        ipv_count < 3
        and vop_count
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há registro histórico de VOPb antes de três "
                "exposições equivalentes a VIP estarem estabelecidas. "
                "Esta regra não converte reforço oral em dose do "
                "esquema básico; revisar a sequência vacinal."
            ),
            interpretation_en=(
                "Historical VOPb is recorded before three "
                "IPV-equivalent exposures are established. "
                "This rule does not convert an oral booster into a "
                "primary-series dose; review the vaccination sequence."
            ),
        )

    # --------------------------------------------------------
    # PRIMARY SERIES — prospective next dose
    # --------------------------------------------------------

    if ipv_count < 3:
        if (
            assessment_date
            < routine_start
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=routine_start,
                interpretation_pt=(
                    "A criança ainda não atingiu a idade de início "
                    "rotineiro da VIP, aos 2 meses."
                ),
                interpretation_en=(
                    "The child has not yet reached the routine "
                    "starting age for IPV at 2 months."
                ),
            )

        if ipv_count == 0:
            if (
                administration_safety_screen_state
                == "not_screened"
            ):
                return _ipv_result(
                    assessment_date=assessment_date,
                    decision="context_required",
                    missing_context=[
                        "administration_safety_screen_state",
                    ],
                    interpretation_pt=(
                        "D1 de VIP está indicada pelo calendário, "
                        "mas a triagem de segurança ainda não foi "
                        "registrada."
                    ),
                    interpretation_en=(
                        "IPV dose 1 is indicated by the schedule, "
                        "but administration-safety screening has not "
                        "yet been documented."
                    ),
                )

            if (
                administration_safety_screen_state
                == "screened_concern"
            ):
                return _ipv_result(
                    assessment_date=assessment_date,
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "A triagem de segurança identificou "
                        "preocupação antes de D1. Revisar sem inferir "
                        "automaticamente CRIE ou produto alternativo."
                    ),
                    interpretation_en=(
                        "Administration-safety screening identified "
                        "a concern before dose 1. Review without "
                        "automatically inferring CRIE or an alternative "
                        "product."
                    ),
                )

            return _ipv_result(
                assessment_date=assessment_date,
                decision="recommend_now",
                interpretation_pt=(
                    "Não há exposição equivalente a VIP documentada "
                    "e a criança está na faixa etária da rotina: "
                    "recomendar D1 agora."
                ),
                interpretation_en=(
                    "No IPV-equivalent exposure is documented and "
                    "the child is within the routine age range: "
                    "recommend dose 1 now."
                ),
            )

        last_primary = primary[
            -1
        ][
            "administration_date"
        ]

        elapsed = (
            assessment_date
            - last_primary
        ).days

        next_number = (
            ipv_count
            + 1
        )

        if (
            elapsed
            < IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    f"D{ipv_count} está válida, mas ainda não "
                    "transcorreram 30 dias para a próxima dose."
                ),
                interpretation_en=(
                    f"Dose {ipv_count} is valid, but 30 days have "
                    "not yet elapsed for the next dose."
                ),
            )

        use_exception = (
            elapsed
            < IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
        )

        if (
            use_exception
            and not exceptional_minimum_interval_authorized
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "O mínimo de 30 dias foi atingido, mas o intervalo "
                    "rotineiramente recomendado é de 60 dias. "
                    "A antecipação entre 30 e 59 dias exige "
                    "autorização excepcional explícita."
                ),
                interpretation_en=(
                    "The 30-day minimum has been reached, but the "
                    "routinely recommended interval is 60 days. "
                    "Acceleration between 30 and 59 days requires "
                    "explicit exceptional authorization."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=use_exception,
                interpretation_pt=(
                    f"D{next_number} está elegível pelo intervalo, "
                    "mas a triagem de segurança ainda não foi "
                    "registrada."
                ),
                interpretation_en=(
                    f"Dose {next_number} is interval-eligible, "
                    "but administration-safety screening has not yet "
                    "been documented."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
                ),
                minimum_interval_applied=use_exception,
                interpretation_pt=(
                    f"A triagem de segurança identificou preocupação "
                    f"antes de D{next_number}; revisar a conduta."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    f"concern before dose {next_number}; review "
                    "the vaccination plan."
                ),
            )

        return _ipv_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_interval_days=(
                IPV_PRIMARY_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                IPV_PRIMARY_MINIMUM_INTERVAL_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    f"O intervalo recomendado de 60 dias foi "
                    f"atingido: recomendar D{next_number} de VIP agora."
                )
                if not use_exception
                else
                (
                    f"Há autorização excepcional explícita para usar "
                    f"o intervalo mínimo: recomendar D{next_number} "
                    f"de VIP agora."
                )
            ),
            interpretation_en=(
                (
                    "The recommended 60-day interval has been reached: "
                    f"recommend IPV dose {next_number} now."
                )
                if not use_exception
                else
                (
                    "Use of the minimum interval is explicitly "
                    f"authorized: recommend IPV dose {next_number} now."
                )
            ),
        )

    # --------------------------------------------------------
    # PRIMARY COMPLETE — inspect any fourth IPV-equivalent event
    # --------------------------------------------------------

    d3 = ipv_exposures[
        2
    ][
        "administration_date"
    ]

    booster_min_date = _add_months_clamped(
        d3,
        IPV_BOOSTER_MINIMUM_MONTHS_AFTER_D3,
    )

    booster_recommended_date = _add_months_clamped(
        d3,
        IPV_BOOSTER_RECOMMENDED_MONTHS_AFTER_D3,
    )

    if ipv_count == 4:
        booster = ipv_exposures[
            3
        ][
            "administration_date"
        ]

        if (
            booster
            < booster_age
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A quarta exposição equivalente a VIP ocorreu "
                    "antes dos 15 meses e não pode ser classificada "
                    "automaticamente como o reforço rotineiro."
                ),
                interpretation_en=(
                    "The fourth IPV-equivalent exposure occurred "
                    "before 15 months of age and cannot automatically "
                    "be classified as the routine booster."
                ),
            )

        if (
            booster
            < booster_min_date
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A quarta exposição equivalente a VIP ocorreu "
                    "antes do intervalo mínimo de 6 meses após D3; "
                    "não classificá-la automaticamente como reforço."
                ),
                interpretation_en=(
                    "The fourth IPV-equivalent exposure occurred "
                    "before the minimum 6-calendar-month interval "
                    "after dose 3; do not automatically classify it "
                    "as the booster."
                ),
            )

        if vop_count >= 2:
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há um reforço equivalente a VIP além de dois "
                    "reforços históricos com VOPb. O calendário atual "
                    "não exige doses adicionais; revisar o registro "
                    "para evitar ocultar vacinação excedente."
                ),
                interpretation_en=(
                    "An IPV-equivalent booster is present in addition "
                    "to two historical VOPb boosters. The current "
                    "schedule does not require additional doses; "
                    "review the record rather than hiding excess "
                    "vaccination."
                ),
            )

        return _ipv_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Três doses básicas válidas e um reforço válido "
                "equivalente a VIP estão documentados. O esquema "
                "rotineiro atual está completo; não existe segundo "
                "reforço rotineiro de VIP aos 4 anos nesta regra."
            ),
            interpretation_en=(
                "Three valid primary doses and one valid "
                "IPV-equivalent booster are documented. The current "
                "routine schedule is complete; this rule has no "
                "second routine IPV booster at age 4 years."
            ),
        )

    # --------------------------------------------------------
    # LEGACY VOP TRANSITION
    # --------------------------------------------------------

    if (
        legacy_reconciliation_relevant
        and not history[
            "legacy_vopb_history_supplied"
        ]
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "A criança já podia ter recebido reforço com VOPb "
                "antes da transição de 4/11/2024, mas o histórico "
                "de VOPb não foi fornecido. Ausência de histórico "
                "não equivale a zero dose; reconciliar antes de "
                "definir o reforço."
            ),
            interpretation_en=(
                "The child could have received a VOPb booster before "
                "the 4 November 2024 transition, but VOPb history was "
                "not supplied. Missing history does not equal zero "
                "doses; reconcile it before determining the booster."
            ),
        )

    if (
        not history[
            "safe_for_transition_evaluation"
        ]
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O esquema básico está completo, mas o histórico "
                "necessário para avaliar a transição VOPb→VIP não "
                "está suficientemente reconciliado."
            ),
            interpretation_en=(
                "The primary series is complete, but the history "
                "needed to evaluate the VOPb-to-IPV transition is "
                "not sufficiently reconciled."
            ),
        )

    if vop_count == 2:
        first_vop = vop_exposures[
            0
        ][
            "administration_date"
        ]

        if first_vop <= d3:
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Dois registros de VOPb existem, porém pelo menos "
                    "um não está cronologicamente após D3. Não é "
                    "seguro tratá-los automaticamente como os dois "
                    "reforços históricos."
                ),
                interpretation_en=(
                    "Two VOPb records are present, but at least one "
                    "is not chronologically after dose 3. They cannot "
                    "safely be treated automatically as the two "
                    "historical boosters."
                ),
            )

        return _ipv_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "O esquema básico com três exposições equivalentes "
                "a VIP está completo e há dois reforços históricos "
                "com VOPb. A orientação de transição considera esse "
                "esquema completo; não administrar nova dose de "
                "rotina por esta regra."
            ),
            interpretation_en=(
                "The three-dose IPV-equivalent primary series is "
                "complete and two historical VOPb boosters are "
                "documented. Transition guidance considers this "
                "schedule complete; do not administer another routine "
                "dose under this rule."
            ),
        )

    if vop_count == 1:
        vop_date = vop_exposures[
            0
        ][
            "administration_date"
        ]

        if (
            vop_date
            <= d3
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "O registro de VOPb não ocorre após D3 e não pode "
                    "ser automaticamente classificado como primeiro "
                    "reforço histórico."
                ),
                interpretation_en=(
                    "The VOPb record does not occur after dose 3 and "
                    "cannot automatically be classified as the first "
                    "historical booster."
                ),
            )

        # The transition source assumes a true historical booster.
        # Fail closed if its chronology would not satisfy even the
        # current minimum D3->booster interval.
        if (
            vop_date
            < booster_min_date
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A VOPb registrada ocorreu antes de 6 meses após "
                    "D3. A regra de transição pressupõe um reforço "
                    "histórico válido; revisar antes de aplicar a "
                    "conduta especial de transição."
                ),
                interpretation_en=(
                    "The recorded VOPb occurred before 6 calendar "
                    "months after dose 3. The transition rule assumes "
                    "a valid historical booster; review before using "
                    "the special transition conduct."
                ),
            )

        transition_min_date = (
            vop_date
            + timedelta(
                days=IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS,
            )
        )

        if (
            assessment_date
            < transition_min_date
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=transition_min_date,
                minimum_interval_days=(
                    IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS
                ),
                interpretation_pt=(
                    "Há um primeiro reforço histórico com VOPb. "
                    "A orientação de transição exige um reforço com "
                    "VIP, mas ainda não transcorreram os 30 dias "
                    "mínimos excepcionais desde a VOPb."
                ),
                interpretation_en=(
                    "One historical VOPb booster is documented. "
                    "Transition guidance requires an IPV booster, "
                    "but the exceptional minimum 30 days since VOPb "
                    "have not yet elapsed."
                ),
            )

        if (
            administration_safety_screen_state
            == "not_screened"
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "administration_safety_screen_state",
                ],
                minimum_interval_days=(
                    IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS
                ),
                minimum_interval_applied=True,
                interpretation_pt=(
                    "A criança está elegível ao reforço VIP da "
                    "transição após VOPb, mas a triagem de segurança "
                    "ainda não foi registrada."
                ),
                interpretation_en=(
                    "The child is eligible for the transition IPV "
                    "booster after VOPb, but administration-safety "
                    "screening has not yet been documented."
                ),
            )

        if (
            administration_safety_screen_state
            == "screened_concern"
        ):
            return _ipv_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                minimum_interval_days=(
                    IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS
                ),
                minimum_interval_applied=True,
                interpretation_pt=(
                    "A triagem de segurança identificou preocupação "
                    "antes do reforço VIP da transição; revisar sem "
                    "inferir CRIE automaticamente."
                ),
                interpretation_en=(
                    "Administration-safety screening identified a "
                    "concern before the transition IPV booster; review "
                    "without automatically inferring CRIE."
                ),
            )

        return _ipv_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            minimum_interval_days=(
                IPV_TRANSITION_VOPB_TO_VIP_MINIMUM_DAYS
            ),
            minimum_interval_applied=True,
            interpretation_pt=(
                "O esquema básico está completo e há um primeiro "
                "reforço histórico com VOPb. Conforme a transição "
                "para esquema exclusivo com VIP, recomendar um "
                "reforço com VIP agora; o mínimo excepcional de "
                "30 dias após VOPb foi cumprido."
            ),
            interpretation_en=(
                "The primary series is complete and one historical "
                "VOPb booster is documented. Under the transition to "
                "an IPV-only schedule, recommend one IPV booster now; "
                "the exceptional 30-day minimum after VOPb has been "
                "satisfied."
            ),
        )

    # --------------------------------------------------------
    # CURRENT SINGLE VIP BOOSTER — no historical VOPb booster
    # --------------------------------------------------------

    if (
        assessment_date
        < booster_age
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=max(
                booster_age,
                booster_min_date,
            ),
            interpretation_pt=(
                "O esquema básico de três doses está completo, mas "
                "a criança ainda não atingiu a idade de 15 meses "
                "para o único reforço rotineiro de VIP."
            ),
            interpretation_en=(
                "The three-dose primary series is complete, but the "
                "child has not yet reached 15 months of age for the "
                "single routine IPV booster."
            ),
        )

    if (
        assessment_date
        < booster_min_date
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=booster_min_date,
            interpretation_pt=(
                "A criança já atingiu 15 meses, porém ainda não "
                "completou o intervalo mínimo de 6 meses após D3 "
                "para o reforço de VIP."
            ),
            interpretation_en=(
                "The child has reached 15 months, but the minimum "
                "6-calendar-month interval after dose 3 for the IPV "
                "booster has not yet elapsed."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            recommended_date=(
                booster_recommended_date
                if assessment_date
                < booster_recommended_date
                else None
            ),
            interpretation_pt=(
                "O reforço único de VIP está elegível pelo intervalo "
                "mínimo, mas a triagem de segurança ainda não foi "
                "registrada."
            ),
            interpretation_en=(
                "The single IPV booster is eligible by the minimum "
                "interval, but administration-safety screening has "
                "not yet been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _ipv_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A triagem de segurança identificou preocupação "
                "antes do reforço único de VIP; revisar a conduta."
            ),
            interpretation_en=(
                "Administration-safety screening identified a concern "
                "before the single IPV booster; review the vaccination "
                "plan."
            ),
        )

    return _ipv_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_date=(
            booster_recommended_date
            if assessment_date
            < booster_recommended_date
            else None
        ),
        interpretation_pt=(
            (
                "O esquema básico está completo, a criança tem pelo "
                "menos 15 meses e já cumpriu o intervalo recomendado "
                "de 9 meses após D3: recomendar o único reforço "
                "rotineiro de VIP agora."
            )
            if (
                assessment_date
                >= booster_recommended_date
            )
            else
            (
                "O esquema básico está completo, a criança tem pelo "
                "menos 15 meses e já cumpriu o intervalo mínimo de "
                "6 meses após D3. O intervalo recomendado é de "
                "9 meses; a atualização pode ser realizada agora "
                "dentro da regra mínima vigente."
            )
        ),
        interpretation_en=(
            (
                "The primary series is complete, the child is at "
                "least 15 months old, and the recommended 9-calendar-"
                "month interval after dose 3 has elapsed: recommend "
                "the single routine IPV booster now."
            )
            if (
                assessment_date
                >= booster_recommended_date
            )
            else
            (
                "The primary series is complete, the child is at "
                "least 15 months old, and the minimum 6-calendar-month "
                "interval after dose 3 has elapsed. The recommended "
                "interval is 9 months; catch-up may proceed now under "
                "the current minimum-interval rule."
            )
        ),
    )



PNEUMOCOCCAL_CHILD_RULE_ID = (
    "PNI26-PNEUMO-CHILD-ROUTINE-001"
)

PNEUMOCOCCAL_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

PNEUMOCOCCAL_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/centrais-de-conteudo/"
    "publicacoes/guias-e-manuais/2026/"
    "guia-tecnico-para-introducao-da-vacina-"
    "pneumococica-20-valente-conjugada-no-programa-"
    "nacional-de-imunizacoes.pdf"
)

PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS = 60
PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS = 30
PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS = 60


def _pneumococcal_result(
    *,
    assessment_date: date,
    vaccine_key: str,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    history_required: bool = False,
    missing_context: list[str] | None = None,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            vaccine_key,

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                PNEUMOCOCCAL_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Guia Técnico para Introdução da Vacina "
                "Pneumocócica 20-valente no PNI"
            ),

            "source_url":
                PNEUMOCOCCAL_SOURCE_URL,

            "source_snapshot_date":
                PNEUMOCOCCAL_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _validate_pneumococcal_normalized_history(
    value: Any,
) -> dict[str, Any]:
    history = _as_plain_dict(
        value
    )

    required = {
        "target_family",
        "history_scope",
        "history_state",
        "present_history_keys",
        "vpc10_history_supplied",
        "vpc20_history_supplied",
        "exposures",
        "exposure_event_count",
        "vpc10_exposure_count",
        "vpc20_exposure_count",
        "mixed_vpc10_vpc20_history",
        "ambiguous_same_day_exposure_dates",
        "unmapped_vaccine_keys",
        "source_history_incomplete",
        "safe_for_chronology_evaluation",
        "safe_for_role_assignment",
    }

    missing = sorted(
        required
        - set(
            history
        )
    )

    if missing:
        raise ValueError(
            "normalized pneumococcal history missing fields: "
            + ", ".join(
                missing
            )
        )

    if (
        history[
            "target_family"
        ]
        != "pneumococcal_conjugate_routine_child"
    ):
        raise ValueError(
            "invalid normalized pneumococcal target_family"
        )

    return history


def _pneumococcal_due_with_safety(
    *,
    assessment_date: date,
    vaccine_key: str,
    administration_safety_screen_state: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_interval_days: int | None = None,
    minimum_interval_days: int | None = None,
    minimum_interval_applied: bool = False,
) -> dict[str, Any]:
    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key=vaccine_key,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                "A dose pneumocócica está indicada pela situação "
                "vacinal atual, mas a triagem de segurança para "
                "administração ainda não foi registrada."
            ),
            interpretation_en=(
                "A pneumococcal dose is indicated by the current "
                "vaccination state, but administration-safety "
                "screening has not yet been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key=vaccine_key,
            decision="special_pathway_review",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                "A triagem de segurança identificou preocupação "
                "antes da vacinação pneumocócica. Revisar a conduta "
                "sem inferir automaticamente RIE ou outro esquema "
                "especial."
            ),
            interpretation_en=(
                "Administration-safety screening identified a "
                "concern before pneumococcal vaccination. Review "
                "the plan without automatically inferring RIE or "
                "another special schedule."
            ),
        )

    return _pneumococcal_result(
        assessment_date=assessment_date,
        vaccine_key=vaccine_key,
        decision="recommend_now",
        recommended_interval_days=(
            recommended_interval_days
        ),
        minimum_interval_days=(
            minimum_interval_days
        ),
        minimum_interval_applied=(
            minimum_interval_applied
        ),
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
    )


def evaluate_pni_pneumococcal_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    pneumococcal_history: Any,
    administration_safety_screen_state: str = "not_screened",
    exceptional_minimum_interval_authorized: bool = False,
) -> dict[str, Any]:
    """
    Evaluate the Brazilian 2026 routine-child VPC10/VPC20
    transition using normalized product-sensitive history.

    The evaluator is current-state based. It does not fabricate
    future D2/booster sequence from the internally inconsistent
    continuation of the exact-11-month/no-history source row.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized "
            "must be boolean"
        )

    history = _validate_pneumococcal_normalized_history(
        pneumococcal_history
    )

    age_2m = _add_months_clamped(
        date_of_birth,
        2,
    )

    age_5m = _add_months_clamped(
        date_of_birth,
        5,
    )

    age_11m = _add_months_clamped(
        date_of_birth,
        11,
    )

    age_12m = _add_months_clamped(
        date_of_birth,
        12,
    )

    age_60m = _add_months_clamped(
        date_of_birth,
        60,
    )

    if (
        assessment_date
        >= age_60m
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="not_applicable",
            interpretation_pt=(
                "A criança está fora da faixa desta regra de rotina, "
                "que termina antes do aniversário de 60 meses. "
                "Não inferir esquema adulto, RIE ou condição especial."
            ),
            interpretation_en=(
                "The child is beyond this routine rule, which ends "
                "before the 60-month birthday. Do not infer an adult, "
                "RIE or special-condition schedule."
            ),
        )

    if (
        history[
            "source_history_incomplete"
        ]
        or history[
            "unmapped_vaccine_keys"
        ]
        or history[
            "ambiguous_same_day_exposure_dates"
        ]
        or not history[
            "safe_for_role_assignment"
        ]
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico pneumocócico está parcial, desconhecido, "
                "contém produto não mapeado ou possível duplicidade. "
                "Reconciliar VPC10/VPC20 antes de atribuir D1, D2 "
                "ou reforço."
            ),
            interpretation_en=(
                "Pneumococcal history is partial or unknown, contains "
                "an unmapped product, or has a possible duplicate. "
                "Reconcile VPC10/VPC20 history before assigning dose "
                "1, dose 2 or booster roles."
            ),
        )

    if (
        not history[
            "vpc10_history_supplied"
        ]
        or not history[
            "vpc20_history_supplied"
        ]
    ):
        missing = []

        if not history[
            "vpc10_history_supplied"
        ]:
            missing.append(
                "pneumococcal_10_history"
            )

        if not history[
            "vpc20_history_supplied"
        ]:
            missing.append(
                "pneumococcal_20_history"
            )

        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="history_required",
            history_required=True,
            missing_context=missing,
            interpretation_pt=(
                "Como a transição de 2026 é sensível ao produto, "
                "é necessário informar separadamente os históricos "
                "de VPC10 e VPC20. Ausência de um histórico não "
                "equivale a zero dose."
            ),
            interpretation_en=(
                "Because the 2026 transition is product-sensitive, "
                "VPC10 and VPC20 histories must both be supplied "
                "separately. A missing product history does not mean "
                "zero doses."
            ),
        )

    exposures = list(
        history[
            "exposures"
        ]
    )

    if (
        len(
            exposures
        )
        != history[
            "exposure_event_count"
        ]
    ):
        raise ValueError(
            "normalized pneumococcal exposure count mismatch"
        )

    if len(
        exposures
    ) > 3:
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "Há mais de três exposições pneumocócicas conjugadas "
                "de rotina documentadas. Revisar o histórico antes "
                "de atribuir função a doses adicionais."
            ),
            interpretation_en=(
                "More than three routine pneumococcal conjugate "
                "exposures are documented. Review the history before "
                "assigning a role to additional doses."
            ),
        )

    for exposure in exposures:
        administration_date = exposure[
            "administration_date"
        ]

        if (
            administration_date
            < date_of_birth
        ):
            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há exposição pneumocócica registrada antes da "
                    "data de nascimento; revisar o registro."
                ),
                interpretation_en=(
                    "A pneumococcal exposure is recorded before the "
                    "date of birth; review the record."
                ),
            )

        if (
            administration_date
            < age_2m
        ):
            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há exposição pneumocócica conjugada antes dos "
                    "2 meses. Esta regra de rotina não possui base "
                    "para validá-la automaticamente."
                ),
                interpretation_en=(
                    "A pneumococcal conjugate exposure occurred before "
                    "2 months of age. This routine rule has no basis "
                    "to validate it automatically."
                ),
            )

    if (
        assessment_date
        < age_2m
    ):
        if exposures:
            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                decision="special_pathway_review",
                interpretation_pt=(
                    "Existe exposição registrada antes da idade "
                    "rotineira inicial de 2 meses; revisar o histórico."
                ),
                interpretation_en=(
                    "An exposure is documented before the routine "
                    "starting age of 2 months; review the history."
                ),
            )

        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="not_due_now",
            recommended_date=age_2m,
            interpretation_pt=(
                "A criança ainda não atingiu 2 meses, idade da D1 "
                "rotineira com VPC20."
            ),
            interpretation_en=(
                "The child has not yet reached 2 months, the routine "
                "age for VPC20 dose 1."
            ),
        )

    # --------------------------------------------------------
    # ZERO HISTORY
    # --------------------------------------------------------

    if not exposures:
        if (
            assessment_date
            >= age_12m
        ):
            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                interpretation_pt=(
                    "Entre 12 meses e 4 anos, 11 meses e 29 dias, "
                    "sem histórico vacinal pneumocócico, recomendar "
                    "dose única de VPC20 agora."
                ),
                interpretation_en=(
                    "From 12 months through 4 years, 11 months and "
                    "29 days, with no pneumococcal vaccination "
                    "history, recommend a single VPC20 dose now."
                ),
            )

        if (
            assessment_date
            >= age_11m
        ):
            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                interpretation_pt=(
                    "A criança está na faixa de 11 meses e não possui "
                    "histórico vacinal: recomendar D1 com VPC20 agora. "
                    "Esta decisão não inventa uma futura D2; a próxima "
                    "avaliação deve usar a situação etária e vacinal "
                    "então documentada."
                ),
                interpretation_en=(
                    "The child is in the 11-month age band with no "
                    "vaccination history: recommend VPC20 dose 1 now. "
                    "This decision does not invent a future dose 2; "
                    "the next assessment must use the age and history "
                    "documented at that later encounter."
                ),
            )

        return _pneumococcal_due_with_safety(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            interpretation_pt=(
                "Não há histórico pneumocócico documentado nesta "
                "faixa pré-12 meses: recomendar D1 com VPC20 agora."
            ),
            interpretation_en=(
                "No pneumococcal history is documented in this "
                "pre-12-month age range: recommend VPC20 dose 1 now."
            ),
        )

    # --------------------------------------------------------
    # ONE EXPOSURE
    # --------------------------------------------------------

    if len(
        exposures
    ) == 1:
        first = exposures[
            0
        ]

        first_date = first[
            "administration_date"
        ]

        first_product = first[
            "source_vaccine_key"
        ]

        elapsed = (
            assessment_date
            - first_date
        ).days

        first_at_or_after_12m = (
            first_date
            >= age_12m
        )

        if (
            assessment_date
            >= age_12m
        ):
            if first_at_or_after_12m:
                if (
                    first_product
                    == "pneumococcal_20"
                ):
                    return _pneumococcal_result(
                        assessment_date=assessment_date,
                        vaccine_key="pneumococcal_20",
                        decision="not_due_now",
                        interpretation_pt=(
                            "A primeira e única exposição foi VPC20 "
                            "administrada a partir de 12 meses. Nessa "
                            "situação de recuperação sem histórico "
                            "prévio, a dose única já completa a camada "
                            "rotineira desta regra."
                        ),
                        interpretation_en=(
                            "The first and only exposure was VPC20 "
                            "administered at or after 12 months. In "
                            "this catch-up state with no earlier "
                            "history, that single dose completes this "
                            "routine rule."
                        ),
                    )

                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "A única exposição pneumocócica foi VPC10 "
                        "administrada a partir de 12 meses. A regra "
                        "rotineira de recuperação nessa faixa indica "
                        "VPC20; revisar antes de atribuir conclusão."
                    ),
                    interpretation_en=(
                        "The only pneumococcal exposure was VPC10 "
                        "administered at or after 12 months. Routine "
                        "catch-up in this age band specifies VPC20; "
                        "review before assigning completion."
                    ),
                )

            booster_date = (
                first_date
                + timedelta(
                    days=(
                        PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                    ),
                )
            )

            if (
                assessment_date
                < booster_date
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="not_due_now",
                    recommended_date=booster_date,
                    minimum_interval_days=(
                        PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                    ),
                    interpretation_pt=(
                        "Há somente D1 documentada antes dos 12 meses. "
                        "O reforço com VPC20 deve respeitar pelo menos "
                        "60 dias após D1."
                    ),
                    interpretation_en=(
                        "Only dose 1 is documented before 12 months. "
                        "The VPC20 booster must be at least 60 days "
                        "after dose 1."
                    ),
                )

            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                minimum_interval_days=(
                    PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A criança tem pelo menos 12 meses e somente D1 "
                    "do esquema básico está documentada. Já decorreram "
                    "60 dias: recomendar um reforço com VPC20 agora."
                ),
                interpretation_en=(
                    "The child is at least 12 months old and only "
                    "dose 1 of the primary schedule is documented. "
                    "Sixty days have elapsed: recommend one VPC20 "
                    "booster now."
                ),
            )

        if (
            assessment_date
            >= age_11m
        ):
            if (
                first_product
                == "pneumococcal_20"
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "Na faixa exata de 11 meses há somente uma D1 "
                        "prévia com VPC20. O quadro fonte explicita "
                        "D1 prévia com VPC10 e ausência de histórico, "
                        "mas não descreve de forma inequívoca este "
                        "estado. Manter revisão por fonte."
                    ),
                    interpretation_en=(
                        "In the exact 11-month age band there is only "
                        "one prior VPC20 dose 1. The source table "
                        "explicitly covers prior VPC10 dose 1 and zero "
                        "history, but does not unambiguously describe "
                        "this state. Keep it under source review."
                    ),
                )

            next_product = "pneumococcal_20"

            use_exception = (
                elapsed
                >= PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                and elapsed
                < PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
            )

            if (
                elapsed
                < PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key=next_product,
                    decision="not_due_now",
                    recommended_date=(
                        first_date
                        + timedelta(
                            days=(
                                PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                            ),
                        )
                    ),
                    recommended_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                    ),
                    minimum_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                    ),
                    interpretation_pt=(
                        "D1 com VPC10 está documentada, mas ainda não "
                        "decorreram 30 dias para D2."
                    ),
                    interpretation_en=(
                        "VPC10 dose 1 is documented, but 30 days have "
                        "not yet elapsed for dose 2."
                    ),
                )

            if (
                use_exception
                and not exceptional_minimum_interval_authorized
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key=next_product,
                    decision="not_due_now",
                    recommended_date=(
                        first_date
                        + timedelta(
                            days=(
                                PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                            ),
                        )
                    ),
                    recommended_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                    ),
                    minimum_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                    ),
                    interpretation_pt=(
                        "O mínimo excepcional de 30 dias foi atingido, "
                        "mas o intervalo recomendado é de 60 dias. "
                        "Antecipação exige autorização excepcional "
                        "explícita."
                    ),
                    interpretation_en=(
                        "The exceptional 30-day minimum has been "
                        "reached, but the recommended interval is "
                        "60 days. Acceleration requires explicit "
                        "exceptional authorization."
                    ),
                )

            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key=next_product,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                recommended_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                ),
                minimum_interval_applied=use_exception,
                interpretation_pt=(
                    "Na faixa de 11 meses, com D1 prévia de VPC10, "
                    "recomendar D2 com VPC20 agora."
                ),
                interpretation_en=(
                    "In the 11-month age band, with prior VPC10 "
                    "dose 1, recommend VPC20 dose 2 now."
                ),
            )

        # Ages 2m through <11m.
        if (
            first_product
            == "pneumococcal_20"
        ):
            next_product = "pneumococcal_10"

        elif (
            first_product
            == "pneumococcal_10"
        ):
            next_product = "pneumococcal_20"

        else:
            raise ValueError(
                "unexpected pneumococcal product"
            )

        # Before 5 months, use the routine 60-day interval only.
        if (
            assessment_date
            < age_5m
        ):
            if (
                elapsed
                < PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key=next_product,
                    decision="not_due_now",
                    recommended_date=(
                        first_date
                        + timedelta(
                            days=(
                                PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                            ),
                        )
                    ),
                    recommended_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                    ),
                    interpretation_pt=(
                        "A primeira dose está documentada, mas o "
                        "intervalo rotineiro de 60 dias para D2 ainda "
                        "não foi completado."
                    ),
                    interpretation_en=(
                        "The first dose is documented, but the routine "
                        "60-day interval for dose 2 has not yet elapsed."
                    ),
                )

            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key=next_product,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                recommended_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    (
                        "Após D1 com VPC20, recomendar D2 com VPC10 "
                        "agora."
                    )
                    if next_product
                    == "pneumococcal_10"
                    else
                    (
                        "O esquema foi iniciado com VPC10; a VPC20 "
                        "pode completar o esquema. Recomendar D2 "
                        "com VPC20 agora."
                    )
                ),
                interpretation_en=(
                    (
                        "After VPC20 dose 1, recommend VPC10 dose 2 "
                        "now."
                    )
                    if next_product
                    == "pneumococcal_10"
                    else
                    (
                        "The schedule was started with VPC10; VPC20 "
                        "may complete it. Recommend VPC20 dose 2 now."
                    )
                ),
            )

        # 5m through <11m: 60d recommended / 30d exceptional.
        if (
            elapsed
            < PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
        ):
            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key=next_product,
                decision="not_due_now",
                recommended_date=(
                    first_date
                    + timedelta(
                        days=(
                            PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                        ),
                    )
                ),
                recommended_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                ),
                interpretation_pt=(
                    "A primeira dose está documentada, mas ainda não "
                    "decorreram 30 dias para a segunda dose."
                ),
                interpretation_en=(
                    "The first dose is documented, but 30 days have "
                    "not yet elapsed for the second dose."
                ),
            )

        use_exception = (
            elapsed
            < PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
        )

        if (
            use_exception
            and not exceptional_minimum_interval_authorized
        ):
            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key=next_product,
                decision="not_due_now",
                recommended_date=(
                    first_date
                    + timedelta(
                        days=(
                            PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                        ),
                    )
                ),
                recommended_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                ),
                minimum_interval_days=(
                    PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                ),
                interpretation_pt=(
                    "O mínimo excepcional de 30 dias foi atingido, "
                    "mas o intervalo recomendado é de 60 dias. "
                    "A antecipação exige autorização excepcional."
                ),
                interpretation_en=(
                    "The exceptional 30-day minimum has been reached, "
                    "but the recommended interval is 60 days. "
                    "Acceleration requires explicit exceptional "
                    "authorization."
                ),
            )

        return _pneumococcal_due_with_safety(
            assessment_date=assessment_date,
            vaccine_key=next_product,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            recommended_interval_days=(
                PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
            ),
            minimum_interval_days=(
                PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
            ),
            minimum_interval_applied=use_exception,
            interpretation_pt=(
                (
                    "Com D1 prévia de VPC20, recomendar D2 com VPC10 "
                    "agora."
                )
                if next_product
                == "pneumococcal_10"
                else
                (
                    "Com D1 prévia de VPC10, recomendar D2 com VPC20 "
                    "agora."
                )
            ),
            interpretation_en=(
                (
                    "With prior VPC20 dose 1, recommend VPC10 dose 2 "
                    "now."
                )
                if next_product
                == "pneumococcal_10"
                else
                (
                    "With prior VPC10 dose 1, recommend VPC20 dose 2 "
                    "now."
                )
            ),
        )

    # --------------------------------------------------------
    # TWO EXPOSURES
    # --------------------------------------------------------

    if len(
        exposures
    ) == 2:
        first = exposures[
            0
        ]

        second = exposures[
            1
        ]

        first_date = first[
            "administration_date"
        ]

        second_date = second[
            "administration_date"
        ]

        first_product = first[
            "source_vaccine_key"
        ]

        second_product = second[
            "source_vaccine_key"
        ]

        first_pre12 = (
            first_date
            < age_12m
        )

        second_pre12 = (
            second_date
            < age_12m
        )

        interval = (
            second_date
            - first_date
        ).days

        if (
            first_pre12
            and second_pre12
        ):
            if (
                interval
                < PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "O intervalo histórico entre as duas doses "
                        "pré-12 meses é inferior a 30 dias; não validar "
                        "automaticamente como D1/D2."
                    ),
                    interpretation_en=(
                        "The historical interval between the two "
                        "pre-12-month doses is shorter than 30 days; "
                        "do not automatically validate them as "
                        "dose 1/dose 2."
                    ),
                )

            if (
                interval
                < PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    recommended_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
                    ),
                    minimum_interval_days=(
                        PNEUMOCOCCAL_PRIMARY_EXCEPTIONAL_MINIMUM_DAYS
                    ),
                    interpretation_pt=(
                        "O intervalo histórico entre D1 e D2 está "
                        "entre 30 e 59 dias sem justificativa "
                        "excepcional estruturada. Revisar antes de "
                        "validar o esquema."
                    ),
                    interpretation_en=(
                        "The historical interval between dose 1 and "
                        "dose 2 is 30 to 59 days without structured "
                        "evidence of the exceptional circumstance. "
                        "Review before validating the series."
                    ),
                )

            allowed_pairs = {
                (
                    "pneumococcal_20",
                    "pneumococcal_10",
                ),
                (
                    "pneumococcal_10",
                    "pneumococcal_20",
                ),
                (
                    "pneumococcal_10",
                    "pneumococcal_10",
                ),
            }

            if (
                (
                    first_product,
                    second_product,
                )
                not in allowed_pairs
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "A sequência de produtos das duas exposições "
                        "pré-12 meses não corresponde a um padrão "
                        "rotineiro/transition explicitamente suportado "
                        "por esta regra."
                    ),
                    interpretation_en=(
                        "The product sequence of the two pre-12-month "
                        "exposures does not match a routine/transition "
                        "pattern explicitly supported by this rule."
                    ),
                )

            booster_date = (
                second_date
                + timedelta(
                    days=(
                        PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                    ),
                )
            )

            due_date = max(
                age_12m,
                booster_date,
            )

            if (
                assessment_date
                < due_date
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="not_due_now",
                    recommended_date=due_date,
                    minimum_interval_days=(
                        PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                    ),
                    interpretation_pt=(
                        "D1 e D2 estão documentadas. O reforço com "
                        "VPC20 é realizado a partir de 12 meses, com "
                        "pelo menos 60 dias após D2."
                    ),
                    interpretation_en=(
                        "Dose 1 and dose 2 are documented. The VPC20 "
                        "booster is given from 12 months of age, at "
                        "least 60 days after dose 2."
                    ),
                )

            return _pneumococcal_due_with_safety(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                minimum_interval_days=(
                    PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "D1 e D2 válidas estão documentadas, a criança "
                    "tem pelo menos 12 meses e já decorreram 60 dias "
                    "após D2: recomendar reforço com VPC20 agora."
                ),
                interpretation_en=(
                    "Valid dose 1 and dose 2 are documented, the child "
                    "is at least 12 months old, and 60 days have "
                    "elapsed since dose 2: recommend a VPC20 booster "
                    "now."
                ),
            )

        # One pre-12m D1 followed by a >=12m exposure can represent
        # the explicit one-D1 catch-up booster.
        if (
            first_pre12
            and not second_pre12
        ):
            if (
                second_product
                != "pneumococcal_20"
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "Após uma D1 pré-12 meses, a exposição "
                        "documentada a partir de 12 meses não é VPC20. "
                        "A regra de recuperação especifica reforço "
                        "com VPC20; revisar."
                    ),
                    interpretation_en=(
                        "After a pre-12-month dose 1, the documented "
                        "exposure at or after 12 months is not VPC20. "
                        "Catch-up specifies a VPC20 booster; review."
                    ),
                )

            if (
                interval
                < PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
            ):
                return _pneumococcal_result(
                    assessment_date=assessment_date,
                    vaccine_key="pneumococcal_20",
                    decision="special_pathway_review",
                    interpretation_pt=(
                        "A VPC20 administrada a partir de 12 meses "
                        "ocorreu antes de 60 dias após D1; não "
                        "classificá-la automaticamente como reforço."
                    ),
                    interpretation_en=(
                        "The VPC20 dose administered at or after "
                        "12 months occurred before 60 days after "
                        "dose 1; do not automatically classify it "
                        "as the booster."
                    ),
                )

            return _pneumococcal_result(
                assessment_date=assessment_date,
                vaccine_key="pneumococcal_20",
                decision="not_due_now",
                interpretation_pt=(
                    "Há uma D1 pré-12 meses seguida de VPC20 válida "
                    "a partir de 12 meses, com pelo menos 60 dias de "
                    "intervalo. A recuperação rotineira está completa."
                ),
                interpretation_en=(
                    "A pre-12-month dose 1 is followed by a valid "
                    "VPC20 dose at or after 12 months with at least "
                    "60 days between them. Routine catch-up is "
                    "complete."
                ),
            )

        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "As duas exposições pneumocócicas ocorreram a partir "
                "de 12 meses ou apresentam cronologia não coberta "
                "pela rotina implementada. Revisar para evitar "
                "ocultar dose excedente."
            ),
            interpretation_en=(
                "Both pneumococcal exposures occurred at or after "
                "12 months, or their chronology is outside the "
                "implemented routine patterns. Review to avoid "
                "hiding an excess dose."
            ),
        )

    # --------------------------------------------------------
    # THREE EXPOSURES
    # --------------------------------------------------------

    first = exposures[
        0
    ]

    second = exposures[
        1
    ]

    third = exposures[
        2
    ]

    first_date = first[
        "administration_date"
    ]

    second_date = second[
        "administration_date"
    ]

    third_date = third[
        "administration_date"
    ]

    if (
        first_date
        >= age_12m
        or second_date
        >= age_12m
        or third_date
        < age_12m
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "Três exposições estão documentadas, mas a cronologia "
                "não corresponde a duas doses primárias pré-12 meses "
                "seguidas de um reforço após 12 meses."
            ),
            interpretation_en=(
                "Three exposures are documented, but their chronology "
                "does not match two primary doses before 12 months "
                "followed by a booster after 12 months."
            ),
        )

    primary_interval = (
        second_date
        - first_date
    ).days

    booster_interval = (
        third_date
        - second_date
    ).days

    if (
        primary_interval
        < PNEUMOCOCCAL_PRIMARY_RECOMMENDED_INTERVAL_DAYS
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico de D1/D2 não possui intervalo rotineiro "
                "de 60 dias com justificativa histórica suficiente "
                "para validação automática."
            ),
            interpretation_en=(
                "The historical dose 1/dose 2 pair does not have the "
                "routine 60-day interval with sufficient historical "
                "justification for automatic validation."
            ),
        )

    allowed_pairs = {
        (
            "pneumococcal_20",
            "pneumococcal_10",
        ),
        (
            "pneumococcal_10",
            "pneumococcal_20",
        ),
        (
            "pneumococcal_10",
            "pneumococcal_10",
        ),
    }

    if (
        (
            first[
                "source_vaccine_key"
            ],
            second[
                "source_vaccine_key"
            ],
        )
        not in allowed_pairs
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "O par histórico D1/D2 possui sequência de produtos "
                "não suportada explicitamente pela regra."
            ),
            interpretation_en=(
                "The historical dose 1/dose 2 pair has a product "
                "sequence not explicitly supported by this rule."
            ),
        )

    if (
        third[
            "source_vaccine_key"
        ]
        != "pneumococcal_20"
        or booster_interval
        < PNEUMOCOCCAL_BOOSTER_MINIMUM_INTERVAL_DAYS
    ):
        return _pneumococcal_result(
            assessment_date=assessment_date,
            vaccine_key="pneumococcal_20",
            decision="special_pathway_review",
            interpretation_pt=(
                "A terceira exposição não pode ser validada "
                "automaticamente como reforço VPC20 após intervalo "
                "mínimo de 60 dias."
            ),
            interpretation_en=(
                "The third exposure cannot automatically be validated "
                "as a VPC20 booster after the minimum 60-day interval."
            ),
        )

    return _pneumococcal_result(
        assessment_date=assessment_date,
        vaccine_key="pneumococcal_20",
        decision="not_due_now",
        interpretation_pt=(
            "D1 e D2 pré-12 meses e um reforço VPC20 válido a partir "
            "de 12 meses estão documentados. A camada rotineira "
            "pneumocócica está completa."
        ),
        interpretation_en=(
            "Dose 1 and dose 2 before 12 months and a valid VPC20 "
            "booster at or after 12 months are documented. The "
            "routine pneumococcal layer is complete."
        ),
    )



INFLUENZA_CHILD_RULE_ID = (
    "PNI26-INFLUENZA-CHILD-ROUTINE-001"
)

INFLUENZA_CHILD_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

INFLUENZA_CHILD_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "composicao/svsa/pni/calendario-tecnico/"
    "instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026"
)

INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS = 30


def _influenza_child_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "influenza",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                INFLUENZA_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                INFLUENZA_CHILD_SOURCE_URL,

            "source_snapshot_date":
                INFLUENZA_CHILD_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _influenza_child_due_with_safety(
    *,
    assessment_date: date,
    administration_safety_screen_state: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_interval_days: int | None = None,
) -> dict[str, Any]:
    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            recommended_interval_days=(
                recommended_interval_days
            ),
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A vacina influenza está indicada pela situação "
                "vacinal atual, mas a triagem de segurança para "
                "administração ainda não foi registrada."
            ),
            interpretation_en=(
                "Influenza vaccination is indicated by the current "
                "vaccination state, but administration-safety "
                "screening has not yet been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            recommended_interval_days=(
                recommended_interval_days
            ),
            interpretation_pt=(
                "A triagem de segurança identificou uma preocupação "
                "antes da vacinação contra influenza. Revisar a "
                "conduta sem inferir automaticamente estratégia "
                "especial ou outra indicação."
            ),
            interpretation_en=(
                "Administration-safety screening identified a "
                "concern before influenza vaccination. Review the "
                "plan without automatically inferring a special "
                "strategy or another indication."
            ),
        )

    return _influenza_child_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_interval_days=(
            recommended_interval_days
        ),
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
    )


def _validate_influenza_normalized_history(
    value: Any,
) -> dict[str, Any]:
    history = _as_plain_dict(
        value
    )

    required = {
        "target_family",
        "current_cycle_key",
        "cycle_key_opaque",
        "cycle_key_parsed",
        "cycle_identity_derived_from_calendar_year",
        "geography_inferred_from_cycle_key",
        "current_cycle_history_state",
        "prior_cycle_vaccination_state",
        "current_cycle_events",
        "current_cycle_event_count",
        "routine_event_count",
        "special_event_count",
        "special_strategy_present",
        "unsupported_product_keys",
        "source_history_incomplete",
        "safe_for_routine_child_evaluation",
        "normalizer_assigns_dose_roles",
    }

    missing = sorted(
        required
        - set(
            history
        )
    )

    if missing:
        raise ValueError(
            "normalized influenza history missing fields: "
            + ", ".join(
                missing
            )
        )

    if (
        history[
            "target_family"
        ]
        != "influenza_routine_child"
    ):
        raise ValueError(
            "invalid normalized influenza target_family"
        )

    if (
        history[
            "cycle_key_opaque"
        ]
        is not True
    ):
        raise ValueError(
            "influenza cycle key must remain opaque"
        )

    if (
        history[
            "cycle_key_parsed"
        ]
        is not False
    ):
        raise ValueError(
            "influenza cycle key parsing is not allowed"
        )

    if (
        history[
            "cycle_identity_derived_from_calendar_year"
        ]
        is not False
    ):
        raise ValueError(
            "influenza cycle identity cannot be calendar-year derived"
        )

    if (
        history[
            "geography_inferred_from_cycle_key"
        ]
        is not False
    ):
        raise ValueError(
            "influenza geography cannot be inferred from cycle key"
        )

    if (
        history[
            "normalizer_assigns_dose_roles"
        ]
        is not False
    ):
        raise ValueError(
            "influenza history normalizer must not assign dose roles"
        )

    return history


def evaluate_pni_influenza_child_routine(
    *,
    assessment_date: date,
    date_of_birth: date,
    influenza_history: Any,
    administration_safety_screen_state: str = "not_screened",
) -> dict[str, Any]:
    """
    Evaluate the 2026 Brazilian routine-child INF3 rule.

    Scope:
      age >=6 months and <6 years.

    The evaluator consumes an explicit cycle-aware normalized
    influenza history. It never derives influenza-cycle identity
    from calendar year and does not consume special-strategy
    evidence or infer private INF4 equivalence.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    history = _validate_influenza_normalized_history(
        influenza_history
    )

    age_6m = _add_months_clamped(
        date_of_birth,
        6,
    )

    age_72m = _add_months_clamped(
        date_of_birth,
        72,
    )

    if (
        history[
            "source_history_incomplete"
        ]
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico de influenza necessário para definir "
                "primovacinação e situação do ciclo atual está "
                "incompleto ou desconhecido. Reconciliar o histórico "
                "antes de recomendar D1, D2 ou dose anual."
            ),
            interpretation_en=(
                "The influenza history needed to determine priming "
                "and current-cycle status is incomplete or unknown. "
                "Reconcile history before recommending dose 1, "
                "dose 2 or the annual dose."
            ),
        )

    if (
        history[
            "unsupported_product_keys"
        ]
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico contém formulação/produto de influenza "
                "fora do contrato INF3 desta regra. Não inferir "
                "equivalência com produto privado ou não suportado."
            ),
            interpretation_en=(
                "The history contains an influenza formulation or "
                "product outside this rule's INF3 contract. Do not "
                "infer equivalence with a private or unsupported "
                "product."
            ),
        )

    if (
        history[
            "special_strategy_present"
        ]
        or history[
            "special_event_count"
        ]
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há evidência de vacinação no ciclo atual registrada "
                "na camada de estratégia especial. Esta regra cobre "
                "somente a rotina infantil e não presume "
                "interoperabilidade entre as estratégias."
            ),
            interpretation_en=(
                "Current-cycle vaccination evidence is recorded in "
                "the special-strategy layer. This rule covers only "
                "the routine-child pathway and does not presume "
                "interoperability between strategies."
            ),
        )

    if not history[
        "safe_for_routine_child_evaluation"
    ]:
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico de influenza não é seguro para "
                "classificação automática na rotina infantil. "
                "Revisar cronologia, produto e evidências do ciclo."
            ),
            interpretation_en=(
                "Influenza history is not safe for automatic "
                "routine-child classification. Review chronology, "
                "product and cycle evidence."
            ),
        )

    events = sorted(
        list(
            history[
                "current_cycle_events"
            ]
        ),
        key=lambda item: item[
            "administration_date"
        ],
    )

    if (
        len(
            events
        )
        != history[
            "current_cycle_event_count"
        ]
    ):
        raise ValueError(
            "normalized influenza current-cycle event count mismatch"
        )

    if (
        len(
            events
        )
        != history[
            "routine_event_count"
        ]
    ):
        raise ValueError(
            "normalized influenza routine event count mismatch"
        )

    for event in events:
        administration_date = event[
            "administration_date"
        ]

        if not isinstance(
            administration_date,
            date,
        ):
            raise ValueError(
                "normalized influenza administration_date "
                "must be a date"
            )

        if (
            event[
                "strategy_layer"
            ]
            != "routine"
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Foi encontrado evento que não pertence à camada "
                    "de rotina infantil. Revisar a estratégia de "
                    "registro antes de interpretar a dose."
                ),
                interpretation_en=(
                    "An event outside the routine-child layer was "
                    "found. Review the registration strategy before "
                    "interpreting the dose."
                ),
            )

        if (
            event[
                "source_product_key"
            ]
            != "influenza"
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Foi encontrado produto de influenza não suportado "
                    "pelo contrato INF3 desta regra."
                ),
                interpretation_en=(
                    "An influenza product not supported by this "
                    "rule's INF3 contract was found."
                ),
            )

        if (
            administration_date
            < date_of_birth
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há vacinação contra influenza registrada antes "
                    "da data de nascimento. Revisar o registro."
                ),
                interpretation_en=(
                    "An influenza vaccination is recorded before the "
                    "date of birth. Review the record."
                ),
            )

        if (
            administration_date
            < age_6m
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há evento rotineiro de influenza registrado "
                    "antes dos 6 meses. Esta regra infantil não o "
                    "valida automaticamente."
                ),
                interpretation_en=(
                    "A routine influenza event is recorded before "
                    "6 months of age. This child rule does not "
                    "automatically validate it."
                ),
            )

        if (
            administration_date
            >= age_72m
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há evento de rotina infantil registrado no "
                    "aniversário de 6 anos ou depois. Esta regra "
                    "termina antes dessa idade."
                ),
                interpretation_en=(
                    "A routine-child event is recorded on or after "
                    "the sixth birthday. This rule ends before "
                    "that age."
                ),
            )

    prior_state = history[
        "prior_cycle_vaccination_state"
    ]

    if (
        prior_state
        not in {
            "documented_none",
            "documented_prior",
            "unknown",
        }
    ):
        raise ValueError(
            "invalid normalized influenza prior-cycle state"
        )

    if (
        prior_state
        == "unknown"
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "Não foi possível determinar se houve vacinação "
                "contra influenza em ciclo anterior. Esse dado é "
                "necessário para distinguir primovacinação de dose "
                "anual."
            ),
            interpretation_en=(
                "It is not known whether influenza vaccination "
                "occurred in a prior cycle. That information is "
                "required to distinguish primary vaccination from "
                "the annual dose."
            ),
        )

    # --------------------------------------------------------
    # NARROW AGE-OUT SOURCE HOLD
    # --------------------------------------------------------
    #
    # This check intentionally precedes the generic >=6y
    # not-applicable branch. A child may have received first-ever
    # D1 while still in scope but reach the sixth birthday before
    # the source-defined 30-day D2 threshold.
    #
    if (
        prior_state
        == "documented_none"
        and len(
            events
        )
        == 1
    ):
        first_date = events[
            0
        ][
            "administration_date"
        ]

        d2_date = (
            first_date
            + timedelta(
                days=(
                    INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
                ),
            )
        )

        if (
            d2_date
            >= age_72m
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_date=d2_date,
                recommended_interval_days=(
                    INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
                ),
                missing_context=[
                    "authoritative_age_out_completion_rule",
                ],
                interpretation_pt=(
                    "A D1 de primovacinação foi administrada antes "
                    "dos 6 anos, porém o marco de 30 dias para D2 "
                    "ocorre no aniversário de 6 anos ou depois. "
                    "A fonte de rotina revisada não explicita a "
                    "continuação após o limite etário; manter revisão "
                    "por fonte e não inferir D2."
                ),
                interpretation_en=(
                    "Primary-vaccination dose 1 was given before age "
                    "6, but the 30-day dose-2 threshold occurs on or "
                    "after the sixth birthday. The reviewed routine "
                    "source does not explicitly address completion "
                    "after the age ceiling; keep this under source "
                    "review and do not infer dose 2."
                ),
            )

    if (
        assessment_date
        < age_6m
    ):
        if events:
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Existe evento de influenza documentado antes "
                    "da idade rotineira inicial de 6 meses. Revisar "
                    "o histórico."
                ),
                interpretation_en=(
                    "An influenza event is documented before the "
                    "routine starting age of 6 months. Review the "
                    "history."
                ),
            )

        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=age_6m,
            interpretation_pt=(
                "A criança ainda não atingiu 6 meses, idade inicial "
                "da rotina infantil de influenza."
            ),
            interpretation_en=(
                "The child has not yet reached 6 months, the starting "
                "age for the routine-child influenza pathway."
            ),
        )

    if (
        assessment_date
        >= age_72m
    ):
        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A criança atingiu 6 anos e está fora da faixa desta "
                "regra rotineira infantil. Não inferir estratégia "
                "especial ou outro grupo de indicação."
            ),
            interpretation_en=(
                "The child has reached age 6 and is outside this "
                "routine-child rule. Do not infer a special strategy "
                "or another eligibility group."
            ),
        )

    # --------------------------------------------------------
    # PREVIOUSLY VACCINATED
    # --------------------------------------------------------
    if (
        prior_state
        == "documented_prior"
    ):
        if not events:
            return _influenza_child_due_with_safety(
                assessment_date=assessment_date,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                interpretation_pt=(
                    "Há vacinação contra influenza documentada em "
                    "ciclo anterior e nenhuma dose de rotina no ciclo "
                    "atual. Recomendar uma dose anual de INF3 agora."
                ),
                interpretation_en=(
                    "Influenza vaccination is documented in a prior "
                    "cycle and there is no routine dose in the current "
                    "cycle. Recommend one annual INF3 dose now."
                ),
            )

        if len(
            events
        ) == 1:
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "Há vacinação prévia contra influenza e uma dose "
                    "de rotina já está documentada no ciclo atual. "
                    "A dose anual deste ciclo está completa."
                ),
                interpretation_en=(
                    "Prior influenza vaccination is documented and "
                    "one routine dose is already recorded in the "
                    "current cycle. The annual dose for this cycle "
                    "is complete."
                ),
            )

        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há vacinação prévia contra influenza e mais de uma "
                "dose de rotina documentada no ciclo atual. A regra "
                "anual prevê uma dose; revisar o histórico."
            ),
            interpretation_en=(
                "Prior influenza vaccination is documented and more "
                "than one routine dose is recorded in the current "
                "cycle. The annual rule calls for one dose; review "
                "the history."
            ),
        )

    # --------------------------------------------------------
    # FIRST-EVER VACCINATION / DOCUMENTED NO PRIOR CYCLE
    # --------------------------------------------------------
    if not events:
        return _influenza_child_due_with_safety(
            assessment_date=assessment_date,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            interpretation_pt=(
                "Não há vacinação prévia contra influenza nem dose "
                "de rotina no ciclo atual. Esta é a primovacinação: "
                "recomendar D1 de INF3 agora."
            ),
            interpretation_en=(
                "There is no prior influenza vaccination and no "
                "routine dose in the current cycle. This is primary "
                "vaccination: recommend INF3 dose 1 now."
            ),
        )

    if len(
        events
    ) == 1:
        first_date = events[
            0
        ][
            "administration_date"
        ]

        d2_date = (
            first_date
            + timedelta(
                days=(
                    INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
                ),
            )
        )

        if (
            assessment_date
            < d2_date
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=d2_date,
                recommended_interval_days=(
                    INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "A D1 da primovacinação está documentada. "
                    "A D2 de INF3 deve ser administrada após "
                    "30 dias; esse intervalo ainda não foi completado."
                ),
                interpretation_en=(
                    "Primary-vaccination dose 1 is documented. "
                    "INF3 dose 2 is given after 30 days; that "
                    "interval has not yet elapsed."
                ),
            )

        return _influenza_child_due_with_safety(
            assessment_date=assessment_date,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            recommended_interval_days=(
                INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
            ),
            interpretation_pt=(
                "A D1 da primovacinação está documentada e já "
                "decorreram 30 dias. Recomendar D2 de INF3 agora."
            ),
            interpretation_en=(
                "Primary-vaccination dose 1 is documented and "
                "30 days have elapsed. Recommend INF3 dose 2 now."
            ),
        )

    if len(
        events
    ) == 2:
        first_date = events[
            0
        ][
            "administration_date"
        ]

        second_date = events[
            1
        ][
            "administration_date"
        ]

        interval = (
            second_date
            - first_date
        ).days

        if (
            interval
            < INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
        ):
            return _influenza_child_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                recommended_interval_days=(
                    INFLUENZA_CHILD_PRIMING_INTERVAL_DAYS
                ),
                interpretation_pt=(
                    "As duas doses da primovacinação estão "
                    "documentadas com intervalo inferior a 30 dias. "
                    "A fonte não autoriza intervalo menor; revisar "
                    "antes de considerar o ciclo completo."
                ),
                interpretation_en=(
                    "The two primary-vaccination doses are documented "
                    "less than 30 days apart. The source does not "
                    "authorize a shorter interval; review before "
                    "considering the cycle complete."
                ),
            )

        return _influenza_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "D1 e D2 da primovacinação estão documentadas com "
                "intervalo válido de pelo menos 30 dias. O ciclo "
                "atual está completo."
            ),
            interpretation_en=(
                "Primary-vaccination doses 1 and 2 are documented "
                "at least 30 days apart. The current cycle is "
                "complete."
            ),
        )

    return _influenza_child_result(
        assessment_date=assessment_date,
        decision="special_pathway_review",
        interpretation_pt=(
            "Há mais eventos de rotina no ciclo atual do que o "
            "esquema infantil implementado permite. Revisar o "
            "histórico."
        ),
        interpretation_en=(
            "There are more routine events in the current cycle "
            "than the implemented child schedule allows. Review "
            "the history."
        ),
    )

COVID_CHILD_RULE_ID = (
    "PNI26-COVID-CHILD-ROUTINE-001"
)

COVID_CHILD_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    11,
)

COVID_CHILD_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "composicao/svsa/pni/calendario-tecnico/"
    "calendario-tecnico-nacional-de-vacinacao-crianca"
)

COVID_CHILD_INTEROPERABILITY_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/estrategia-de-vacinacao-contra-a-"
    "covid-19-2024-2a-edicao"
)

COVID_RULE_PRODUCT_PFIZER = (
    "covid_pfizer_comirnaty_pediatric_under5"
)

COVID_RULE_PRODUCT_MODERNA = (
    "covid_moderna_spikevax"
)

COVID_RULE_PRODUCT_CORONAVAC = (
    "covid_coronavac_legacy"
)

COVID_CHILD_HEALTHY_CONTEXT_STATES = frozenset(
    {
        "screened_none",
        "screened_special_condition_present",
        "not_screened",
    }
)

COVID_CHILD_CURRENT_NEXT_PRODUCTS = {
    ():
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            COVID_RULE_PRODUCT_MODERNA,
            COVID_RULE_PRODUCT_PFIZER,
        ),

    (
        COVID_RULE_PRODUCT_MODERNA,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_CORONAVAC,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            COVID_RULE_PRODUCT_MODERNA,
        ),
}

COVID_CHILD_PRODUCT_PREFERENCE = {
    ():
        (
            COVID_RULE_PRODUCT_PFIZER,
            "current_2026_first_option",
            "pfizer_unavailable",
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            "homologous_priority",
            None,
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            COVID_RULE_PRODUCT_PFIZER,
            "homologous_priority",
            None,
        ),

    (
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            COVID_RULE_PRODUCT_MODERNA,
            "homologous_priority",
            None,
        ),

    (
        COVID_RULE_PRODUCT_PFIZER,
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            None,
            "mixed_history_no_new_preference_inferred",
            None,
        ),

    (
        COVID_RULE_PRODUCT_MODERNA,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            None,
            "mixed_history_no_new_preference_inferred",
            None,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
    ):
        (
            None,
            "legacy_history_complete_with_available_mrna",
            None,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_CORONAVAC,
    ):
        (
            None,
            "legacy_history_complete_with_available_mrna",
            None,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_PFIZER,
    ):
        (
            None,
            "mixed_history_no_new_preference_inferred",
            None,
        ),

    (
        COVID_RULE_PRODUCT_CORONAVAC,
        COVID_RULE_PRODUCT_MODERNA,
    ):
        (
            None,
            "mixed_history_no_new_preference_inferred",
            None,
        ),
}




def _covid_child_base_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "covid_19",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                COVID_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                COVID_CHILD_SOURCE_URL,

            "source_snapshot_date":
                COVID_CHILD_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }

def _validate_covid_child_normalized_history(
    *,
    date_of_birth,
    covid_history,
):
    if hasattr(
        covid_history,
        "model_dump",
    ):
        history = covid_history.model_dump()

    elif isinstance(
        covid_history,
        dict,
    ):
        history = dict(
            covid_history
        )

    else:
        raise ValueError(
            "covid_history must be a normalized mapping or model"
        )

    if (
        history.get(
            "target_family"
        )
        != "covid_19_healthy_child_under5_basic_series"
    ):
        raise ValueError(
            "covid_history target_family is incompatible "
            "with the healthy-child under-5 rule"
        )

    if (
        history.get(
            "registration_role_defines_clinical_ordinal"
        )
        is not False
    ):
        raise ValueError(
            "COVID registration role cannot define "
            "clinical exposure ordinal"
        )

    if (
        history.get(
            "clinical_ordinal_derived_from_chronology"
        )
        is not True
    ):
        raise ValueError(
            "COVID clinical exposure ordinal must derive "
            "from dated chronology"
        )

    if (
        history.get(
            "normalizer_assigns_due_decision"
        )
        is not False
    ):
        raise ValueError(
            "COVID history normalizer must not assign "
            "a due decision"
        )

    if (
        history.get(
            "special_condition_inferred"
        )
        is not False
    ):
        raise ValueError(
            "COVID history normalizer cannot infer "
            "special-condition eligibility"
        )

    if (
        history.get(
            "synthetic_score_applied"
        )
        is not False
    ):
        raise ValueError(
            "COVID history normalizer cannot apply "
            "a synthetic score"
        )

    if (
        history.get(
            "age_out_rule_resolved"
        )
        is not True
    ):
        raise ValueError(
            "COVID age-out rule must remain resolved"
        )

    if (
        history.get(
            "post_age5_under5_completion_allowed"
        )
        is not False
    ):
        raise ValueError(
            "COVID under-5 completion cannot continue "
            "after age 5"
        )

    expected_age_6m = _add_months_clamped(
        date_of_birth,
        6,
    )

    expected_age_5y = _add_months_clamped(
        date_of_birth,
        60,
    )

    if (
        history.get(
            "age_6m_date"
        )
        != expected_age_6m
    ):
        raise ValueError(
            "COVID normalized 6-month boundary does not "
            "match date_of_birth"
        )

    if (
        history.get(
            "age_5y_date"
        )
        != expected_age_5y
    ):
        raise ValueError(
            "COVID normalized fifth-birthday boundary does not "
            "match date_of_birth"
        )

    events = history.get(
        "events"
    )

    if not isinstance(
        events,
        list,
    ):
        raise ValueError(
            "COVID normalized events must be a list"
        )

    under5_events = [
        event
        for event in events
        if (
            isinstance(
                event,
                dict,
            )
            and event.get(
                "age_scope_at_exposure"
            )
            == "under5_series_age"
        )
    ]

    if (
        len(
            under5_events
        )
        != history.get(
            "valid_under5_exposure_count"
        )
    ):
        raise ValueError(
            "COVID normalized under-5 exposure count "
            "does not reconcile to events"
        )

    for ordinal, event in enumerate(
        under5_events,
        1,
    ):
        if (
            event.get(
                "clinical_exposure_ordinal"
            )
            != ordinal
        ):
            raise ValueError(
                "COVID normalized clinical exposure ordinals "
                "are not chronological"
            )

    sequence = history.get(
        "clinical_product_sequence"
    )

    if not isinstance(
        sequence,
        list,
    ):
        raise ValueError(
            "COVID normalized clinical_product_sequence "
            "must be a list"
        )

    if sequence != [
        event.get(
            "product_key"
        )
        for event in under5_events
    ]:
        raise ValueError(
            "COVID normalized product sequence does not "
            "reconcile to under-5 events"
        )

    return history


def _covid_child_product_output(
    sequence,
):
    from clinical_tools.pni_history import (
        COVID_CHILD_AUTHORIZED_PRODUCT_PREFIXES,
        COVID_CHILD_COMPLETE_PRODUCT_SEQUENCES,
    )

    prefix = tuple(
        sequence
    )

    allowed = (
        COVID_CHILD_CURRENT_NEXT_PRODUCTS.get(
            prefix
        )
    )

    preference = (
        COVID_CHILD_PRODUCT_PREFERENCE.get(
            prefix
        )
    )

    if (
        allowed is None
        or preference is None
    ):
        raise ValueError(
            "COVID current continuation table has no "
            "entry for this incomplete prefix"
        )

    preferred, basis, choice_condition = (
        preference
    )

    options = []

    for product in allowed:
        resulting = (
            prefix
            + (
                product,
            )
        )

        if (
            resulting
            in COVID_CHILD_COMPLETE_PRODUCT_SEQUENCES
        ):
            resulting_state = (
                "source_authorized_complete"
            )

            next_interval = None

        elif (
            resulting
            in COVID_CHILD_AUTHORIZED_PRODUCT_PREFIXES
        ):
            resulting_state = (
                "source_authorized_incomplete_prefix"
            )

            if len(
                resulting
            ) == 1:
                next_interval = 28

            elif len(
                resulting
            ) == 2:
                next_interval = 56

            else:
                raise ValueError(
                    "COVID incomplete resulting sequence has "
                    "unsupported clinical exposure count"
                )

        else:
            raise ValueError(
                "COVID current continuation table diverges "
                "from the locked historical sequence table"
            )

        if preferred is None:
            option_role = (
                "source_allowed_no_preference"
            )

        elif product == preferred:
            option_role = "preferred"

        else:
            option_role = (
                "allowed_alternative"
            )

        condition = None

        if (
            prefix == ()
            and product
            == COVID_RULE_PRODUCT_MODERNA
        ):
            condition = (
                "pfizer_unavailable"
            )

        options.append(
            {
                "product_key":
                    product,

                "option_role":
                    option_role,

                "condition":
                    condition,

                "resulting_product_sequence":
                    list(
                        resulting
                    ),

                "resulting_sequence_state":
                    resulting_state,

                "next_minimum_interval_days":
                    next_interval,
            }
        )

    return {
        "allowed_next_product_keys":
            list(
                allowed
            ),

        "preferred_next_product_key":
            preferred,

        "preferred_product_basis":
            basis,

        "product_choice_condition":
            choice_condition,

        "next_product_options":
            options,
    }


def _covid_child_empty_product_output():
    return {
        "allowed_next_product_keys":
            [],

        "preferred_next_product_key":
            None,

        "preferred_product_basis":
            None,

        "product_choice_condition":
            None,

        "next_product_options":
            [],
    }


def _covid_child_result(
    *,
    decision,
    assessment_date,
    recommended_date=None,
    recommended_interval_days=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
    history_required=False,
    missing_context=None,
    interpretation_pt,
    interpretation_en,
    product_output=None,
    age_out_closure_applied=False,
):
    from schemas import (
        PniCovidChildRuleResult,
    )

    if missing_context is None:
        missing_context = []

    if product_output is None:
        product_output = (
            _covid_child_empty_product_output()
        )

    base_result = _covid_child_base_result(
        assessment_date=assessment_date,
        decision=decision,
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
        recommended_date=recommended_date,
        recommended_interval_days=recommended_interval_days,
        history_required=history_required,
        missing_context=missing_context,
    )

    if hasattr(
        base_result,
        "model_dump",
    ):
        payload = base_result.model_dump()

    else:
        payload = dict(
            base_result
        )

    payload.update(
        product_output
    )

    payload[
        "age_out_closure_applied"
    ] = age_out_closure_applied

    return (
        PniCovidChildRuleResult
        .model_validate(
            payload
        )
        .model_dump()
    )


def _covid_child_due_with_safety(
    *,
    assessment_date,
    administration_safety_screen_state,
    recommended_interval_days,
    minimum_interval_days,
    product_output,
    interpretation_pt,
    interpretation_en,
):
    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _covid_child_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A próxima dose do esquema básico está "
                "temporalmente indicada, mas a avaliação de "
                "segurança para administração ainda não foi "
                "documentada."
            ),
            interpretation_en=(
                "The next basic-series dose is temporally due, "
                "but administration safety screening has not "
                "yet been documented."
            ),
            product_output=(
                _covid_child_empty_product_output()
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Há preocupação documentada na avaliação de "
                "segurança para administração. O caso deve ser "
                "revisto antes de aplicar a próxima dose."
            ),
            interpretation_en=(
                "A concern was documented during administration "
                "safety screening. Review is required before "
                "giving the next dose."
            ),
            product_output=(
                _covid_child_empty_product_output()
            ),
        )

    if (
        administration_safety_screen_state
        != "screened_no_concern"
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    return _covid_child_result(
        decision="recommend_now",
        assessment_date=assessment_date,
        recommended_date=assessment_date,
        recommended_interval_days=(
            recommended_interval_days
        ),
        minimum_interval_days=(
            minimum_interval_days
        ),
        minimum_interval_applied=False,
        history_required=False,
        missing_context=[],
        interpretation_pt=(
            interpretation_pt
        ),
        interpretation_en=(
            interpretation_en
        ),
        product_output=(
            product_output
        ),
    )


def evaluate_pni_covid_child_routine(
    *,
    assessment_date,
    date_of_birth,
    covid_history,
    healthy_child_context_state="not_screened",
    administration_safety_screen_state="not_screened",
):
    """
    Evaluate the healthy routine-child COVID-19 basic-series
    pathway from the exact 6-month birthday until age 5.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        healthy_child_context_state
        not in COVID_CHILD_HEALTHY_CONTEXT_STATES
    ):
        raise ValueError(
            "invalid healthy_child_context_state"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    history = (
        _validate_covid_child_normalized_history(
            date_of_birth=date_of_birth,
            covid_history=covid_history,
        )
    )

    age_6m = history[
        "age_6m_date"
    ]

    age_5y = history[
        "age_5y_date"
    ]

    events = history[
        "events"
    ]

    under5_events = [
        event
        for event in events
        if (
            event.get(
                "age_scope_at_exposure"
            )
            == "under5_series_age"
        )
    ]

    supported_products = {
        COVID_RULE_PRODUCT_PFIZER,
        COVID_RULE_PRODUCT_MODERNA,
        COVID_RULE_PRODUCT_CORONAVAC,
    }

    supported_under5_exposure_count = sum(
        1
        for event in under5_events
        if (
            event.get(
                "product_key"
            )
            in supported_products
        )
    )

    if (
        assessment_date
        < age_6m
    ):
        return _covid_child_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=age_6m,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A rotina infantil de covid-19 deste núcleo "
                "começa no aniversário exato de 6 meses."
            ),
            interpretation_en=(
                "This COVID-19 child-routine core begins on "
                "the exact 6-month birthday."
            ),
        )

    if (
        assessment_date
        >= age_5y
    ):
        if (
            supported_under5_exposure_count
            >= 1
        ):
            return _covid_child_result(
                decision="not_applicable",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "A pessoa já atingiu 5 anos e possui pelo "
                    "menos uma exposição documentada e reconhecida "
                    "à vacina contra covid-19 antes dessa idade. "
                    "Pela regra federal de transição etária, o "
                    "esquema infantil abaixo de 5 anos é encerrado "
                    "e não se recomenda continuar D2/D3 por este "
                    "núcleo."
                ),
                interpretation_en=(
                    "The person has reached age 5 and has at least "
                    "one documented, recognized COVID-19 vaccine "
                    "exposure before that age. Under the federal "
                    "age-out rule, the under-5 series is closed and "
                    "this core does not continue a pending D2/D3."
                ),
                age_out_closure_applied=True,
            )

        if under5_events:
            return _covid_child_result(
                decision="special_pathway_review",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "Há exposição infantil registrada antes dos "
                    "5 anos, mas a evidência de produto não pode "
                    "ser usada automaticamente para aplicar a "
                    "regra de encerramento. É necessária revisão."
                ),
                interpretation_en=(
                    "An under-5 COVID-19 exposure is recorded, "
                    "but its product evidence cannot be used "
                    "automatically for age-out closure. Review "
                    "is required."
                ),
            )

        if history[
            "source_history_incomplete"
        ]:
            return _covid_child_result(
                decision="history_required",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=True,
                missing_context=[
                    "complete_product_sensitive_covid_history",
                ],
                interpretation_pt=(
                    "O histórico de vacinação contra covid-19 "
                    "está incompleto; não é possível confirmar "
                    "se a regra de encerramento aos 5 anos se "
                    "aplica."
                ),
                interpretation_en=(
                    "The COVID-19 vaccination history is "
                    "incomplete; it is not possible to confirm "
                    "whether the age-5 closure rule applies."
                ),
            )

        return _covid_child_result(
            decision="not_applicable",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A pessoa já atingiu 5 anos e não há exposição "
                "infantil documentada no histórico completo. "
                "Este núcleo específico para menores de 5 anos "
                "não se aplica."
            ),
            interpretation_en=(
                "The person has reached age 5 and the complete "
                "history contains no documented under-5 exposure. "
                "This under-5-specific core no longer applies."
            ),
            age_out_closure_applied=False,
        )

    if (
        healthy_child_context_state
        == "not_screened"
    ):
        return _covid_child_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[
                "healthy_child_context_state",
            ],
            interpretation_pt=(
                "É necessário confirmar explicitamente se a "
                "criança pertence ao caminho de rotina sem "
                "condição especial antes de aplicar esta regra."
            ),
            interpretation_en=(
                "Explicit confirmation that the child belongs "
                "to the routine pathway without a qualifying "
                "special condition is required before applying "
                "this rule."
            ),
        )

    if (
        healthy_child_context_state
        == "screened_special_condition_present"
    ):
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Foi identificada condição especial. Este núcleo "
                "cobre apenas a rotina da criança sem condição "
                "especial; o esquema específico deve ser avaliado "
                "separadamente."
            ),
            interpretation_en=(
                "A qualifying special condition is present. "
                "This core covers only the routine child pathway; "
                "the special schedule must be evaluated separately."
            ),
        )

    if history[
        "source_history_incomplete"
    ]:
        return _covid_child_result(
            decision="history_required",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=True,
            missing_context=[
                "complete_product_sensitive_covid_history",
            ],
            interpretation_pt=(
                "É necessário histórico completo e datado, com "
                "identificação de produto, para definir de forma "
                "segura o próximo passo do esquema infantil."
            ),
            interpretation_en=(
                "A complete dated history with product identity "
                "is required to determine the next child-series "
                "step safely."
            ),
        )

    if not history[
        "safe_for_under5_series_evaluation"
    ]:
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O histórico normalizado contém evidência que "
                "impede avaliação automática do esquema infantil "
                "de covid-19 e requer revisão."
            ),
            interpretation_en=(
                "The normalized history contains evidence that "
                "prevents automatic evaluation of the COVID-19 "
                "child series and requires review."
            ),
        )

    sequence = tuple(
        history[
            "clinical_product_sequence"
        ]
    )

    sequence_state = history[
        "product_sequence_state"
    ]

    if (
        sequence_state
        == "source_authorized_complete"
    ):
        return _covid_child_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O esquema básico infantil documentado está "
                "completo. Para criança sem condição especial, "
                "este núcleo não indica dose periódica de rotina."
            ),
            interpretation_en=(
                "The documented child basic series is complete. "
                "For a child without a qualifying special "
                "condition, this core does not recommend a "
                "routine periodic dose."
            ),
        )

    if (
        sequence_state
        not in {
            "documented_zero_exposure",
            "source_authorized_incomplete_prefix",
        }
    ):
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A sequência de produtos não corresponde a um "
                "prefixo federal autorizado para avaliação "
                "automática."
            ),
            interpretation_en=(
                "The product sequence does not correspond to a "
                "federally authorized prefix for automatic "
                "evaluation."
            ),
        )

    try:
        product_output = (
            _covid_child_product_output(
                sequence
            )
        )

    except ValueError:
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O prefixo histórico é reconhecido, mas não há "
                "transição atual explicitamente autorizada neste "
                "núcleo."
            ),
            interpretation_en=(
                "The historical prefix is recognized, but this "
                "core has no explicitly authorized current "
                "transition for it."
            ),
        )

    if len(
        sequence
    ) == 0:
        recommended_interval_days = None
        minimum_interval_days = None
        due_date = assessment_date

    elif len(
        sequence
    ) == 1:
        recommended_interval_days = 28
        minimum_interval_days = 28

        due_date = (
            under5_events[
                -1
            ][
                "administration_date"
            ]
            + timedelta(
                days=28,
            )
        )

    elif len(
        sequence
    ) == 2:
        recommended_interval_days = 56
        minimum_interval_days = 56

        due_date = (
            under5_events[
                -1
            ][
                "administration_date"
            ]
            + timedelta(
                days=56,
            )
        )

    else:
        return _covid_child_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A sequência incompleta possui número de "
                "exposições incompatível com a tabela federal "
                "implementada."
            ),
            interpretation_en=(
                "The incomplete sequence has an exposure count "
                "that is incompatible with the implemented "
                "federal table."
            ),
        )

    if (
        due_date
        >= age_5y
        and assessment_date
        < due_date
    ):
        return _covid_child_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=age_5y,
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O intervalo necessário para a próxima exposição "
                "só seria atingido no aniversário de 5 anos ou "
                "depois. A rotina abaixo de 5 anos encerra nessa "
                "data; nenhuma continuação D2/D3 após o limite "
                "etário é inferida."
            ),
            interpretation_en=(
                "The required interval for the next exposure "
                "would mature on or after the fifth birthday. "
                "The under-5 routine closes at that boundary; "
                "no post-age-5 D2/D3 continuation is inferred."
            ),
            product_output=(
                _covid_child_empty_product_output()
            ),
        )

    if (
        assessment_date
        < due_date
    ):
        return _covid_child_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=due_date,
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A próxima exposição do esquema básico ainda "
                "não atingiu o intervalo mínimo aplicável. "
                "As opções estruturadas de produto correspondem "
                "ao próximo passo quando a data indicada for "
                "alcançada."
            ),
            interpretation_en=(
                "The next basic-series exposure has not yet "
                "reached the applicable minimum interval. "
                "The structured product options describe the "
                "next step once the indicated date is reached."
            ),
            product_output=(
                product_output
            ),
        )

    if len(
        sequence
    ) == 0:
        interpretation_pt = (
            "A criança está na faixa etária da rotina e não há "
            "doses documentadas. A vacinação pode ser iniciada "
            "agora. Pfizer/Comirnaty é a primeira opção atual; "
            "Moderna/Spikevax é alternativa quando Pfizer não "
            "estiver disponível."
        )

        interpretation_en = (
            "The child is within the routine age range and has "
            "no documented doses. Vaccination may start now. "
            "Pfizer/Comirnaty is the current first option; "
            "Moderna/Spikevax is an alternative when Pfizer is "
            "unavailable."
        )

    elif sequence == (
        COVID_RULE_PRODUCT_MODERNA,
    ):
        interpretation_pt = (
            "A próxima exposição está indicada agora. A opção "
            "homóloga Moderna completa o esquema M-M; a opção "
            "Pfizer produz o prefixo misto M-P e mantém a "
            "necessidade de uma terceira exposição após pelo "
            "menos 56 dias."
        )

        interpretation_en = (
            "The next exposure is due now. Homologous Moderna "
            "completes the M-M series; choosing Pfizer produces "
            "the mixed M-P prefix and leaves a third exposure "
            "required after at least 56 days."
        )

    else:
        interpretation_pt = (
            "A próxima exposição do esquema básico está indicada "
            "agora. As opções de produto e suas consequências "
            "de sequência estão registradas de forma estruturada "
            "no resultado."
        )

        interpretation_en = (
            "The next basic-series exposure is due now. "
            "The allowed products and their resulting sequence "
            "consequences are recorded structurally in the result."
        )

    return _covid_child_due_with_safety(
        assessment_date=assessment_date,
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
        recommended_interval_days=(
            recommended_interval_days
        ),
        minimum_interval_days=(
            minimum_interval_days
        ),
        product_output=(
            product_output
        ),
        interpretation_pt=(
            interpretation_pt
        ),
        interpretation_en=(
            interpretation_en
        ),
    )

YELLOW_FEVER_RULE_ID = (
    "PNI26-YELLOW-FEVER-ROUTINE-001"
)

YELLOW_FEVER_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

YELLOW_FEVER_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "composicao/svsa/pni/calendario-tecnico/"
    "instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026"
)

YELLOW_FEVER_ROUTINE_CONTEXT_STATES = frozenset(
    {
        "not_screened",
        "screened_routine_no_special_condition",
        "screened_special_condition_present",
    }
)

YELLOW_FEVER_LIVE_GROUPS = frozenset(
    {
        "mmr",
        "mmrv",
        "varicella",
        "dengue",
    }
)

YELLOW_FEVER_EXCEPTIONAL_15_DAY_GROUPS = frozenset(
    {
        "mmr",
        "mmrv",
        "varicella",
    }
)


def _yellow_fever_result(
    *,
    decision,
    assessment_date,
    recommended_date=None,
    recommended_interval_days=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
    history_required=False,
    missing_context=None,
    interpretation_pt,
    interpretation_en,
):
    if missing_context is None:
        missing_context = []

    return _yellow_fever_base_result(
        assessment_date=assessment_date,
        decision=decision,
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
        recommended_date=recommended_date,
        recommended_interval_days=recommended_interval_days,
        history_required=history_required,
        missing_context=missing_context,
    )




def _yellow_fever_base_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "yellow_fever",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                YELLOW_FEVER_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                YELLOW_FEVER_SOURCE_URL,

            "source_snapshot_date":
                YELLOW_FEVER_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }

def _validate_yellow_fever_normalized_history(
    *,
    date_of_birth,
    yellow_fever_history,
):
    if hasattr(
        yellow_fever_history,
        "model_dump",
    ):
        history = (
            yellow_fever_history
            .model_dump()
        )

    elif isinstance(
        yellow_fever_history,
        dict,
    ):
        history = dict(
            yellow_fever_history
        )

    else:
        raise ValueError(
            "yellow_fever_history must be a normalized mapping or model"
        )

    if (
        history.get(
            "target_family"
        )
        != "yellow_fever_routine_history"
    ):
        raise ValueError(
            "yellow_fever_history target_family is incompatible"
        )

    if (
        history.get(
            "registration_role_defines_clinical_role"
        )
        is not False
    ):
        raise ValueError(
            "yellow-fever registration role cannot define clinical role"
        )

    if (
        history.get(
            "clinical_role_derived_from_product_age_chronology"
        )
        is not True
    ):
        raise ValueError(
            "yellow-fever clinical role must derive from "
            "product, age and chronology"
        )

    if (
        history.get(
            "normalizer_assigns_due_decision"
        )
        is not False
    ):
        raise ValueError(
            "yellow-fever history normalizer must not assign due state"
        )

    if (
        history.get(
            "epidemiologic_context_inferred"
        )
        is not False
    ):
        raise ValueError(
            "yellow-fever history normalizer cannot infer "
            "epidemiologic context"
        )

    if (
        history.get(
            "special_condition_inferred"
        )
        is not False
    ):
        raise ValueError(
            "yellow-fever history normalizer cannot infer "
            "special conditions"
        )

    if (
        history.get(
            "synthetic_score_applied"
        )
        is not False
    ):
        raise ValueError(
            "yellow-fever history normalizer cannot apply "
            "a synthetic score"
        )

    expected = {
        "age_6m_date":
            _add_months_clamped(
                date_of_birth,
                6,
            ),

        "age_9m_date":
            _add_months_clamped(
                date_of_birth,
                9,
            ),

        "age_4y_date":
            _add_months_clamped(
                date_of_birth,
                48,
            ),

        "age_5y_date":
            _add_months_clamped(
                date_of_birth,
                60,
            ),

        "age_60y_date":
            _add_months_clamped(
                date_of_birth,
                720,
            ),
    }

    for field, value in expected.items():
        if history.get(
            field
        ) != value:
            raise ValueError(
                f"yellow-fever normalized {field} does not "
                "match date_of_birth"
            )

    if not isinstance(
        history.get(
            "events"
        ),
        list,
    ):
        raise ValueError(
            "yellow-fever normalized events must be a list"
        )

    return history


def _yellow_fever_validate_interaction_context(
    *,
    assessment_date,
    interaction_context,
):
    from schemas import (
        PniYellowFeverInteractionContext,
    )

    if interaction_context is None:
        return None

    context = (
        PniYellowFeverInteractionContext
        .model_validate(
            interaction_context
        )
    )

    for event in context.recent_live_vaccine_events:
        if (
            event.administration_date
            > assessment_date
        ):
            raise ValueError(
                "recent live-vaccine event cannot follow assessment_date"
            )

    return context


def _yellow_fever_interaction_gate(
    *,
    assessment_date,
    date_of_birth,
    interaction_context,
):
    age_2y = _add_months_clamped(
        date_of_birth,
        24,
    )

    under2 = (
        assessment_date
        < age_2y
    )

    context = (
        _yellow_fever_validate_interaction_context(
            assessment_date=assessment_date,
            interaction_context=interaction_context,
        )
    )

    if (
        context is None
        or context.history_screen_state
        == "not_screened"
    ):
        return {
            "state":
                "context_required",

            "missing_context":
                [
                    "yellow_fever_live_vaccine_interaction_context",
                ],

            "recommended_date":
                None,

            "recommended_interval_days":
                None,

            "minimum_interval_days":
                None,

            "minimum_interval_applied":
                False,
        }

    emergency_state = (
        context
        .epidemiologic_emergency_concomitant_circulation_state
    )

    same_day_groups = set(
        context.planned_same_day_vaccine_groups
    )

    same_day_groups.update(
        event.vaccine_group
        for event
        in context.recent_live_vaccine_events
        if (
            event.administration_date
            == assessment_date
        )
    )

    if (
        under2
        and "dengue"
        in same_day_groups
    ):
        return {
            "state":
                "special_pathway_review",

            "missing_context":
                [],

            "recommended_date":
                None,

            "recommended_interval_days":
                None,

            "minimum_interval_days":
                None,

            "minimum_interval_applied":
                False,
        }

    under2_mmr_same_day = bool(
        same_day_groups
        & {
            "mmr",
            "mmrv",
        }
    )

    if (
        under2
        and under2_mmr_same_day
    ):
        if (
            emergency_state
            == "not_assessed"
        ):
            return {
                "state":
                    "context_required",

                "missing_context":
                    [
                        "epidemiologic_emergency_"
                        "concomitant_circulation_state",
                    ],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    None,

                "minimum_interval_days":
                    None,

                "minimum_interval_applied":
                    False,
            }

        if (
            emergency_state
            != "present"
        ):
            return {
                "state":
                    "special_pathway_review",

                "missing_context":
                    [],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    30,

                "minimum_interval_days":
                    15,

                "minimum_interval_applied":
                    False,
            }

    blocking_dates = []
    used_exceptional_15 = False

    for event in (
        context.recent_live_vaccine_events
    ):
        if (
            event.administration_date
            == assessment_date
        ):
            continue

        group = event.vaccine_group

        if (
            under2
            and group
            == "dengue"
        ):
            return {
                "state":
                    "special_pathway_review",

                "missing_context":
                    [],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    None,

                "minimum_interval_days":
                    None,

                "minimum_interval_applied":
                    False,
            }

        interval_days = 30

        if (
            group
            in YELLOW_FEVER_EXCEPTIONAL_15_DAY_GROUPS
            and context
            .exceptional_15_day_interval_authorized
        ):
            interval_days = 15
            used_exceptional_15 = True

        threshold = (
            event.administration_date
            + timedelta(
                days=interval_days,
            )
        )

        if (
            assessment_date
            < threshold
        ):
            blocking_dates.append(
                (
                    threshold,
                    group,
                    interval_days,
                )
            )

    if blocking_dates:
        recommended_date = max(
            item[
                0
            ]
            for item
            in blocking_dates
        )

        if any(
            item[
                2
            ]
            == 30
            for item
            in blocking_dates
        ):
            applied_interval = 30
            exceptional_applied = False

        else:
            applied_interval = 15
            exceptional_applied = True

        return {
            "state":
                "not_due_now",

            "missing_context":
                [],

            "recommended_date":
                recommended_date,

            "recommended_interval_days":
                30,

            "minimum_interval_days":
                (
                    15
                    if all(
                        item[
                            1
                        ]
                        in YELLOW_FEVER_EXCEPTIONAL_15_DAY_GROUPS
                        for item
                        in blocking_dates
                    )
                    else 30
                ),

            "minimum_interval_applied":
                exceptional_applied,

            "applied_interval_days":
                applied_interval,
        }

    return {
        "state":
            "clear",

        "missing_context":
            [],

        "recommended_date":
            None,

        "recommended_interval_days":
            30,

        "minimum_interval_days":
            (
                15
                if used_exceptional_15
                else 30
            ),

        "minimum_interval_applied":
            used_exceptional_15,
    }


def _yellow_fever_due_with_context_and_safety(
    *,
    assessment_date,
    date_of_birth,
    routine_context_state,
    interaction_context,
    administration_safety_screen_state,
    indication_pt,
    indication_en,
):
    if (
        routine_context_state
        == "not_screened"
    ):
        return _yellow_fever_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[
                "yellow_fever_routine_context_state",
            ],
            interpretation_pt=(
                "A vacina contra febre amarela está indicada "
                "pela idade e pelo histórico, mas é necessário "
                "confirmar explicitamente a ausência de condição "
                "especial antes da recomendação de rotina."
            ),
            interpretation_en=(
                "Yellow-fever vaccination is indicated by age "
                "and history, but absence of a qualifying special "
                "condition must be explicitly confirmed before a "
                "routine recommendation is made."
            ),
        )

    if (
        routine_context_state
        == "screened_special_condition_present"
    ):
        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Foi identificada condição especial. Este núcleo "
                "implementa apenas a rotina não excepcional da "
                "vacina febre amarela; a elegibilidade deve ser "
                "avaliada pela via específica."
            ),
            interpretation_en=(
                "A qualifying special condition is present. "
                "This core implements only the nonexceptional "
                "yellow-fever routine; eligibility must be "
                "reviewed through the appropriate special pathway."
            ),
        )

    interaction = _yellow_fever_interaction_gate(
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
        interaction_context=interaction_context,
    )

    if (
        interaction[
            "state"
        ]
        == "context_required"
    ):
        return _yellow_fever_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                interaction[
                    "recommended_interval_days"
                ]
            ),
            minimum_interval_days=(
                interaction[
                    "minimum_interval_days"
                ]
            ),
            minimum_interval_applied=(
                interaction[
                    "minimum_interval_applied"
                ]
            ),
            history_required=False,
            missing_context=(
                interaction[
                    "missing_context"
                ]
            ),
            interpretation_pt=(
                "A vacina febre amarela está indicada pelo "
                "histórico, mas falta contexto explícito sobre "
                "vacinas vivas recentes ou planejadas para "
                "confirmar a administração segura neste momento."
            ),
            interpretation_en=(
                "Yellow-fever vaccination is indicated by "
                "history, but explicit context about recent or "
                "planned live vaccines is missing, so current "
                "administration cannot yet be confirmed."
            ),
        )

    if (
        interaction[
            "state"
        ]
        == "special_pathway_review"
    ):
        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                interaction[
                    "recommended_interval_days"
                ]
            ),
            minimum_interval_days=(
                interaction[
                    "minimum_interval_days"
                ]
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A programação informada de vacina viva não "
                "pode ser resolvida automaticamente pela regra "
                "de rotina da febre amarela. É necessária revisão "
                "da coadministração ou do intervalo."
            ),
            interpretation_en=(
                "The reported live-vaccine plan cannot be "
                "resolved automatically by the routine "
                "yellow-fever rule. Coadministration or spacing "
                "requires review."
            ),
        )

    if (
        interaction[
            "state"
        ]
        == "not_due_now"
    ):
        return _yellow_fever_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=(
                interaction[
                    "recommended_date"
                ]
            ),
            recommended_interval_days=(
                interaction[
                    "recommended_interval_days"
                ]
            ),
            minimum_interval_days=(
                interaction[
                    "minimum_interval_days"
                ]
            ),
            minimum_interval_applied=(
                interaction[
                    "minimum_interval_applied"
                ]
            ),
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A febre amarela está indicada pelo histórico, "
                "mas o intervalo exigido após outra vacina viva "
                "ainda não foi atingido."
            ),
            interpretation_en=(
                "Yellow-fever vaccination is indicated by "
                "history, but the required interval after another "
                "live vaccine has not yet elapsed."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _yellow_fever_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A vacina está indicada e o contexto de vacinas "
                "vivas não impede a administração, mas a avaliação "
                "de segurança ainda não foi documentada."
            ),
            interpretation_en=(
                "Vaccination is indicated and live-vaccine "
                "spacing does not prevent administration, but "
                "administration safety screening has not yet "
                "been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Há preocupação documentada na avaliação de "
                "segurança para administração da vacina febre "
                "amarela. O caso requer revisão."
            ),
            interpretation_en=(
                "A concern was documented during yellow-fever "
                "administration safety screening. Review is required."
            ),
        )

    return _yellow_fever_result(
        decision="recommend_now",
        assessment_date=assessment_date,
        recommended_date=assessment_date,
        recommended_interval_days=None,
        minimum_interval_days=None,
        minimum_interval_applied=False,
        history_required=False,
        missing_context=[],
        interpretation_pt=indication_pt,
        interpretation_en=indication_en,
    )


def evaluate_pni_yellow_fever_routine(
    *,
    assessment_date,
    date_of_birth,
    yellow_fever_history,
    routine_context_state="not_screened",
    interaction_context=None,
    administration_safety_screen_state="not_screened",
):
    """
    Evaluate the nonexceptional routine VFA pathway from
    exact age 9 months through 59y11m29d.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        routine_context_state
        not in YELLOW_FEVER_ROUTINE_CONTEXT_STATES
    ):
        raise ValueError(
            "invalid yellow-fever routine_context_state"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    history = (
        _validate_yellow_fever_normalized_history(
            date_of_birth=date_of_birth,
            yellow_fever_history=yellow_fever_history,
        )
    )

    age_9m = history[
        "age_9m_date"
    ]

    age_4y = history[
        "age_4y_date"
    ]

    age_5y = history[
        "age_5y_date"
    ]

    age_60y = history[
        "age_60y_date"
    ]

    if (
        assessment_date
        >= age_60y
    ):
        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A pessoa atingiu 60 anos. A vacinação contra "
                "febre amarela nessa faixa depende de avaliação "
                "individual de risco-benefício e está fora deste "
                "núcleo de rotina."
            ),
            interpretation_en=(
                "The person has reached age 60. Yellow-fever "
                "vaccination at this age requires individual "
                "risk-benefit assessment and is outside this "
                "routine core."
            ),
        )

    if history[
        "source_history_incomplete"
    ]:
        return _yellow_fever_result(
            decision="history_required",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=True,
            missing_context=[
                "complete_product_sensitive_yellow_fever_history",
            ],
            interpretation_pt=(
                "É necessário histórico completo, datado e com "
                "tipo de dose identificado para interpretar com "
                "segurança o esquema de febre amarela."
            ),
            interpretation_en=(
                "A complete dated history with dose type "
                "identified is required to interpret the "
                "yellow-fever schedule safely."
            ),
        )

    if not history[
        "safe_for_routine_evaluation"
    ]:
        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O histórico normalizado contém evidência que "
                "impede interpretação automática segura da "
                "rotina de febre amarela e requer revisão."
            ),
            interpretation_en=(
                "The normalized history contains evidence that "
                "prevents safe automatic interpretation of the "
                "yellow-fever routine and requires review."
            ),
        )

    events = history[
        "events"
    ]

    dose_zero_events = [
        event
        for event in events
        if (
            event[
                "clinical_role"
            ]
            == "exceptional_dose_zero"
        )
    ]

    standard_events = [
        event
        for event in events
        if (
            event[
                "standard_series_ordinal"
            ]
            is not None
        )
    ]

    pre5_standard_events = [
        event
        for event in standard_events
        if (
            event[
                "clinical_role"
            ]
            == "standard_series_dose_before5"
        )
    ]

    age5plus_standard_events = [
        event
        for event in standard_events
        if (
            event[
                "clinical_role"
            ]
            == "standard_series_dose_age5_to59"
        )
    ]

    if (
        assessment_date
        < age_9m
    ):
        due_date = age_9m

        if dose_zero_events:
            due_date = max(
                due_date,
                dose_zero_events[
                    -1
                ][
                    "administration_date"
                ]
                + timedelta(
                    days=30,
                ),
            )

        return _yellow_fever_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=due_date,
            recommended_interval_days=None,
            minimum_interval_days=(
                30
                if dose_zero_events
                else None
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A rotina de febre amarela ainda não iniciou. "
                "A primeira dose padrão é programada a partir "
                "dos 9 meses, respeitando 30 dias após eventual "
                "dose zero."
            ),
            interpretation_en=(
                "The routine yellow-fever schedule has not yet "
                "started. The first standard dose begins at "
                "9 months, with a 30-day interval after any "
                "documented dose zero."
            ),
        )

    if history[
        "fractional_regularization_required"
    ]:
        return _yellow_fever_due_with_context_and_safety(
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
            routine_context_state=routine_context_state,
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            indication_pt=(
                "Há histórico de dose fracionada de 2018 ainda "
                "sem dose padrão posterior para regularização. "
                "Está indicada uma dose padrão de febre amarela "
                "agora, se não houver impedimento pelos demais "
                "contextos avaliados."
            ),
            indication_en=(
                "A 2018 fractional-dose history remains without "
                "a later standard dose for regularization. "
                "One standard yellow-fever dose is indicated now "
                "if the other evaluated contexts do not prevent "
                "administration."
            ),
        )

    if (
        assessment_date
        < age_5y
    ):
        standard_count = len(
            pre5_standard_events
        )

        if standard_count == 0:
            due_date = age_9m

            if dose_zero_events:
                due_date = max(
                    due_date,
                    dose_zero_events[
                        -1
                    ][
                        "administration_date"
                    ]
                    + timedelta(
                        days=30,
                    ),
                )

            if (
                assessment_date
                < due_date
            ):
                return _yellow_fever_result(
                    decision="not_due_now",
                    assessment_date=assessment_date,
                    recommended_date=due_date,
                    recommended_interval_days=None,
                    minimum_interval_days=(
                        30
                        if dose_zero_events
                        else None
                    ),
                    minimum_interval_applied=False,
                    history_required=False,
                    missing_context=[],
                    interpretation_pt=(
                        "A primeira dose padrão ainda não atingiu "
                        "a data aplicável da rotina."
                    ),
                    interpretation_en=(
                        "The first standard dose has not yet "
                        "reached its applicable routine date."
                    ),
                )

            return _yellow_fever_due_with_context_and_safety(
                assessment_date=assessment_date,
                date_of_birth=date_of_birth,
                routine_context_state=routine_context_state,
                interaction_context=interaction_context,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                indication_pt=(
                    "A criança está na faixa etária da rotina "
                    "e não possui dose padrão válida. A primeira "
                    "dose padrão de febre amarela está indicada agora."
                ),
                indication_en=(
                    "The child is within the routine age range "
                    "and has no valid standard dose. The first "
                    "standard yellow-fever dose is indicated now."
                ),
            )

        if standard_count == 1:
            first_standard = (
                pre5_standard_events[
                    0
                ][
                    "administration_date"
                ]
            )

            due_date = max(
                age_4y,
                first_standard
                + timedelta(
                    days=30,
                ),
            )

            if (
                assessment_date
                < due_date
            ):
                return _yellow_fever_result(
                    decision="not_due_now",
                    assessment_date=assessment_date,
                    recommended_date=due_date,
                    recommended_interval_days=None,
                    minimum_interval_days=30,
                    minimum_interval_applied=False,
                    history_required=False,
                    missing_context=[],
                    interpretation_pt=(
                        "Há uma dose padrão válida antes dos "
                        "5 anos, mas o reforço infantil ainda "
                        "não atingiu a data aplicável."
                    ),
                    interpretation_en=(
                        "One valid standard dose was given before "
                        "age 5, but the child booster has not yet "
                        "reached its applicable date."
                    ),
                )

            return _yellow_fever_due_with_context_and_safety(
                assessment_date=assessment_date,
                date_of_birth=date_of_birth,
                routine_context_state=routine_context_state,
                interaction_context=interaction_context,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                indication_pt=(
                    "Há uma dose padrão válida antes dos 5 anos "
                    "e o reforço infantil está indicado agora."
                ),
                indication_en=(
                    "One valid standard dose was given before "
                    "age 5 and the child booster is indicated now."
                ),
            )

        if standard_count == 2:
            return _yellow_fever_result(
                decision="not_due_now",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "O esquema padrão de febre amarela está "
                    "completo para esta faixa etária."
                ),
                interpretation_en=(
                    "The standard yellow-fever series is complete "
                    "for this age range."
                ),
            )

        return _yellow_fever_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O histórico padrão abaixo de 5 anos não "
                "corresponde a um estado de rotina interpretável."
            ),
            interpretation_en=(
                "The under-5 standard-dose history does not "
                "match an automatically interpretable routine state."
            ),
        )

    if age5plus_standard_events:
        return _yellow_fever_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Há dose padrão documentada a partir dos "
                "5 anos; a situação vacinal de rotina é "
                "considerada completa."
            ),
            interpretation_en=(
                "A standard dose is documented at or after "
                "age 5; the routine vaccination state is "
                "considered complete."
            ),
        )

    pre5_count = len(
        pre5_standard_events
    )

    if pre5_count >= 2:
        return _yellow_fever_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Há duas doses padrão válidas documentadas "
                "antes dos 5 anos; a situação vacinal de rotina "
                "é considerada completa."
            ),
            interpretation_en=(
                "Two valid standard doses are documented before "
                "age 5; the routine vaccination state is "
                "considered complete."
            ),
        )

    if pre5_count == 1:
        prior = (
            pre5_standard_events[
                0
            ][
                "administration_date"
            ]
        )

        due_date = (
            prior
            + timedelta(
                days=30,
            )
        )

        if (
            assessment_date
            < due_date
        ):
            return _yellow_fever_result(
                decision="not_due_now",
                assessment_date=assessment_date,
                recommended_date=due_date,
                recommended_interval_days=None,
                minimum_interval_days=30,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "Há uma dose padrão antes dos 5 anos, mas "
                    "o intervalo mínimo para o reforço ainda não "
                    "foi atingido. A obrigação de reforço não é "
                    "cancelada pela passagem do quinto aniversário."
                ),
                interpretation_en=(
                    "One standard dose was given before age 5, "
                    "but the minimum interval for the booster has "
                    "not yet elapsed. The booster obligation is "
                    "not cancelled by crossing the fifth birthday."
                ),
            )

        return _yellow_fever_due_with_context_and_safety(
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
            routine_context_state=routine_context_state,
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            indication_pt=(
                "Há uma única dose padrão documentada antes "
                "dos 5 anos. Está indicada uma dose de reforço "
                "de febre amarela agora."
            ),
            indication_en=(
                "Exactly one standard dose is documented before "
                "age 5. One yellow-fever booster dose is indicated now."
            ),
        )

    if pre5_count == 0:
        return _yellow_fever_due_with_context_and_safety(
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
            routine_context_state=routine_context_state,
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            indication_pt=(
                "Não há dose padrão documentada. Entre 5 e "
                "59 anos, está indicada uma dose padrão de "
                "febre amarela agora."
            ),
            indication_en=(
                "No standard dose is documented. From age 5 "
                "through 59, one standard yellow-fever dose is "
                "indicated now."
            ),
        )

    return _yellow_fever_result(
        decision="special_pathway_review",
        assessment_date=assessment_date,
        recommended_date=None,
        recommended_interval_days=None,
        minimum_interval_days=None,
        minimum_interval_applied=False,
        history_required=False,
        missing_context=[],
        interpretation_pt=(
            "O histórico de febre amarela não corresponde a "
            "um estado de rotina automaticamente interpretável."
        ),
        interpretation_en=(
            "The yellow-fever history does not match an "
            "automatically interpretable routine state."
        ),
    )

MMR_RULE_ID = (
    "PNI26-MMR-ROUTINE-001"
)

MMR_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

MMR_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/publicacoes/"
    "instrucao-normativa-que-instrui-o-calendario-"
    "nacional-de-vacinacao-2026.pdf/@@download/file"
)

MMR_OCCUPATION_CONTEXT_STATES = frozenset(
    {
        "not_screened",
        "not_health_worker",
        "health_worker",
    }
)

MMR_PREGNANCY_STATUSES = frozenset(
    {
        "not_screened",
        "pregnant",
        "not_pregnant",
        "not_applicable",
    }
)

MMR_SPECIAL_CONDITION_SCREEN_STATES = frozenset(
    {
        "not_screened",
        "screened_none",
        "screened_special_condition_present",
    }
)

MMR_EXTERNAL_LIVE_GROUPS = frozenset(
    {
        "yellow_fever",
        "varicella",
        "dengue",
    }
)

MMR_EXCEPTIONAL_15_DAY_EXTERNAL_GROUPS = frozenset(
    {
        "yellow_fever",
        "varicella",
    }
)


def _validate_mmr_normalized_history(
    *,
    date_of_birth,
    mmr_history,
):
    if hasattr(
        mmr_history,
        "model_dump",
    ):
        history = (
            mmr_history
            .model_dump()
        )

    elif isinstance(
        mmr_history,
        dict,
    ):
        history = dict(
            mmr_history
        )

    else:
        raise ValueError(
            "mmr_history must be a normalized mapping or model"
        )

    if (
        history.get(
            "target_family"
        )
        != "mmr_routine_history"
    ):
        raise ValueError(
            "mmr_history target_family is incompatible"
        )

    expected = {
        "age_6m_date":
            _add_months_clamped(
                date_of_birth,
                6,
            ),

        "age_12m_date":
            _add_months_clamped(
                date_of_birth,
                12,
            ),

        "age_15m_date":
            _add_months_clamped(
                date_of_birth,
                15,
            ),

        "age_30y_date":
            _add_months_clamped(
                date_of_birth,
                360,
            ),

        "age_60y_date":
            _add_months_clamped(
                date_of_birth,
                720,
            ),
    }

    for field, value in expected.items():
        if history.get(
            field
        ) != value:
            raise ValueError(
                f"MMR normalized {field} does not match date_of_birth"
            )

    if (
        history.get(
            "registration_role_defines_clinical_role"
        )
        is not False
    ):
        raise ValueError(
            "MMR registration role cannot define clinical role"
        )

    if (
        history.get(
            "clinical_role_derived_from_product_age_chronology"
        )
        is not True
    ):
        raise ValueError(
            "MMR clinical role must derive from "
            "product, age and chronology"
        )

    for field in (
        "normalizer_assigns_due_decision",
        "occupation_inferred",
        "pregnancy_inferred",
        "epidemiologic_context_inferred",
        "special_condition_inferred",
        "synthetic_score_applied",
    ):
        if (
            history.get(
                field
            )
            is not False
        ):
            raise ValueError(
                f"MMR normalized history has invalid {field}"
            )

    if not isinstance(
        history.get(
            "events"
        ),
        list,
    ):
        raise ValueError(
            "MMR normalized events must be a list"
        )

    return history


def _mmr_validate_interaction_context(
    *,
    assessment_date,
    interaction_context,
):
    from schemas import (
        PniMmrInteractionContext,
    )

    if interaction_context is None:
        return None

    context = (
        PniMmrInteractionContext
        .model_validate(
            interaction_context
        )
    )

    for event in context.recent_live_vaccine_events:
        if (
            event.administration_date
            > assessment_date
        ):
            raise ValueError(
                "recent MMR live-vaccine event "
                "cannot follow assessment_date"
            )

    return context


def _mmr_external_interaction_gate(
    *,
    assessment_date,
    date_of_birth,
    interaction_context,
):
    age_2y = _add_months_clamped(
        date_of_birth,
        24,
    )

    under2 = (
        assessment_date
        < age_2y
    )

    context = (
        _mmr_validate_interaction_context(
            assessment_date=assessment_date,
            interaction_context=interaction_context,
        )
    )

    if (
        context is None
        or context.history_screen_state
        == "not_screened"
    ):
        return {
            "state":
                "context_required",

            "missing_context":
                [
                    "mmr_live_vaccine_interaction_context",
                ],

            "recommended_date":
                None,

            "recommended_interval_days":
                None,

            "minimum_interval_days":
                None,

            "minimum_interval_applied":
                False,
        }

    emergency_state = (
        context
        .epidemiologic_emergency_concomitant_circulation_state
    )

    same_day_groups = set(
        context.planned_same_day_vaccine_groups
    )

    same_day_groups.update(
        event.vaccine_group
        for event
        in context.recent_live_vaccine_events
        if (
            event.administration_date
            == assessment_date
        )
    )

    if (
        under2
        and "dengue"
        in same_day_groups
    ):
        return {
            "state":
                "special_pathway_review",

            "missing_context":
                [],

            "recommended_date":
                None,

            "recommended_interval_days":
                None,

            "minimum_interval_days":
                None,

            "minimum_interval_applied":
                False,
        }

    if (
        under2
        and "yellow_fever"
        in same_day_groups
    ):
        if (
            emergency_state
            == "not_assessed"
        ):
            return {
                "state":
                    "context_required",

                "missing_context":
                    [
                        "epidemiologic_emergency_"
                        "concomitant_circulation_state",
                    ],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    None,

                "minimum_interval_days":
                    None,

                "minimum_interval_applied":
                    False,
            }

        if (
            emergency_state
            != "present"
        ):
            return {
                "state":
                    "special_pathway_review",

                "missing_context":
                    [],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    30,

                "minimum_interval_days":
                    15,

                "minimum_interval_applied":
                    False,
            }

    blocking_dates = []
    exceptional_15_used = False

    for event in (
        context.recent_live_vaccine_events
    ):
        if (
            event.administration_date
            == assessment_date
        ):
            continue

        group = event.vaccine_group

        if (
            under2
            and group
            == "dengue"
        ):
            return {
                "state":
                    "special_pathway_review",

                "missing_context":
                    [],

                "recommended_date":
                    None,

                "recommended_interval_days":
                    None,

                "minimum_interval_days":
                    None,

                "minimum_interval_applied":
                    False,
            }

        interval_days = 30

        if (
            group
            in MMR_EXCEPTIONAL_15_DAY_EXTERNAL_GROUPS
            and context
            .exceptional_15_day_interval_authorized
        ):
            interval_days = 15
            exceptional_15_used = True

        threshold = (
            event.administration_date
            + timedelta(
                days=interval_days,
            )
        )

        if (
            assessment_date
            < threshold
        ):
            blocking_dates.append(
                (
                    threshold,
                    group,
                    interval_days,
                )
            )

    if blocking_dates:
        recommended_date = max(
            item[
                0
            ]
            for item
            in blocking_dates
        )

        if any(
            item[
                2
            ]
            == 30
            for item
            in blocking_dates
        ):
            minimum_interval_days = 30
            minimum_interval_applied = False

        else:
            minimum_interval_days = 15
            minimum_interval_applied = True

        return {
            "state":
                "not_due_now",

            "missing_context":
                [],

            "recommended_date":
                recommended_date,

            "recommended_interval_days":
                30,

            "minimum_interval_days":
                minimum_interval_days,

            "minimum_interval_applied":
                minimum_interval_applied,
        }

    return {
        "state":
            "clear",

        "missing_context":
            [],

        "recommended_date":
            None,

        "recommended_interval_days":
            30,

        "minimum_interval_days":
            (
                15
                if exceptional_15_used
                else 30
            ),

        "minimum_interval_applied":
            exceptional_15_used,
    }


def _mmr_due_with_context_and_safety(
    *,
    assessment_date,
    date_of_birth,
    pregnancy_status,
    special_condition_screen_state,
    interaction_context,
    administration_safety_screen_state,
    internal_recommended_interval_days,
    internal_minimum_interval_days,
    internal_minimum_interval_applied,
    indication_pt,
    indication_en,
):
    if (
        pregnancy_status
        == "not_screened"
    ):
        return _mmr_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=(
                internal_minimum_interval_applied
            ),
            history_required=False,
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "A dose de tríplice viral está indicada pela "
                "idade e pelo histórico, mas o estado gestacional "
                "precisa ser explicitamente avaliado antes da "
                "administração."
            ),
            interpretation_en=(
                "An MMR dose is indicated by age and history, "
                "but pregnancy status must be explicitly assessed "
                "before administration."
            ),
        )

    if (
        pregnancy_status
        == "pregnant"
    ):
        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A vacina tríplice viral é contraindicada durante "
                "a gestação. A dose não deve ser administrada "
                "neste momento; a situação deve ser conduzida "
                "pela via clínica apropriada."
            ),
            interpretation_en=(
                "MMR vaccination is contraindicated during "
                "pregnancy. The dose should not be administered "
                "now and the case should follow the appropriate "
                "clinical pathway."
            ),
        )

    if (
        special_condition_screen_state
        == "not_screened"
    ):
        return _mmr_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=(
                internal_minimum_interval_applied
            ),
            history_required=False,
            missing_context=[
                "mmr_special_condition_screen_state",
            ],
            interpretation_pt=(
                "A dose está indicada, mas é necessário confirmar "
                "explicitamente a ausência de condição especial "
                "relevante para vacina viva antes da recomendação "
                "de rotina."
            ),
            interpretation_en=(
                "The dose is indicated, but absence of a relevant "
                "special condition for live vaccination must be "
                "explicitly confirmed before a routine "
                "recommendation is made."
            ),
        )

    if (
        special_condition_screen_state
        == "screened_special_condition_present"
    ):
        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Foi identificada condição especial relevante "
                "para vacina viva. Este núcleo implementa apenas "
                "a rotina não excepcional da tríplice viral; "
                "é necessária avaliação pela via específica."
            ),
            interpretation_en=(
                "A special condition relevant to live vaccination "
                "is present. This core implements only the "
                "nonexceptional MMR routine; review through the "
                "appropriate special pathway is required."
            ),
        )

    interaction = _mmr_external_interaction_gate(
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
        interaction_context=interaction_context,
    )

    if (
        interaction[
            "state"
        ]
        == "context_required"
    ):
        return _mmr_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=(
                internal_minimum_interval_applied
            ),
            history_required=False,
            missing_context=(
                interaction[
                    "missing_context"
                ]
            ),
            interpretation_pt=(
                "A dose de tríplice viral está indicada pelo "
                "histórico, mas falta contexto explícito sobre "
                "outras vacinas vivas recentes ou planejadas."
            ),
            interpretation_en=(
                "An MMR dose is indicated by history, but explicit "
                "context about other recent or planned live "
                "vaccines is missing."
            ),
        )

    if (
        interaction[
            "state"
        ]
        == "special_pathway_review"
    ):
        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                interaction[
                    "recommended_interval_days"
                ]
            ),
            minimum_interval_days=(
                interaction[
                    "minimum_interval_days"
                ]
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A programação informada de vacina viva não pode "
                "ser resolvida automaticamente pela regra de rotina "
                "da tríplice viral. É necessária revisão da "
                "coadministração ou do intervalo."
            ),
            interpretation_en=(
                "The reported live-vaccine plan cannot be resolved "
                "automatically by the routine MMR rule. "
                "Coadministration or spacing requires review."
            ),
        )

    if (
        interaction[
            "state"
        ]
        == "not_due_now"
    ):
        return _mmr_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=(
                interaction[
                    "recommended_date"
                ]
            ),
            recommended_interval_days=(
                interaction[
                    "recommended_interval_days"
                ]
            ),
            minimum_interval_days=(
                interaction[
                    "minimum_interval_days"
                ]
            ),
            minimum_interval_applied=(
                interaction[
                    "minimum_interval_applied"
                ]
            ),
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A dose de tríplice viral está indicada pelo "
                "histórico, mas o intervalo necessário após outra "
                "vacina viva ainda não foi atingido."
            ),
            interpretation_en=(
                "An MMR dose is indicated by history, but the "
                "required interval after another live vaccine "
                "has not yet elapsed."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _mmr_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=assessment_date,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=(
                internal_minimum_interval_applied
            ),
            history_required=False,
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A dose está indicada e os demais contextos "
                "avaliados não impedem a administração, mas a "
                "avaliação de segurança ainda não foi documentada."
            ),
            interpretation_en=(
                "The dose is indicated and the other assessed "
                "contexts do not prevent administration, but "
                "administration safety screening has not yet "
                "been documented."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=(
                internal_recommended_interval_days
            ),
            minimum_interval_days=(
                internal_minimum_interval_days
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "Há preocupação documentada na avaliação de "
                "segurança para administração da tríplice viral. "
                "O caso requer revisão."
            ),
            interpretation_en=(
                "A concern was documented during MMR "
                "administration safety screening. Review is required."
            ),
        )

    result = _mmr_result(
        decision="recommend_now",
        assessment_date=assessment_date,
        recommended_date=assessment_date,
        recommended_interval_days=(
            internal_recommended_interval_days
        ),
        minimum_interval_days=(
            internal_minimum_interval_days
        ),
        minimum_interval_applied=(
            internal_minimum_interval_applied
        ),
        history_required=False,
        missing_context=[],
        interpretation_pt=indication_pt,
        interpretation_en=indication_en,
    )

    # Preserve explicitly applied prospective minimum-interval
    # provenance on a successful ready-to-administer result.
    #
    # The shared result helper may normalize interval metadata for
    # an immediately due dose.  For MMR, however, a source-authorized
    # 15-day exception is clinically material provenance and must
    # remain visible in the language-neutral result contract.
    if (
        internal_minimum_interval_applied
        and internal_minimum_interval_days
        is not None
    ):
        result[
            "minimum_interval_days"
        ] = internal_minimum_interval_days

        result[
            "minimum_interval_applied"
        ] = True

    return result


def _mmr_complete_result(
    *,
    assessment_date,
    interpretation_pt,
    interpretation_en,
):
    return _mmr_result(
        decision="not_due_now",
        assessment_date=assessment_date,
        recommended_date=None,
        recommended_interval_days=None,
        minimum_interval_days=None,
        minimum_interval_applied=False,
        history_required=False,
        missing_context=[],
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
    )


def evaluate_pni_mmr_routine(
    *,
    assessment_date,
    date_of_birth,
    mmr_history,
    occupation_context_state="not_screened",
    pregnancy_status="not_screened",
    special_condition_screen_state="not_screened",
    interaction_context=None,
    administration_safety_screen_state="not_screened",
    exceptional_minimum_interval_authorized=False,
):
    """
    Evaluate the ordinary PNI 2026 SCR/MMR routine.

    General population:
      [12m,30y) -> 2 general-valid component doses
      [30y,60y) -> 1 general-valid component dose

    Health workers:
      2 occupational-valid component doses, minimum 30 days.

    A source-authorized 15-day prospective exception can accelerate
    the general series only; it never lowers the occupational minimum.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        occupation_context_state
        not in MMR_OCCUPATION_CONTEXT_STATES
    ):
        raise ValueError(
            "invalid MMR occupation_context_state"
        )

    if (
        pregnancy_status
        not in MMR_PREGNANCY_STATUSES
    ):
        raise ValueError(
            "invalid MMR pregnancy_status"
        )

    if (
        special_condition_screen_state
        not in MMR_SPECIAL_CONDITION_SCREEN_STATES
    ):
        raise ValueError(
            "invalid MMR special_condition_screen_state"
        )

    if (
        administration_safety_screen_state
        not in PNI_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized must be boolean"
        )

    history = _validate_mmr_normalized_history(
        date_of_birth=date_of_birth,
        mmr_history=mmr_history,
    )

    age_12m = history[
        "age_12m_date"
    ]

    age_15m = history[
        "age_15m_date"
    ]

    age_30y = history[
        "age_30y_date"
    ]

    age_60y = history[
        "age_60y_date"
    ]

    events = history[
        "events"
    ]

    dose_zero_events = [
        event
        for event in events
        if (
            event[
                "clinical_role"
            ]
            == "dose_zero_history"
        )
    ]

    general_counted_events = [
        event
        for event in events
        if (
            event[
                "routine_component_ordinal"
            ]
            is not None
            and event[
                "general_series_counted"
            ]
        )
    ]

    occupational_counted_events = [
        event
        for event in events
        if (
            event[
                "routine_component_ordinal"
            ]
            is not None
            and event[
                "occupational_series_counted"
            ]
        )
    ]

    general_count = history[
        "general_valid_component_dose_count"
    ]

    occupational_count = history[
        "occupational_valid_component_dose_count"
    ]

    if (
        assessment_date
        >= age_60y
    ):
        if (
            occupation_context_state
            == "not_health_worker"
        ):
            return _mmr_complete_result(
                assessment_date=assessment_date,
                interpretation_pt=(
                    "A pessoa tem 60 anos ou mais e não foi "
                    "identificada como trabalhador da saúde. "
                    "A vacinação SCR fora dessa condição está "
                    "fora do núcleo de rotina implementado."
                ),
                interpretation_en=(
                    "The person is age 60 or older and is not "
                    "identified as a health worker. MMR vaccination "
                    "outside that condition is outside this "
                    "implemented routine core."
                ),
            )

        if (
            occupation_context_state
            == "not_screened"
        ):
            return _mmr_result(
                decision="context_required",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[
                    "mmr_occupation_context_state",
                ],
                interpretation_pt=(
                    "A partir dos 60 anos, a condição de "
                    "trabalhador da saúde pode modificar a "
                    "conduta para tríplice viral e precisa ser "
                    "explicitamente informada."
                ),
                interpretation_en=(
                    "At age 60 or older, health-worker status can "
                    "change the MMR pathway and must be explicitly "
                    "reported."
                ),
            )

        if history[
            "source_history_incomplete"
        ]:
            return _mmr_result(
                decision="history_required",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=True,
                missing_context=[
                    "complete_product_sensitive_mmr_history",
                ],
                interpretation_pt=(
                    "Para trabalhador da saúde com 60 anos ou "
                    "mais, é necessário histórico vacinal completo "
                    "antes de avaliar a situação."
                ),
                interpretation_en=(
                    "For a health worker age 60 or older, complete "
                    "vaccination history is required before the "
                    "status can be assessed."
                ),
            )

        if not history[
            "safe_for_routine_evaluation"
        ]:
            return _mmr_result(
                decision="special_pathway_review",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=None,
                minimum_interval_days=None,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "O histórico SCR/MMR não permite interpretação "
                    "automática segura para trabalhador da saúde "
                    "com 60 anos ou mais."
                ),
                interpretation_en=(
                    "The MMR history cannot be interpreted safely "
                    "and automatically for a health worker age "
                    "60 or older."
                ),
            )

        if (
            occupational_count
            >= 2
        ):
            return _mmr_complete_result(
                assessment_date=assessment_date,
                interpretation_pt=(
                    "Há duas doses ocupacionalmente válidas "
                    "documentadas. Não há dose adicional indicada "
                    "por este núcleo."
                ),
                interpretation_en=(
                    "Two occupationally valid doses are documented. "
                    "No additional dose is indicated by this core."
                ),
            )

        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=30,
            minimum_interval_days=30,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O trabalhador da saúde com 60 anos ou mais "
                "apresenta esquema incompleto. A atualização deve "
                "ser precedida de avaliação individual pelo "
                "serviço de saúde."
            ),
            interpretation_en=(
                "The health worker age 60 or older has an incomplete "
                "MMR schedule. Updating vaccination requires prior "
                "individual assessment by the health service."
            ),
        )

    if history[
        "source_history_incomplete"
    ]:
        return _mmr_result(
            decision="history_required",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=True,
            missing_context=[
                "complete_product_sensitive_mmr_history",
            ],
            interpretation_pt=(
                "É necessário histórico completo, datado e com "
                "produto identificado para interpretar com segurança "
                "o esquema de tríplice viral."
            ),
            interpretation_en=(
                "A complete dated history with exact product "
                "identity is required to interpret the MMR "
                "schedule safely."
            ),
        )

    if not history[
        "safe_for_routine_evaluation"
    ]:
        return _mmr_result(
            decision="special_pathway_review",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=None,
            minimum_interval_days=None,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "O histórico SCR/MMR normalizado contém evidência "
                "que impede interpretação automática segura da "
                "rotina e requer revisão."
            ),
            interpretation_en=(
                "The normalized MMR history contains evidence that "
                "prevents safe automatic routine interpretation "
                "and requires review."
            ),
        )

    if (
        assessment_date
        < age_12m
    ):
        due_date = age_12m

        if dose_zero_events:
            due_date = max(
                due_date,
                dose_zero_events[
                    -1
                ][
                    "administration_date"
                ]
                + timedelta(
                    days=30,
                ),
            )

        return _mmr_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=due_date,
            recommended_interval_days=None,
            minimum_interval_days=(
                30
                if dose_zero_events
                else None
            ),
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A rotina SCR/MMR ainda não iniciou. A primeira "
                "dose de rotina começa aos 12 meses, respeitando "
                "30 dias após eventual dose zero."
            ),
            interpretation_en=(
                "The routine MMR schedule has not yet started. "
                "The first routine dose begins at 12 months, "
                "respecting 30 days after any documented dose zero."
            ),
        )

    if (
        assessment_date
        < age_30y
    ):
        if (
            general_count
            == 0
        ):
            due_date = age_12m

            if dose_zero_events:
                due_date = max(
                    due_date,
                    dose_zero_events[
                        -1
                    ][
                        "administration_date"
                    ]
                    + timedelta(
                        days=30,
                    ),
                )

            if (
                assessment_date
                < due_date
            ):
                return _mmr_result(
                    decision="not_due_now",
                    assessment_date=assessment_date,
                    recommended_date=due_date,
                    recommended_interval_days=None,
                    minimum_interval_days=(
                        30
                        if dose_zero_events
                        else None
                    ),
                    minimum_interval_applied=False,
                    history_required=False,
                    missing_context=[],
                    interpretation_pt=(
                        "A primeira dose de rotina ainda não "
                        "atingiu a data aplicável."
                    ),
                    interpretation_en=(
                        "The first routine MMR dose has not yet "
                        "reached its applicable date."
                    ),
                )

            return _mmr_due_with_context_and_safety(
                assessment_date=assessment_date,
                date_of_birth=date_of_birth,
                pregnancy_status=pregnancy_status,
                special_condition_screen_state=(
                    special_condition_screen_state
                ),
                interaction_context=interaction_context,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                internal_recommended_interval_days=None,
                internal_minimum_interval_days=(
                    30
                    if dose_zero_events
                    else None
                ),
                internal_minimum_interval_applied=False,
                indication_pt=(
                    "Não há dose SCR/MMR de rotina válida. "
                    "A primeira dose de tríplice viral está "
                    "indicada agora."
                ),
                indication_en=(
                    "No valid routine MMR dose is documented. "
                    "The first MMR dose is indicated now."
                ),
            )

        if (
            general_count
            == 1
        ):
            first_general = (
                general_counted_events[
                    0
                ][
                    "administration_date"
                ]
            )

            ordinary_due = max(
                age_15m,
                first_general
                + timedelta(
                    days=30,
                ),
            )

            exceptional_due = max(
                age_15m,
                first_general
                + timedelta(
                    days=15,
                ),
            )

            if (
                assessment_date
                < exceptional_due
            ):
                return _mmr_result(
                    decision="not_due_now",
                    assessment_date=assessment_date,
                    recommended_date=(
                        exceptional_due
                        if exceptional_minimum_interval_authorized
                        else ordinary_due
                    ),
                    recommended_interval_days=30,
                    minimum_interval_days=(
                        15
                        if exceptional_minimum_interval_authorized
                        else 30
                    ),
                    minimum_interval_applied=False,
                    history_required=False,
                    missing_context=[],
                    interpretation_pt=(
                        "Há uma dose válida, mas a segunda dose "
                        "ainda não atingiu a data aplicável."
                    ),
                    interpretation_en=(
                        "One valid dose is documented, but the "
                        "second dose has not yet reached its "
                        "applicable date."
                    ),
                )

            if (
                assessment_date
                < ordinary_due
            ):
                if (
                    not exceptional_minimum_interval_authorized
                ):
                    return _mmr_result(
                        decision="not_due_now",
                        assessment_date=assessment_date,
                        recommended_date=ordinary_due,
                        recommended_interval_days=30,
                        minimum_interval_days=30,
                        minimum_interval_applied=False,
                        history_required=False,
                        missing_context=[],
                        interpretation_pt=(
                            "Há uma dose válida, mas o intervalo "
                            "ordinário de 30 dias ainda não foi "
                            "atingido."
                        ),
                        interpretation_en=(
                            "One valid dose is documented, but the "
                            "ordinary 30-day interval has not yet "
                            "elapsed."
                        ),
                    )

                if (
                    occupation_context_state
                    == "not_screened"
                ):
                    return _mmr_result(
                        decision="context_required",
                        assessment_date=assessment_date,
                        recommended_date=assessment_date,
                        recommended_interval_days=30,
                        minimum_interval_days=15,
                        minimum_interval_applied=True,
                        history_required=False,
                        missing_context=[
                            "mmr_occupation_context_state",
                        ],
                        interpretation_pt=(
                            "A segunda dose poderia ser antecipada "
                            "pela exceção geral de 15 dias, mas o "
                            "intervalo mínimo de trabalhador da "
                            "saúde permanece 30 dias. A condição "
                            "ocupacional precisa ser informada."
                        ),
                        interpretation_en=(
                            "The second dose could be accelerated "
                            "under the general 15-day exception, "
                            "but the health-worker minimum remains "
                            "30 days. Occupational status must be "
                            "reported."
                        ),
                    )

                if (
                    occupation_context_state
                    == "health_worker"
                ):
                    return _mmr_result(
                        decision="not_due_now",
                        assessment_date=assessment_date,
                        recommended_date=ordinary_due,
                        recommended_interval_days=30,
                        minimum_interval_days=30,
                        minimum_interval_applied=False,
                        history_required=False,
                        missing_context=[],
                        interpretation_pt=(
                            "Para trabalhador da saúde, o intervalo "
                            "mínimo entre as duas doses permanece "
                            "30 dias."
                        ),
                        interpretation_en=(
                            "For a health worker, the minimum "
                            "interval between the two doses remains "
                            "30 days."
                        ),
                    )

                return _mmr_due_with_context_and_safety(
                    assessment_date=assessment_date,
                    date_of_birth=date_of_birth,
                    pregnancy_status=pregnancy_status,
                    special_condition_screen_state=(
                        special_condition_screen_state
                    ),
                    interaction_context=interaction_context,
                    administration_safety_screen_state=(
                        administration_safety_screen_state
                    ),
                    internal_recommended_interval_days=30,
                    internal_minimum_interval_days=15,
                    internal_minimum_interval_applied=True,
                    indication_pt=(
                        "Há uma dose válida e a exceção de intervalo "
                        "mínimo de 15 dias foi explicitamente "
                        "autorizada para a série geral. A segunda "
                        "dose está indicada agora."
                    ),
                    indication_en=(
                        "One valid dose is documented and the "
                        "15-day minimum-interval exception was "
                        "explicitly authorized for the general "
                        "series. The second dose is indicated now."
                    ),
                )

            return _mmr_due_with_context_and_safety(
                assessment_date=assessment_date,
                date_of_birth=date_of_birth,
                pregnancy_status=pregnancy_status,
                special_condition_screen_state=(
                    special_condition_screen_state
                ),
                interaction_context=interaction_context,
                administration_safety_screen_state=(
                    administration_safety_screen_state
                ),
                internal_recommended_interval_days=30,
                internal_minimum_interval_days=30,
                internal_minimum_interval_applied=False,
                indication_pt=(
                    "Há uma dose SCR/MMR válida e a segunda dose "
                    "está indicada agora."
                ),
                indication_en=(
                    "One valid MMR dose is documented and the "
                    "second dose is indicated now."
                ),
            )

        if (
            occupational_count
            >= 2
        ):
            return _mmr_complete_result(
                assessment_date=assessment_date,
                interpretation_pt=(
                    "Há pelo menos duas doses SCR/MMR válidas "
                    "também pelo critério ocupacional de 30 dias. "
                    "O esquema está completo."
                ),
                interpretation_en=(
                    "At least two MMR doses are valid under the "
                    "30-day occupational criterion. The schedule "
                    "is complete."
                ),
            )

        if (
            occupation_context_state
            == "not_screened"
        ):
            return _mmr_result(
                decision="context_required",
                assessment_date=assessment_date,
                recommended_date=None,
                recommended_interval_days=30,
                minimum_interval_days=30,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[
                    "mmr_occupation_context_state",
                ],
                interpretation_pt=(
                    "O esquema geral está completo, mas uma ou "
                    "mais doses não satisfazem o intervalo "
                    "ocupacional de 30 dias. A condição de "
                    "trabalhador da saúde precisa ser informada."
                ),
                interpretation_en=(
                    "The general series is complete, but one or "
                    "more doses do not satisfy the 30-day "
                    "occupational interval. Health-worker status "
                    "must be reported."
                ),
            )

        if (
            occupation_context_state
            == "not_health_worker"
        ):
            return _mmr_complete_result(
                assessment_date=assessment_date,
                interpretation_pt=(
                    "O esquema geral de duas doses SCR/MMR está "
                    "completo."
                ),
                interpretation_en=(
                    "The two-dose general MMR series is complete."
                ),
            )

        last_occupational = (
            occupational_counted_events[
                -1
            ][
                "administration_date"
            ]
        )

        occupational_due = (
            last_occupational
            + timedelta(
                days=30,
            )
        )

        if (
            assessment_date
            < occupational_due
        ):
            return _mmr_result(
                decision="not_due_now",
                assessment_date=assessment_date,
                recommended_date=occupational_due,
                recommended_interval_days=30,
                minimum_interval_days=30,
                minimum_interval_applied=False,
                history_required=False,
                missing_context=[],
                interpretation_pt=(
                    "O esquema geral está completo, mas o "
                    "trabalhador da saúde ainda precisa completar "
                    "duas doses separadas por pelo menos 30 dias."
                ),
                interpretation_en=(
                    "The general series is complete, but the "
                    "health worker still requires two doses "
                    "separated by at least 30 days."
                ),
            )

        return _mmr_due_with_context_and_safety(
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
            pregnancy_status=pregnancy_status,
            special_condition_screen_state=(
                special_condition_screen_state
            ),
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            internal_recommended_interval_days=30,
            internal_minimum_interval_days=30,
            internal_minimum_interval_applied=False,
            indication_pt=(
                "O esquema geral está completo, mas o trabalhador "
                "da saúde ainda não possui duas doses válidas pelo "
                "intervalo ocupacional de 30 dias. Uma dose está "
                "indicada agora."
            ),
            indication_en=(
                "The general series is complete, but the health "
                "worker does not yet have two doses valid under "
                "the 30-day occupational interval. One dose is "
                "indicated now."
            ),
        )

    # Age 30 through 59.
    if (
        general_count
        == 0
    ):
        return _mmr_due_with_context_and_safety(
            assessment_date=assessment_date,
            date_of_birth=date_of_birth,
            pregnancy_status=pregnancy_status,
            special_condition_screen_state=(
                special_condition_screen_state
            ),
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            internal_recommended_interval_days=None,
            internal_minimum_interval_days=None,
            internal_minimum_interval_applied=False,
            indication_pt=(
                "Não há dose SCR/MMR válida documentada. "
                "Entre 30 e 59 anos, pelo menos uma dose está "
                "indicada agora."
            ),
            indication_en=(
                "No valid MMR dose is documented. From age 30 "
                "through 59, at least one dose is indicated now."
            ),
        )

    if (
        occupational_count
        >= 2
    ):
        return _mmr_complete_result(
            assessment_date=assessment_date,
            interpretation_pt=(
                "Há pelo menos duas doses SCR/MMR válidas pelo "
                "critério ocupacional de 30 dias. O esquema está "
                "completo tanto para a população geral quanto "
                "para trabalhador da saúde."
            ),
            interpretation_en=(
                "At least two MMR doses are valid under the "
                "30-day occupational criterion. The schedule is "
                "complete for both the general population and "
                "health workers."
            ),
        )

    if (
        occupation_context_state
        == "not_screened"
    ):
        return _mmr_result(
            decision="context_required",
            assessment_date=assessment_date,
            recommended_date=None,
            recommended_interval_days=30,
            minimum_interval_days=30,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[
                "mmr_occupation_context_state",
            ],
            interpretation_pt=(
                "A meta geral de uma dose está satisfeita, mas "
                "trabalhadores da saúde precisam de duas doses. "
                "A condição ocupacional precisa ser informada "
                "antes de declarar o esquema completo."
            ),
            interpretation_en=(
                "The one-dose general target is satisfied, but "
                "health workers require two doses. Occupational "
                "status must be reported before the schedule can "
                "be declared complete."
            ),
        )

    if (
        occupation_context_state
        == "not_health_worker"
    ):
        return _mmr_complete_result(
            assessment_date=assessment_date,
            interpretation_pt=(
                "Há pelo menos uma dose SCR/MMR válida e a pessoa "
                "não é trabalhador da saúde. O esquema geral para "
                "30 a 59 anos está completo."
            ),
            interpretation_en=(
                "At least one valid MMR dose is documented and "
                "the person is not a health worker. The general "
                "schedule for ages 30–59 is complete."
            ),
        )

    last_occupational = (
        occupational_counted_events[
            -1
        ][
            "administration_date"
        ]
    )

    occupational_due = (
        last_occupational
        + timedelta(
            days=30,
        )
    )

    if (
        assessment_date
        < occupational_due
    ):
        return _mmr_result(
            decision="not_due_now",
            assessment_date=assessment_date,
            recommended_date=occupational_due,
            recommended_interval_days=30,
            minimum_interval_days=30,
            minimum_interval_applied=False,
            history_required=False,
            missing_context=[],
            interpretation_pt=(
                "A meta geral está completa, mas o trabalhador "
                "da saúde necessita de uma segunda dose com "
                "intervalo mínimo de 30 dias."
            ),
            interpretation_en=(
                "The general target is complete, but the health "
                "worker requires a second dose with a minimum "
                "30-day interval."
            ),
        )

    return _mmr_due_with_context_and_safety(
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
        pregnancy_status=pregnancy_status,
        special_condition_screen_state=(
            special_condition_screen_state
        ),
        interaction_context=interaction_context,
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
        internal_recommended_interval_days=30,
        internal_minimum_interval_days=30,
        internal_minimum_interval_applied=False,
        indication_pt=(
            "A pessoa é trabalhador da saúde e possui apenas uma "
            "dose ocupacionalmente válida. A segunda dose está "
            "indicada agora."
        ),
        indication_en=(
            "The person is a health worker with only one "
            "occupationally valid dose. The second dose is "
            "indicated now."
        ),
    )

def _mmr_base_result(
    *,
    assessment_date: date,
    decision: str,
    interpretation_pt: str,
    interpretation_en: str,
    recommended_date: date | None = None,
    recommended_interval_days: int | None = None,
    history_required: bool = False,
    missing_context: list[str] | None = None,
) -> dict[str, Any]:
    interpretation_pt = interpretation_pt.strip()
    interpretation_en = interpretation_en.strip()

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "mmr",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                MMR_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                MMR_SOURCE_URL,

            "source_snapshot_date":
                MMR_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }

def _mmr_result(
    *,
    decision,
    assessment_date,
    recommended_date=None,
    recommended_interval_days=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
    history_required=False,
    missing_context=None,
    interpretation_pt,
    interpretation_en,
):
    if missing_context is None:
        missing_context = []

    result = _mmr_base_result(
        assessment_date=assessment_date,
        decision=decision,
        interpretation_pt=interpretation_pt,
        interpretation_en=interpretation_en,
        recommended_date=recommended_date,
        recommended_interval_days=recommended_interval_days,
        history_required=history_required,
        missing_context=missing_context,
    )

    result[
        "minimum_interval_days"
    ] = minimum_interval_days

    result[
        "minimum_interval_applied"
    ] = minimum_interval_applied

    return result
DTP_CHILD_RULE_ID = (
    "PNI26-DTP-CHILD-ROUTINE-001"
)

DTP_CHILD_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

DTP_CHILD_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf"
)

DTP_SPECIAL_CONDITION_SCREEN_STATES = {
    "not_screened",
    "screened_none",
    "screened_special_condition_present",
}

DTP_ADMINISTRATION_SAFETY_SCREEN_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}


def _dtp_child_result(
    *,
    assessment_date,
    decision,
    interpretation_pt,
    interpretation_en,
    recommended_date=None,
    history_required=False,
    missing_context=None,
):
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "dtp",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        # Six-month DTP intervals are calendar-month rules.
        # Do not misrepresent them as a fixed day count.
        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                DTP_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                DTP_CHILD_SOURCE_URL,

            "source_snapshot_date":
                DTP_CHILD_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _dtp_child_due_with_context_and_safety(
    *,
    assessment_date,
    special_condition_screen_state,
    administration_safety_screen_state,
    indication_pt,
    indication_en,
):
    if (
        special_condition_screen_state
        == "not_screened"
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dtp_special_condition_screen_state",
            ],
            interpretation_pt=(
                "Uma dose de DTP estaria indicada pela cronologia "
                "de rotina, mas é necessário confirmar primeiro "
                "se há condição clínica ou antecedente de evento "
                "adverso relevante que exija via especial/CRIE."
            ),
            interpretation_en=(
                "A routine DTP dose would otherwise be indicated, "
                "but relevant clinical conditions or a prior serious "
                "adverse event requiring a special/CRIE pathway must "
                "first be assessed."
            ),
        )

    if (
        special_condition_screen_state
        == "screened_special_condition_present"
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há condição especial documentada em situação na "
                "qual uma dose de DTP seria, de outro modo, devida. "
                "Não automatizar DTP de células inteiras; revisar "
                "via especial/CRIE."
            ),
            interpretation_en=(
                "A special condition is documented when a DTP dose "
                "would otherwise be due. Do not automate whole-cell "
                "DTP; review the special/CRIE pathway."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Uma dose de DTP estaria indicada pela rotina, mas "
                "a triagem de segurança para administração ainda "
                "não foi concluída."
            ),
            interpretation_en=(
                "A routine DTP dose would otherwise be indicated, "
                "but administration-safety screening has not yet "
                "been completed."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há preocupação de segurança documentada antes de "
                "uma dose de DTP que seria devida. Revisar a situação "
                "antes da administração."
            ),
            interpretation_en=(
                "A safety concern is documented before a DTP dose "
                "that would otherwise be due. Review before "
                "administration."
            ),
        )

    return _dtp_child_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_date=assessment_date,
        interpretation_pt=indication_pt,
        interpretation_en=indication_en,
    )


def evaluate_pni_dtp_child_routine(
    *,
    assessment_date,
    date_of_birth,
    dtp_history,
    special_condition_screen_state="not_screened",
    administration_safety_screen_state="not_screened",
):
    """
    Evaluate the routine childhood DTP booster layer.

    This core consumes only the locked normalized DTP child-history
    representation. It does not reinterpret raw pentavalent/DTP
    records and does not use aggregate toxoid counts as series
    completion evidence.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        special_condition_screen_state
        not in DTP_SPECIAL_CONDITION_SCREEN_STATES
    ):
        raise ValueError(
            "invalid special_condition_screen_state"
        )

    if (
        administration_safety_screen_state
        not in DTP_ADMINISTRATION_SAFETY_SCREEN_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        dtp_history,
        dict,
    ):
        raise ValueError(
            "dtp_history must be normalized DTP history"
        )

    if (
        dtp_history.get(
            "model_id"
        )
        != "PNI26-DTP-CHILD-HISTORY-001"
    ):
        raise ValueError(
            "dtp_history model_id is not recognized"
        )

    if (
        dtp_history.get(
            "target_family"
        )
        != "dtp_child_booster_history"
    ):
        raise ValueError(
            "dtp_history target_family is not recognized"
        )

    age_15m = dtp_history.get(
        "age_15m_date"
    )

    age_4y = dtp_history.get(
        "age_4y_date"
    )

    age_7y = dtp_history.get(
        "age_7y_date"
    )

    if not all(
        isinstance(
            value,
            date,
        )
        for value in (
            age_15m,
            age_4y,
            age_7y,
        )
    ):
        raise ValueError(
            "dtp_history age boundaries are incomplete"
        )

    if (
        dtp_history.get(
            "source_history_incomplete"
        )
        is True
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico necessário para interpretar a série "
                "infantil de DTP está incompleto ou contém doses "
                "prévias sem data exata."
            ),
            interpretation_en=(
                "The history required to interpret the childhood "
                "DTP series is incomplete or contains prior doses "
                "without exact dates."
            ),
        )

    if (
        dtp_history.get(
            "safe_for_routine_evaluation"
        )
        is not True
    ):
        reasons = list(
            dtp_history.get(
                "invalid_history_reasons"
            )
            or []
        )

        rendered = (
            ", ".join(
                reasons
            )
            if reasons
            else "unspecified_history_conflict"
        )

        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico DTP/pentavalente contém cronologia, "
                "identidade de produto ou evidência que não pode ser "
                "classificada automaticamente com segurança. "
                f"Motivos normalizados: {rendered}."
            ),
            interpretation_en=(
                "The DTP/pentavalent history contains chronology, "
                "product identity, or evidence that cannot be safely "
                "classified automatically. "
                f"Normalized reasons: {rendered}."
            ),
        )

    # Exact seventh birthday closes ordinary childhood DTP.
    if assessment_date >= age_7y:
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A partir do sétimo aniversário, a camada infantil "
                "de rotina da DTP está encerrada. Este núcleo não "
                "gera automaticamente uma recomendação de dT."
            ),
            interpretation_en=(
                "From the seventh birthday onward, the routine "
                "childhood DTP layer is closed. This core does not "
                "automatically generate a dT recommendation."
            ),
        )

    if (
        dtp_history.get(
            "dtp_r2_history_valid"
        )
        is True
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Os dois reforços infantis válidos de DTP já estão "
                "documentados; não há nova dose de DTP de rotina "
                "indicada nesta camada."
            ),
            interpretation_en=(
                "Both valid childhood DTP boosters are documented; "
                "no additional routine DTP dose is indicated in "
                "this layer."
            ),
        )

    if (
        dtp_history.get(
            "pentavalent_basic_series_complete"
        )
        is not True
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "A série básica qualificadora de três doses de "
                "pentavalente não está completa neste histórico. "
                "A DTP não deve ser promovida automaticamente a "
                "reforço antes desse pré-requisito."
            ),
            interpretation_en=(
                "The qualifying three-dose pentavalent basic series "
                "is not complete in this history. DTP must not be "
                "automatically promoted to a booster before that "
                "prerequisite is met."
            ),
        )

    qualifying_d3 = dtp_history.get(
        "qualifying_pentavalent_d3_date"
    )

    if not isinstance(
        qualifying_d3,
        date,
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A série pentavalente consta como completa, mas a "
                "data qualificadora de D3 não está disponível para "
                "calcular com segurança o reforço de DTP."
            ),
            interpretation_en=(
                "The pentavalent series is marked complete, but the "
                "qualifying dose-3 date is unavailable for safe DTP "
                "booster timing."
            ),
        )

    # --------------------------------------------------------
    # R1
    # --------------------------------------------------------
    if (
        dtp_history.get(
            "dtp_r1_history_valid"
        )
        is not True
    ):
        d3_plus_6m = _add_months_clamped(
            qualifying_d3,
            6,
        )

        earliest_r1 = max(
            age_15m,
            d3_plus_6m,
        )

        if earliest_r1 >= age_7y:
            return _dtp_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                interpretation_pt=(
                    "A data mínima possível para R1 de DTP cai no "
                    "sétimo aniversário ou depois dele. A oportunidade "
                    "de DTP infantil está encerrada; este núcleo não "
                    "sintetiza a sequência futura de dT."
                ),
                interpretation_en=(
                    "The earliest possible DTP booster 1 date falls "
                    "on or after the seventh birthday. The childhood "
                    "DTP opportunity is closed; this core does not "
                    "synthesize the later dT schedule."
                ),
            )

        if assessment_date < earliest_r1:
            return _dtp_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=earliest_r1,
                interpretation_pt=(
                    "R1 de DTP ainda não é devido. A primeira data "
                    "válida é a mais tardia entre 15 meses de idade "
                    "e seis meses-calendário após D3 da pentavalente."
                ),
                interpretation_en=(
                    "DTP booster 1 is not yet due. The first valid "
                    "date is the later of age 15 months and six "
                    "calendar months after pentavalent dose 3."
                ),
            )

        return _dtp_child_due_with_context_and_safety(
            assessment_date=assessment_date,
            special_condition_screen_state=(
                special_condition_screen_state
            ),
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            indication_pt=(
                "A série básica de pentavalente está completa, a "
                "criança está com pelo menos 15 meses e já decorreram "
                "seis meses-calendário desde D3. Recomendar R1 de DTP "
                "agora."
            ),
            indication_en=(
                "The pentavalent basic series is complete, the child "
                "is at least 15 months old, and six calendar months "
                "have elapsed since dose 3. Recommend DTP booster 1 "
                "now."
            ),
        )

    # --------------------------------------------------------
    # R2
    # --------------------------------------------------------
    r1_date = dtp_history.get(
        "dtp_r1_event_date"
    )

    if not isinstance(
        r1_date,
        date,
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "R1 consta como válido, mas sua data não está "
                "disponível para determinar R2 com segurança."
            ),
            interpretation_en=(
                "Booster 1 is marked valid, but its date is not "
                "available to determine booster 2 safely."
            ),
        )

    earliest_r2 = dtp_history.get(
        "r2_earliest_date"
    )

    expected_earliest_r2 = max(
        age_4y,
        _add_months_clamped(
            r1_date,
            6,
        ),
    )

    if (
        not isinstance(
            earliest_r2,
            date,
        )
        or earliest_r2
        != expected_earliest_r2
    ):
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A data mínima normalizada para R2 não é consistente "
                "com o maior valor entre 4 anos de idade e seis "
                "meses-calendário após R1."
            ),
            interpretation_en=(
                "The normalized earliest booster-2 date is not "
                "consistent with the later of age 4 years and six "
                "calendar months after booster 1."
            ),
        )

    if earliest_r2 >= age_7y:
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "R1 é válido, porém R2 só poderia ocorrer no sétimo "
                "aniversário ou depois dele ao respeitar o intervalo "
                "mínimo de seis meses-calendário. Não comprimir o "
                "intervalo; a oportunidade de R2 com DTP está encerrada."
            ),
            interpretation_en=(
                "Booster 1 is valid, but booster 2 could only occur "
                "on or after the seventh birthday while respecting "
                "the six-calendar-month minimum. Do not compress the "
                "interval; the DTP booster-2 opportunity is closed."
            ),
        )

    if assessment_date < earliest_r2:
        return _dtp_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=earliest_r2,
            interpretation_pt=(
                "R2 de DTP ainda não é devido. A primeira data válida "
                "é a mais tardia entre o quarto aniversário e seis "
                "meses-calendário após R1."
            ),
            interpretation_en=(
                "DTP booster 2 is not yet due. The first valid date "
                "is the later of the fourth birthday and six calendar "
                "months after booster 1."
            ),
        )

    return _dtp_child_due_with_context_and_safety(
        assessment_date=assessment_date,
        special_condition_screen_state=(
            special_condition_screen_state
        ),
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
        indication_pt=(
            "R1 de DTP é válido, a criança atingiu pelo menos 4 anos "
            "e já decorreram seis meses-calendário desde R1. Recomendar "
            "R2 de DTP agora."
        ),
        indication_en=(
            "DTP booster 1 is valid, the child is at least 4 years "
            "old, and six calendar months have elapsed since booster "
            "1. Recommend DTP booster 2 now."
        ),
    )
VARICELLA_CHILD_RULE_ID = (
    "PNI26-VARICELLA-CHILD-ROUTINE-001"
)

VARICELLA_CHILD_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

VARICELLA_CHILD_SOURCE_URL = (
    'https://www.gov.br/saude/pt-br/vacinacao/publicacoes/instrucao-normativa-que-instrui-o-calendario-nacional-de-vacinacao-2026.pdf'
)

VARICELLA_DISEASE_HISTORY_STATES = {
    "not_screened",
    "screened_no_prior_varicella",
    "screened_prior_varicella_history_uncertain",
    "screened_confirmed_prior_varicella",
}

VARICELLA_PREGNANCY_STATES = {
    "not_screened",
    "pregnant",
    "not_pregnant",
    "unknown",
    "not_applicable",
}

VARICELLA_SPECIAL_CONDITION_STATES = {
    "not_screened",
    "screened_none",
    "screened_special_condition_present",
}

VARICELLA_ADMINISTRATION_SAFETY_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}


def _varicella_child_add_months_clamped(
    value,
    months,
):
    from calendar import monthrange

    zero_based = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + zero_based // 12
    )

    month = (
        zero_based % 12
        + 1
    )

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def _varicella_child_result(
    *,
    assessment_date,
    decision,
    interpretation_pt,
    interpretation_en,
    recommended_date=None,
    history_required=False,
    missing_context=None,
):
    interpretation_pt = (
        interpretation_pt.strip()
    )

    interpretation_en = (
        interpretation_en.strip()
    )

    if not interpretation_pt:
        raise ValueError(
            "interpretation_pt must not be empty"
        )

    if not interpretation_en:
        raise ValueError(
            "interpretation_en must not be empty"
        )

    return {
        "vaccine_key":
            "varicella",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        # The internal VZ child-series interval is calendar-month
        # based. External live-vaccine spacing is represented by
        # exact recommended dates rather than overloading this field.
        "recommended_interval_days":
            None,

        "minimum_interval_days":
            None,

        "minimum_interval_applied":
            False,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                VARICELLA_CHILD_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                VARICELLA_CHILD_SOURCE_URL,

            "source_snapshot_date":
                VARICELLA_CHILD_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt,

        "interpretation_en":
            interpretation_en,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _varicella_child_due_with_context_gates(
    *,
    assessment_date,
    dose_label,
    disease_history_state,
    pregnancy_status,
    special_condition_screen_state,
    interaction_context,
    administration_safety_screen_state,
):
    import schemas

    if (
        disease_history_state
        == "not_screened"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "varicella_disease_history_state",
            ],
            interpretation_pt=(
                "Uma dose de varicela estaria indicada pela cronologia "
                "vacinal, mas o histórico prévio de varicela ainda "
                "precisa ser verificado."
            ),
            interpretation_en=(
                "A varicella dose would otherwise be indicated by "
                "vaccination chronology, but prior varicella disease "
                "history must first be assessed."
            ),
        )

    if (
        disease_history_state
        == "screened_confirmed_prior_varicella"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há histórico pregresso confirmado de varicela. "
                "A vacinação de rotina da população geral não é "
                "indicada por esta camada."
            ),
            interpretation_en=(
                "Confirmed prior varicella disease is documented. "
                "General-population routine vaccination is not "
                "indicated by this layer."
            ),
        )

    if pregnancy_status in {
        "not_screened",
        "unknown",
    }:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "Uma dose de varicela estaria indicada, mas o estado "
                "gestacional aplicável ainda não foi esclarecido."
            ),
            interpretation_en=(
                "A varicella dose would otherwise be indicated, but "
                "applicable pregnancy status has not yet been resolved."
            ),
        )

    if (
        pregnancy_status
        == "pregnant"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A vacina varicela é de vírus vivo atenuado e há "
                "gestação documentada. Não automatizar a administração; "
                "seguir a via de contraindicação/avaliação clínica."
            ),
            interpretation_en=(
                "Varicella vaccine is live attenuated and pregnancy is "
                "documented. Do not automate administration; follow the "
                "contraindication/clinical-review pathway."
            ),
        )

    if (
        special_condition_screen_state
        == "not_screened"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "special_condition_screen_state",
            ],
            interpretation_pt=(
                "Uma dose de varicela estaria indicada, mas é necessário "
                "confirmar ausência de condição especial relevante para "
                "vacina de vírus vivo/CRIE."
            ),
            interpretation_en=(
                "A varicella dose would otherwise be indicated, but "
                "relevant live-vaccine/CRIE special conditions must "
                "first be assessed."
            ),
        )

    if (
        special_condition_screen_state
        == "screened_special_condition_present"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há condição especial documentada em situação na qual "
                "a dose de varicela seria, de outro modo, devida. "
                "Revisar a via especial/CRIE antes da administração."
            ),
            interpretation_en=(
                "A special condition is documented when a varicella "
                "dose would otherwise be due. Review the special/CRIE "
                "pathway before administration."
            ),
        )

    if interaction_context is None:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "varicella_interaction_context",
            ],
            interpretation_pt=(
                "Uma dose de varicela estaria indicada, mas o histórico "
                "recente de vacina tríplice viral/febre amarela ainda "
                "não foi verificado."
            ),
            interpretation_en=(
                "A varicella dose would otherwise be indicated, but "
                "recent MMR/yellow-fever live-vaccine history has not "
                "yet been assessed."
            ),
        )

    if not isinstance(
        interaction_context,
        schemas.PniVaricellaInteractionContext,
    ):
        raise ValueError(
            "interaction_context must be "
            "PniVaricellaInteractionContext"
        )

    if (
        interaction_context.history_screen_state
        == "not_screened"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "varicella_interaction_history_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas a triagem de interação "
                "com vacina tríplice viral/febre amarela está incompleta."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but screening "
                "for MMR/yellow-fever live-vaccine interaction is "
                "incomplete."
            ),
        )

    # Same-day administration is permitted with both modeled groups.
    # Planned same-day groups therefore do not impose a delay and there
    # is deliberately no under-2 MMR/VFA emergency restriction here.
    wait_until = None

    if (
        interaction_context.history_screen_state
        == "screened_relevant_live_vaccine_history"
    ):
        required_days = (
            15
            if (
                interaction_context
                .exceptional_15_day_interval_authorized
            )
            else 30
        )

        from datetime import timedelta

        for event in (
            interaction_context
            .recent_live_vaccine_events
        ):
            if (
                event.administration_date
                > assessment_date
            ):
                raise ValueError(
                    "recent live-vaccine event cannot "
                    "follow assessment_date"
                )

            actual_days = (
                assessment_date
                - event.administration_date
            ).days

            # Zero means same-day administration and is allowed.
            if actual_days == 0:
                continue

            threshold = (
                event.administration_date
                + timedelta(
                    days=required_days,
                )
            )

            if (
                assessment_date
                < threshold
            ):
                if (
                    wait_until is None
                    or threshold
                    > wait_until
                ):
                    wait_until = threshold

    if wait_until is not None:
        if (
            interaction_context
            .exceptional_15_day_interval_authorized
        ):
            interval_pt = (
                "o mínimo excepcional explicitamente autorizado "
                "de 15 dias"
            )

            interval_en = (
                "the explicitly authorized exceptional "
                "15-day minimum"
            )

        else:
            interval_pt = (
                "o intervalo ordinário de 30 dias"
            )

            interval_en = (
                "the ordinary 30-day interval"
            )

        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=wait_until,
            interpretation_pt=(
                f"{dose_label} de varicela está indicada pela "
                f"cronologia da série, porém {interval_pt} após "
                "vacina tríplice viral/febre amarela administrada "
                "em dia diferente ainda não foi alcançado."
            ),
            interpretation_en=(
                f"Varicella {dose_label} is indicated by the series "
                f"chronology, but {interval_en} after an MMR/"
                "yellow-fever vaccine given on a different day has "
                "not yet elapsed."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "Uma dose de varicela estaria indicada, mas a triagem "
                "de segurança para administração ainda não foi concluída."
            ),
            interpretation_en=(
                "A varicella dose would otherwise be indicated, but "
                "administration-safety screening has not yet been "
                "completed."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há preocupação de segurança documentada antes de uma "
                "dose de varicela que seria devida. Revisar antes da "
                "administração."
            ),
            interpretation_en=(
                "A safety concern is documented before a varicella "
                "dose that would otherwise be due. Review before "
                "administration."
            ),
        )

    return _varicella_child_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_date=assessment_date,
        interpretation_pt=(
            f"Recomendar {dose_label} da vacina varicela monovalente "
            "agora. Em indisponibilidade da varicela monovalente, a "
            "tetraviral pode ser utilizada conforme histórico vacinal "
            "e orientações vigentes."
        ),
        interpretation_en=(
            f"Recommend monovalent varicella {dose_label} now. "
            "If monovalent varicella vaccine is unavailable, MMRV/SCRV "
            "may be used according to vaccination history and current "
            "guidance."
        ),
    )


def evaluate_pni_varicella_child_routine(
    *,
    assessment_date,
    date_of_birth,
    varicella_history,
    disease_history_state="not_screened",
    pregnancy_status="not_screened",
    special_condition_screen_state="not_screened",
    interaction_context=None,
    administration_safety_screen_state="not_screened",
):
    """
    Evaluate the general-child routine varicella layer.

    The evaluator consumes only the locked normalized VZ history.
    It does not parse raw monovalent or MMR/SCRV histories.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if assessment_date < date_of_birth:
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        disease_history_state
        not in VARICELLA_DISEASE_HISTORY_STATES
    ):
        raise ValueError(
            "invalid disease_history_state"
        )

    if (
        pregnancy_status
        not in VARICELLA_PREGNANCY_STATES
    ):
        raise ValueError(
            "invalid pregnancy_status"
        )

    if (
        special_condition_screen_state
        not in VARICELLA_SPECIAL_CONDITION_STATES
    ):
        raise ValueError(
            "invalid special_condition_screen_state"
        )

    if (
        administration_safety_screen_state
        not in VARICELLA_ADMINISTRATION_SAFETY_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        varicella_history,
        dict,
    ):
        raise ValueError(
            "varicella_history must be normalized VZ history"
        )

    if (
        varicella_history.get(
            "model_id"
        )
        != "PNI26-VARICELLA-CHILD-HISTORY-001"
    ):
        raise ValueError(
            "varicella_history model_id is not recognized"
        )

    if (
        varicella_history.get(
            "target_family"
        )
        != "varicella_child_routine_history"
    ):
        raise ValueError(
            "varicella_history target_family is not recognized"
        )

    age_15m = varicella_history.get(
        "age_15m_date"
    )

    age_4y = varicella_history.get(
        "age_4y_date"
    )

    age_7y = varicella_history.get(
        "age_7y_date"
    )

    if not all(
        isinstance(
            value,
            date,
        )
        for value in (
            age_15m,
            age_4y,
            age_7y,
        )
    ):
        raise ValueError(
            "varicella_history age boundaries are incomplete"
        )

    if (
        varicella_history.get(
            "source_history_incomplete"
        )
        is True
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico necessário para interpretar a vacinação "
                "infantil contra varicela está incompleto ou contém "
                "evidência sem data exata."
            ),
            interpretation_en=(
                "The history required to interpret childhood varicella "
                "vaccination is incomplete or contains evidence without "
                "an exact date."
            ),
        )

    if (
        varicella_history.get(
            "safe_for_routine_evaluation"
        )
        is not True
    ):
        reasons = list(
            varicella_history.get(
                "invalid_history_reasons"
            )
            or []
        )

        rendered = (
            ", ".join(
                reasons
            )
            if reasons
            else "unspecified_history_conflict"
        )

        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico de varicela contém evidência que não pode "
                "ser interpretada automaticamente com segurança no "
                f"núcleo de rotina. Motivos normalizados: {rendered}."
            ),
            interpretation_en=(
                "The varicella history contains evidence that cannot "
                "be safely interpreted automatically by the routine "
                f"core. Normalized reasons: {rendered}."
            ),
        )

    if assessment_date >= age_7y:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A partir do sétimo aniversário, esta camada de rotina "
                "da população geral infantil para varicela está "
                "encerrada. Este núcleo não sintetiza resgate, "
                "ocupacional, indígena ou pós-exposição."
            ),
            interpretation_en=(
                "From the seventh birthday onward, this general-child "
                "routine varicella layer is closed. This core does not "
                "synthesize rescue, occupational, Indigenous, or "
                "post-exposure schedules."
            ),
        )

    valid_count = int(
        varicella_history.get(
            "valid_child_component_dose_count"
        )
        or 0
    )

    if (
        varicella_history.get(
            "child_series_complete"
        )
        is True
        or valid_count >= 2
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Duas doses válidas com componente varicela já estão "
                "documentadas para a série infantil; nenhuma nova dose "
                "de rotina é indicada nesta camada."
            ),
            interpretation_en=(
                "Two valid varicella-containing doses are already "
                "documented for the childhood series; no additional "
                "routine dose is indicated in this layer."
            ),
        )

    if valid_count == 0:
        if assessment_date < age_15m:
            return _varicella_child_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=age_15m,
                interpretation_pt=(
                    "A primeira dose de rotina contra varicela ainda "
                    "não é devida. A agenda oportuna inicia aos "
                    "15 meses de idade."
                ),
                interpretation_en=(
                    "The first routine varicella dose is not yet due. "
                    "The timely schedule begins at age 15 months."
                ),
            )

        return _varicella_child_due_with_context_gates(
            assessment_date=assessment_date,
            dose_label="D1",
            disease_history_state=disease_history_state,
            pregnancy_status=pregnancy_status,
            special_condition_screen_state=(
                special_condition_screen_state
            ),
            interaction_context=interaction_context,
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
        )

    if valid_count != 1:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A contagem normalizada de doses válidas contra "
                "varicela não corresponde a uma série infantil "
                "interpretável automaticamente."
            ),
            interpretation_en=(
                "The normalized count of valid varicella doses does "
                "not correspond to a childhood series that can be "
                "interpreted automatically."
            ),
        )

    first_valid = varicella_history.get(
        "first_valid_component_date"
    )

    if not isinstance(
        first_valid,
        date,
    ):
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há uma dose válida registrada, mas sua data não está "
                "disponível para determinar D2 com segurança."
            ),
            interpretation_en=(
                "One valid dose is recorded, but its date is unavailable "
                "for safe determination of dose 2."
            ),
        )

    first_plus_3m = (
        _varicella_child_add_months_clamped(
            first_valid,
            3,
        )
    )

    if first_valid == age_15m:
        # Timely D1 preserves the timely D2 agenda at exact age 4.
        earliest_d2 = max(
            age_4y,
            first_plus_3m,
        )

        d2_timing_pt = (
            "Como D1 foi administrada na agenda oportuna aos "
            "15 meses, D2 permanece na agenda dos 4 anos."
        )

        d2_timing_en = (
            "Because dose 1 was administered on the timely "
            "15-month schedule, dose 2 remains scheduled for age 4."
        )

    else:
        # Federal catch-up language directs missed schedules to be
        # updated as soon as possible according to history while
        # respecting the child interval.
        earliest_d2 = first_plus_3m

        d2_timing_pt = (
            "Como D1 foi administrada em resgate após a agenda "
            "oportuna, D2 segue o intervalo de 3 meses-calendário "
            "sem aguardar automaticamente até os 4 anos."
        )

        d2_timing_en = (
            "Because dose 1 was given as catch-up after the timely "
            "schedule, dose 2 follows the three-calendar-month "
            "interval without automatically waiting until age 4."
        )

    if earliest_d2 >= age_7y:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "Há uma dose válida, porém a próxima data permitida "
                "após o intervalo de três meses-calendário cai no "
                "sétimo aniversário ou depois dele. O intervalo não "
                "deve ser comprimido e este núcleo não sintetiza "
                "resgate a partir dos 7 anos."
            ),
            interpretation_en=(
                "One valid dose is documented, but the next permitted "
                "date after the three-calendar-month interval falls on "
                "or after the seventh birthday. The interval must not "
                "be compressed, and this core does not synthesize "
                "age-7-plus rescue."
            ),
        )

    if assessment_date < earliest_d2:
        return _varicella_child_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=earliest_d2,
            interpretation_pt=(
                f"D2 ainda não é devida. {d2_timing_pt} "
                f"Primeira data válida: {earliest_d2.isoformat()}."
            ),
            interpretation_en=(
                f"Dose 2 is not yet due. {d2_timing_en} "
                f"First valid date: {earliest_d2.isoformat()}."
            ),
        )

    return _varicella_child_due_with_context_gates(
        assessment_date=assessment_date,
        dose_label="D2",
        disease_history_state=disease_history_state,
        pregnancy_status=pregnancy_status,
        special_condition_screen_state=(
            special_condition_screen_state
        ),
        interaction_context=interaction_context,
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
    )
DENGUE_TAKEDA_RULE_ID = (
    "PNI26-DNG4-TAKEDA-ROUTINE-001"
)

DENGUE_TAKEDA_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

DENGUE_TAKEDA_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf/"
    "@@download/file"
)

DENGUE_TAKEDA_PREGNANCY_STATES = {
    "not_screened",
    "pregnant",
    "not_pregnant",
    "unknown",
    "not_applicable",
}

DENGUE_TAKEDA_BREASTFEEDING_STATES = {
    "not_screened",
    "breastfeeding",
    "not_breastfeeding",
    "unknown",
    "not_applicable",
}

DENGUE_TAKEDA_SPECIAL_CONDITION_STATES = {
    "not_screened",
    "screened_none",
    "screened_special_condition_present",
}

DENGUE_TAKEDA_ADMINISTRATION_SAFETY_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}


def _dengue_takeda_add_months_clamped(
    value,
    months,
):
    from calendar import monthrange

    zero_based = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + zero_based // 12
    )

    month = (
        zero_based % 12
        + 1
    )

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def _dengue_takeda_result(
    *,
    assessment_date,
    decision,
    interpretation_pt,
    interpretation_en,
    recommended_date=None,
    history_required=False,
    missing_context=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
):
    return {
        "vaccine_key":
            "dengue",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            None,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                DENGUE_TAKEDA_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                DENGUE_TAKEDA_SOURCE_URL,

            "source_snapshot_date":
                DENGUE_TAKEDA_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt.strip(),

        "interpretation_en":
            interpretation_en.strip(),

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _dengue_takeda_due_context_gates(
    *,
    assessment_date,
    date_of_birth,
    dose_label,
    valid_d1_date,
    age_15y,
    clinical_timing_context,
    live_vaccine_interaction_context,
    pregnancy_status,
    breastfeeding_status,
    special_condition_screen_state,
    administration_safety_screen_state,
):
    from datetime import timedelta

    import schemas

    if clinical_timing_context is None:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_clinical_timing_context",
            ],
            interpretation_pt=(
                "A dose da vacina dengue Takeda estaria indicada pela "
                "cronologia vacinal, mas o contexto clínico de dengue, "
                "outras arboviroses e hemoderivados ainda precisa ser "
                "verificado."
            ),
            interpretation_en=(
                "The Takeda dengue dose would otherwise be indicated "
                "by vaccination chronology, but dengue, other "
                "arbovirus, and blood-product timing context must "
                "first be assessed."
            ),
        )

    if not isinstance(
        clinical_timing_context,
        schemas.PniDengueClinicalTimingContext,
    ):
        raise ValueError(
            "clinical_timing_context must be "
            "PniDengueClinicalTimingContext"
        )

    context = clinical_timing_context

    for onset in context.dengue_onset_dates:
        if onset > assessment_date:
            raise ValueError(
                "dengue onset date cannot follow assessment_date"
            )

        if onset < date_of_birth:
            raise ValueError(
                "dengue onset date cannot precede date_of_birth"
            )

    for event in context.other_arbovirus_events:
        if event.recovery_date > assessment_date:
            raise ValueError(
                "other-arbovirus recovery date cannot "
                "follow assessment_date"
            )

        if event.recovery_date < date_of_birth:
            raise ValueError(
                "other-arbovirus recovery date cannot "
                "precede date_of_birth"
            )

    treatment_end = (
        context
        .latest_relevant_blood_product_treatment_end_date
    )

    if (
        treatment_end is not None
        and treatment_end > assessment_date
    ):
        raise ValueError(
            "blood-product treatment-end date cannot "
            "follow assessment_date"
        )

    if (
        treatment_end is not None
        and treatment_end < date_of_birth
    ):
        raise ValueError(
            "blood-product treatment-end date cannot "
            "precede date_of_birth"
        )

    if (
        context.dengue_history_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_history_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas o histórico clínico de "
                "dengue ainda não foi rastreado."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but clinical "
                "dengue history has not yet been screened."
            ),
        )

    if (
        context.dengue_history_screen_state
        == "screened_dengue_history"
    ):
        if dose_label == "D1":
            latest_onset = max(
                context.dengue_onset_dates
            )

            disease_threshold = (
                _dengue_takeda_add_months_clamped(
                    latest_onset,
                    6,
                )
            )

            if disease_threshold >= age_15y:
                return _dengue_takeda_result(
                    assessment_date=assessment_date,
                    decision="not_applicable",
                    interpretation_pt=(
                        "Há dengue prévia documentada e o intervalo "
                        "recomendado de seis meses alcança ou ultrapassa "
                        "o 15º aniversário. Este núcleo não inicia uma "
                        "nova série Takeda fora da faixa 10–14 anos."
                    ),
                    interpretation_en=(
                        "Prior dengue is documented and the recommended "
                        "six-calendar-month interval reaches or passes "
                        "the fifteenth birthday. This core does not "
                        "initiate a new Takeda series outside ages "
                        "10–14."
                    ),
                )

            if assessment_date < disease_threshold:
                return _dengue_takeda_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    recommended_date=disease_threshold,
                    interpretation_pt=(
                        "D1 da vacina dengue Takeda ainda não é devida "
                        "porque o intervalo recomendado de seis meses-"
                        "calendário após dengue prévia ainda não foi "
                        "alcançado."
                    ),
                    interpretation_en=(
                        "Takeda dengue dose 1 is not yet due because "
                        "the recommended six-calendar-month interval "
                        "after prior dengue has not yet elapsed."
                    ),
                )

        else:
            assert valid_d1_date is not None

            post_d1_onsets = [
                onset
                for onset in context.dengue_onset_dates
                if onset >= valid_d1_date
            ]

            if post_d1_onsets:
                latest_post_d1 = max(
                    post_d1_onsets
                )

                disease_threshold = (
                    latest_post_d1
                    + timedelta(
                        days=30,
                    )
                )

                if assessment_date < disease_threshold:
                    return _dengue_takeda_result(
                        assessment_date=assessment_date,
                        decision="not_due_now",
                        recommended_date=disease_threshold,
                        interpretation_pt=(
                            "D2 da vacina dengue Takeda ainda não deve "
                            "ser administrada: é necessário respeitar "
                            "30 dias após o início do episódio de dengue "
                            "ocorrido depois de D1. A série não é "
                            "reiniciada."
                        ),
                        interpretation_en=(
                            "Takeda dengue dose 2 should not yet be "
                            "given: 30 days must elapse after onset of "
                            "the dengue episode occurring after dose 1. "
                            "The series is not restarted."
                        ),
                    )

    if (
        context.other_arbovirus_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_other_arbovirus_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas o histórico recente de "
                "febre amarela, chikungunya ou zika ainda precisa ser "
                "verificado."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but recent "
                "yellow fever, chikungunya, or Zika history must first "
                "be assessed."
            ),
        )

    if (
        context.other_arbovirus_screen_state
        == "screened_relevant_other_arbovirus_history"
    ):
        arbovirus_threshold = max(
            event.recovery_date
            + timedelta(
                days=30,
            )
            for event in context.other_arbovirus_events
        )

        if assessment_date < arbovirus_threshold:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=arbovirus_threshold,
                interpretation_pt=(
                    "A vacinação contra dengue deve aguardar 30 dias "
                    "após a recuperação da arbovirose relevante "
                    "documentada."
                ),
                interpretation_en=(
                    "Dengue vaccination should wait until 30 days "
                    "after documented recovery from the relevant "
                    "arboviral illness."
                ),
            )

    if (
        context.blood_product_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_blood_product_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas exposição recente a "
                "imunoglobulina, sangue, plasma ou hemoderivado ainda "
                "precisa ser verificada."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but recent "
                "immunoglobulin, blood, plasma, or blood-product "
                "exposure must first be assessed."
            ),
        )

    blood_minimum_applied = False

    if (
        context.blood_product_screen_state
        == "screened_relevant_blood_product_exposure"
    ):
        assert treatment_end is not None

        ordinary_threshold = (
            _dengue_takeda_add_months_clamped(
                treatment_end,
                3,
            )
        )

        minimum_threshold = (
            treatment_end
            + timedelta(
                days=42,
            )
        )

        if (
            context.minimum_6_week_interval_authorized
        ):
            if assessment_date < minimum_threshold:
                return _dengue_takeda_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    recommended_date=minimum_threshold,
                    minimum_interval_days=42,
                    minimum_interval_applied=True,
                    interpretation_pt=(
                        "Foi autorizada a utilização do intervalo "
                        "mínimo de seis semanas após o término do "
                        "tratamento com imunoglobulina/hemoderivado, "
                        "mas esse mínimo de 42 dias ainda não foi "
                        "alcançado."
                    ),
                    interpretation_en=(
                        "Use of the minimum six-week interval after "
                        "immunoglobulin/blood-product treatment was "
                        "authorized, but the 42-day minimum has not "
                        "yet elapsed."
                    ),
                )

            if assessment_date < ordinary_threshold:
                blood_minimum_applied = True

        elif assessment_date < ordinary_threshold:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=ordinary_threshold,
                interpretation_pt=(
                    "A vacinação contra dengue deve aguardar o "
                    "intervalo ordinário de três meses-calendário "
                    "após o término do tratamento com "
                    "imunoglobulina/hemoderivado."
                ),
                interpretation_en=(
                    "Dengue vaccination should wait for the ordinary "
                    "three-calendar-month interval after completion "
                    "of immunoglobulin/blood-product treatment."
                ),
            )

    if live_vaccine_interaction_context is None:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_live_vaccine_interaction_context",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas o histórico recente de "
                "outra vacina viva/atenuada ainda precisa ser "
                "verificado."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but recent "
                "other live/attenuated vaccine history must first be "
                "assessed."
            ),
        )

    if not isinstance(
        live_vaccine_interaction_context,
        schemas.PniDengueLiveVaccineInteractionContext,
    ):
        raise ValueError(
            "live_vaccine_interaction_context must be "
            "PniDengueLiveVaccineInteractionContext"
        )

    interaction = (
        live_vaccine_interaction_context
    )

    if (
        interaction.history_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "dengue_live_vaccine_history_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada, mas a triagem de outra "
                "vacina viva/atenuada está incompleta."
            ),
            interpretation_en=(
                "The dose would otherwise be indicated, but screening "
                "for another live/attenuated vaccine is incomplete."
            ),
        )

    interaction_threshold = None

    if (
        interaction.history_screen_state
        == "screened_relevant_live_vaccine_history"
    ):
        for event in interaction.recent_live_vaccine_events:
            if event.administration_date > assessment_date:
                raise ValueError(
                    "live-vaccine event cannot follow assessment_date"
                )

            if event.administration_date < date_of_birth:
                raise ValueError(
                    "live-vaccine event cannot precede date_of_birth"
                )

            elapsed = (
                assessment_date
                - event.administration_date
            ).days

            # Same-day administration is explicitly permitted.
            if elapsed == 0:
                continue

            threshold = (
                event.administration_date
                + timedelta(
                    days=30,
                )
            )

            if assessment_date < threshold:
                if (
                    interaction_threshold is None
                    or threshold > interaction_threshold
                ):
                    interaction_threshold = threshold

    if interaction_threshold is not None:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=interaction_threshold,
            interpretation_pt=(
                "A dose da vacina dengue Takeda deve aguardar "
                "30 dias após outra vacina viva/atenuada administrada "
                "em dia diferente."
            ),
            interpretation_en=(
                "The Takeda dengue dose should wait until 30 days "
                "after another live/attenuated vaccine given on a "
                "different day."
            ),
        )

    if pregnancy_status in {
        "not_screened",
        "unknown",
    }:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                "A dose estaria indicada hoje, mas o estado gestacional "
                "aplicável ainda precisa ser esclarecido."
            ),
            interpretation_en=(
                "The dose would otherwise be due today, but applicable "
                "pregnancy status must first be resolved."
            ),
        )

    if pregnancy_status == "pregnant":
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há gestação documentada. A vacina dengue atenuada "
                "não deve ser administrada automaticamente; seguir "
                "a via de contraindicação/avaliação clínica."
            ),
            interpretation_en=(
                "Pregnancy is documented. The attenuated dengue "
                "vaccine should not be administered automatically; "
                "follow the contraindication/clinical-review pathway."
            ),
        )

    if breastfeeding_status in {
        "not_screened",
        "unknown",
    }:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "breastfeeding_status",
            ],
            interpretation_pt=(
                "A dose estaria indicada hoje, mas o estado de "
                "amamentação aplicável ainda precisa ser esclarecido."
            ),
            interpretation_en=(
                "The dose would otherwise be due today, but applicable "
                "breastfeeding status must first be resolved."
            ),
        )

    if breastfeeding_status == "breastfeeding":
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há amamentação documentada. A vacina dengue atenuada "
                "não deve ser administrada automaticamente; seguir "
                "a via de contraindicação/avaliação clínica."
            ),
            interpretation_en=(
                "Breastfeeding is documented. The attenuated dengue "
                "vaccine should not be administered automatically; "
                "follow the contraindication/clinical-review pathway."
            ),
        )

    if (
        special_condition_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "special_condition_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada hoje, mas condições especiais "
                "relevantes para vacina atenuada ainda precisam ser "
                "rastreadas."
            ),
            interpretation_en=(
                "The dose would otherwise be due today, but special "
                "conditions relevant to an attenuated vaccine must "
                "first be screened."
            ),
        )

    if (
        special_condition_screen_state
        == "screened_special_condition_present"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há condição especial documentada, como possível "
                "imunodeficiência ou imunossupressão, em situação na "
                "qual a dose seria devida. Revisar a via clínica "
                "especial antes da administração."
            ),
            interpretation_en=(
                "A special condition such as possible immunodeficiency "
                "or immunosuppression is documented when the dose would "
                "otherwise be due. Review the special clinical pathway "
                "before administration."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="context_required",
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                "A dose estaria indicada hoje, mas a triagem de "
                "segurança para administração ainda não foi concluída."
            ),
            interpretation_en=(
                "The dose would otherwise be due today, but "
                "administration-safety screening has not yet been "
                "completed."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há preocupação de segurança documentada antes da "
                "administração, como reação grave prévia ou doença "
                "febril aguda moderada/grave. Revisar antes de vacinar."
            ),
            interpretation_en=(
                "A safety concern is documented before administration, "
                "such as a prior severe reaction or moderate/severe "
                "acute febrile illness. Review before vaccination."
            ),
        )

    return _dengue_takeda_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_date=assessment_date,
        minimum_interval_days=(
            42
            if blood_minimum_applied
            else None
        ),
        minimum_interval_applied=(
            blood_minimum_applied
        ),
        interpretation_pt=(
            f"Recomendar {dose_label} da vacina dengue Takeda agora. "
            "Este núcleo não substitui Takeda por Butantan e não "
            "infere elegibilidade de estratégias separadas."
        ),
        interpretation_en=(
            f"Recommend Takeda dengue {dose_label} now. "
            "This core does not substitute Butantan for Takeda and "
            "does not infer eligibility for separate strategies."
        ),
    )


def evaluate_pni_dengue_takeda_routine(
    *,
    assessment_date,
    date_of_birth,
    dengue_history,
    clinical_timing_context=None,
    live_vaccine_interaction_context=None,
    pregnancy_status="not_screened",
    breastfeeding_status="not_screened",
    special_condition_screen_state="not_screened",
    administration_safety_screen_state="not_screened",
):
    """
    Evaluate the national position-20 Takeda dengue routine layer.

    Only locked normalized product-sensitive dengue history is consumed.
    Butantan strategies and legacy Sanofi revaccination are not
    synthesized by this core.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if assessment_date < date_of_birth:
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        pregnancy_status
        not in DENGUE_TAKEDA_PREGNANCY_STATES
    ):
        raise ValueError(
            "invalid pregnancy_status"
        )

    if (
        breastfeeding_status
        not in DENGUE_TAKEDA_BREASTFEEDING_STATES
    ):
        raise ValueError(
            "invalid breastfeeding_status"
        )

    if (
        special_condition_screen_state
        not in DENGUE_TAKEDA_SPECIAL_CONDITION_STATES
    ):
        raise ValueError(
            "invalid special_condition_screen_state"
        )

    if (
        administration_safety_screen_state
        not in DENGUE_TAKEDA_ADMINISTRATION_SAFETY_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        dengue_history,
        dict,
    ):
        raise ValueError(
            "dengue_history must be normalized DNG4 history"
        )

    if (
        dengue_history.get(
            "model_id"
        )
        != "PNI26-DNG4-TAKEDA-HISTORY-001"
    ):
        raise ValueError(
            "dengue_history model_id is not recognized"
        )

    if (
        dengue_history.get(
            "target_family"
        )
        != "dengue_takeda_routine_history"
    ):
        raise ValueError(
            "dengue_history target_family is not recognized"
        )

    age_10y = dengue_history.get(
        "age_10y_date"
    )

    age_15y = dengue_history.get(
        "age_15y_date"
    )

    age_60y = dengue_history.get(
        "age_60y_date"
    )

    if not all(
        isinstance(
            value,
            date,
        )
        for value in (
            age_10y,
            age_15y,
            age_60y,
        )
    ):
        raise ValueError(
            "dengue_history age boundaries are incomplete"
        )

    expected_age_10y = (
        _dengue_takeda_add_months_clamped(
            date_of_birth,
            120,
        )
    )

    expected_age_15y = (
        _dengue_takeda_add_months_clamped(
            date_of_birth,
            180,
        )
    )

    expected_age_60y = (
        _dengue_takeda_add_months_clamped(
            date_of_birth,
            720,
        )
    )

    if (
        age_10y != expected_age_10y
        or age_15y != expected_age_15y
        or age_60y != expected_age_60y
    ):
        raise ValueError(
            "dengue_history does not match date_of_birth"
        )

    if (
        dengue_history.get(
            "source_history_incomplete"
        )
        is True
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico necessário para interpretar a vacinação "
                "contra dengue está incompleto, parcial ou contém "
                "evidência sem data exata."
            ),
            interpretation_en=(
                "The history required to interpret dengue vaccination "
                "is incomplete, partial, or contains evidence without "
                "an exact date."
            ),
        )

    if (
        dengue_history.get(
            "safe_for_routine_evaluation"
        )
        is not True
    ):
        reasons = list(
            dengue_history.get(
                "invalid_history_reasons"
            )
            or []
        )

        rendered = (
            ", ".join(
                reasons
            )
            if reasons
            else "unspecified_history_conflict"
        )

        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico de vacinação contra dengue contém "
                "evidência que exige revisão e não pode ser "
                "interpretada automaticamente pelo núcleo Takeda de "
                f"rotina. Motivos: {rendered}."
            ),
            interpretation_en=(
                "The dengue vaccination history contains evidence "
                "requiring review and cannot be interpreted "
                "automatically by the routine Takeda core. "
                f"Reasons: {rendered}."
            ),
        )

    if (
        dengue_history.get(
            "position20_series_complete"
        )
        is True
    ):
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            interpretation_pt=(
                "O esquema relevante para esta camada já está completo "
                "por duas doses válidas de Takeda ou por desfecho "
                "histórico de manejo de erro explicitamente aceito."
            ),
            interpretation_en=(
                "The series relevant to this layer is already complete "
                "through two valid Takeda doses or an explicitly "
                "accepted historical error-management outcome."
            ),
        )

    valid_count = int(
        dengue_history.get(
            "valid_takeda_dose_count"
        )
        or 0
    )

    valid_d1_date = dengue_history.get(
        "valid_takeda_d1_date"
    )

    if valid_count == 0:
        if assessment_date < age_10y:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=age_10y,
                interpretation_pt=(
                    "A iniciação de rotina com a vacina dengue Takeda "
                    "ainda não é devida nesta camada. A faixa nacional "
                    "inicia no 10º aniversário."
                ),
                interpretation_en=(
                    "Routine initiation with Takeda dengue vaccine is "
                    "not yet due in this layer. The national target "
                    "window begins on the tenth birthday."
                ),
            )

        if assessment_date >= age_15y:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_applicable",
                interpretation_pt=(
                    "A partir do 15º aniversário este núcleo não inicia "
                    "uma nova série Takeda. Estratégias com Butantan ou "
                    "outras populações são avaliadas separadamente."
                ),
                interpretation_en=(
                    "From the fifteenth birthday onward this core does "
                    "not initiate a new Takeda series. Butantan "
                    "strategies and other populations are evaluated "
                    "separately."
                ),
            )

        dose_label = "D1"

    elif valid_count == 1:
        if not isinstance(
            valid_d1_date,
            date,
        ):
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há uma dose Takeda válida registrada, mas sua data "
                    "não está disponível para determinar D2 com "
                    "segurança."
                ),
                interpretation_en=(
                    "One valid Takeda dose is recorded, but its date "
                    "is unavailable for safe determination of dose 2."
                ),
            )

        next_history_date = dengue_history.get(
            "next_corrective_takeda_date"
        )

        if not isinstance(
            next_history_date,
            date,
        ):
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "Há D1 válida, mas a próxima data Takeda permitida "
                    "não pôde ser determinada pelo histórico "
                    "normalizado."
                ),
                interpretation_en=(
                    "A valid dose 1 is documented, but the next "
                    "permitted Takeda date could not be determined "
                    "from normalized history."
                ),
            )

        public_completion_date = max(
            age_10y,
            next_history_date,
        )

        if assessment_date < public_completion_date:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=public_completion_date,
                interpretation_pt=(
                    "D2 da vacina dengue Takeda ainda não é devida "
                    "nesta camada. A data combina a abertura da faixa "
                    "pública aos 10 anos com a cronologia válida do "
                    "esquema já iniciado."
                ),
                interpretation_en=(
                    "Takeda dengue dose 2 is not yet due in this layer. "
                    "The date combines opening of the public target "
                    "window at age 10 with valid chronology of the "
                    "already-started series."
                ),
            )

        if assessment_date >= age_60y:
            return _dengue_takeda_result(
                assessment_date=assessment_date,
                decision="not_applicable",
                interpretation_pt=(
                    "Há uma série Takeda previamente iniciada, mas esta "
                    "camada não automatiza sua conclusão a partir do "
                    "60º aniversário."
                ),
                interpretation_en=(
                    "A Takeda series was previously started, but this "
                    "layer does not automate its completion from the "
                    "sixtieth birthday onward."
                ),
            )

        dose_label = "D2"

    else:
        return _dengue_takeda_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "A contagem normalizada de doses Takeda não corresponde "
                "a uma série interpretável automaticamente."
            ),
            interpretation_en=(
                "The normalized Takeda dose count does not correspond "
                "to a series that can be interpreted automatically."
            ),
        )

    return _dengue_takeda_due_context_gates(
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
        dose_label=dose_label,
        valid_d1_date=(
            valid_d1_date
            if dose_label == "D2"
            else None
        ),
        age_15y=age_15y,
        clinical_timing_context=clinical_timing_context,
        live_vaccine_interaction_context=(
            live_vaccine_interaction_context
        ),
        pregnancy_status=pregnancy_status,
        breastfeeding_status=breastfeeding_status,
        special_condition_screen_state=(
            special_condition_screen_state
        ),
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
    )
DT_ROUTINE_RULE_ID = (
    "PNI26-DT-ROUTINE-001"
)

DT_ROUTINE_SOURCE_SNAPSHOT_DATE = date(
    2026,
    9,
    12,
)

DT_ROUTINE_SOURCE_URL = (
    "https://www.gov.br/saude/pt-br/vacinacao/"
    "publicacoes/instrucao-normativa-que-instrui-o-"
    "calendario-nacional-de-vacinacao-2026.pdf/"
    "@@download/file"
)

DT_PREGNANCY_STATES = {
    "not_screened",
    "pregnant",
    "not_pregnant",
    "unknown",
    "not_applicable",
}

DT_DTPA_PRIORITY_OCCUPATION_STATES = {
    "not_screened",
    "screened_no_dtpa_priority_occupation",
    "screened_dtpa_priority_occupation",
}

DT_EXPOSURE_RISK_STATES = {
    "not_screened",
    "screened_no_relevant_exposure",
    "screened_relevant_diphtheria_or_tetanus_exposure",
}

DT_ADMINISTRATION_SAFETY_STATES = {
    "not_screened",
    "screened_no_concern",
    "screened_concern",
}


def _dt_add_years_clamped(
    value,
    years,
):
    from calendar import monthrange

    target_year = (
        value.year
        + years
    )

    target_day = min(
        value.day,
        monthrange(
            target_year,
            value.month,
        )[1],
    )

    return date(
        target_year,
        value.month,
        target_day,
    )


def _dt_greedy_subsequence(
    dates,
    minimum_spacing_days,
):
    counted = []

    for value in sorted(
        dates
    ):
        if not counted:
            counted.append(
                value
            )
            continue

        elapsed = (
            value
            - counted[
                -1
            ]
        ).days

        if (
            elapsed
            >= minimum_spacing_days
        ):
            counted.append(
                value
            )

    return counted


def _derive_dt_schedule_history(
    *,
    date_of_birth,
    antigen_history,
):
    import schemas

    try:
        validated = (
            schemas
            .PniAntigenHistorySummary
            .model_validate(
                antigen_history
            )
        )

    except Exception as exc:
        raise ValueError(
            "antigen_history must satisfy "
            "PniAntigenHistorySummary"
        ) from exc

    data = validated.model_dump(
        mode="python"
    )

    target_antigens = set(
        data[
            "target_antigens"
        ]
    )

    if target_antigens != {
        "diphtheria_toxoid",
        "tetanus_toxoid",
    }:
        raise ValueError(
            "antigen_history must target diphtheria "
            "and tetanus toxoids"
        )

    exposures = list(
        data[
            "exposures"
        ]
    )

    physical_dates = []

    special_pathway_exposure_present = False

    for exposure in exposures:
        exposure_date = exposure[
            "administration_date"
        ]

        if not isinstance(
            exposure_date,
            date,
        ):
            raise ValueError(
                "toxoid exposure date must be a date"
            )

        if exposure_date < date_of_birth:
            raise ValueError(
                "toxoid exposure cannot precede date_of_birth"
            )

        components = set(
            exposure[
                "antigen_components"
            ]
        )

        if not {
            "diphtheria_toxoid",
            "tetanus_toxoid",
        }.issubset(
            components
        ):
            raise ValueError(
                "normalized toxoid exposure lacks required D/T components"
            )

        physical_dates.append(
            exposure_date
        )

        if exposure.get(
            "special_pathway_product"
        ):
            special_pathway_exposure_present = True

    physical_dates.sort()

    routine_primary_dates = (
        _dt_greedy_subsequence(
            physical_dates,
            60,
        )
    )

    minimum_possible_primary_dates = (
        _dt_greedy_subsequence(
            physical_dates,
            30,
        )
    )

    routine_primary_count = len(
        routine_primary_dates
    )

    minimum_possible_primary_count = len(
        minimum_possible_primary_dates
    )

    primary_series_complete_proven = (
        routine_primary_count
        >= 3
    )

    historical_interval_ambiguity = (
        not primary_series_complete_proven
        and (
            routine_primary_count
            != minimum_possible_primary_count
        )
    )

    latest_counted_primary_date = (
        routine_primary_dates[
            -1
        ]
        if routine_primary_dates
        else None
    )

    latest_physical_dt_exposure_date = (
        physical_dates[
            -1
        ]
        if physical_dates
        else None
    )

    return {
        "normalized_history":
            data,

        "physical_dates":
            physical_dates,

        "routine_primary_dates":
            routine_primary_dates,

        "minimum_possible_primary_dates":
            minimum_possible_primary_dates,

        "routine_primary_count":
            routine_primary_count,

        "minimum_possible_primary_count":
            minimum_possible_primary_count,

        "primary_series_complete_proven":
            primary_series_complete_proven,

        "historical_interval_ambiguity":
            historical_interval_ambiguity,

        "latest_counted_primary_date":
            latest_counted_primary_date,

        "latest_physical_dt_exposure_date":
            latest_physical_dt_exposure_date,

        "special_pathway_exposure_present":
            special_pathway_exposure_present,
    }


def _dt_routine_result(
    *,
    assessment_date,
    decision,
    interpretation_pt,
    interpretation_en,
    recommended_date=None,
    recommended_interval_days=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
    history_required=False,
    missing_context=None,
):
    return {
        "vaccine_key":
            "dt",

        "layer":
            "routine",

        "decision":
            decision,

        "assessment_date":
            assessment_date,

        "recommended_date":
            recommended_date,

        "recommended_interval_days":
            recommended_interval_days,

        "minimum_interval_days":
            minimum_interval_days,

        "minimum_interval_applied":
            minimum_interval_applied,

        "history_required":
            history_required,

        "missing_context":
            list(
                missing_context
                or []
            ),

        "provenance": {
            "rule_id":
                DT_ROUTINE_RULE_ID,

            "authority":
                "Ministério da Saúde / SVSA / DPNI",

            "authority_rank":
                1,

            "source_title": (
                "Instrução Normativa do Calendário "
                "Nacional de Vacinação 2026"
            ),

            "source_url":
                DT_ROUTINE_SOURCE_URL,

            "source_snapshot_date":
                DT_ROUTINE_SOURCE_SNAPSHOT_DATE,

            "rule_effective_from":
                None,

            "rule_effective_until":
                None,
        },

        "interpretation_pt":
            interpretation_pt.strip(),

        "interpretation_en":
            interpretation_en.strip(),

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }


def _dt_due_time_redirect_and_safety_gates(
    *,
    assessment_date,
    pregnancy_status,
    dtpa_priority_occupation_state,
    administration_safety_screen_state,
    dose_description_pt,
    dose_description_en,
    recommended_interval_days=None,
    minimum_interval_days=None,
    minimum_interval_applied=False,
):
    if pregnancy_status in {
        "not_screened",
        "unknown",
    }:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="context_required",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            missing_context=[
                "pregnancy_status",
            ],
            interpretation_pt=(
                f"{dose_description_pt} estaria indicada, mas o "
                "estado gestacional aplicável ainda precisa ser "
                "esclarecido para coordenar dT com a via de dTpa."
            ),
            interpretation_en=(
                f"{dose_description_en} would otherwise be indicated, "
                "but applicable pregnancy status must first be "
                "resolved so dT can be coordinated with the dTpa "
                "pathway."
            ),
        )

    if pregnancy_status == "pregnant":
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                "Há gestação documentada e uma dose contendo "
                "difteria/tétano estaria indicada pelo calendário. "
                "A dT não é tratada aqui como contraindicada; é "
                "necessário coordenar a conclusão da série dT com a "
                "dose de dTpa própria da gestação."
            ),
            interpretation_en=(
                "Pregnancy is documented and a diphtheria/tetanus-"
                "containing dose would otherwise be due. dT is not "
                "treated here as contraindicated; completion of the "
                "dT series must be coordinated with the pregnancy-"
                "specific dTpa dose."
            ),
        )

    if (
        dtpa_priority_occupation_state
        == "not_screened"
    ):
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="context_required",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            missing_context=[
                "dtpa_priority_occupation_state",
            ],
            interpretation_pt=(
                f"{dose_description_pt} estaria indicada, mas ainda "
                "é necessário verificar se existe uma ocupação/grupo "
                "com recomendação específica de dTpa."
            ),
            interpretation_en=(
                f"{dose_description_en} would otherwise be indicated, "
                "but it is still necessary to determine whether a "
                "source-defined occupation/group has a specific dTpa "
                "recommendation."
            ),
        )

    if (
        dtpa_priority_occupation_state
        == "screened_dtpa_priority_occupation"
    ):
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                "Há grupo ocupacional/prioritário com recomendação "
                "específica de dTpa. Este núcleo geral de dT não "
                "inventa a sequência ocupacional de dTpa; revisar a "
                "via apropriada."
            ),
            interpretation_en=(
                "A source-defined occupational/priority group with a "
                "specific dTpa recommendation is documented. This "
                "general dT core does not invent the occupational dTpa "
                "sequence; review the appropriate pathway."
            ),
        )

    if (
        administration_safety_screen_state
        == "not_screened"
    ):
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="context_required",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            missing_context=[
                "administration_safety_screen_state",
            ],
            interpretation_pt=(
                f"{dose_description_pt} estaria indicada, mas a "
                "triagem de segurança antes da administração ainda "
                "não foi concluída."
            ),
            interpretation_en=(
                f"{dose_description_en} would otherwise be indicated, "
                "but administration-safety screening has not yet been "
                "completed."
            ),
        )

    if (
        administration_safety_screen_state
        == "screened_concern"
    ):
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_interval_applied
            ),
            interpretation_pt=(
                "Há preocupação de segurança documentada antes da "
                "administração de dT — por exemplo reação tipo Arthus, "
                "hipersensibilidade, evento neurológico relevante ou "
                "doença febril aguda moderada/grave. Revisar antes de "
                "vacinar."
            ),
            interpretation_en=(
                "A safety concern is documented before dT "
                "administration—for example an Arthus-type reaction, "
                "hypersensitivity, a relevant neurological event, or "
                "moderate/severe acute febrile illness. Review before "
                "vaccination."
            ),
        )

    return None


def evaluate_pni_dt_routine(
    *,
    assessment_date,
    date_of_birth,
    antigen_history,
    pregnancy_status="not_screened",
    dtpa_priority_occupation_state="not_screened",
    exposure_risk_state="not_screened",
    administration_safety_screen_state="not_screened",
    exceptional_minimum_interval_authorized=False,
):
    """
    Evaluate Brazil PNI 2026 position-21 dT routine schedule.

    The evaluator consumes the locked normalized cross-vaccine
    diphtheria/tetanus toxoid history. It does not parse raw vaccine
    histories and does not duplicate maternal or occupational dTpa
    sequencing.
    """

    from datetime import timedelta

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if assessment_date < date_of_birth:
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if pregnancy_status not in DT_PREGNANCY_STATES:
        raise ValueError(
            "invalid pregnancy_status"
        )

    if (
        dtpa_priority_occupation_state
        not in DT_DTPA_PRIORITY_OCCUPATION_STATES
    ):
        raise ValueError(
            "invalid dtpa_priority_occupation_state"
        )

    if exposure_risk_state not in DT_EXPOSURE_RISK_STATES:
        raise ValueError(
            "invalid exposure_risk_state"
        )

    if (
        administration_safety_screen_state
        not in DT_ADMINISTRATION_SAFETY_STATES
    ):
        raise ValueError(
            "invalid administration_safety_screen_state"
        )

    if not isinstance(
        exceptional_minimum_interval_authorized,
        bool,
    ):
        raise ValueError(
            "exceptional_minimum_interval_authorized must be bool"
        )

    derived = _derive_dt_schedule_history(
        date_of_birth=date_of_birth,
        antigen_history=antigen_history,
    )

    normalized = derived[
        "normalized_history"
    ]

    if normalized[
        "source_history_incomplete"
    ]:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico reconciliado de vacinas contendo toxoides "
                "diftérico e tetânico está incompleto ou desconhecido."
            ),
            interpretation_en=(
                "The reconciled history of vaccines containing "
                "diphtheria and tetanus toxoids is incomplete or "
                "unknown."
            ),
        )

    if (
        normalized[
            "safe_for_interval_evaluation"
        ]
        is not True
        or normalized[
            "safe_for_basic_series_count"
        ]
        is not True
    ):
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="history_required",
            history_required=True,
            interpretation_pt=(
                "O histórico D/T contém ambiguidade de mesma data, "
                "produto não mapeado ou outra limitação que impede "
                "contagem/intervalo seguros."
            ),
            interpretation_en=(
                "The D/T history contains same-day ambiguity, an "
                "unmapped product, or another limitation preventing "
                "safe counting or interval evaluation."
            ),
        )

    if derived[
        "special_pathway_exposure_present"
    ]:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "Há exposição D/T proveniente de produto explicitamente "
                "marcado como via especial. Este núcleo de rotina não "
                "converte automaticamente essa evidência em cronologia "
                "geral de dT."
            ),
            interpretation_en=(
                "A D/T exposure from a product explicitly marked as a "
                "special pathway is present. This routine core does not "
                "automatically convert that evidence into general dT "
                "schedule chronology."
            ),
        )

    age_7y = _dt_add_years_clamped(
        date_of_birth,
        7,
    )

    if assessment_date < age_7y:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="not_applicable",
            interpretation_pt=(
                "A camada de rotina da dupla adulto (dT) inicia aos "
                "7 anos. Antes disso, utilizar as regras pediátricas "
                "apropriadas."
            ),
            interpretation_en=(
                "The adult-type diphtheria-tetanus (dT) routine layer "
                "starts at age 7. Before then, use the appropriate "
                "paediatric schedule rules."
            ),
        )

    if derived[
        "historical_interval_ambiguity"
    ]:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="special_pathway_review",
            interpretation_pt=(
                "O histórico contém intervalo(s) de 30–59 dias que "
                "alteram a posição possível na série básica, mas não "
                "há prova de autorização histórica para o intervalo "
                "mínimo excepcional. Revisar o esquema."
            ),
            interpretation_en=(
                "The history contains one or more 30–59-day intervals "
                "that alter the possible basic-series position, but "
                "there is no evidence that the exceptional historical "
                "minimum interval was authorised. Review the series."
            ),
        )

    routine_count = derived[
        "routine_primary_count"
    ]

    latest_physical = derived[
        "latest_physical_dt_exposure_date"
    ]

    if not derived[
        "primary_series_complete_proven"
    ]:
        if routine_count > 2:
            return _dt_routine_result(
                assessment_date=assessment_date,
                decision="special_pathway_review",
                interpretation_pt=(
                    "A cronologia da série básica D/T não pôde ser "
                    "interpretada de forma consistente."
                ),
                interpretation_en=(
                    "The D/T basic-series chronology could not be "
                    "interpreted consistently."
                ),
            )

        dose_position = (
            routine_count
            + 1
        )

        if routine_count == 0:
            due_date = age_7y

            if assessment_date < due_date:
                return _dt_routine_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    recommended_date=due_date,
                    interpretation_pt=(
                        "A primeira dose da série básica com dT ainda "
                        "não é devida antes dos 7 anos."
                    ),
                    interpretation_en=(
                        "The first dT basic-series dose is not yet due "
                        "before age 7."
                    ),
                )

            minimum_applied = False
            recommended_interval_days = None
            minimum_interval_days = None

        else:
            last_counted = derived[
                "latest_counted_primary_date"
            ]

            assert isinstance(
                last_counted,
                date,
            )

            assert isinstance(
                latest_physical,
                date,
            )

            absolute_physical_floor = (
                latest_physical
                + timedelta(
                    days=30,
                )
            )

            ordinary_due = max(
                last_counted
                + timedelta(
                    days=60,
                ),
                absolute_physical_floor,
            )

            exceptional_due = max(
                last_counted
                + timedelta(
                    days=30,
                ),
                absolute_physical_floor,
            )

            if (
                exceptional_minimum_interval_authorized
            ):
                due_date = exceptional_due

                minimum_applied = True

                recommended_interval_days = 60
                minimum_interval_days = 30

            else:
                due_date = ordinary_due

                minimum_applied = False

                recommended_interval_days = 60
                minimum_interval_days = None

            if assessment_date < due_date:
                return _dt_routine_result(
                    assessment_date=assessment_date,
                    decision="not_due_now",
                    recommended_date=due_date,
                    recommended_interval_days=(
                        recommended_interval_days
                    ),
                    minimum_interval_days=(
                        minimum_interval_days
                    ),
                    minimum_interval_applied=(
                        minimum_applied
                    ),
                    interpretation_pt=(
                        f"A dose {dose_position} da série básica com "
                        "dT ainda não é devida. O calendário respeita "
                        "o intervalo recomendado de 60 dias ou, quando "
                        "explicitamente autorizado, o mínimo de "
                        "30 dias, sem ignorar exposição D/T física "
                        "mais recente."
                    ),
                    interpretation_en=(
                        f"Basic-series dT dose {dose_position} is not "
                        "yet due. The schedule respects the recommended "
                        "60-day interval or, when explicitly authorised, "
                        "the 30-day minimum without ignoring a more "
                        "recent physical D/T exposure."
                    ),
                )

        gate = _dt_due_time_redirect_and_safety_gates(
            assessment_date=assessment_date,
            pregnancy_status=pregnancy_status,
            dtpa_priority_occupation_state=(
                dtpa_priority_occupation_state
            ),
            administration_safety_screen_state=(
                administration_safety_screen_state
            ),
            dose_description_pt=(
                f"A dose {dose_position} da série básica com dT"
            ),
            dose_description_en=(
                f"Basic-series dT dose {dose_position}"
            ),
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_applied
            ),
        )

        if gate is not None:
            return gate

        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="recommend_now",
            recommended_date=assessment_date,
            recommended_interval_days=(
                recommended_interval_days
            ),
            minimum_interval_days=(
                minimum_interval_days
            ),
            minimum_interval_applied=(
                minimum_applied
            ),
            interpretation_pt=(
                f"Recomendar agora a dose {dose_position} da série "
                "básica com vacina dT. O esquema não é reiniciado por "
                "atraso."
            ),
            interpretation_en=(
                f"Recommend basic-series dT dose {dose_position} now. "
                "The series is not restarted because of delay."
            ),
        )

    assert isinstance(
        latest_physical,
        date,
    )

    booster_anchor = latest_physical

    five_year_date = _dt_add_years_clamped(
        booster_anchor,
        5,
    )

    ten_year_date = _dt_add_years_clamped(
        booster_anchor,
        10,
    )

    if assessment_date < five_year_date:
        return _dt_routine_result(
            assessment_date=assessment_date,
            decision="not_due_now",
            recommended_date=five_year_date,
            interpretation_pt=(
                "A série básica D/T está completa e ainda não foram "
                "alcançados 5 anos desde a última dose contendo "
                "toxoides diftérico e tetânico. Nenhum reforço é "
                "indicado por esta camada hoje."
            ),
            interpretation_en=(
                "The D/T basic series is complete and 5 years have "
                "not yet elapsed since the last diphtheria/tetanus-"
                "containing dose. No booster is indicated by this "
                "layer today."
            ),
        )

    booster_due = False

    if assessment_date < ten_year_date:
        if exposure_risk_state == "not_screened":
            return _dt_routine_result(
                assessment_date=assessment_date,
                decision="context_required",
                missing_context=[
                    "exposure_risk_state",
                ],
                interpretation_pt=(
                    "A série básica está completa e transcorreram entre "
                    "5 e menos de 10 anos desde a última dose D/T. É "
                    "necessário verificar exposição relevante a "
                    "difteria ou tétano antes de decidir sobre reforço "
                    "antecipado."
                ),
                interpretation_en=(
                    "The basic series is complete and between 5 and "
                    "less than 10 years have elapsed since the last "
                    "D/T-containing dose. Relevant diphtheria or "
                    "tetanus exposure must be assessed before deciding "
                    "on an accelerated booster."
                ),
            )

        if (
            exposure_risk_state
            == "screened_no_relevant_exposure"
        ):
            return _dt_routine_result(
                assessment_date=assessment_date,
                decision="not_due_now",
                recommended_date=ten_year_date,
                interpretation_pt=(
                    "Não há exposição relevante documentada. O próximo "
                    "reforço de rotina com dT é aos 10 anos-calendário "
                    "da última dose contendo D/T."
                ),
                interpretation_en=(
                    "No relevant exposure is documented. The next "
                    "routine dT booster is due 10 calendar years after "
                    "the last D/T-containing dose."
                ),
            )

        assert (
            exposure_risk_state
            == "screened_relevant_diphtheria_or_tetanus_exposure"
        )

        booster_due = True

    else:
        booster_due = True

    assert booster_due

    gate = _dt_due_time_redirect_and_safety_gates(
        assessment_date=assessment_date,
        pregnancy_status=pregnancy_status,
        dtpa_priority_occupation_state=(
            dtpa_priority_occupation_state
        ),
        administration_safety_screen_state=(
            administration_safety_screen_state
        ),
        dose_description_pt=(
            "O reforço com dT"
        ),
        dose_description_en=(
            "The dT booster"
        ),
    )

    if gate is not None:
        return gate

    if assessment_date >= ten_year_date:
        pt_reason = (
            "foram alcançados 10 anos-calendário desde a última "
            "dose contendo toxoides diftérico e tetânico"
        )

        en_reason = (
            "10 calendar years have elapsed since the last "
            "diphtheria/tetanus-containing dose"
        )

    else:
        pt_reason = (
            "há exposição relevante documentada e foram alcançados "
            "5 anos-calendário desde a última dose contendo D/T"
        )

        en_reason = (
            "relevant exposure is documented and 5 calendar years "
            "have elapsed since the last D/T-containing dose"
        )

    return _dt_routine_result(
        assessment_date=assessment_date,
        decision="recommend_now",
        recommended_date=assessment_date,
        interpretation_pt=(
            "Recomendar reforço com vacina dT agora porque "
            f"{pt_reason}."
        ),
        interpretation_en=(
            "Recommend a dT booster now because "
            f"{en_reason}."
        ),
    )
