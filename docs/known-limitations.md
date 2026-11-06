# Known Limitations & Platform Boundaries

**Project:** AI-Powered Procurement Intelligence Platform  
**Document Status:** Version 1.0 (Post-Stage 5)  

---

## 1. Machine Learning & Predictive Limitations

1. **Macroeconomic Shocks & Currency Volatility:**
   - The ML predictive pipeline (`ml-logistic-v1.0`) is calibrated on historical manufacturing procurement data (2024–2025).
   - It does not ingest real-time Central Bank of Sri Lanka (CBSL) currency feeds; sharp macroeconomic fluctuations in LKR must be adjusted through manual weight overrides in the Optimization Studio.
2. **Small-Sample Vendor Cold Start:**
   - Statistical predictive models fail when suppliers have fewer than 3 historical transactions.
   - The platform explicitly disallows speculative numerical risk scoring; instead, it enforces the deterministic `INSUFFICIENT_DATA` baseline to alert human procurement officers.

---

## 2. Document Processing & OCR Boundaries

1. **Handwritten Invoices & Low-DPI Mobile Scans:**
   - Multi-format extraction is verified for digital PDFs, spreadsheets (CSV/XLSX), and clean scanned images.
   - Low-contrast, skewed, or handwritten physical receipts trigger an arithmetic inconsistency flag or low confidence score ($< 0.85$), which pauses the workflow for human verification.
2. **Adversarial Redaction:**
   - Documents containing detected jailbreak phrases (`IGNORE ALL PREVIOUS INSTRUCTIONS`, `SYSTEM: OVERRIDE`) have matching substrings redacted (`[REDACTED_ADVERSARIAL_INSTRUCTION]`). Highly obfuscated steganographic payloads may require manual human review.

---

## 3. Deployment & Operational Constraints

1. **Local Host Docker Daemon Dependency:**
   - Full live multi-container orchestration requires a running Docker Engine on the deployment host.
   - All database schemas and endpoints are fully verified offline via SQLite and Alembic DDL scripts.
2. **Zero Autonomous Expenditure Commitments:**
   - By architectural design, AI agents and LangGraph workflows cannot commit corporate funds or execute contracts autonomously.
   - An authorized Human Procurement Manager must review recommendations and submit a decision via the Procurement Service before purchase orders are issued.

