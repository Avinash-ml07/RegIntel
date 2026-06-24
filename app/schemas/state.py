from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict

class RegulatoryMetadata(BaseModel):
    authority: str = Field(description="Regulatory source authority (e.g., RBI, SEBI)")
    circular_id: str = Field(description="Unique circular identifier or reference number")
    publish_date: str = Field(description="Parsed publish date of the circular")
    effective_date: str = Field(description="Calculated effective compliance date")
    subject: str = Field(description="Extracted circular subject header")

class StructuralClause(BaseModel):
    clause_id: str = Field(description="Synthesized structured unique ID")
    clause_reference: str = Field(description="Section/clause reference identifier (e.g., 1.1, Section 2(a))")
    title: str = Field(description="Parsed structural header or categorical designation")
    text: str = Field(description="Extracted clean body text under the clause")
    metadata: RegulatoryMetadata = Field(description="Regulatory document's parent metadata")

class MeasurableActionPoint(BaseModel):
    originating_clause: str = Field(description="Reference key of the clause generating this action point")
    identified_policy_gap: str = Field(description="Mismatch found between local bank policy and regulatory mandate")
    concrete_action_required: str = Field(description="Specific, step-by-step technical or operational change required")
    binary_testable_success_criterion: str = Field(description="Clear test case verifying completion of the mandate")
    deadline: str = Field(description="Target completion date or timeline requirement")
    responsible_departments: List[str] = Field(description="Internal bank divisions responsible for execution")

class RegulatoryState(TypedDict):
    raw_text: str
    source_url: str
    clauses: List[StructuralClause]
    maps: List[MeasurableActionPoint]
    encrypted_privacy_map: str  # Fernet encrypted symmetric key-value map
    status: str
    errors: List[str]