from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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

class HemodynamicsInput(BaseModel):
    systolic_bp: float = Field(gt=0)
    diastolic_bp: float = Field(gt=0)
    heart_rate: float = Field(gt=0)


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

    interpretation_pt: str
    interpretation_en: str

    map_note_pt: str
    map_note_en: str
