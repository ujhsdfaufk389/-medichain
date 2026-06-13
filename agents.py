import json
from llm_client import LLMClient
from band_client import BandClient

llm = LLMClient()


class IntakeAgent:
    """
    Agent 1: Patient ki file padhta hai.
    Band room banata hai aur case data post karta hai.
    """
    NAME = "IntakeAgent"

    def run(self, case_data: dict, band: BandClient) -> dict:
        print(f"\n{'='*50}")
        print(f"[{self.NAME}] Starting intake processing...")

        prompt = f"""You are a medical intake specialist.
Extract structured information from this prior authorization request.
Return ONLY valid JSON with these fields:
patient_age, diagnosis_code, diagnosis_description, procedure_code,
procedure_description, insurance_plan, doctor_notes_summary,
uploaded_documents (list), missing_required_fields (list),
confidence_score (0-1), intake_status.

Case data:
{json.dumps(case_data, indent=2)}"""

        result_str = llm.complete(
            prompt,
            provider   = "aiml",
            system_msg = "You are a medical intake specialist. Return JSON only."
        )

        try:
            result = json.loads(result_str)
        except:
            result = {"raw_response": result_str, "intake_status": "PARSE_ERROR"}

        # Band room banao
        room_id = band.create_room(
            name     = f"PriorAuth-{case_data.get('case_id', 'UNKNOWN')}",
            metadata = {
                "case_id":    case_data.get("case_id"),
                "stage":      "intake",
                "created_by": self.NAME
            }
        )

        # Band mein post karo
        band.post_message(
            room_id    = room_id,
            agent_name = self.NAME,
            content    = f"INTAKE ANALYSIS COMPLETE:\n{json.dumps(result, indent=2)}",
            metadata   = {"stage": "intake", "data": result}
        )

        # Context update karo
        band.update_context(room_id, "intake_result", result)
        band.update_context(room_id, "case_id", case_data.get("case_id"))

        print(f"[{self.NAME}] Done. Room ID: {room_id}")
        return {"room_id": room_id, "result": result}


class MedicalNecessityAgent:
    """
    Agent 2: Clinical evidence check karta hai.
    Intake Agent ka Band message padh ke kaam karta hai.
    """
    NAME = "MedicalNecessityAgent"

    def run(self, room_id: str, band: BandClient) -> dict:
        print(f"\n{'='*50}")
        print(f"[{self.NAME}] Reading Band room history...")

        # Band se pehle ka kaam padho
        band_history = band.get_room_summary(room_id)

        prompt = f"""You are a medical necessity reviewer.
Review the intake analysis from the Band room and assess medical necessity.
Return ONLY valid JSON with these fields:
medical_necessity_assessment (NECESSARY/LIKELY_NECESSARY/UNCLEAR/NOT_NECESSARY),
diagnosis_supports_procedure (true/false),
clinical_evidence_present (list),
clinical_evidence_missing (list),
necessity_score (0-1),
recommendation,
notes.

Band room history (previous agent findings):
{band_history}"""

        result_str = llm.complete(
            prompt,
            provider   = "aiml",
            system_msg = "You are a medical necessity reviewer. Return JSON only."
        )

        try:
            result = json.loads(result_str)
        except:
            result = {"raw_response": result_str}

        band.post_message(
            room_id    = room_id,
            agent_name = self.NAME,
            content    = f"MEDICAL NECESSITY REVIEW:\n{json.dumps(result, indent=2)}",
            metadata   = {"stage": "medical_necessity", "data": result}
        )

        band.update_context(room_id, "medical_necessity_result", result)

        print(f"[{self.NAME}] Done.")
        return {"result": result}


class InsurancePolicyAgent:
    """
    Agent 3: Insurance policy check karta hai.
    Featherless AI (Mistral-7B) use karta hai.
    Band se pehle dono agents ka kaam padh ke kaam karta hai.
    """
    NAME = "InsurancePolicyAgent"

    def run(self, room_id: str, policy_data: dict,
            band: BandClient) -> dict:
        print(f"\n{'='*50}")
        print(f"[{self.NAME}] Reading Band room + checking policy...")

        band_history = band.get_room_summary(room_id)

        prompt = f"""You are an insurance policy analyst.
Review the agent findings from Band and check against the insurance policy.
Return ONLY valid JSON with these fields:
procedure_covered (true/false),
prerequisites_met (list),
prerequisites_missing (list),
policy_verdict (APPROVED/DENIED/NEEDS_MORE_INFO),
policy_reason (string),
cited_policy_section (string),
confidence_score (0-1).

Band room history (previous agents' findings):
{band_history}

Insurance Policy Rules:
{json.dumps(policy_data, indent=2)}"""

        result_str = llm.complete(
            prompt,
            provider   = "featherless",
            system_msg = "You are an insurance policy analyst. Return JSON only."
        )

        try:
            result = json.loads(result_str)
        except:
            result = {"raw_response": result_str}

        band.post_message(
            room_id    = room_id,
            agent_name = self.NAME,
            content    = f"INSURANCE POLICY ANALYSIS:\n{json.dumps(result, indent=2)}",
            metadata   = {"stage": "policy_check", "data": result}
        )

        band.update_context(room_id, "policy_result", result)

        print(f"[{self.NAME}] Done.")
        return {"result": result}


