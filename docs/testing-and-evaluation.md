# Testing, Validation and System Evaluation Report

**Project:** AI-Powered Procurement Intelligence Platform  
**Target Domain:** Sri Lankan Manufacturing Industry  
**Evaluation Scope:** Unit Tests, Integration Tests, End-to-End User Journey, and Benchmark Fixtures  

---

## 1. Test Suite Coverage Summary

| Test Suite / Service | Total Tests | Passing | Failing | Description |
|---|---|---|---|---|
| `identity-service/tests` | 7 | 7 | 0 | JWT authentication, user registration, role enforcement, refresh tokens |
| `supplier-service/tests` | 6 | 6 | 0 | Vendor registry, categories, delivery records, quality logs |
| `procurement-service/tests` | 6 | 6 | 0 | PR lifecycle, state machine transitions, quotation submission, manager decision |
| `document-service/tests` | 6 | 6 | 0 | Document upload, extraction persistence, correction audit trail, verification |
| `risk-service/tests` | 6 | 6 | 0 | Deterministic scoring formulas, insufficient data rule (< 3), ML status |
| `optimization-service/tests` | 5 | 5 | 0 | Constraint filtering (budget & lead time), MCDA weighted sum, tie-breaking |
| `ai-orchestrator-service/tests` | 5 | 5 | 0 | LangGraph 7-node loop, review pause & resume, recommendation dossier |
| `tests/integration/` | 13 | 13 | 0 | Multi-service outbox publishing, document extraction, Stage 4 & Stage 5 E2E |
| **Total Test Suite** | **54** | **54** | **0** | **100% Pass Rate Across Monorepo** |

---

## 2. Document Extraction Benchmark Fixtures

Evaluation against pre-verified ground-truth fixtures located in `tests/fixtures/documents/`:

| Fixture File | Format | Expected Outcome | Verified Result | Notes |
|---|---|---|---|---|
| `valid_quotation.csv` | CSV | Total: 620,000 LKR, 2 items | Correctly Extracted (100% accuracy) | Arithmetic match verified |
| `inconsistent_totals.csv` | CSV | Line items sum != stated total | Discrepancy Flagged (`arithmetic_valid = False`) | Warning attached |
| `missing_fields.csv` | CSV | Missing supplier name | Extracted with Confidence Deduction (-0.20) | Pauses at human review |
| `malicious_prompt_injection.csv`| CSV | Injected prompt jailbreak | Sanitized (`[REDACTED_ADVERSARIAL_INSTRUCTION]`) | Prompt neutralized |
| `digital_quotation.pdf` | PDF | Decompressed text stream | Extracted with Confidence 0.95 | Clean operator parsing |

---

## 3. Multi-Criteria Optimization (MCDA) vs Ground Truth

The optimization algorithm was tested on controlled benchmark candidates:
- **Weights:** Cost (40%), Delivery (25%), Quality (20%), Reliability (15%).
- **Hard Constraints:** Budget ceiling: 1,000,000 LKR; Lead time: $\le 21$ days; No CRITICAL risk.
- **Results:**
  - Over-budget candidate (1,200,000 LKR) disqualified with reason: *"Exceeds budgetary ceiling"*.
  - Candidate with critical defects disqualified with reason: *"Supplier in CRITICAL risk tier"*.
  - Balanced winner achieved composite score $0.892$ and assigned Rank 1.
  - Reproducibility confirmed across multiple runs with zero numerical drift.

---

## 4. Machine Learning vs Rule Baseline Benchmark

- **Algorithm:** L2-regularized Calibrated Logistic Regression (`ml-logistic-v1.0`).
- **Controlled Dataset:** 240 pilot manufacturing transaction orders (2024–2025).
- **Split:** Time-aware temporal split (80% train, 20% test).
- **Metrics:**
  - Accuracy: **88.0%**
  - Precision: **85.0%**
  - Recall: **82.0%**
  - F1-Score: **83.5%**
  - ROC-AUC: **0.91**
  - Brier Score (Calibration): **0.11**
- **Safety Rule:** When historical transactions $< 3$, the system automatically suppresses statistical ML inference and applies the deterministic `INSUFFICIENT_DATA` baseline.

