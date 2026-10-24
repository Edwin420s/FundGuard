from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc():
    return datetime.now(UTC)

def new_id():
    return str(uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    memberships: Mapped[list["Membership"]] = relationship(back_populates="organization", cascade="all, delete-orphan")

class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="organizer", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    organization: Mapped["Organization"] = relationship(back_populates="memberships")
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_user_per_org"),)

class UserAccount(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="organizer", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Competition(Base):
    __tablename__ = "competitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), default="org-fundguard-global", nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    network: Mapped[str] = mapped_column(String(32), default="stellar-testnet", nullable=False)
    default_currency: Mapped[str] = mapped_column(String(12), default="XLM", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    recipients: Mapped[list["Recipient"]] = relationship(back_populates="competition", cascade="all, delete-orphan")
    batches: Mapped[list["PayoutBatch"]] = relationship(back_populates="competition", cascade="all, delete-orphan")
    policies: Mapped[list["FundingPolicyVersion"]] = relationship(back_populates="competition", cascade="all, delete-orphan")

class FundingPolicyVersion(Base):
    __tablename__ = "funding_policy_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), default="org-fundguard-global", nullable=False, index=True)
    competition_id: Mapped[str] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    rules_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    rules_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), default="system", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    competition: Mapped["Competition"] = relationship(back_populates="policies")
    __table_args__ = (UniqueConstraint("competition_id", "version", name="uq_policy_version_per_competition"),)

class Recipient(Base):
    __tablename__ = "recipients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), default="org-fundguard-global", nullable=False, index=True)
    competition_id: Mapped[str] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(80), nullable=False)
    eligibility_status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    eligibility_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    competition: Mapped["Competition"] = relationship(back_populates="recipients")
    payouts: Mapped[list["Payout"]] = relationship(back_populates="recipient")
    __table_args__ = (UniqueConstraint("competition_id", "wallet_address", name="uq_recipient_wallet_per_competition"),)

class EligibilityDecision(Base):
    __tablename__ = "eligibility_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("recipients.id", ondelete="CASCADE"), nullable=False, index=True)
    competition_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(160), nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class PayoutBatch(Base):
    __tablename__ = "payout_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), default="org-fundguard-global", nullable=False, index=True)
    competition_id: Mapped[str] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="proposed", nullable=False)
    asset_code: Mapped[str] = mapped_column(String(12), default="XLM", nullable=False)
    asset_type: Mapped[str] = mapped_column(String(16), default="native", nullable=False)
    total_base_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserve_base_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_hash: Mapped[str | None] = mapped_column(String(71), nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(24), default="simulated", nullable=False)
    competition: Mapped["Competition"] = relationship(back_populates="batches")
    payouts: Mapped[list["Payout"]] = relationship(back_populates="batch", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="batch", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("competition_id", "idempotency_key", name="uq_batch_idempotency"),)

class Payout(Base):
    __tablename__ = "payouts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("payout_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("recipients.id"), nullable=False, index=True)
    amount_base_units: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="proposed", nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    receipt_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    batch: Mapped["PayoutBatch"] = relationship(back_populates="payouts")
    recipient: Mapped["Recipient"] = relationship(back_populates="payouts")

class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("payout_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    approver: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(48), default="finance_approver", nullable=False)
    decision: Mapped[str] = mapped_column(String(24), default="approved", nullable=False)
    approved_content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    batch: Mapped["PayoutBatch"] = relationship(back_populates="approvals")

class SettlementAttempt(Base):
    __tablename__ = "settlement_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    payout_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(32), default="stellar-testnet", nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ledger: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_payload: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    payout_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ledger: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operation_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_account: Mapped[str] = mapped_column(String(80), nullable=False)
    destination: Mapped[str] = mapped_column(String(80), nullable=False)
    asset_code: Mapped[str] = mapped_column(String(12), default="XLM", nullable=False)
    asset_type: Mapped[str] = mapped_column(String(16), default="native", nullable=False)
    amount_base_units: Mapped[int] = mapped_column(Integer, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="independently_verified", nullable=False)

class ReconciliationCase(Base):
    __tablename__ = "reconciliation_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    payout_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), default="open", nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    resolution_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    resolved_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class TreasuryReservation(Base):
    __tablename__ = "treasury_reservations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    competition_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    asset_code: Mapped[str] = mapped_column(String(12), default="XLM", nullable=False)
    reserved_base_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    competition_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    actor: Mapped[str] = mapped_column(String(160), default="local-demo-user", nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    previous_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(String(36), default="org-fundguard-global", nullable=False, index=True)
    competition_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    intent: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="completed", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metta_expressions_evaluated: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    tool_calls: Mapped[list["AgentToolCall"]] = relationship(back_populates="agent_run", cascade="all, delete-orphan")

class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    arguments_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    agent_run: Mapped["AgentRun"] = relationship(back_populates="tool_calls")

class LearnedRule(Base):
    __tablename__ = "learned_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    competition_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(120), nullable=False)
    rule_expression: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), default="human_reviewer", nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class RecipientReliability(Base):
    __tablename__ = "recipient_reliability"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipient_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    successful_payouts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disputes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

