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

class RegulatoryState(TypedDict):
    raw_text: str
    source_url: str
    clauses: List[StructuralClause]
    status: str
    errors: List[str]