from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LivenessResponse(BaseModel):
    status: Literal["ok"]
    api_version: str


class ReadinessResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
    assets: Literal["ok"]
    api_version: str
    database_revision: str
    sae_enabled: bool
    clinical_content: Literal["certified"]
    clinical_content_manifest_sha256: str


# Backwards import compatibility for integrations that referenced the old schema name.
HealthResponse = ReadinessResponse


class ClassificationLinkOut(ORMModel):
    classification: Literal["NIC", "NOC"]
    code: str
    label_en: str
    label_pt: str
    edition: str
    role: Literal["primary", "alternative"]
    applicability: str
    applicability_en: str
    applicability_pt: str
    confidence: str
    verification_status: str
    source_language: str
    source_reference: str
    source_page: str | None = None
    review_date: date
    notes: str | None = None


class SAEDiagnosticOut(ORMModel):
    id: int
    code: str
    description_en: str
    description_pt: str
    intervention_en: str
    intervention_pt: str
    outcome_en: str
    outcome_pt: str
    mapping_status: str
    mapping_methodology: str
    mapping_review_date: date | None = None
    mapping_notes: str | None = None
    nanda_edition: str | None = None
    nanda_domain: str | None = None
    nanda_class: str | None = None
    nanda_source_page: str | None = None
    nanda_pdf_page: str | None = None
    nic_edition: str | None = None
    nic_code: str | None = None
    nic_label_en: str | None = None
    nic_label_pt: str | None = None
    noc_edition: str | None = None
    noc_code: str | None = None
    noc_label_en: str | None = None
    noc_label_pt: str | None = None
    mapping_confidence: str | None = None
    mapping_reference: str | None = None
    mapping_rationale: str | None = None
    nic_links: list[ClassificationLinkOut] = Field(default_factory=list)
    noc_links: list[ClassificationLinkOut] = Field(default_factory=list)


class SAEMetadataResponse(BaseModel):
    record_count: int = Field(ge=0)
    link_count: int = Field(ge=0)
    diagnoses_with_contextual_alternatives: int = Field(ge=0)
    mapping_model: str
    code_format: str
    mapping_status: str
    mapping_methodology: str
    nanda_reference: str
    nic_reference: str
    noc_reference: str
    confidence_counts: dict[str, int]
    licensing_profile: str
    licensing_note: str
    english_variant: Literal["en-GB"]
    portuguese_variant: Literal["pt-BR"]


class SAESearchResponse(BaseModel):
    query: str
    limit: int
    offset: int
    returned: int
    items: list[SAEDiagnosticOut]


class ClassificationIndexItem(BaseModel):
    code: str
    label_en: str
    label_pt: str
    edition: str
    mapped_diagnoses: int = Field(ge=0)


class ClassificationIndexResponse(BaseModel):
    classification: Literal["NIC", "NOC"]
    returned: int
    items: list[ClassificationIndexItem]


class ClassificationLinkedDiagnosis(BaseModel):
    nanda_code: str
    description_en: str
    description_pt: str
    role: Literal["primary", "alternative"]
    applicability: str
    applicability_en: str
    applicability_pt: str
    confidence: str
    verification_status: str


class ClassificationMappingResponse(BaseModel):
    classification: Literal["NIC", "NOC"]
    code: str
    label_en: str
    label_pt: str
    edition: str
    mapped_diagnoses: int = Field(ge=0)
    linked_diagnoses: list[ClassificationLinkedDiagnosis]


PolicyStatus = Literal["current", "superseded", "historical", "needs_review"]


class PolicyOut(ORMModel):
    id: int
    policy_name: str
    directive: str
    target_demographic: str
    clinical_guideline: str
    source_title: str
    source_url: HttpUrl
    source_page: str | None = None
    source_publication_date: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    last_clinical_review: date
    source_version: str | None = None
    status: PolicyStatus
    review_notes: str | None = None
    evidence_level: str


class PolicyListResponse(BaseModel):
    policy_name: str
    returned: int
    items: list[PolicyOut]


class PolicyIndexItem(BaseModel):
    policy_name: str = Field(min_length=1, max_length=20)
    directives: int = Field(ge=0)


class PolicyIndexResponse(BaseModel):
    items: list[PolicyIndexItem]


# ---------------------------------------------------------------------------
# v2 clinical-tool language/provenance contract.
# API_VERSION remains 1.4.5 until final v2.0.0 qualification.
# ---------------------------------------------------------------------------

TranslationStatus = Literal[
    "official_original",
    "official_translation",
    "validated_translation",
    "informative_translation",
    "local_translation",
    "local_translation_with_disclaimer_required",
    "not_applicable",
]


BrazilApplicabilityStatus = Literal[
    "national_standard",
    "national_variant",
    "validated_brazilian_adaptation",
    "complementary_brazil_guidance",
    "no_national_variant_identified",
    "not_applicable",
]


BrazilReviewStatus = Literal[
    "pass",
    "remediation_required",
    "metadata_remediation_required",
    "pending",
]


class ClinicalToolMetadataResponse(BaseModel):
    id: str
    name_pt: str
    name_en: str
    description_pt: str
    description_en: str

    aliases_pt: list[str]
    aliases_en: list[str]

    publisher: str
    source_title: str
    source_version: str
    source_url: HttpUrl

    source_language: str
    canonical_language: str

    translation_status_pt: TranslationStatus
    translation_status_en: TranslationStatus

    translation_disclaimer_required: bool
    translation_disclaimer_source_url: HttpUrl | None = None

    translation_note_pt: str | None = None
    translation_note_en: str | None = None

    population_pt: str
    population_en: str

    limitations_pt: list[str]
    limitations_en: list[str]

    licensing_note_pt: str
    licensing_note_en: str

    clinical_review_date: date
    offline_capable: bool

    # v2 Brazil clinical-harmonization contract.
    # Optional while legacy/v2 tools are remediated sequentially.
    brazil_applicability_status: BrazilApplicabilityStatus | None = None

    brazil_review_date: date | None = None
    brazil_authority: str | None = None
    brazil_source_title: str | None = None
    brazil_source_url: HttpUrl | None = None
    brazil_document_or_portaria: str | None = None

    brazil_scope_pt: str | None = None
    brazil_scope_en: str | None = None

    brazil_differs_from_international: bool | None = None

    brazil_difference_notes_pt: str | None = None
    brazil_difference_notes_en: str | None = None

    final_brazil_review_status: BrazilReviewStatus | None = None



NEWS2Consciousness = Literal[
    "alert",
    "new_confusion",
    "voice",
    "pain",
    "unresponsive",
]


class NEWS2Input(BaseModel):
    respiration_rate: int = Field(gt=0)
    spo2: int = Field(ge=1, le=100)

    spo2_scale: Literal[1, 2] = 1
    scale2_prescribed: bool = False
    supplemental_oxygen: bool = False

    systolic_bp: int = Field(gt=0)
    pulse: int = Field(gt=0)

    consciousness: NEWS2Consciousness

    temperature: float = Field(
        ge=20.0,
        le=50.0,
    )


class NEWS2Components(BaseModel):
    respiration_rate: int = Field(ge=0, le=3)
    spo2: int = Field(ge=0, le=3)
    supplemental_oxygen: int = Field(ge=0, le=2)
    systolic_bp: int = Field(ge=0, le=3)
    pulse: int = Field(ge=0, le=3)
    consciousness: int = Field(ge=0, le=3)
    temperature: int = Field(ge=0, le=3)


class NEWS2Response(BaseModel):
    tool: Literal["news2"]

    total: int = Field(
        ge=0,
        le=19,
    )

    components: NEWS2Components

    spo2_scale: Literal[1, 2]
    scale2_prescribed: bool
    supplemental_oxygen: bool

    single_parameter_red_score: bool

    aggregate_band: Literal[
        "zero",
        "low",
        "medium",
        "high",
    ]

    aggregate_label_pt: str
    aggregate_label_en: str

    trigger_code: Literal[
        "zero",
        "low",
        "single_red",
        "medium",
        "high",
    ]

    trigger_label_pt: str
    trigger_label_en: str

    monitoring_code: Literal[
        "minimum_12_hourly",
        "minimum_4_to_6_hourly",
        "minimum_hourly",
        "continuous",
    ]

    monitoring_pt: str
    monitoring_en: str

    response_pt: str
    response_en: str

    clinical_judgement_note_pt: str
    clinical_judgement_note_en: str


# ---------------------------------------------------------------------------
# v2 Item 2 — adult renal tools.
# ---------------------------------------------------------------------------

RenalSex = Literal[
    "female",
    "male",
]

CreatinineUnit = Literal[
    "mg/dL",
    "umol/L",
]

ACRUnit = Literal[
    "mg/g",
    "mg/mmol",
]


class EGFRInput(BaseModel):
    age_years: int = Field(
        ge=18,
        le=120,
    )
    sex: RenalSex
    serum_creatinine: float = Field(gt=0)
    creatinine_unit: CreatinineUnit = "mg/dL"


