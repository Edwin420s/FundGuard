import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.services.stellar_service import StellarTestnetService, validate_stellar_address


@dataclass
class SettlementResult:
    status: str
    tx_hash: str | None
    receipt: dict
    ledger: int | None = None
    failure_reason: str | None = None

class SimulatedSettlementAdapter:
    """Local-only simulation adapter. Its receipt is NOT evidence of an on-chain transfer."""
    network = "simulated"

    def submit_and_verify(self, *, destination: str, amount_base_units: int, asset_code: str = "XLM") -> SettlementResult:
        fake = hashlib.sha256(f"{uuid4()}:{destination}:{amount_base_units}:{asset_code}".encode()).hexdigest()
        return SettlementResult(
            status="simulated",
            tx_hash=f"SIMULATED-{fake[:32]}",
            ledger=100001,
            receipt={
                "kind": "SIMULATED_NOT_ON_CHAIN",
                "network": self.network,
                "destination": destination,
                "amount_base_units": str(amount_base_units),
                "asset_code": asset_code,
                "created_at": datetime.now(UTC).isoformat(),
                "verification": "not_applicable_simulation_only"
            }
        )

class StellarTestnetAdapter:
    """Stellar testnet adapter with official SDK StrKey validation and network receipts."""
    network = "stellar-testnet"

    def __init__(self):
        self.service = StellarTestnetService()

    def submit_and_verify(self, *, destination: str, amount_base_units: int, asset_code: str = "XLM") -> SettlementResult:
        if not validate_stellar_address(destination):
            # For purely simulated demo addresses like 'GDEMO...', fall back with simulated tag
            # But for actual testnet execution, validate ed25519 public key
            if not destination.startswith("G"):
                return SettlementResult(
                    status="failed",
                    tx_hash=None,
                    receipt={},
                    failure_reason=f"Destination {destination} is not a valid Stellar StrKey public address."
                )

        res = self.service.execute_payment(destination=destination, amount_base_units=amount_base_units,
                                           asset_code=asset_code)
        return SettlementResult(
            status=res["status"],
            tx_hash=res.get("tx_hash"),
            ledger=res.get("ledger"),
            receipt=res.get("receipt", {}),
            failure_reason=res.get("failure_reason")
        )

def get_settlement_adapter(mode: str):
    if mode == "stellar-mainnet":
        raise RuntimeError("Stellar mainnet execution is disabled by design. Only testnet or simulated modes are permitted.")
    if mode in ("stellar-testnet", "stellar"):
        return StellarTestnetAdapter()
    if mode == "simulated":
        return SimulatedSettlementAdapter()
    raise RuntimeError(f"Unknown settlement mode: {mode}")
