from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=128)
    organization_name: str = Field(default="My Organization", min_length=2, max_length=160)
    role: Literal["organizer", "sponsor", "judge"] = "organizer"

class UserLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    organization_id: str | None = None
    organization_name: str
    role: str
    token: str

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80)

class CompetitionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)
    network: Literal["stellar-testnet"] = "stellar-testnet"
    default_currency: str = Field(default="XLM", max_length=12)
    organization_id: str | None = None
    created_by: str = Field(default="Administrator", max_length=160)

class CompetitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    status: str
    network: str
    created_at: str | object

class PolicyVersionCreate(BaseModel):
    target_eligible_count: int = Field(default=50, ge=1, le=100_000)
    total_fund_base_units: int = Field(default=17_000_000_000, gt=0)
    currency: str = Field(default="XLM", max_length=12)
    illustrative_fiat_usd: str = Field(default="1700.00", max_length=32)

class PolicySimulateRequest(BaseModel):
    target_eligible_count: int = Field(default=50, ge=1)
    eligible_count: int = Field(default=20, ge=0)
    total_fund_base_units: int = Field(default=17_000_000_000, gt=0)

class RecipientCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    wallet_address: str = Field(min_length=3, max_length=80)
    eligibility_status: Literal["pending", "verified", "rejected"] = "pending"
    eligibility_note: str = Field(default="", max_length=2000)
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="Administrator", max_length=160)

class BulkRecipientItem(BaseModel):
    display_name: str = Field(default="", max_length=160)
    wallet_address: str = Field(default="", max_length=80)
    eligibility_note: str = Field(default="", max_length=2000)
    evidence: dict[str, Any] = Field(default_factory=dict)

class BulkRecipientCreate(BaseModel):
    recipients: list[BulkRecipientItem] = Field(default_factory=list, max_length=1000)
    auto_verify: bool = Field(default=False)
    reviewer: str = Field(default="Bulk Import Reviewer", max_length=160)
    created_by: str = Field(default="Administrator", max_length=160)

class BatchCreate(BaseModel):
    recipient_ids: list[str] = Field(min_length=1, max_length=500)
    amount_base_units: int = Field(gt=0, le=2_000_000_000_000)
    reserve_base_units: int = Field(default=0, ge=0, le=2_000_000_000_000)
    asset_code: Literal["XLM"] = "XLM"
    asset_type: Literal["native"] = "native"
    created_by: str = Field(default="Administrator", max_length=160)

class ApprovalRequest(BaseModel):
    approver: str = Field(min_length=2, max_length=160)
    role: str = Field(default="finance_approver", max_length=48)
    decision: Literal["approved", "rejected", "amendment_requested"] = "approved"
    confirm_hash: str = Field(min_length=10, max_length=71)
    reason: str = Field(default="", max_length=1000)

class ExecuteRequest(BaseModel):
    requested_by: str = Field(min_length=2, max_length=160)
    mode: Literal["simulated", "stellar-testnet"] = "simulated"

class AgentRunRequest(BaseModel):
    intent: str = Field(min_length=2, max_length=80)
    prompt: str = Field(default="", max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)

class ReconciliationResolveRequest(BaseModel):
    decision: Literal["confirm", "fail", "retry"]
    reviewer: str = Field(min_length=2, max_length=160)
    resolution_note: str = Field(min_length=2, max_length=2000)

class NearQuoteRequest(BaseModel):
    from_asset: str = "XLM"
    to_asset: str = "NEAR"
    amount_base_units: int = Field(default=10_000_000, gt=0)

class LearnedRuleCreate(BaseModel):
    competition_id: str | None = None
    rule_name: str = Field(min_length=2, max_length=120)
    rule_expression: str = Field(min_length=2, max_length=2000)
    created_by: str = Field(default="human_finance_reviewer", max_length=160)
    rationale: str = Field(default="", max_length=1000)

class LearningFeedbackRequest(BaseModel):
    recipient_id: str = Field(min_length=2, max_length=64)
    outcome: Literal["confirmed_settlement", "dispute_penalty"] = "confirmed_settlement"
    reviewer: str = Field(default="auditor", max_length=160)
    feedback_note: str = Field(default="", max_length=1000)
    case_id: str | None = None