class EGFRResponse(BaseModel):
    tool: Literal["egfr_ckd_epi_2021"]
    equation: str
    race_coefficient_used: Literal[False]
    age_years: int
    sex: RenalSex
    creatinine_mg_dl: float
    egfr_ml_min_1_73m2: float

    gfr_category: Literal[
        "G1",
        "G2",
        "G3a",
        "G3b",
        "G4",
        "G5",
    ]

    gfr_category_label_pt: str
    gfr_category_label_en: str
    interpretation_pt: str
    interpretation_en: str


class CKDClassificationInput(BaseModel):
    egfr_ml_min_1_73m2: float = Field(ge=0)

    acr: float | None = Field(
        default=None,
        ge=0,
    )

    acr_unit: ACRUnit = "mg/g"

    chronicity_at_least_3_months: bool = False
    other_kidney_damage_marker: bool = False
    on_dialysis: bool = False


class BrazilPCDTCKDContext(BaseModel):
    pcdt_stage: Literal[
        "1",
        "2",
        "3A",
        "3B",
        "4",
        "5",
        "5D",
    ] | None

    pcdt_stage_label_pt: str | None
    pcdt_stage_label_en: str | None

    pcdt_stage_requires_damage_marker: bool

    pcdt_stage_note_pt: str
    pcdt_stage_note_en: str

    kidney_damage_marker_present: bool

    pcdt_acr_category: Literal[
        "A1",
        "A2",
        "A3",
    ] | None

    pcdt_acr_category_evaluable: bool
    pcdt_acr_exact_300_ambiguous: bool

    pcdt_acr_note_pt: str
    pcdt_acr_note_en: str

    pcdt_ckd_status_code: Literal[
        "criteria_met",
        "chronicity_not_established",
        "criteria_not_met_by_supplied_data",
    ]

    pcdt_ckd_status_pt: str
    pcdt_ckd_status_en: str

    pcdt_equation_calculation_applied: Literal[False]

    pcdt_equation_status: Literal[
        "not_implemented_due_verified_source_conflict"
    ]

    race_or_ancestry_input_used: Literal[False]

    source_version: str


class CKDClassificationResponse(BaseModel):
    tool: Literal["ckd_classification"]

    gfr_category: Literal[
        "G1",
        "G2",
        "G3a",
        "G3b",
        "G4",
        "G5",
    ]

    gfr_category_label_pt: str
    gfr_category_label_en: str

    albuminuria_category: Literal[
        "A1",
        "A2",
        "A3",
    ] | None

    albuminuria_category_label_pt: str | None
    albuminuria_category_label_en: str | None

    ga_classification: str

    chronicity_at_least_3_months: bool
    other_kidney_damage_marker: bool
    on_dialysis: bool

    brazil_pcdt_context: BrazilPCDTCKDContext

    ckd_status_code: Literal[
        "criteria_met",
        "chronicity_not_established",
        "criteria_not_met_by_supplied_data",
    ]

    ckd_status_pt: str
    ckd_status_en: str

    classification_note_pt: str
    classification_note_en: str


class KDIGOAKIInput(BaseModel):
    current_creatinine: float | None = Field(
        default=None,
        gt=0,
    )

    current_creatinine_unit: CreatinineUnit = "mg/dL"

    baseline_creatinine: float | None = Field(
        default=None,
        gt=0,
    )

    baseline_creatinine_unit: CreatinineUnit | None = None

    baseline_interval_hours: float | None = Field(
        default=None,
        ge=0,
    )

    weight_kg: float | None = Field(
        default=None,
        gt=0,
    )

    urine_output_ml: float | None = Field(
        default=None,
        ge=0,
    )

    urine_output_duration_hours: float | None = Field(
        default=None,
        gt=0,
    )

    anuria_duration_hours: float | None = Field(
        default=None,
        ge=0,
    )

    renal_replacement_therapy: bool = False


class KDIGOAKIResponse(BaseModel):
    tool: Literal["kdigo_aki"]

    evaluable: bool
    aki_criteria_met: bool | None

    stage: Literal[
        0,
        1,
        2,
        3,
    ] | None

    creatinine_stage: Literal[
        0,
        1,
        2,
        3,
    ] | None

    urine_output_stage: Literal[
        0,
        1,
        2,
        3,
    ] | None

    rrt_stage: Literal[3] | None

    current_creatinine_mg_dl: float | None

    creatinine_ratio: float | None
    creatinine_delta_mg_dl: float | None
    urine_output_ml_kg_h: float | None

    criteria_codes: list[str]
    criteria_pt: list[str]
    criteria_en: list[str]

    interpretation_pt: str
    interpretation_en: str


# ---------------------------------------------------------------------------
# v2 Item 3 — haemodynamic calculations.
# ---------------------------------------------------------------------------

HemodynamicsClinicalContext = Literal[
    "none",
    "septic_shock",
    "obstetric_hemorrhage",
]


class HemodynamicsInput(BaseModel):
    systolic_bp: float = Field(gt=0)
    diastolic_bp: float = Field(gt=0)
    heart_rate: float = Field(gt=0)

    clinical_context: HemodynamicsClinicalContext = "none"


class HemodynamicsResponse(BaseModel):
    tool: Literal["hemodynamics"]

    systolic_bp_mm_hg: float
    diastolic_bp_mm_hg: float
    heart_rate_bpm: float

    pulse_pressure_mm_hg: float
    mean_arterial_pressure_mm_hg: float

    shock_index: float
    modified_shock_index: float

    map_method: str
    pulse_pressure_method: str
    shock_index_method: str
    modified_shock_index_method: str

    threshold_classification_applied: Literal[False]
    universal_threshold_inference_applied: Literal[False]

    clinical_context: HemodynamicsClinicalContext

    brazil_context_guidance_applied: bool

    brazil_context_rule_code: Literal[
        "none",
        "septic_shock_map_target",
        "obstetric_hemorrhage_si_trigger",
    ]

    brazil_context_threshold_value: float | None
    brazil_context_threshold_unit: str | None

    brazil_context_operator: Literal[
        ">=",
        ">",
    ] | None

    brazil_context_observed_value: float | None
    brazil_context_rule_met: bool | None

    brazil_context_label_pt: str
    brazil_context_label_en: str

    brazil_context_interpretation_pt: str
    brazil_context_interpretation_en: str

    interpretation_pt: str
    interpretation_en: str

    map_note_pt: str
    map_note_en: str


# ---------------------------------------------------------------------------
# v2 Item 4 — oxygenation P/F and S/F ratios.
# ---------------------------------------------------------------------------

class OxygenationInput(BaseModel):
    fio2_percent: float = Field(
        ge=21,
        le=100,
    )

    pao2_mm_hg: float | None = Field(
        default=None,
        gt=0,
    )

    spo2_percent: float | None = Field(
        default=None,
        ge=1,
        le=100,
    )


class OxygenationResponse(BaseModel):
    tool: Literal["oxygenation_ratios"]

    fio2_percent: float
    fio2_fraction: float

    pao2_mm_hg: float | None
    spo2_percent: float | None

    pf_ratio_mm_hg: float | None
    sf_ratio: float | None

    pf_method: str
    sf_method: str

    ards_classification_applied: Literal[False]

    sf_spo2_above_97_caution: bool | None
    global_ards_sf_threshold_applicable: bool | None

    interpretation_pt: str
    interpretation_en: str

    sf_note_pt: str | None
    sf_note_en: str | None

    fio2_note_pt: str
    fio2_note_en: str


# ---------------------------------------------------------------------------
# v2 Item 5 — acid-base / metabolic toolkit.
# ---------------------------------------------------------------------------

class MetabolicToolkitInput(BaseModel):
    sodium_meq_l: float = Field(gt=0)

    chloride_meq_l: float | None = Field(
        default=None,
        gt=0,
    )

    bicarbonate_meq_l: float | None = Field(
        default=None,
        gt=0,
    )

    albumin_g_dl: float | None = Field(
        default=None,
        gt=0,
    )

    glucose_mg_dl: float | None = Field(
        default=None,
        ge=0,
    )

    bun_mg_dl: float | None = Field(
        default=None,
        ge=0,
    )

    paco2_mm_hg: float | None = Field(
        default=None,
        gt=0,
    )

    metabolic_acidosis_confirmed: bool = False


class MetabolicToolkitResponse(BaseModel):
    tool: Literal["acid_base_metabolic"]

    sodium_meq_l: float
    chloride_meq_l: float | None
    bicarbonate_meq_l: float | None
    albumin_g_dl: float | None
    glucose_mg_dl: float | None
    bun_mg_dl: float | None
    paco2_mm_hg: float | None

    anion_gap_meq_l: float | None
    albumin_corrected_anion_gap_meq_l: float | None

    anion_gap_formula: str
    albumin_correction_formula: str
    albumin_correction_applied: bool

    calculated_osmolality_mosm_kg: float | None
    osmolality_formula: str

    corrected_sodium_meq_l: float | None
    corrected_sodium_delta_meq_l: float | None
    corrected_sodium_method: str | None

    metabolic_acidosis_confirmed: bool

    winter_analysis_applied: bool
    winter_expected_paco2_mm_hg: float | None
    winter_lower_mm_hg: float | None
    winter_upper_mm_hg: float | None

    winter_compensation_status: Literal[
        "within_expected",
        "paco2_above_expected",
        "paco2_below_expected",
    ] | None

    winter_interpretation_pt: str | None
    winter_interpretation_en: str | None

    delta_analysis_applied: bool

    delta_ag_basis: Literal[
        "albumin_corrected",
        "uncorrected",
    ] | None

    delta_ratio: float | None

    delta_interpretation_code: Literal[
        "suggests_additional_nagma",
        "compatible_with_predominant_hagma",
        "suggests_additional_metabolic_alkalosis",
    ] | None

    delta_interpretation_pt: str | None
    delta_interpretation_en: str | None

    validity_notes_pt: list[str]
    validity_notes_en: list[str]

    interpretation_pt: str
    interpretation_en: str

