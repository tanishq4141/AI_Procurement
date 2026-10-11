from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ProcurementRequest(BaseModel):
    employee_name: str = Field(..., description="Full name of requesting employee")
    department: str = Field(..., description="Department name (e.g. Engineering, Marketing)")
    tool_name: str = Field(..., description="Name of software or tool requested")
    estimated_cost: Optional[float] = Field(None, description="Estimated total cost in USD")
    seat_count: Optional[int] = Field(None, description="Number of user seats requested")
    vendor_name: Optional[str] = Field(None, description="Software vendor or publisher name")
    vendor_url: Optional[str] = Field(None, description="Vendor website or documentation URL")
    justification: str = Field(..., description="Business need and intended use case")
    handles_customer_data: Optional[bool] = Field(False, description="Whether software accesses production systems or sensitive/customer data")
    architecture: Optional[Literal["ARCHITECTURE_A", "ARCHITECTURE_B"]] = Field(
        "ARCHITECTURE_A", description="Target agent architecture"
    )

class EvidenceItem(BaseModel):
    source: Literal["software_catalog", "team_budget", "vendor_security", "policy"] = Field(
        ..., description="Data source producing the evidence"
    )
    fact: str = Field(..., description="Verified direct factual finding or quote from data/tool")
    status: Literal["PASS", "FAIL", "WARNING"] = Field(
        ..., description="Assessment status against compliance policy"
    )

class ToolExecutionTrace(BaseModel):
    tool_name: str
    arguments: dict
    output: dict
    duration_ms: float
    status: Literal["SUCCESS", "ERROR"] = "SUCCESS"
    error_message: Optional[str] = None

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

class ProcurementRecommendation(BaseModel):
    recommendation: Literal["APPROVE", "REJECT", "ESCALATE_FOR_REVIEW", "REQUEST_MORE_INFO"] = Field(
        ..., description="High-level decision action"
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list, description="Structured verified evidence from deterministic checks & tools"
    )
    approvals_required: List[str] = Field(
        default_factory=list,
        description="Required stakeholders: DIRECT_MANAGER, DEPT_HEAD, IT_SECURITY, FINANCE_VP"
    )
    missing_information: List[str] = Field(
        default_factory=list, description="Required fields or clarifications missing from the request"
    )
    risk_flags: List[str] = Field(
        default_factory=list, description="Identified compliance, financial, or security risks"
    )
    next_step: str = Field(
        ..., description="Immediate next actionable step for human reviewer or requester"
    )
    # Execution metadata for evaluation and UI observability
    architecture: Optional[str] = None
    execution_time_ms: Optional[float] = None
    tool_calls: Optional[List[ToolExecutionTrace]] = Field(default_factory=list)
    token_usage: Optional[TokenUsage] = None

class HumanReviewAction(BaseModel):
    request_id: str
    decision: Literal["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"]
    target_escalation: Optional[str] = None
    notes: Optional[str] = None
    reviewer: str = "Procurement Reviewer"
