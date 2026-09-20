import re
from datetime import datetime, timezone


class ComplaintGraph:
    """Rule-based complaint analyzer for the AIVOA intake workflow."""

    def analyze(self, complaint_text: str, category: str = "general") -> dict:
        complaint = self.extract_complaint(complaint_text, source="Manual")

        return {
            "summary": complaint_text[:200],
            "category": complaint["complaint_type"] or category or "general",
            "severity": complaint["initial_severity"] or "Medium",
            "recommended_action": self._recommended_action(complaint),
            "complaint": complaint,
        }

    def extract_complaint(self, complaint_text: str, source: str = "Email / Text") -> dict:
        text = (complaint_text or "").strip()
        severity = self._detect_severity(text)
        complaint_type = self._detect_complaint_type(text)

        return {
            "complaint_source": source,
            "customer_name": self._extract_label(text, ["customer", "customer name", "client", "from"]),
            "product_name": self._extract_label(text, ["product", "product name", "material", "item"]),
            "product_strength": self._extract_label(
                text,
                ["strength", "grade", "product strength", "product grade"],
            ),
            "batch_number": self._extract_batch(text),
            "manufacturing_date": self._extract_label(
                text,
                ["manufacturing date", "mfg date", "mfg", "manufactured on"],
            ),
            "expiry_date": self._extract_label(text, ["expiry date", "exp date", "expiry", "expires"]),
            "quantity_affected": self._extract_quantity(text),
            "complaint_type": complaint_type,
            "complaint_date": self._extract_complaint_date(text),
            "description": text,
            "initial_severity": severity,
            "severity": severity,
            "priority": self._priority_for_severity(severity),
        }

    def _detect_complaint_type(self, text: str) -> str:
        lowered = text.lower()

        if self._contains_any(lowered, ["late", "delay", "waiting", "slow", "timeout"]):
            return "Service Delay"
        if self._contains_any(lowered, ["payment", "charge", "refund", "billing", "invoice"]):
            return "Billing"
        if self._contains_any(lowered, ["harassment", "abuse", "unsafe", "threat", "fraud"]):
            return "Safety"
        if self._contains_any(lowered, ["quality", "defect", "fault", "broken", "contamination"]):
            return "Product Quality"
        if self._contains_any(lowered, ["temperature", "humidity", "storage", "stability"]):
            return "Storage Condition"

        return "General"

    def _detect_severity(self, text: str) -> str:
        lowered = text.lower()

        if self._contains_any(lowered, ["death", "fatal", "life threatening", "critical", "unsafe"]):
            return "Critical"
        if self._contains_any(lowered, ["recall", "contamination", "fraud", "threat", "serious"]):
            return "High"
        if self._contains_any(lowered, ["delay", "broken", "defect", "incorrect", "failed"]):
            return "Medium"

        return "Low"

    def _recommended_action(self, complaint: dict) -> str:
        severity = complaint.get("initial_severity", "").lower()
        complaint_type = complaint.get("complaint_type", "").lower()

        if severity == "critical":
            return "Escalate immediately for quality and safety review"
        if severity == "high":
            return "Open investigation and notify QA lead"
        if "billing" in complaint_type:
            return "Verify commercial records and customer communication"
        if "product quality" in complaint_type:
            return "Initiate product quality investigation"

        return "Review and triage complaint"

    def _priority_for_severity(self, severity: str) -> str:
        return {
            "Critical": "Urgent",
            "High": "High",
            "Medium": "Normal",
            "Low": "Low",
        }.get(severity, "Normal")

    def _extract_label(self, text: str, labels: list[str]) -> str:
        for label in labels:
            pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+?)\s*$"
            match = re.search(pattern, text)
            if match:
                return self._clean_value(match.group(1))

        return ""

    def _extract_batch(self, text: str) -> str:
        label_value = self._extract_label(
            text,
            ["batch", "batch number", "batch no", "lot", "lot number", "lot no"],
        )
        if label_value:
            return label_value

        match = re.search(
            r"(?i)\b(?:batch|lot)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-_/]{2,})",
            text,
        )
        return self._clean_value(match.group(1)) if match else ""

    def _extract_quantity(self, text: str) -> str:
        label_value = self._extract_label(
            text,
            ["quantity affected", "affected quantity", "quantity", "qty"],
        )
        if label_value:
            return label_value

        match = re.search(r"(?i)\b(\d+(?:\.\d+)?)\s*(kg|g|mg|l|ml|units|packs|boxes)\b", text)
        if not match:
            return ""

        return f"{match.group(1)} {match.group(2)}"

    def _extract_complaint_date(self, text: str) -> str:
        label_value = self._extract_label(
            text,
            ["complaint date", "date of complaint", "received date", "date"],
        )
        if label_value:
            return label_value

        match = re.search(
            r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4})\b",
            text,
        )
        if match:
            return match.group(1)

        return datetime.now(timezone.utc).date().isoformat()

    def _clean_value(self, value: str) -> str:
        return value.strip().strip(".,;")

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)