# ---------------------------------------------------------------------------
# v2 Item 5B — Brazil Ministry methanol/toxicology context.
# ---------------------------------------------------------------------------

class BrazilMethanolInput(BaseModel):
    explicit_methanol_context: Literal[True]

    sodium_mmol_l: float = Field(
        gt=0,
    )

    potassium_mmol_l: float | None = Field(
        default=None,
        gt=0,
    )

    chloride_mmol_l: float | None = Field(
        default=None,
        gt=0,
    )

    bicarbonate_mmol_l: float | None = Field(
        default=None,
        gt=0,
    )

    glucose_mmol_l: float | None = Field(
        default=None,
        ge=0,
    )

    urea_mmol_l: float | None = Field(
        default=None,
        ge=0,
    )

    measured_osmolality_mosm_kg: float | None = Field(
        default=None,
        gt=0,
    )


class BrazilMethanolResponse(BaseModel):
    tool: Literal["brazil_methanol_context"]

    explicit_methanol_context: Literal[True]

    sodium_mmol_l: float
    potassium_mmol_l: float | None
    chloride_mmol_l: float | None
    bicarbonate_mmol_l: float | None

    glucose_mmol_l: float | None
    urea_mmol_l: float | None

    measured_osmolality_mosm_kg: float | None

    ministry_anion_gap_mmol_l: float | None
    ministry_anion_gap_formula: str
    ministry_anion_gap_potassium_included: Literal[True]

    anion_gap_gt_12: bool | None

    ministry_calculated_osmolality_mosm_kg: float | None
    ministry_calculated_osmolality_formula: str

    ministry_osmolality_input_unit: Literal["mmol/L"]
    ministry_osmolality_uses_urea_not_bun: Literal[True]

    osmolar_gap_mosm_kg: float | None
    osmolar_gap_formula: str
    osmolar_gap_calculation_applied: bool

    osmolar_gap_gt_10: bool | None
    osmolar_gap_gt_25: bool | None

    normal_osmolar_gap_excludes_late_poisoning: Literal[False]

    methanol_diagnosis_applied: Literal[False]
    automatic_toxicology_context_inference_applied: Literal[False]

    thresholds_contextual_only: Literal[True]

    urea_bun_substitution_applied: Literal[False]
    unit_domain_mixed: Literal[False]

    validity_notes_pt: list[str]
    validity_notes_en: list[str]

    interpretation_pt: str
    interpretation_en: str


# ---------------------------------------------------------------------------
# v2 Item 6 — WHO paediatric growth + Brazil SISVAN interpretation.
# ---------------------------------------------------------------------------

GrowthSex = Literal[
    "male",
    "female",
]

GrowthAgeUnit = Literal[
    "days",
    "months",
]

GrowthAgeBasis = Literal[
    "chronological",
    "corrected",
]

GrowthMeasurementPosition = Literal[
    "length",
    "height",
]


class GrowthInput(BaseModel):
    sex: GrowthSex

    age_value: float = Field(
        ge=0,
    )

    age_unit: GrowthAgeUnit

    age_basis: GrowthAgeBasis = "chronological"

    weight_kg: float | None = Field(
        default=None,
        gt=0,
    )

    length_height_cm: float | None = Field(
        default=None,
        gt=0,
    )

    measurement_position: GrowthMeasurementPosition | None = None

    head_circumference_cm: float | None = Field(
        default=None,
        gt=0,
    )

    oedema: bool = False


class GrowthClassification(BaseModel):
    code: str
    label_pt: str
    label_en: str


class GrowthIndicatorResult(BaseModel):
    indicator: Literal[
        "weight_for_age",
        "length_height_for_age",
        "weight_for_length_height",
        "bmi_for_age",
        "head_circumference_for_age",
    ]

    z_score: float

    percentile: float | None
    percentile_available: bool

    reference_standard: str
    reference_table: str

    classification_who: GrowthClassification | None = None
    classification_br: GrowthClassification | None = None

    classification_z_basis: str

    plausibility_flag: bool
    who_plausibility_range: str

    brazil_routine_monitoring_applicable: bool | None = None


class GrowthIndicators(BaseModel):
    weight_for_age: GrowthIndicatorResult | None = None
    length_height_for_age: GrowthIndicatorResult | None = None
    weight_for_length_height: GrowthIndicatorResult | None = None
    bmi_for_age: GrowthIndicatorResult | None = None
    head_circumference_for_age: GrowthIndicatorResult | None = None


class GrowthProvenance(BaseModel):
    who2006_commit: str
    who2007_commit: str
    brazil_policy: str


class GrowthResponse(BaseModel):
    tool: Literal["who_pediatric_growth"]

    sex: GrowthSex

    age_input_value: float
    age_input_unit: GrowthAgeUnit
    age_basis: GrowthAgeBasis

    who_age_days: int
    who_age_months: float

    oedema: bool

    measurement_position_input: GrowthMeasurementPosition | None
    measurement_position_effective: GrowthMeasurementPosition | None

    measurement_adjustment_cm: float

    length_height_input_cm: float | None
    length_height_effective_cm: float | None

    bmi_kg_m2: float | None

    indicators: GrowthIndicators

    warnings_pt: list[str]
    warnings_en: list[str]

    provenance: GrowthProvenance


# ---------------------------------------------------------------------------
# v2 Item 7 — Brazil falls / clinical-functional vulnerability.
# ---------------------------------------------------------------------------

CadernetaFallsItemKey = Literal[
    "fall_previous_year",
    "cane_or_walker_recommended",
    "unsteady_while_walking",
    "uses_furniture_for_support",
    "concern_about_falling",
    "needs_hands_to_rise_from_chair",
    "difficulty_stepping_onto_curb",
    "toilet_urgency",
    "reduced_foot_sensation",
    "medication_dizziness_or_fatigue",
    "sleep_or_mood_medication",
    "sadness_or_depressed_mood",
]


class CadernetaFallsInput(BaseModel):
    age_years: int = Field(
        ge=60,
    )

    fall_previous_year: bool
    cane_or_walker_recommended: bool
    unsteady_while_walking: bool
    uses_furniture_for_support: bool
    concern_about_falling: bool
    needs_hands_to_rise_from_chair: bool
    difficulty_stepping_onto_curb: bool
    toilet_urgency: bool
    reduced_foot_sensation: bool
    medication_dizziness_or_fatigue: bool
    sleep_or_mood_medication: bool
    sadness_or_depressed_mood: bool


class CadernetaFallsResponse(BaseModel):
    tool: Literal[
        "brazil_caderneta_falls_checkup_2026"
    ]

    age_years: int = Field(
        ge=60,
    )

    positive_items_count: int = Field(
        ge=0,
        le=12,
    )

    positive_items: list[
        CadernetaFallsItemKey
    ]

    assessment_indicated: bool

    any_yes_rule_applied: Literal[True]

    weighted_score_applied: Literal[False]

    foreign_weighted_score_imported: Literal[False]

    fall_risk_classification_applied: Literal[False]

    automatic_ivcf_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str


IVCF20DimensionKey = Literal[
    "age",
    "health_perception",
    "instrumental_adl",
    "basic_adl",
    "cognition",
    "mood",
    "upper_limb_mobility",
    "aerobic_muscular_capacity",
    "gait",
    "continence",
    "vision",
    "hearing",
    "multiple_comorbidities",
]


class IVCF20Input(BaseModel):
    age_years: int = Field(
        ge=60,
    )

    self_rated_health_regular_or_poor: bool

    stopped_shopping_due_health: bool
    stopped_managing_money_due_health: bool
    stopped_housework_due_health: bool

    stopped_bathing_due_health: bool

    forgetfulness_noted_by_others: bool
    worsening_forgetfulness: bool
    forgetfulness_impairs_daily_activity: bool

    depressed_or_hopeless_last_month: bool
    anhedonia_last_month: bool

    unable_raise_arms_above_shoulders: bool
    unable_handle_small_objects: bool

    unintentional_weight_loss_criterion: bool
    bmi_lt_22: bool
    calf_circumference_lt_31_cm: bool
    gait_4m_gt_5_seconds: bool

    walking_difficulty_impairs_daily_activity: bool
    two_or_more_falls_last_year: bool

    urinary_or_fecal_incontinence: bool
    vision_impairs_daily_activity: bool
    hearing_impairs_daily_activity: bool

    five_or_more_chronic_conditions: bool
    five_or_more_daily_medications: bool
    hospitalized_last_six_months: bool


