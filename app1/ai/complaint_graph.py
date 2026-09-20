import json
import os
from typing import TypedDict, Any

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, START, END

from app1.ai.complaint import ComplaintGraph as RuleBasedComplaintGraph


load_dotenv()


class ComplaintState(TypedDict, total=False):
    raw_text: str
    source: str

    complaint: dict

    missing_fields: list[str]
    completeness_score: int

    risk_level: str
    risk_reason: str
    key_risks: list[str]
    recommended_action: str

    summary: str

    ai_error: str


class ComplaintGraph:
    """
    LangGraph-based AI complaint workflow.

    Flow:
        extract -> completeness -> risk -> summary
    """

    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing from backend/.env"
            )

        self.client = Groq(api_key=api_key)

        # Existing rule-based fallback
        self.rule_based = RuleBasedComplaintGraph()

        # Build LangGraph
        self.graph = self._build_graph()

    # =========================================================
    # GRAPH
    # =========================================================

    def _build_graph(self):
        workflow = StateGraph(ComplaintState)

        workflow.add_node(
            "extract_complaint",
            self.extract_complaint_node
        )

        workflow.add_node(
            "check_completeness",
            self.check_completeness_node
        )

        workflow.add_node(
            "assess_risk",
            self.assess_risk_node
        )

        workflow.add_node(
            "generate_summary",
            self.generate_summary_node
        )

        workflow.add_edge(
            START,
            "extract_complaint"
        )

        workflow.add_edge(
            "extract_complaint",
            "check_completeness"
        )

        workflow.add_edge(
            "check_completeness",
            "assess_risk"
        )

        workflow.add_edge(
            "assess_risk",
            "generate_summary"
        )

        workflow.add_edge(
            "generate_summary",
            END
        )

        return workflow.compile()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def analyze(
        self,
        complaint_text: str,
        category: str = "general",
        source: str = "Manual"
    ) -> dict:

        text = (complaint_text or "").strip()

        if not text:
            raise ValueError(
                "Complaint text cannot be empty"
            )

        state = {
            "raw_text": text,
            "source": source,
        }

        result = self.graph.invoke(state)

        complaint = result.get(
            "complaint",
            {}
        )

        if not complaint:
            complaint = self.rule_based.extract_complaint(
                text,
                source=source
            )

        final_category = (
            complaint.get("complaint_type")
            or category
            or "General"
        )

        final_severity = (
            result.get("risk_level")
            or complaint.get("initial_severity")
            or "Medium"
        )

        return {
            "summary": result.get(
                "summary",
                text[:200]
            ),

            "category": final_category,

            "severity": final_severity,

            "recommended_action": result.get(
                "recommended_action",
                ""
            ),

            "complaint": complaint,

            "completeness": {
                "score": result.get(
                    "completeness_score",
                    0
                ),
                "missing_fields": result.get(
                    "missing_fields",
                    []
                ),
            },

            "risk": {
                "risk_level": result.get(
                    "risk_level",
                    final_severity
                ),
                "risk_reason": result.get(
                    "risk_reason",
                    ""
                ),
                "key_risks": result.get(
                    "key_risks",
                    []
                ),
                "recommended_action": result.get(
                    "recommended_action",
                    ""
                ),
            },

            "ai_error": result.get(
                "ai_error",
                ""
            ),
        }

    def extract_complaint(
        self,
        complaint_text: str,
        source: str = "Email / Text"
    ) -> dict:
        """
        Compatibility method for your current main.py.
        """

        result = self.analyze(
            complaint_text,
            source=source
        )

        return result["complaint"]

    def assistant_update(self, message: str, complaint: dict) -> dict:
        """Apply a user's instruction to the current complaint details."""
        allowed_fields = [
            "complaintSource", "customerName", "productName",
            "productStrength", "batchNumber", "manufacturingDate",
            "expiryDate", "quantityAffected", "complaintType",
            "complaintDate", "description", "initialSeverity", "priority",
        ]
        system_prompt = f"""
You are an AI complaint intake assistant. Apply the user's instruction to the
current complaint form. Never invent values that the user did not provide.

Return ONLY valid JSON in this exact structure:
{{
  "reply": "A concise explanation of what you changed or why no change was made.",
  "updates": {{"fieldName": "new value"}}
}}

Only include changed fields in updates. Allowed field names are:
{json.dumps(allowed_fields)}
Use an empty string only when the user explicitly asks to clear a field.
"""
        user_prompt = f"""
Current complaint form:
{json.dumps(complaint)}

User instruction:
{message}
"""
        result = self._call_llm(system_prompt, user_prompt)
        updates = result.get("updates", {})
        if not isinstance(updates, dict):
            updates = {}
        updates = {
            field: str(value)
            for field, value in updates.items()
            if field in allowed_fields and value is not None
        }
        return {
            "reply": result.get("reply", "I could not identify a form update."),
            "updates": updates,
        }

    # =========================================================
    # GROQ CALL
    # =========================================================

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> dict:

        response = self.client.chat.completions.create(
            model=self.MODEL,

            temperature=0,

            response_format={
                "type": "json_object"
            },

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "Groq returned an empty response"
            )

        return self._parse_json(content)

    # =========================================================
    # NODE 1: EXTRACTION
    # =========================================================

    def extract_complaint_node(
        self,
        state: ComplaintState
    ) -> dict:

        text = state["raw_text"]
        source = state.get(
            "source",
            "Email / Text"
        )

        system_prompt = """
You are an AI complaint intake assistant
for a pharmaceutical manufacturing
quality management system.

Extract factual information from the
customer complaint.

Never invent missing information.

Return ONLY valid JSON.

Required JSON structure:

{
  "complaint_source": "",
  "customer_name": "",
  "product_name": "",
  "product_strength": "",
  "batch_number": "",
  "manufacturing_date": "",
  "expiry_date": "",
  "quantity_affected": "",
  "complaint_type": "",
  "complaint_date": "",
  "description": "",
  "initial_severity": "",
  "severity": "",
  "priority": ""
}

Allowed severity values:
Low, Medium, High, Critical

Possible complaint types:
Product Quality
Packaging
Labeling
Contamination
Storage Condition
Delivery
Documentation
Other

Priority values:
Low, Normal, High, Urgent
"""

        user_prompt = f"""
Source:
{source}

Complaint text:
{text}
"""

        try:

            result = self._call_llm(
                system_prompt,
                user_prompt
            )

            # Fill source if model left it empty
            result["complaint_source"] = (
                result.get("complaint_source")
                or source
            )

            return {
                "complaint": result
            }

        except Exception as exc:

            # Existing rule-based fallback
            fallback = (
                self.rule_based
                .extract_complaint(
                    text,
                    source=source
                )
            )

            return {
                "complaint": fallback,

                "ai_error": str(exc)
            }

    # =========================================================
    # NODE 2: COMPLETENESS
    # =========================================================

    def check_completeness_node(
        self,
        state: ComplaintState
    ) -> dict:

        complaint = state["complaint"]

        required_fields = [
            "customer_name",
            "product_name",
            "batch_number",
            "complaint_date",
            "description",
            "complaint_type",
            "initial_severity",
        ]

        missing_fields = []

        for field in required_fields:

            value = complaint.get(field)

            if not value or not str(value).strip():
                missing_fields.append(field)

        total = len(required_fields)

        present = total - len(
            missing_fields
        )

        score = round(
            (present / total) * 100
        )

        return {
            "missing_fields": missing_fields,
            "completeness_score": score
        }

    # =========================================================
    # NODE 3: RISK
    # =========================================================

    def assess_risk_node(
        self,
        state: ComplaintState
    ) -> dict:

        complaint = state["complaint"]

        prompt = f"""
Analyze this pharmaceutical customer complaint.

Complaint:

{json.dumps(
    complaint,
    indent=2
)}

Return ONLY valid JSON:

{{
  "risk_level": "Low",
  "risk_reason": "",
  "key_risks": [],
  "recommended_action": ""
}}

Risk level must be exactly:
Low
Medium
High
Critical

Important:
This is an AI recommendation for
complaint triage.

Do not claim that a regulatory,
quality or safety decision has
already been made.
"""

        try:

            result = self._call_llm(
                """
You are an AI risk-triage assistant
for a pharmaceutical customer
complaint management system.

Assess potential complaint risk
from the information provided.
""",
                prompt
            )

            return {
                "risk_level": (
                    result.get(
                        "risk_level",
                        "Medium"
                    )
                ),

                "risk_reason": (
                    result.get(
                        "risk_reason",
                        ""
                    )
                ),

                "key_risks": (
                    result.get(
                        "key_risks",
                        []
                    )
                ),

                "recommended_action": (
                    result.get(
                        "recommended_action",
                        "Review and triage complaint"
                    )
                )
            }

        except Exception:

            severity = (
                complaint.get(
                    "initial_severity",
                    "Medium"
                )
            )

            fallback = (
                self.rule_based
                ._recommended_action(
                    complaint
                )
            )

            return {
                "risk_level": severity,
                "risk_reason": (
                    "Fallback rule-based "
                    "assessment."
                ),
                "key_risks": [],
                "recommended_action": fallback
            }

    # =========================================================
    # NODE 4: SUMMARY
    # =========================================================

    def generate_summary_node(
        self,
        state: ComplaintState
    ) -> dict:

        complaint = state["complaint"]

        prompt = f"""
Create a concise complaint summary
for a Quality Assurance user.

Complaint:

{json.dumps(
    complaint,
    indent=2
)}

Return ONLY:

{{
  "summary": ""
}}

Keep the summary to 3-4 sentences.
Do not invent facts.
"""

        try:

            result = self._call_llm(
                """
You are a pharmaceutical
complaint documentation assistant.
""",
                prompt
            )

            return {
                "summary": result.get(
                    "summary",
                    ""
                )
            }

        except Exception:

            description = (
                complaint.get(
                    "description",
                    ""
                )
            )

            return {
                "summary": description[:500]
            }

    # =========================================================
    # JSON PARSER
    # =========================================================

    @staticmethod
    def _parse_json(content: str) -> dict:

        content = content.strip()

        if content.startswith(
            "```json"
        ):
            content = content[
                7:
            ].strip()

        if content.startswith(
            "```"
        ):
            content = content[
                3:
            ].strip()

        if content.endswith(
            "```"
        ):
            content = content[
                :-3
            ].strip()

        data = json.loads(content)

        if not isinstance(
            data,
            dict
        ):
            raise ValueError(
                "LLM response was not a JSON object"
            )

        return data