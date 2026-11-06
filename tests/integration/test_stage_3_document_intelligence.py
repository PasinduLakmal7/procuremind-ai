import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from shared.extraction.extractor import QuotationExtractor

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "documents"


def test_valid_csv_extraction():
    csv_bytes = (FIXTURES_DIR / "valid_quotation.csv").read_bytes()
    res = QuotationExtractor.process_document(csv_bytes, "valid_quotation.csv")

    assert res.supplier_name == "Lanka Steel Fabricators PLC"
    assert res.quotation_number == "QUO-LSF-2026-004"
    assert len(res.line_items) == 2
    assert res.line_items[0].item_name == "Steel Angle Bar 50x50x5mm"
    assert res.line_items[0].quantity == 100.0
    assert res.line_items[0].unit_price == 3200.0
    assert res.arithmetic_valid is True
    assert res.overall_confidence >= 0.90


def test_inconsistent_totals_arithmetic_flag():
    csv_bytes = (FIXTURES_DIR / "inconsistent_totals.csv").read_bytes()
    res = QuotationExtractor.process_document(csv_bytes, "inconsistent_totals.csv")

    assert res.supplier_name == "Precision Cutters Ltd"
    # Items sum: 50*4000 (200,000) + 2*35000 (70,000) = 270,000. But stated total is 999,999!
    assert res.arithmetic_valid is False
    assert any("Arithmetic Mismatch" in f for f in res.flagged_reasons)
    # Confidence should be penalized for arithmetic failure
    assert res.overall_confidence < 0.85


def test_missing_fields_warning():
    csv_bytes = (FIXTURES_DIR / "missing_fields.csv").read_bytes()
    res = QuotationExtractor.process_document(csv_bytes, "missing_fields.csv")

    assert any("Supplier name" in f for f in res.flagged_reasons)
    assert any("Quotation reference number" in f for f in res.flagged_reasons)
    assert res.overall_confidence < 0.80


def test_malicious_prompt_injection_sanitization():
    csv_bytes = (FIXTURES_DIR / "malicious_prompt_injection.csv").read_bytes()
    res = QuotationExtractor.process_document(csv_bytes, "malicious_prompt_injection.csv")

    assert res.supplier_name == "Infiltrator Tech"
    # Adversarial instruction should have triggered security alert
    assert any("Security Alert" in f for f in res.flagged_reasons)


def test_digital_pdf_stream_extraction():
    pdf_bytes = (FIXTURES_DIR / "digital_quotation.pdf").read_bytes()
    res = QuotationExtractor.process_document(pdf_bytes, "digital_quotation.pdf")

    assert "Ceylon Structural Engineering" in res.supplier_name
    assert "QUO-CSE-2026-105" in res.quotation_number
    assert res.total_cost == 1250000.0
    assert res.overall_confidence >= 0.80