class IVCF20DimensionScores(BaseModel):
    age: int = Field(
        ge=0,
        le=3,
    )

    health_perception: int = Field(
        ge=0,
        le=1,
    )

    instrumental_adl: int = Field(
        ge=0,
        le=4,
    )

    basic_adl: int = Field(
        ge=0,
        le=6,
    )

    cognition: int = Field(
        ge=0,
        le=4,
    )

    mood: int = Field(
        ge=0,
        le=4,
    )

    upper_limb_mobility: int = Field(
        ge=0,
        le=2,
    )

    aerobic_muscular_capacity: int = Field(
        ge=0,
        le=2,
    )

    gait: int = Field(
        ge=0,
        le=4,
    )

    continence: int = Field(
        ge=0,
        le=2,
    )

    vision: int = Field(
        ge=0,
        le=2,
    )

    hearing: int = Field(
        ge=0,
        le=2,
    )

    multiple_comorbidities: int = Field(
        ge=0,
        le=4,
    )


class IVCF20Response(BaseModel):
    tool: Literal["ivcf20"]

    age_years: int = Field(
        ge=60,
    )

    total_score: int = Field(
        ge=0,
        le=40,
    )

    classification_code: Literal[
        "low",
        "moderate",
        "high",
    ]

    classification_pt: str
    classification_en: str

    dimension_scores: IVCF20DimensionScores

    altered_dimensions: list[
        IVCF20DimensionKey
    ]

    reapplication_months_minimum: Literal[
        6,
        12,
    ]

    reapply_after_sentinel_event: Literal[True]

    complete_assessment_required: Literal[True]

    gait_4m_gt_5_seconds: bool

    gait_4m_is_tug: Literal[False]

    fall_risk_classification_applied: Literal[False]

    automatic_caderneta_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str


# ---------------------------------------------------------------------------
# v2 Item 7 complementary layer — CDC STEADI assessments.
#
# These remain separate from the Brazil-primary Caderneta 2026 and IVCF-20
# instruments. No cross-instrument synthetic score is permitted.
# ---------------------------------------------------------------------------

SteadiSourceRole = Literal[
    "complementary_international_guidance",
]


class SteadiTUGInput(BaseModel):
    time_seconds: float = Field(
        gt=0,
    )

    walking_aid_used: bool

    standard_3m_protocol_confirmed: bool


class SteadiTUGResponse(BaseModel):
    tool: Literal[
        "steadi_timed_up_and_go"
    ]

    source_role: SteadiSourceRole

    time_seconds: float = Field(
        gt=0,
    )

    course_distance_m: Literal[3]
    course_distance_ft: Literal[10]

    walking_aid_allowed: Literal[True]
    walking_aid_used: bool

    threshold_seconds: Literal[12]

    threshold_comparison: Literal[
        ">=",
    ]

    increased_fall_risk: bool

    ivcf_four_meter_gait_inferred: Literal[False]

    national_sus_threshold_applied: Literal[False]

    automatic_cross_instrument_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str


SteadiReferenceSex = Literal[
    "male",
    "female",
]


SteadiChairAgeBand = Literal[
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80-84",
    "85-89",
    "90-94",
]


class SteadiChairStand30sInput(BaseModel):
    age_years: int = Field(
        ge=60,
    )

    sex: SteadiReferenceSex

    repetitions: int = Field(
        ge=0,
    )

    arms_required_to_stand: bool

    standard_30_second_protocol_confirmed: bool


class SteadiChairStand30sResponse(BaseModel):
    tool: Literal[
        "steadi_30_second_chair_stand"
    ]

    source_role: SteadiSourceRole

    age_years: int = Field(
        ge=60,
    )

    reference_sex: SteadiReferenceSex

    observed_repetitions_input: int = Field(
        ge=0,
    )

    arms_required_to_stand: bool

    test_stopped_due_to_arm_use: bool

    recorded_repetitions: int = Field(
        ge=0,
    )

    reference_age_band: SteadiChairAgeBand | None

    below_average_threshold: int | None

    threshold_comparison: Literal[
        "<",
    ]

    reference_classification_available: bool

    below_average: bool | None

    increased_fall_risk: bool | None

    reference_table_maximum_age_years: Literal[
        94
    ]

    cutoff_extrapolated: Literal[False]

    national_sus_threshold_applied: Literal[False]

    automatic_cross_instrument_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str


SteadiBalanceStage = Literal[
    "side_by_side",
    "semi_tandem",
    "tandem",
    "one_leg",
]


class SteadiFourStageBalanceInput(BaseModel):
    side_by_side_seconds: float = Field(
        ge=0,
        le=10,
    )

    semi_tandem_seconds: float | None = Field(
        default=None,
        ge=0,
        le=10,
    )

    tandem_seconds: float | None = Field(
        default=None,
        ge=0,
        le=10,
    )

    one_leg_seconds: float | None = Field(
        default=None,
        ge=0,
        le=10,
    )

    assistive_device_used: bool

    standard_four_stage_protocol_confirmed: bool


class SteadiFourStageBalanceResponse(BaseModel):
    tool: Literal[
        "steadi_four_stage_balance"
    ]

    source_role: SteadiSourceRole

    side_by_side_seconds: float = Field(
        ge=0,
        le=10,
    )

    semi_tandem_seconds: float | None = Field(
        ge=0,
        le=10,
    )

    tandem_seconds: float | None = Field(
        ge=0,
        le=10,
    )

    one_leg_seconds: float | None = Field(
        ge=0,
        le=10,
    )

    target_seconds_per_stage: Literal[10]

    last_stage_attempted: SteadiBalanceStage

    tandem_held_10_seconds: bool

    increased_fall_risk: bool

    assistive_device_allowed: Literal[False]

    assistive_device_used: Literal[False]

    eyes_open_required: Literal[True]

    national_sus_threshold_applied: Literal[False]

    automatic_cross_instrument_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str


class SteadiOrthostaticBPInput(BaseModel):
    supine_sbp_mm_hg: float = Field(
        gt=0,
    )

    supine_dbp_mm_hg: float = Field(
        gt=0,
    )

    supine_pulse_bpm: float = Field(
        gt=0,
    )

    standing_1m_sbp_mm_hg: float = Field(
        gt=0,
    )

    standing_1m_dbp_mm_hg: float = Field(
        gt=0,
    )

    standing_1m_pulse_bpm: float = Field(
        gt=0,
    )

    standing_3m_sbp_mm_hg: float = Field(
        gt=0,
    )

    standing_3m_dbp_mm_hg: float = Field(
        gt=0,
    )

    standing_3m_pulse_bpm: float = Field(
        gt=0,
    )

    lightheaded_or_dizzy: bool

    standard_5_1_3_protocol_confirmed: bool


class SteadiOrthostaticBPResponse(BaseModel):
    tool: Literal[
        "steadi_orthostatic_blood_pressure"
    ]

    source_role: SteadiSourceRole

    supine_sbp_mm_hg: float = Field(
        gt=0,
    )

    supine_dbp_mm_hg: float = Field(
        gt=0,
    )

    supine_pulse_bpm: float = Field(
        gt=0,
    )

    standing_1m_sbp_mm_hg: float = Field(
        gt=0,
    )

    standing_1m_dbp_mm_hg: float = Field(
        gt=0,
    )

    standing_1m_pulse_bpm: float = Field(
        gt=0,
    )

    standing_3m_sbp_mm_hg: float = Field(
        gt=0,
    )

    standing_3m_dbp_mm_hg: float = Field(
        gt=0,
    )

    standing_3m_pulse_bpm: float = Field(
        gt=0,
    )

    supine_rest_minutes: Literal[5]

    standing_measurement_minutes: tuple[
        Literal[1],
        Literal[3],
    ]

    systolic_drop_1m_mm_hg: float
    systolic_drop_3m_mm_hg: float

    diastolic_drop_1m_mm_hg: float
    diastolic_drop_3m_mm_hg: float

    maximum_systolic_drop_mm_hg: float
    maximum_diastolic_drop_mm_hg: float

    systolic_drop_threshold_mm_hg: Literal[20]

    diastolic_drop_threshold_mm_hg: Literal[10]

    systolic_threshold_met: bool
    diastolic_threshold_met: bool

    lightheaded_or_dizzy: bool

    abnormal_steadi_orthostatic_assessment: bool

    fall_risk_classification_applied: Literal[False]

    national_sus_threshold_applied: Literal[False]

    automatic_cross_instrument_inference_applied: Literal[False]

    synthetic_cross_instrument_score_applied: Literal[False]

    interpretation_pt: str
    interpretation_en: str



# ---------------------------------------------------------------------------
# v2 Item 10 — Glasgow Coma Scale, GCS-P, and FOUR Score API contracts.
#
# The HTTP boundary accepts raw observations only.
# GCS-P does not accept a client-derived GCS total/result as its authority;
# the API constructs the canonical GCS result server-side.
#
# Explicit unavailable states remain distinct from invalid supplied values:
# - GCS uses "NT";
# - pupil reactivity may be explicit null;
# - FOUR domains may be explicit null.
# ---------------------------------------------------------------------------

GCSComponentName = Literal[
    "eye",
    "verbal",
    "motor",
]

GCSEyeScore = Annotated[
    int,
    Field(
        strict=True,
        ge=1,
        le=4,
    ),
]

GCSVerbalScore = Annotated[
    int,
    Field(
        strict=True,
        ge=1,
        le=5,
    ),
]

GCSMotorScore = Annotated[
    int,
    Field(
        strict=True,
        ge=1,
        le=6,
    ),
]