class ComplianceRiskAgent:
    """
    Agent 4: Risk aur compliance check karta hai.
    Saare Band messages padh ke risk assess karta hai.
    """
    NAME = "ComplianceRiskAgent"

    def run(self, room_id: str, band: BandClient) -> dict:
        print(f"\n{'='*50}")
        print(f"[{self.NAME}] Reading full Band room for risk analysis...")

        band_history = band.get_room_summary(room_id)

        prompt = f"""You are a healthcare compliance and risk analyst.
Review the complete agent discussion from Band and assess compliance and risk.
Return ONLY valid JSON with these fields:
compliance_status (COMPLIANT/NON_COMPLIANT/REVIEW_NEEDED),
data_privacy_check (PASS/FAIL),
synthetic_data_confirmed (true/false),
hipaa_flags (list),
risk_level (LOW/MEDIUM/HIGH),
risk_factors (list),
human_review_required (true/false),
human_review_reason (string),
audit_trail_notes (list),
compliance_score (0-1).

Complete Band room history:
{band_history}"""

        result_str = llm.complete(
            prompt,
            provider   = "aiml",
            system_msg = "You are a compliance analyst. Return JSON only."
        )

        try:
            result = json.loads(result_str)
        except:
            result = {"raw_response": result_str}

        band.post_message(
            room_id    = room_id,
            agent_name = self.NAME,
            content    = f"COMPLIANCE & RISK ASSESSMENT:\n{json.dumps(result, indent=2)}",
            metadata   = {"stage": "compliance_risk", "data": result}
        )

        band.update_context(room_id, "compliance_result", result)

        # High risk hai toh human ko alert karo Band ke through
        if result.get("risk_level") == "HIGH":
            band.notify_human(
                room_id,
                "HIGH RISK case detected. Immediate human review required."
            )

        print(f"[{self.NAME}] Done.")
        return {"result": result}


class DecisionCoordinatorAgent:
    """
    Agent 5: Final decision deta hai.
    Saare agents ka Band room history padh ke final packet banata hai.
    """
    NAME = "DecisionCoordinator"

    def run(self, room_id: str, band: BandClient) -> dict:
        print(f"\n{'='*50}")
        print(f"[{self.NAME}] Reading complete Band room history...")

        # Saara Band room padho
        band_history = band.get_room_summary(room_id)

        prompt = f"""You are the final decision coordinator for medical prior authorization.
Read the complete multi-agent discussion from Band and produce the final recommendation.
Return ONLY valid JSON with these fields:
final_status (APPROVED/DENIED/NEEDS_MORE_INFORMATION/ESCALATE_TO_HUMAN),
justification (detailed string),
missing_documents (list),
policy_reason (string),
risk_level (LOW/MEDIUM/HIGH),
next_steps (list),
agents_consulted (list),
decision_confidence (0-1),
human_reviewer_note (string - always required),
disclaimer (string).

IMPORTANT: Always include human_reviewer_note. Never claim AI makes final decision.

Complete Band room history from all agents:
{band_history}"""

        result_str = llm.complete(
            prompt,
            provider   = "aiml",
            system_msg = "You are a decision coordinator. Return JSON only.",
            max_tokens = 1500
        )

        try:
            result = json.loads(result_str)
        except:
            result = {"raw_response": result_str,
                      "final_status": "ESCALATE_TO_HUMAN"}

        band.post_message(
            room_id    = room_id,
            agent_name = self.NAME,
            content    = f"FINAL DECISION PACKET:\n{json.dumps(result, indent=2)}",
            metadata   = {"stage": "final_decision", "data": result}
        )

        # Human escalation always karo
        band.notify_human(
            room_id,
            f"Review complete. Status: {result.get('final_status')}. "
            f"Human sign-off required before any action."
        )

        print(f"[{self.NAME}] FINAL STATUS: {result.get('final_status')}")
        return {"result": result}