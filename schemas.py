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