GCSEyeValue = (
    GCSEyeScore
    | Literal["NT"]
)

GCSVerbalValue = (
    GCSVerbalScore
    | Literal["NT"]
)

GCSMotorValue = (
    GCSMotorScore
    | Literal["NT"]
)

GCSIncompleteReason = Literal[
    "not_testable_component",
]


class GCSInput(BaseModel):
    eye: GCSEyeValue
    verbal: GCSVerbalValue
    motor: GCSMotorValue


class GCSComponents(BaseModel):
    eye: GCSEyeValue
    verbal: GCSVerbalValue
    motor: GCSMotorValue


class GCSResponse(BaseModel):
    tool: Literal[
        "gcs"
    ]

    evaluable: bool

    total: int | None = Field(
        ge=3,
        le=15,
    )

    components: GCSComponents

    nt_components: list[
        GCSComponentName
    ]

    incomplete_reason: (
        GCSIncompleteReason
        | None
    )


GCSIncompleteGCSPReason = Literal[
    "gcs_not_numeric",
    "pupil_reactivity_unknown",
]


PupilReactivityValue = Annotated[
    int,
    Field(
        strict=True,
        ge=0,
        le=2,
    ),
]


class GCSPInput(BaseModel):
    eye: GCSEyeValue
    verbal: GCSVerbalValue
    motor: GCSMotorValue

    # Required field, but explicit null is a valid
    # clinical "unknown/unavailable" state.
    unreactive_pupils: (
        PupilReactivityValue
        | None
    )


class GCSPResponse(BaseModel):
    tool: Literal[
        "gcs_p"
    ]

    evaluable: bool

    total: int | None = Field(
        ge=1,
        le=15,
    )

    gcs: GCSResponse

    gcs_total: int | None = Field(
        ge=3,
        le=15,
    )

    unreactive_pupils: (
        PupilReactivityValue
        | None
    )

    pupil_reactivity_score: (
        PupilReactivityValue
        | None
    )

    incomplete_reasons: list[
        GCSIncompleteGCSPReason
    ]


FOURDomainName = Literal[
    "eye",
    "motor",
    "brainstem",
    "respiration",
]

FOURDomainValue = Annotated[
    int,
    Field(
        strict=True,
        ge=0,
        le=4,
    ),
]

FOURIncompleteReason = Literal[
    "domain_unavailable",
]


class FOURInput(BaseModel):
    # Each field is required at the HTTP boundary.
    # Explicit null means that domain is unavailable
    # and therefore prevents a numeric total.
    eye: FOURDomainValue | None
    motor: FOURDomainValue | None
    brainstem: FOURDomainValue | None
    respiration: FOURDomainValue | None


class FOURComponents(BaseModel):
    eye: FOURDomainValue | None
    motor: FOURDomainValue | None
    brainstem: FOURDomainValue | None
    respiration: FOURDomainValue | None


class FOURResponse(BaseModel):
    tool: Literal[
        "four"
    ]

    evaluable: bool

    total: int | None = Field(
        ge=0,
        le=16,
    )

    components: FOURComponents

    missing_domains: list[
        FOURDomainName
    ]

    incomplete_reason: (
        FOURIncompleteReason
        | None
    )


# ---------------------------------------------------------------------------
# v2 Item 8 — Brazil 2026 PNI normalized data contracts.
#
# DATA MODEL ONLY.
# No vaccine-specific eligibility or due/not-due rules are implemented here.
#
# Core boundaries:
# - assessment/effective dates are first-class;
# - unknown history != documented zero-dose history;
# - routine/campaign/rescue/outbreak/special pathways remain distinct;
# - special conditions are explicit inputs, never silently inferred;
# - no synthetic vaccination score.
# ---------------------------------------------------------------------------

PniRecommendationLayer = Literal[
    "routine",
    "seasonal_strategy",
    "rescue_strategy",
    "outbreak_or_blocking",
    "travel_or_area_risk",
    "special_condition",
]


PniHistoryState = Literal[
    "documented_zero_dose",
    "documented_doses",
    "partial_record",
    "unknown",
]


PniDoseDocumentationSource = Literal[
    "official_registry",
    "vaccination_card",
    "other_health_document",
    "patient_or_caregiver_report",
]


PniPregnancyStatus = Literal[
    "pregnant",
    "not_pregnant",
    "unknown",
    "not_applicable",
]


PniMaternalHbsAgStatus = Literal[
    "positive",
    "negative",
    "unknown_or_unavailable",
]


PniBreastfeedingStatus = Literal[
    "breastfeeding",
    "not_breastfeeding",
    "unknown",
]


PniClinicalEvidenceSource = Literal[
    "documented",
    "patient_or_caregiver_report",
]


PniAntigenComponent = Literal[
    "diphtheria_toxoid",
    "tetanus_toxoid",
    "pertussis_antigen",
]


PniCrossVaccineHistoryScope = Literal[
    "complete",
    "partial",
    "unknown",
]


PniAntigenHistoryState = Literal[
    "documented_zero_exposure",
    "documented_exposures",
    "partial_record",
    "unknown",
]


class PniAntigenExposureRecord(BaseModel):
    administration_date: date

    gestational_age_weeks_at_administration: int | None = Field(
        default=None,
        ge=0,
        le=45,
    )

    antigen_components: list[PniAntigenComponent] = Field(
        min_length=1,
    )

    source_vaccine_key: str = Field(
        min_length=1,
        max_length=100,
    )

    source_product_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    documentation_source: PniDoseDocumentationSource

    pregnancy_episode_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    special_pathway_product: bool = False

    @model_validator(
        mode="after"
    )
    def validate_antigen_components(
        self,
    ):
        if (
            len(self.antigen_components)
            != len(set(self.antigen_components))
        ):
            raise ValueError(
                "antigen_components must not contain duplicates"
            )

        return self


class PniAntigenHistorySummary(BaseModel):
    target_antigens: list[PniAntigenComponent] = Field(
        min_length=1,
    )

    history_scope: PniCrossVaccineHistoryScope

    history_state: PniAntigenHistoryState

    exposures: list[PniAntigenExposureRecord] = Field(
        default_factory=list,
    )

    exposure_event_count: int = Field(
        ge=0,
    )

    last_exposure_date: date | None = None

    ambiguous_same_day_exposure_dates: list[date] = Field(
        default_factory=list,
    )

    unmapped_vaccine_keys: list[str] = Field(
        default_factory=list,
    )

    source_history_incomplete: bool

    safe_for_interval_evaluation: bool
    safe_for_basic_series_count: bool

    @model_validator(
        mode="after"
    )
    def validate_summary(
        self,
    ):
        if (
            len(self.target_antigens)
            != len(set(self.target_antigens))
        ):
            raise ValueError(
                "target_antigens must not contain duplicates"
            )

        if (
            self.exposure_event_count
            != len(self.exposures)
        ):
            raise ValueError(
                "exposure_event_count must equal exposures length"
            )

        if self.exposures:
            expected_last = max(
                exposure.administration_date
                for exposure
                in self.exposures
            )

            if (
                self.last_exposure_date
                != expected_last
            ):
                raise ValueError(
                    "last_exposure_date must match latest exposure"
                )

        elif (
            self.last_exposure_date
            is not None
        ):
            raise ValueError(
                "last_exposure_date requires at least one exposure"
            )

        if (
            self.safe_for_interval_evaluation
            or self.safe_for_basic_series_count
        ):
            if (
                self.history_scope
                != "complete"
            ):
                raise ValueError(
                    "safe antigen-history evaluation requires complete scope"
                )

            if (
                self.source_history_incomplete
                or self.unmapped_vaccine_keys
                or self.ambiguous_same_day_exposure_dates
            ):
                raise ValueError(
                    "safe antigen-history evaluation cannot contain ambiguity"
                )

            if self.history_state not in {
                "documented_zero_exposure",
                "documented_exposures",
            }:
                raise ValueError(
                    "safe antigen-history evaluation requires documented state"
                )

        return self


PniRuleDecision = Literal[
    "recommend_now",
    "not_due_now",
    "future_recommendation",
    "history_required",
    "context_required",
    "special_pathway_review",
    "not_applicable",
]


class PniBcgVaccinationEvidence(BaseModel):
    vaccination_record_present: bool | None = None
    scar_present: bool | None = None
    palpable_nodule_present: bool | None = None

    @model_validator(
        mode="after"
    )
    def validate_evidence(
        self,
    ):
        if all(
            value is None
            for value in (
                self.vaccination_record_present,
                self.scar_present,
                self.palpable_nodule_present,
            )
        ):
            raise ValueError(
                "BCG evidence requires at least one assessed evidence field"
            )

        return self


class PniBreastfeedingContext(BaseModel):
    status: PniBreastfeedingStatus

    youngest_breastfed_child_date_of_birth: date | None = None

    @model_validator(
        mode="after"
    )
    def validate_breastfeeding_context(
        self,
    ):
        if (
            self.status
            != "breastfeeding"
            and self.youngest_breastfed_child_date_of_birth
            is not None
        ):
            raise ValueError(
                "breastfed-child date of birth requires breastfeeding status"
            )

        return self


