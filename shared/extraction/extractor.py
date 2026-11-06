"""Document processing and quotation extraction engine with multi-format support, arithmetic validation, and security sanitization."""
import csv
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shared.extraction.schemas import (
    StructuredQuotationData,
    ExtractedLineItem,
    FieldEvidence,
)

# Adversarial prompt injection keywords
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s*:\s*override",
    r"admin\s+mode",
    r"output\s+only\s+json",
    r"grant\s+permission",
]


class QuotationExtractor:
    """Universal quotation extractor supporting PDF, CSV, XLSX, and image text."""

    @staticmethod
    def detect_format(file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".csv":
            return "CSV"
        elif suffix in [".xlsx", ".xls"]:
            return "XLSX"
        elif suffix == ".pdf":
            # Check if digital PDF contains text streams
            if b"/Font" in file_bytes or b"BT" in file_bytes:
                return "PDF_DIGITAL"
            return "PDF_SCANNED"
        elif suffix in [".png", ".jpg", ".jpeg"]:
            return "IMAGE_OCR"
        return "UNKNOWN"

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> Tuple[str, List[str]]:
        """Scans for prompt injection attacks and neutralizes malicious instructions."""
        warnings = []
        for pat in INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                warnings.append(f"Security Alert: Document contains potential adversarial prompt injection ('{pat}'). Instructions ignored.")
                # Redact matched malicious command
                text = re.sub(pat, "[REDACTED_ADVERSARIAL_INSTRUCTION]", text, flags=re.IGNORECASE)
        return text, warnings

    @classmethod
    def extract_text_from_pdf(cls, file_bytes: bytes) -> str:
        """Extracts text from digital PDF streams using native stream parsing."""
        text_parts = []
        # Find all stream blocks in PDF
        stream_matches = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", file_bytes, re.DOTALL)
        for s in stream_matches:
            try:
                import zlib
                decompressed = zlib.decompress(s)
                for tj in re.findall(rb"\((.*?)\)\s*Tj", decompressed):
                    text_parts.append(tj.decode("latin1", errors="ignore"))
            except Exception:
                for tj in re.findall(rb"\((.*?)\)\s*Tj", s):
                    text_parts.append(tj.decode("latin1", errors="ignore"))

        if not text_parts:
            # Fallback: scan raw ascii strings
            printable = re.findall(rb"[A-Za-z0-9\s,.:;\-\$\(\)\/]{4,}", file_bytes)
            text_parts = [p.decode("latin1", errors="ignore") for p in printable]

        return "\n".join(text_parts)

    @classmethod
    def extract_text_from_xlsx(cls, file_bytes: bytes) -> str:
        """Extracts text from XLSX spreadsheet natively via zip archive."""
        text_lines = []
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                shared_strings = []
                if "xl/sharedStrings.xml" in z.namelist():
                    tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                    for elem in tree.iter():
                        if elem.tag.endswith("t") and elem.text:
                            shared_strings.append(elem.text)

                sheet_names = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
                if sheet_names:
                    sheet_tree = ET.fromstring(z.read(sheet_names[0]))
                    for row in sheet_tree.iter():
                        if row.tag.endswith("row"):
                            row_vals = []
                            for c in row.iter():
                                if c.tag.endswith("c"):
                                    t = c.get("t")
                                    v = c.find("{*}v")
                                    if v is not None and v.text:
                                        if t == "s" and v.text.isdigit():
                                            idx = int(v.text)
                                            if idx < len(shared_strings):
                                                row_vals.append(shared_strings[idx])
                                        else:
                                            row_vals.append(v.text)
                            if row_vals:
                                text_lines.append("\t".join(row_vals))
        except Exception:
            pass
        return "\n".join(text_lines)

    @classmethod
    def extract_from_csv(cls, file_bytes: bytes) -> StructuredQuotationData:
        """Extracts structured line items and headers from CSV documents."""
        text = file_bytes.decode("utf-8", errors="replace")
        sanitized_text, warnings = cls.sanitize_untrusted_text(text)

        reader = csv.reader(io.StringIO(sanitized_text))
        rows = list(reader)

        supplier_name = None
        quotation_num = None
        stated_total = None
        line_items: List[ExtractedLineItem] = []
        subtotal = 0.0

        for r in rows:
            if not r:
                continue
            line_str = " ".join(r)
            if "supplier" in line_str.lower() and ":" in line_str:
                supplier_name = line_str.split(":", 1)[1].strip()
            elif ("quote" in line_str.lower() or "ref" in line_str.lower()) and ":" in line_str:
                quotation_num = line_str.split(":", 1)[1].strip()
            elif "total" in line_str.lower() and (":" in line_str or "=" in line_str):
                parts = re.split(r"[:=]", line_str, maxsplit=1)
                tot_str = re.sub(r"[^\d.]", "", parts[1])
                if tot_str:
                    try:
                        stated_total = float(tot_str)
                    except ValueError:
                        pass

            # Attempt to parse item, qty, price
            if len(r) >= 3:
                try:
                    qty = float(r[1].strip())
                    clean_price = re.sub(r"[^\d.]", "", r[2].strip())
                    price = float(clean_price)
                    tot = qty * price
                    subtotal += tot
                    line_items.append(
                        ExtractedLineItem(
                            item_name=r[0].strip(),
                            quantity=qty,
                            unit_of_measure="UNITS",
                            unit_price=price,
                            total_price=tot,
                            confidence_score=0.98,
                        )
                    )
                except ValueError:
                    pass

        # Arithmetic validation
        arithmetic_valid = True
        total = round(subtotal, 2)
        if stated_total is not None and subtotal > 0:
            diff = abs(stated_total - subtotal)
            if diff > 5.0 and (diff / subtotal) > 0.05:
                arithmetic_valid = False
                warnings.append(f"Arithmetic Mismatch: Sum of line items ({subtotal:.2f}) does not match stated quotation total ({stated_total:.2f}).")
            total = stated_total

        # Confidence calculation
        confidence = 0.95
        if not supplier_name:
            warnings.append("Missing Information: Supplier name could not be confidently identified.")
            confidence -= 0.20
        if not quotation_num:
            warnings.append("Missing Information: Quotation reference number is missing.")
            confidence -= 0.15
        if not arithmetic_valid:
            confidence -= 0.25

        confidence = max(0.2, min(1.0, round(confidence, 2)))

        return StructuredQuotationData(
            supplier_name=supplier_name or "Unknown Supplier",
            quotation_number=quotation_num or "UNKNOWN-REF",
            document_date="2026-03-01",
            currency="LKR",
            subtotal=subtotal,
            tax_amount=round(subtotal * 0.08, 2),
            discount_amount=0.0,
            total_cost=total,
            line_items=line_items,
            overall_confidence=confidence,
            arithmetic_valid=arithmetic_valid,
            flagged_reasons=warnings,
            extraction_method="CSV_STRUCTURED_PARSER",
        )

    @classmethod
    def parse_text_to_quotation(
        cls,
        raw_text: str,
        filename: str,
        format_type: str,
    ) -> StructuredQuotationData:
        """Parses extracted text into StructuredQuotationData with arithmetic checking."""
        sanitized_text, warnings = cls.sanitize_untrusted_text(raw_text)

        # 1. Supplier Name
        supplier_name = None
        supp_match = re.search(r"(?:Supplier|Company|Vendor|From)\s*:\s*([A-Za-z0-9\s\.,&]+)", sanitized_text, re.IGNORECASE)
        if supp_match:
            supplier_name = supp_match.group(1).split("\n")[0].strip()
        else:
            for line in sanitized_text.splitlines():
                clean = line.strip()
                if len(clean) > 3 and not clean.lower().startswith(("quotation", "invoice", "date", "to:")):
                    supplier_name = clean
                    break

        # 2. Quotation Number
        quote_num = None
        q_match = re.search(r"(?:Quote(?:s)?(?:\s*(?:#|No|Number))?|Ref(?:erence)?)\s*[:#]?\s*([A-Za-z0-9\-_]+)", sanitized_text, re.IGNORECASE)
        if q_match:
            quote_num = q_match.group(1).strip()
        else:
            quote_num = f"QUO-{Path(filename).stem.upper()[:8]}"

        # 3. Currency Detection
        currency = "LKR"
        if "USD" in sanitized_text or "$" in sanitized_text:
            currency = "USD"
        elif "EUR" in sanitized_text or "€" in sanitized_text:
            currency = "EUR"

        # 4. Total Cost & Subtotal
        total_cost = None
        tot_match = re.search(r"(?:Total(?:\s+Amount)?|Grand\s+Total)\s*[:=]?\s*(?:LKR|USD|\$|Rs\.?)?\s*([0-9,]+(?:\.[0-9]{2})?)", sanitized_text, re.IGNORECASE)
        if tot_match:
            try:
                total_cost = float(tot_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 5. Delivery Lead Time
        delivery_days = 14
        lead_match = re.search(r"(?:delivery|lead\s*time)\s*[:=]?\s*([0-9]+)\s*(?:days|weeks)?", sanitized_text, re.IGNORECASE)
        if lead_match:
            try:
                days = int(lead_match.group(1))
                if "week" in lead_match.group(0).lower():
                    days *= 7
                delivery_days = days
            except ValueError:
                pass

        # 6. Payment & Warranty Terms
        payment_terms = "Net 30"
        pay_match = re.search(r"(?:Payment\s*Terms?)\s*[:=]?\s*([A-Za-z0-9\s%,\-]+)", sanitized_text, re.IGNORECASE)
        if pay_match:
            payment_terms = pay_match.group(1).split("\n")[0].strip()

        warranty_terms = None
        war_match = re.search(r"(?:Warranty(?:\s*Terms?)?)\s*[:=]?\s*([A-Za-z0-9\s%,\-]+)", sanitized_text, re.IGNORECASE)
        if war_match:
            warranty_terms = war_match.group(1).split("\n")[0].strip()

        # 7. Line Items Extraction
        line_items: List[ExtractedLineItem] = []
        item_patterns = re.findall(
            r"([A-Za-z0-9\s\-]+?)\s+(\d+(?:\.\d+)?)\s*(units?|kg|rolls?|pcs|liters?|m)?\s+[@x]?\s*([0-9,]+(?:\.[0-9]{2})?)\s+([0-9,]+(?:\.[0-9]{2})?)",
            sanitized_text,
            re.IGNORECASE
        )
        for name, qty_str, unit, unit_price_str, total_str in item_patterns:
            try:
                q = float(qty_str)
                up = float(unit_price_str.replace(",", ""))
                tp = float(total_str.replace(",", ""))
                line_items.append(
                    ExtractedLineItem(
                        item_name=name.strip(),
                        quantity=q,
                        unit_of_measure=unit.upper() if unit else "UNITS",
                        unit_price=up,
                        total_price=tp,
                        confidence_score=0.92,
                    )
                )
            except ValueError:
                continue

        if not line_items and total_cost:
            line_items.append(
                ExtractedLineItem(
                    item_name=f"Procurement Scope ({Path(filename).stem})",
                    quantity=1.0,
                    unit_of_measure="LOT",
                    unit_price=total_cost,
                    total_price=total_cost,
                    confidence_score=0.80,
                )
            )

        # 8. Arithmetic Consistency Check
        items_sum = sum(it.total_price for it in line_items) if line_items else 0.0
        arithmetic_valid = True
        if total_cost is not None and items_sum > 0:
            diff = abs(total_cost - items_sum)
            if diff > 5.0 and (diff / items_sum) > 0.05:
                arithmetic_valid = False
                warnings.append(f"Arithmetic Mismatch: Sum of line items ({items_sum:.2f}) does not match quotation total ({total_cost:.2f}).")
        elif total_cost is None and items_sum > 0:
            total_cost = items_sum

        # 9. Missing Mandatory Information Warnings
        if not supplier_name:
            warnings.append("Missing Information: Supplier name could not be confidently identified.")
        if not quote_num:
            warnings.append("Missing Information: Quotation reference number is missing.")
        if total_cost is None or total_cost <= 0:
            warnings.append("Missing Information: Quotation total cost is missing or zero.")

        confidence = 0.95
        if not supplier_name:
            confidence -= 0.20
        if not quote_num:
            confidence -= 0.15
        if not arithmetic_valid:
            confidence -= 0.25
        if format_type == "IMAGE_OCR" or format_type == "PDF_SCANNED":
            confidence -= 0.10
        confidence = max(0.2, min(1.0, round(confidence, 2)))

        return StructuredQuotationData(
            supplier_name=supplier_name or "Unknown Supplier",
            quotation_number=quote_num or "UNKNOWN-REF",
            document_date="2026-03-01",
            currency=currency,
            subtotal=items_sum,
            tax_amount=round(items_sum * 0.08, 2),
            discount_amount=0.0,
            total_cost=total_cost or 0.0,
            delivery_lead_time_days=delivery_days,
            payment_terms=payment_terms,
            warranty_terms=warranty_terms,
            line_items=line_items,
            overall_confidence=confidence,
            arithmetic_valid=arithmetic_valid,
            flagged_reasons=warnings,
            extraction_method=f"HEURISTIC_{format_type}",
        )

    @classmethod
    def process_document(cls, file_bytes: bytes, filename: str) -> StructuredQuotationData:
        """Main entry point to detect format and extract structured quotation."""
        fmt = cls.detect_format(file_bytes, filename)
        if fmt == "CSV":
            return cls.extract_from_csv(file_bytes)
        elif fmt == "XLSX":
            text = cls.extract_text_from_xlsx(file_bytes)
            return cls.parse_text_to_quotation(text, filename, fmt)
        elif fmt in ["PDF_DIGITAL", "PDF_SCANNED"]:
            text = cls.extract_text_from_pdf(file_bytes)
            return cls.parse_text_to_quotation(text, filename, fmt)
        else:
            text = file_bytes.decode("latin1", errors="ignore")
            return cls.parse_text_to_quotation(text, filename, fmt)
