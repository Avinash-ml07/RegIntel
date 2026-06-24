from pydantic import BaseModel, Field
from typing import List

class MeasurableActionPointSchema(BaseModel):
    originating_clause: str = Field(description="Reference ID of the clause generating this item.")
    identified_policy_gap: str = Field(description="Observed gap between existing system/policy and new regulation.")
    concrete_action_required: str = Field(description="Direct, precise technical task or operational action required.")
    binary_testable_success_criterion: str = Field(description="A strictly binary verification check (Pass/Fail criteria).")
    deadline: str = Field(description="Relative or absolute completion target timeframe.")
    responsible_departments: List[str] = Field(description="List of internal target teams to coordinate execution.")

class MAPListSchema(BaseModel):
    maps: List[MeasurableActionPointSchema] = Field(description="Collection of generated actionable tasks.")