class PniDiseaseEvent(BaseModel):
    disease_key: str = Field(
        min_length=1,
        max_length=100,
    )

    event_date: date | None = None

    evidence_source: PniClinicalEvidenceSource

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class PniExposureEvent(BaseModel):
    exposure_key: str = Field(
        min_length=1,
        max_length=100,
    )

    event_date: date

    evidence_source: PniClinicalEvidenceSource

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class PniTravelContext(BaseModel):
    destination_country: str = Field(
        min_length=2,
        max_length=100,
    )

    destination_federative_unit: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
    )

    destination_municipality: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    departure_date: date
    return_date: date | None = None

    @model_validator(
        mode="after"
    )
    def validate_travel_window(
        self,
    ):
        if (
            self.return_date
            is not None
            and self.return_date
            < self.departure_date
        ):
            raise ValueError(
                "travel return_date cannot precede departure_date"
            )

        return self


class PniDoseRecord(BaseModel):
    administration_date: date

    gestational_age_weeks_at_administration: int | None = Field(
        default=None,
        ge=0,
        le=45,
    )

    pregnancy_episode_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    product_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    product_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    dose_number: int | None = Field(
        default=None,
        ge=1,
    )

    dose_label: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    documentation_source: PniDoseDocumentationSource


class PniVaccineHistory(BaseModel):
    vaccine_key: str = Field(
        min_length=1,
        max_length=100,
    )

    history_state: PniHistoryState

    doses: list[PniDoseRecord] = Field(
        default_factory=list,
    )

    reported_prior_doses_without_exact_dates: int = Field(
        default=0,
        ge=0,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    @model_validator(
        mode="after"
    )
    def validate_history_state(
        self,
    ):
        exact_doses = len(
            self.doses
        )

        undated_doses = (
            self.reported_prior_doses_without_exact_dates
        )

        if (
            self.history_state
            == "unknown"
        ):
            if (
                exact_doses != 0
                or undated_doses != 0
            ):
                raise ValueError(
                    "unknown history cannot contain dose records"
                )

        elif (
            self.history_state
            == "documented_zero_dose"
        ):
            if (
                exact_doses != 0
                or undated_doses != 0
            ):
                raise ValueError(
                    "documented zero-dose history cannot contain prior doses"
                )

        elif (
            self.history_state
            == "documented_doses"
        ):
            if exact_doses == 0:
                raise ValueError(
                    "documented_doses requires at least one dated dose"
                )

        elif (
            self.history_state
            == "partial_record"
        ):
            if (
                exact_doses == 0
                and undated_doses == 0
            ):
                raise ValueError(
                    "partial_record requires some known or reported dose evidence"
                )

        return self


class PniAssessmentContext(BaseModel):
    assessment_date: date
    date_of_birth: date

    pregnancy_status: PniPregnancyStatus = (
        "not_applicable"
    )

    gestational_age_weeks: int | None = Field(
        default=None,
        ge=0,
        le=45,
    )

    postpartum_days: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )

    pregnancy_episode_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    postpartum_pregnancy_episode_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    maternal_hbsag_status: PniMaternalHbsAgStatus | None = None

    birth_weight_grams: int | None = Field(
        default=None,
        gt=0,
    )

    current_weight_grams: int | None = Field(
        default=None,
        ge=1,
    )

    bcg_vaccination_evidence: PniBcgVaccinationEvidence | None = None

    breastfeeding: PniBreastfeedingContext | None = None

    disease_history: list[PniDiseaseEvent] = Field(
        default_factory=list,
    )

    exposure_events: list[PniExposureEvent] = Field(
        default_factory=list,
    )

    travel_contexts: list[PniTravelContext] = Field(
        default_factory=list,
    )

    occupational_groups: list[str] = Field(
        default_factory=list,
    )

    special_condition_codes: list[str] = Field(
        default_factory=list,
    )

    epidemiologic_context_codes: list[str] = Field(
        default_factory=list,
    )

    federative_unit: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
    )

    municipality: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    @model_validator(
        mode="after"
    )
    def validate_context(
        self,
    ):
        if (
            self.assessment_date
            < self.date_of_birth
        ):
            raise ValueError(
                "assessment_date cannot precede date_of_birth"
            )

        if (
            self.pregnancy_status
            != "pregnant"
            and self.gestational_age_weeks
            is not None
        ):
            raise ValueError(
                "gestational_age_weeks requires pregnancy_status=pregnant"
            )

        if (
            self.pregnancy_status
            == "pregnant"
            and self.postpartum_days
            is not None
        ):
            raise ValueError(
                "pregnancy and postpartum context cannot coexist"
            )

        if (
            self.pregnancy_episode_key
            is not None
            and self.pregnancy_status
            != "pregnant"
        ):
            raise ValueError(
                "pregnancy_episode_key requires pregnancy_status=pregnant"
            )

        if (
            self.postpartum_pregnancy_episode_key
            is not None
            and self.postpartum_days
            is None
        ):
            raise ValueError(
                "postpartum_pregnancy_episode_key requires postpartum_days"
            )

        if (
            self.postpartum_pregnancy_episode_key
            is not None
            and self.pregnancy_status
            == "pregnant"
        ):
            raise ValueError(
                "postpartum pregnancy episode cannot coexist with pregnancy"
            )

        if (
            self.breastfeeding
            is not None
            and self.breastfeeding.youngest_breastfed_child_date_of_birth
            is not None
            and self.breastfeeding.youngest_breastfed_child_date_of_birth
            > self.assessment_date
        ):
            raise ValueError(
                "breastfed-child date of birth cannot follow assessment_date"
            )

        for event in self.disease_history:
            if (
                event.event_date
                is not None
                and event.event_date
                > self.assessment_date
            ):
                raise ValueError(
                    "disease event_date cannot follow assessment_date"
                )

        for event in self.exposure_events:
            if (
                event.event_date
                > self.assessment_date
            ):
                raise ValueError(
                    "exposure event_date cannot follow assessment_date"
                )

        return self


class PniAssessmentRequest(BaseModel):
    context: PniAssessmentContext

    histories: list[PniVaccineHistory] = Field(
        default_factory=list,
    )

    requested_layers: list[PniRecommendationLayer] = Field(
        default_factory=lambda: [
            "routine",
        ],
        min_length=1,
    )

    @model_validator(
        mode="after"
    )
    def validate_request(
        self,
    ):
        vaccine_keys = [
            history.vaccine_key
            for history
            in self.histories
        ]

        if (
            len(vaccine_keys)
            != len(set(vaccine_keys))
        ):
            raise ValueError(
                "duplicate vaccine history entries are not allowed"
            )

        if (
            len(self.requested_layers)
            != len(set(self.requested_layers))
        ):
            raise ValueError(
                "requested_layers must not contain duplicates"
            )

        return self


class PniRuleProvenance(BaseModel):
    rule_id: str = Field(
        min_length=1,
        max_length=150,
    )

    authority: str = Field(
        min_length=1,
        max_length=300,
    )

    authority_rank: int = Field(
        ge=1,
    )

    source_title: str = Field(
        min_length=1,
        max_length=500,
    )

    source_url: HttpUrl

    source_snapshot_date: date

    rule_effective_from: date | None = None
    rule_effective_until: date | None = None

    @model_validator(
        mode="after"
    )
    def validate_effective_dates(
        self,
    ):
        if (
            self.rule_effective_from
            is not None
            and self.rule_effective_until
            is not None
            and self.rule_effective_until
            < self.rule_effective_from
        ):
            raise ValueError(
                "rule_effective_until cannot precede rule_effective_from"
            )

        return self


class PniRuleResult(BaseModel):
    vaccine_key: str = Field(
        min_length=1,
        max_length=100,
    )

    layer: PniRecommendationLayer

    decision: PniRuleDecision

    assessment_date: date

    recommended_date: date | None = None

    recommended_interval_days: int | None = Field(
        default=None,
        ge=0,
    )

    minimum_interval_days: int | None = Field(
        default=None,
        ge=0,
    )

    minimum_interval_applied: bool = False

    history_required: bool = False

    missing_context: list[str] = Field(
        default_factory=list,
    )

    provenance: PniRuleProvenance

    interpretation_pt: str
    interpretation_en: str

    special_condition_inferred: Literal[False] = False

    synthetic_score_applied: Literal[False] = False

    @model_validator(
        mode="after"
    )
    def validate_rule_result(
        self,
    ):
        if (
            self.minimum_interval_applied
            and self.minimum_interval_days
            is None
        ):
            raise ValueError(
                "minimum_interval_applied requires minimum_interval_days"
            )

        if (
            self.recommended_interval_days
            is not None
            and self.minimum_interval_days
            is not None
            and self.minimum_interval_days
            > self.recommended_interval_days
        ):
            raise ValueError(
                "minimum interval cannot exceed recommended interval"
            )

        if (
            self.decision
            == "future_recommendation"
            and self.recommended_date
            is None
        ):
            raise ValueError(
                "future_recommendation requires recommended_date"
            )

        if (
            self.decision
            == "history_required"
            and not self.history_required
        ):
            raise ValueError(
                "history_required decision must set history_required=true"
            )

        if (
            self.decision
            == "context_required"
            and not self.missing_context
        ):
            raise ValueError(
                "context_required decision requires missing_context"
            )

        return self


