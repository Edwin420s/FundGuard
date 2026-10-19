# Stellar Testnet Integration Guide — Omega FundGuard

## 1. Overview & Current Status

Stellar Testnet integration in **Omega FundGuard** is **fully implemented and verified end-to-end**. The system provides production-grade integration with the official Stellar Python SDK (`stellar-sdk >= 13.0.0`), live Horizon RPC servers, ed25519 StrKey public key validation, automated testnet Friendbot funding, custody account isolation, and independent on-chain transaction & payment-operation verification.

---

## 2. Key Architectural Invariants

1. **Integer Base Units (Stellar Stroops):**
   - Financial transitions never use floating-point arithmetic.
   - Conversion standard: $1\text{ XLM} = 10,000,000\text{ stroops}$.
   - Amounts are strictly validated and stored as positive integer base units.

2. **Official StrKey Ed25519 Address Validation:**
   - Addresses are validated using the official Stellar SDK:
     ```python
     StrKey.is_valid_ed25519_public_key(address.strip())
     ```
   - Unrecognized addresses, malformed checksums, or non-ed25519 public keys are rejected with validation errors.

3. **Isolated Signer / Custody Boundary:**
   - Secret keys are held strictly on the backend custody boundary (`stellar_testnet_custody.json` or environment `STELLAR_SOURCE_SECRET_KEY`).
   - The browser frontend and the Omega MeTTa agent **never** receive or transmit secret keys.

4. **Dynamic Operation Routing (`create_account` vs `payment`):**
   - On the Stellar testnet, sending a payment to an uninitialized account fails with `op_no_destination`.
   - The FundGuard settlement engine inspects the destination account on Horizon prior to building the transaction:
     - **Unfunded recipient:** Appends `create_account_op` with `starting_balance`.
     - **Existing recipient:** Appends `payment_op` with native `Asset.native()`.

5. **Independent Horizon Verification:**
   - After transaction broadcast, `verify_transaction_and_payment` independently queries Horizon:
     1. Checks `https://horizon-testnet.stellar.org/transactions/{tx_hash}` for confirmation and ledger index.
     2. Queries `https://horizon-testnet.stellar.org/transactions/{tx_hash}/operations` to verify the exact destination, asset type/code (`XLM`), and stroops amount.
     3. Accepts both `payment` and `create_account` native operations.

6. **Safety & Mainnet Disablement:**
   - Mainnet execution is strictly prohibited by software design:
     ```python
     if mode == "stellar-mainnet":
         raise RuntimeError("Stellar mainnet execution is disabled by design. Only testnet or simulated modes are permitted.")
     ```

---

## 3. Real On-Chain Testnet Verification

Live testnet transactions have been broadcast and independently verified on Stellar Testnet Horizon:

| Parameter | Network Evidence |
| :--- | :--- |
| **Network** | `stellar-testnet` (`Test SDF Network ; September 2015`) |
| **Transaction Hash** | `ad0d83372555028f7e0f2c07b234608d8b91e7efc2655d896756bbb157ae4bbc` |
| **Confirmed Ledger** | `5354762` |
| **Operation Type** | `create_account` |
| **Verified Amount** | `34.0000000 XLM` (`340,000,000 stroops`) |
| **Destination** | `GCQ7LIPWUGSV72PCO3TCS3W5EGLG7XJ2WUSCJUSN7P25FCRQ7ZJ6222E` |
| **Explorer Link** | [Stellar.Expert Testnet Explorer](https://stellar.expert/explorer/testnet/tx/ad0d83372555028f7e0f2c07b234608d8b91e7efc2655d896756bbb157ae4bbc) |

---

## 4. REST API Endpoints

The backend exposes dedicated Stellar Testnet endpoints under `/api/v1/stellar/`:

- `GET /api/v1/stellar/custody`: Loads custody public key, live Horizon balance, sequence number, and funded status.
- `POST /api/v1/stellar/fund-friendbot`: Automates funding of the custody account with 10,000 testnet XLM via `https://friendbot.stellar.org`.
- `POST /api/v1/stellar/generate-keypair?fund_via_friendbot=true`: Generates a valid ed25519 keypair and optionally funds it.
- `POST /api/v1/stellar/verify-tx?tx_hash=...&destination=...&amount_base_units=...`: Queries Horizon RPC to independently verify an on-chain transaction.

---

## 5. Frontend Stellar Testnet Console

The React dashboard includes a dedicated **Stellar Testnet Console** view and toolbar selector:

- **Settlement Mode Toggle:** Seamlessly toggle between `Simulated Mode` (offline testing) and `Stellar Testnet` (live Horizon operations).
- **Custody Keypair Card:** Live display of custody public key, sequence, subentries, and live XLM/stroops balance.
- **Friendbot Quick Top-Up:** 1-click button to fund the custody account with 10,000 testnet XLM.
- **Auto-Generate Testnet Recipient:** 1-click generation and funding of genuine StrKey testnet accounts for hackathon teams.
- **Horizon Transaction Inspector:** Paste any transaction hash, destination, and amount to trigger an on-chain verification check with direct link to `stellar.expert`.