PniCovidHistoryProductKey = Literal[
    "covid_pfizer_comirnaty_pediatric_under5",
    "covid_moderna_spikevax",
    "covid_coronavac_legacy",
]

PniCovidCurrentProductKey = Literal[
    "covid_pfizer_comirnaty_pediatric_under5",
    "covid_moderna_spikevax",
]

PniCovidOptionRole = Literal[
    "preferred",
    "allowed_alternative",
    "source_allowed_no_preference",
]

PniCovidPreferenceBasis = Literal[
    "current_2026_first_option",
    "homologous_priority",
    "mixed_history_no_new_preference_inferred",
    "legacy_history_complete_with_available_mrna",
]

PniCovidProductChoiceCondition = Literal[
    "pfizer_unavailable",
]

PniCovidSequenceState = Literal[
    "source_authorized_incomplete_prefix",
    "source_authorized_complete",
]


class PniCovidNextProductOption(BaseModel):
    product_key: PniCovidCurrentProductKey

    option_role: PniCovidOptionRole

    condition: (
        PniCovidProductChoiceCondition
        | None
    ) = None

    resulting_product_sequence: list[
        PniCovidHistoryProductKey
    ] = Field(
        min_length=1,
    )

    resulting_sequence_state: PniCovidSequenceState

    next_minimum_interval_days: (
        Literal[
            28,
            56,
        ]
        | None
    ) = None

    @model_validator(
        mode="after"
    )
    def validate_covid_option(
        self,
    ):
        if (
            self.resulting_product_sequence[
                -1
            ]
            != self.product_key
        ):
            raise ValueError(
                "COVID option product must be the final "
                "resulting clinical exposure"
            )

        if (
            self.resulting_sequence_state
            == "source_authorized_complete"
            and self.next_minimum_interval_days
            is not None
        ):
            raise ValueError(
                "complete COVID option cannot require "
                "another minimum interval"
            )

        if (
            self.resulting_sequence_state
            == "source_authorized_incomplete_prefix"
            and self.next_minimum_interval_days
            is None
        ):
            raise ValueError(
                "incomplete COVID option must expose "
                "the next minimum interval"
            )

        return self


class PniCovidChildRuleResult(PniRuleResult):
    allowed_next_product_keys: list[
        PniCovidCurrentProductKey
    ] = Field(
        default_factory=list,
    )

    preferred_next_product_key: (
        PniCovidCurrentProductKey
        | None
    ) = None

    preferred_product_basis: (
        PniCovidPreferenceBasis
        | None
    ) = None

    product_choice_condition: (
        PniCovidProductChoiceCondition
        | None
    ) = None

    next_product_options: list[
        PniCovidNextProductOption
    ] = Field(
        default_factory=list,
    )

    age_out_closure_applied: bool = False

    @model_validator(
        mode="after"
    )
    def validate_covid_product_output(
        self,
    ):
        allowed = list(
            self.allowed_next_product_keys
        )

        if (
            len(
                allowed
            )
            != len(
                set(
                    allowed
                )
            )
        ):
            raise ValueError(
                "COVID allowed_next_product_keys "
                "must not contain duplicates"
            )

        option_products = [
            option.product_key
            for option
            in self.next_product_options
        ]

        if (
            len(
                option_products
            )
            != len(
                set(
                    option_products
                )
            )
        ):
            raise ValueError(
                "COVID next_product_options "
                "must not contain duplicate products"
            )

        if (
            set(
                allowed
            )
            != set(
                option_products
            )
        ):
            raise ValueError(
                "COVID allowed products and option products "
                "must describe the same product set"
            )

        preferred_options = [
            option
            for option
            in self.next_product_options
            if (
                option.option_role
                == "preferred"
            )
        ]

        if (
            self.preferred_next_product_key
            is None
        ):
            if preferred_options:
                raise ValueError(
                    "COVID result without preferred product "
                    "cannot mark an option preferred"
                )

        else:
            if (
                self.preferred_next_product_key
                not in allowed
            ):
                raise ValueError(
                    "preferred COVID product must belong "
                    "to allowed_next_product_keys"
                )

            if (
                len(
                    preferred_options
                )
                != 1
                or preferred_options[
                    0
                ].product_key
                != self.preferred_next_product_key
            ):
                raise ValueError(
                    "COVID preferred option must uniquely match "
                    "preferred_next_product_key"
                )

        if (
            self.product_choice_condition
            is not None
            and not any(
                option.condition
                == self.product_choice_condition
                for option
                in self.next_product_options
            )
        ):
            raise ValueError(
                "COVID product_choice_condition must be represented "
                "by at least one product option"
            )

        if self.age_out_closure_applied:
            if (
                self.decision
                != "not_applicable"
            ):
                raise ValueError(
                    "COVID age-out closure requires "
                    "decision=not_applicable"
                )

            if (
                allowed
                or self.next_product_options
                or self.preferred_next_product_key
                is not None
            ):
                raise ValueError(
                    "COVID age-out closure cannot expose "
                    "a current next-product recommendation"
                )

        return self


class PniAssessmentResponse(BaseModel):
    tool: Literal[
        "brazil_pni_2026"
    ]

    assessment_date: date
    source_snapshot_date: date

    requested_layers: list[PniRecommendationLayer]

    results: list[PniRuleResult]

    routine_strategy_layers_merged: Literal[False] = False

    special_condition_inference_applied: Literal[False] = False

    synthetic_score_applied: Literal[False] = False

PniYellowFeverLiveVaccineGroup = Literal[
    "mmr",
    "mmrv",
    "varicella",
    "dengue",
]

PniYellowFeverInteractionHistoryScreenState = Literal[
    "not_screened",
    "screened_no_relevant_recent_live_vaccine",
    "screened_relevant_live_vaccine_history",
]

PniYellowFeverEmergencyState = Literal[
    "not_assessed",
    "not_present",
    "present",
]


class PniYellowFeverLiveVaccineEvent(BaseModel):
    vaccine_group: PniYellowFeverLiveVaccineGroup
    administration_date: date


class PniYellowFeverInteractionContext(BaseModel):
    history_screen_state: (
        PniYellowFeverInteractionHistoryScreenState
    )

    recent_live_vaccine_events: list[
        PniYellowFeverLiveVaccineEvent
    ] = Field(
        default_factory=list,
    )

    planned_same_day_vaccine_groups: list[
        PniYellowFeverLiveVaccineGroup
    ] = Field(
        default_factory=list,
    )

    epidemiologic_emergency_concomitant_circulation_state: (
        PniYellowFeverEmergencyState
    ) = "not_assessed"

    exceptional_15_day_interval_authorized: bool = False

    @model_validator(
        mode="after"
    )
    def validate_yellow_fever_interaction_context(
        self,
    ):
        if (
            self.history_screen_state
            == "screened_no_relevant_recent_live_vaccine"
            and self.recent_live_vaccine_events
        ):
            raise ValueError(
                "screened-clear VFA interaction context "
                "cannot contain recent live-vaccine events"
            )

        if (
            self.history_screen_state
            == "screened_relevant_live_vaccine_history"
            and not self.recent_live_vaccine_events
        ):
            raise ValueError(
                "documented VFA live-vaccine history state "
                "requires at least one recent event"
            )

        event_keys = [
            (
                event.vaccine_group,
                event.administration_date,
            )
            for event
            in self.recent_live_vaccine_events
        ]

        if len(
            event_keys
        ) != len(
            set(
                event_keys
            )
        ):
            raise ValueError(
                "duplicate VFA live-vaccine interaction event"
            )

        if len(
            self.planned_same_day_vaccine_groups
        ) != len(
            set(
                self.planned_same_day_vaccine_groups
            )
        ):
            raise ValueError(
                "duplicate planned same-day VFA vaccine group"
            )

        return self

PniMmrExternalLiveVaccineGroup = Literal[
    "yellow_fever",
    "varicella",
    "dengue",
]

PniMmrInteractionHistoryScreenState = Literal[
    "not_screened",
    "screened_no_relevant_recent_live_vaccine",
    "screened_relevant_live_vaccine_history",
]

PniMmrEmergencyState = Literal[
    "not_assessed",
    "not_present",
    "present",
]


class PniMmrLiveVaccineEvent(BaseModel):
    vaccine_group: PniMmrExternalLiveVaccineGroup
    administration_date: date


class PniMmrInteractionContext(BaseModel):
    history_screen_state: (
        PniMmrInteractionHistoryScreenState
    )

    recent_live_vaccine_events: list[
        PniMmrLiveVaccineEvent
    ] = Field(
        default_factory=list,
    )

    planned_same_day_vaccine_groups: list[
        PniMmrExternalLiveVaccineGroup
    ] = Field(
        default_factory=list,
    )

    epidemiologic_emergency_concomitant_circulation_state: (
        PniMmrEmergencyState
    ) = "not_assessed"

    exceptional_15_day_interval_authorized: bool = False

    @model_validator(
        mode="after"
    )
    def validate_mmr_interaction_context(
        self,
    ):
        if (
            self.history_screen_state
            == "screened_no_relevant_recent_live_vaccine"
            and self.recent_live_vaccine_events
        ):
            raise ValueError(
                "screened-clear MMR interaction context "
                "cannot contain recent live-vaccine events"
            )

        if (
            self.history_screen_state
            == "screened_relevant_live_vaccine_history"
            and not self.recent_live_vaccine_events
        ):
            raise ValueError(
                "documented MMR live-vaccine history state "
                "requires at least one recent event"
            )

        event_keys = [
            (
                event.vaccine_group,
                event.administration_date,
            )
            for event
            in self.recent_live_vaccine_events
        ]

        if len(
            event_keys
        ) != len(
            set(
                event_keys
            )
        ):
            raise ValueError(
                "duplicate MMR live-vaccine interaction event"
            )

        if len(
            self.planned_same_day_vaccine_groups
        ) != len(
            set(
                self.planned_same_day_vaccine_groups
            )
        ):
            raise ValueError(
                "duplicate planned same-day MMR vaccine group"
            )

        return self

PniVaricellaExternalLiveVaccineGroup = Literal[
    "mmr",
    "yellow_fever",
]

PniVaricellaInteractionHistoryScreenState = Literal[
    "not_screened",
    "screened_no_relevant_recent_live_vaccine",
    "screened_relevant_live_vaccine_history",
]

class PniVaricellaLiveVaccineEvent(BaseModel):
    vaccine_group: PniVaricellaExternalLiveVaccineGroup
    administration_date: date


class PniVaricellaInteractionContext(BaseModel):
    history_screen_state: (
        PniVaricellaInteractionHistoryScreenState
    )

    recent_live_vaccine_events: list[
        PniVaricellaLiveVaccineEvent
    ] = Field(
        default_factory=list,
    )

    planned_same_day_vaccine_groups: list[
        PniVaricellaExternalLiveVaccineGroup
    ] = Field(
        default_factory=list,
    )

    exceptional_15_day_interval_authorized: bool = False

    @model_validator(
        mode="after"
    )
    def validate_varicella_interaction_context(
        self,
    ):
        if (
            self.history_screen_state
            == "screened_no_relevant_recent_live_vaccine"
            and self.recent_live_vaccine_events
        ):
            raise ValueError(
                "screened-clear VZ interaction context "
                "cannot contain recent live-vaccine events"
            )

        if (
            self.history_screen_state
            == "screened_relevant_live_vaccine_history"
            and not self.recent_live_vaccine_events
        ):
            raise ValueError(
                "documented VZ live-vaccine history state "
                "requires at least one recent event"
            )

        event_keys = [
            (
                event.vaccine_group,
                event.administration_date,
            )
            for event
            in self.recent_live_vaccine_events
        ]

        if len(
            event_keys
        ) != len(
            set(
                event_keys
            )
        ):
            raise ValueError(
                "duplicate VZ live-vaccine interaction event"
            )

        if len(
            self.planned_same_day_vaccine_groups
        ) != len(
            set(
                self.planned_same_day_vaccine_groups
            )
        ):
            raise ValueError(
                "duplicate planned same-day VZ vaccine group"
            )

        return self

PniDengueDiseaseHistoryScreenState = Literal[
    "not_screened",
    "screened_no_relevant_dengue_history",
    "screened_dengue_history",
]

PniDengueOtherArbovirusDisease = Literal[
    "yellow_fever",
    "chikungunya",
    "zika",
]

PniDengueOtherArbovirusScreenState = Literal[
    "not_screened",
    "screened_no_relevant_other_arbovirus",
    "screened_relevant_other_arbovirus_history",
]

PniDengueBloodProductScreenState = Literal[
    "not_screened",
    "screened_no_relevant_blood_product_exposure",
    "screened_relevant_blood_product_exposure",
]

PniDengueLiveVaccineHistoryScreenState = Literal[
    "not_screened",
    "screened_no_relevant_recent_live_vaccine",
    "screened_relevant_live_vaccine_history",
]


class PniDengueOtherArbovirusEvent(BaseModel):
    disease: PniDengueOtherArbovirusDisease
    recovery_date: date


class PniDengueClinicalTimingContext(BaseModel):
    dengue_history_screen_state: (
        PniDengueDiseaseHistoryScreenState
    )

    dengue_onset_dates: list[
        date
    ] = Field(
        default_factory=list,
    )

    other_arbovirus_screen_state: (
        PniDengueOtherArbovirusScreenState
    )

    other_arbovirus_events: list[
        PniDengueOtherArbovirusEvent
    ] = Field(
        default_factory=list,
    )

    blood_product_screen_state: (
        PniDengueBloodProductScreenState
    )

    latest_relevant_blood_product_treatment_end_date: (
        date | None
    ) = None

    minimum_6_week_interval_authorized: bool = False

    @model_validator(
        mode="after"
    )
    def validate_dengue_clinical_timing_context(
        self,
    ):
        if (
            self.dengue_history_screen_state
            == "screened_no_relevant_dengue_history"
            and self.dengue_onset_dates
        ):
            raise ValueError(
                "screened-clear dengue history cannot "
                "contain dengue onset dates"
            )

        if (
            self.dengue_history_screen_state
            == "screened_dengue_history"
            and not self.dengue_onset_dates
        ):
            raise ValueError(
                "documented dengue history requires "
                "at least one onset date"
            )

        if (
            self.dengue_history_screen_state
            != "screened_dengue_history"
            and self.dengue_onset_dates
        ):
            raise ValueError(
                "dengue onset dates require documented "
                "dengue history state"
            )

        if len(
            self.dengue_onset_dates
        ) != len(
            set(
                self.dengue_onset_dates
            )
        ):
            raise ValueError(
                "duplicate dengue onset date"
            )

        if (
            self.other_arbovirus_screen_state
            == "screened_no_relevant_other_arbovirus"
            and self.other_arbovirus_events
        ):
            raise ValueError(
                "screened-clear other-arbovirus history "
                "cannot contain events"
            )

        if (
            self.other_arbovirus_screen_state
            == "screened_relevant_other_arbovirus_history"
            and not self.other_arbovirus_events
        ):
            raise ValueError(
                "documented other-arbovirus history "
                "requires at least one event"
            )

        if (
            self.other_arbovirus_screen_state
            != "screened_relevant_other_arbovirus_history"
            and self.other_arbovirus_events
        ):
            raise ValueError(
                "other-arbovirus events require documented "
                "relevant-history state"
            )

        arbovirus_keys = [
            (
                event.disease,
                event.recovery_date,
            )
            for event in self.other_arbovirus_events
        ]

        if len(
            arbovirus_keys
        ) != len(
            set(
                arbovirus_keys
            )
        ):
            raise ValueError(
                "duplicate other-arbovirus recovery event"
            )

        if (
            self.blood_product_screen_state
            == "screened_no_relevant_blood_product_exposure"
            and (
                self.latest_relevant_blood_product_treatment_end_date
                is not None
                or self.minimum_6_week_interval_authorized
            )
        ):
            raise ValueError(
                "screened-clear blood-product context cannot "
                "contain treatment timing or minimum authorization"
            )

        if (
            self.blood_product_screen_state
            == "screened_relevant_blood_product_exposure"
            and (
                self.latest_relevant_blood_product_treatment_end_date
                is None
            )
        ):
            raise ValueError(
                "documented blood-product exposure requires "
                "treatment-end date"
            )

        if (
            self.blood_product_screen_state
            != "screened_relevant_blood_product_exposure"
            and (
                self.latest_relevant_blood_product_treatment_end_date
                is not None
            )
        ):
            raise ValueError(
                "blood-product treatment-end date requires "
                "documented relevant exposure"
            )

        if (
            self.minimum_6_week_interval_authorized
            and (
                self.blood_product_screen_state
                != "screened_relevant_blood_product_exposure"
            )
        ):
            raise ValueError(
                "six-week minimum authorization requires "
                "documented relevant blood-product exposure"
            )

        return self


class PniDengueExternalLiveVaccineEvent(BaseModel):
    administration_date: date


class PniDengueLiveVaccineInteractionContext(BaseModel):
    history_screen_state: (
        PniDengueLiveVaccineHistoryScreenState
    )

    recent_live_vaccine_events: list[
        PniDengueExternalLiveVaccineEvent
    ] = Field(
        default_factory=list,
    )

    planned_same_day_live_vaccine: bool = False

    @model_validator(
        mode="after"
    )
    def validate_dengue_live_vaccine_interaction_context(
        self,
    ):
        if (
            self.history_screen_state
            == "screened_no_relevant_recent_live_vaccine"
            and self.recent_live_vaccine_events
        ):
            raise ValueError(
                "screened-clear DNG4 live-vaccine context "
                "cannot contain recent events"
            )

        if (
            self.history_screen_state
            == "screened_relevant_live_vaccine_history"
            and not self.recent_live_vaccine_events
        ):
            raise ValueError(
                "documented DNG4 live-vaccine history "
                "requires at least one event"
            )

        if (
            self.history_screen_state
            != "screened_relevant_live_vaccine_history"
            and self.recent_live_vaccine_events
        ):
            raise ValueError(
                "DNG4 live-vaccine events require "
                "documented relevant-history state"
            )

        event_dates = [
            event.administration_date
            for event in self.recent_live_vaccine_events
        ]

        if len(
            event_dates
        ) != len(
            set(
                event_dates
            )
        ):
            raise ValueError(
                "duplicate DNG4 live-vaccine interaction event"
            )

        return self
