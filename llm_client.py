import os
import json
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    LLM Wrapper - AI/ML API aur Featherless AI dono support karta hai.
    Demo mode mein mock responses deta hai (koi API key nahi chahiye).
    """
    
    def __init__(self):
        self.mode = os.getenv("APP_MODE", "demo")
        print(f"[LLMClient] Mode: {self.mode}")
        
        if self.mode == "live":
            from openai import OpenAI
            
            self.aiml_client = OpenAI(
                api_key  = os.getenv("AIML_API_KEY", ""),
                base_url = os.getenv("AIML_BASE_URL", 
                                     "https://api.aimlapi.com/v1")
            )
            self.featherless_client = OpenAI(
                api_key  = os.getenv("FEATHERLESS_API_KEY", ""),
                base_url = os.getenv("FEATHERLESS_BASE_URL",
                                     "https://api.featherless.ai/v1")
            )

    def complete(self, prompt: str, provider: str = "aiml",
                 system_msg: str = "You are a helpful assistant.",
                 max_tokens: int = 1000) -> str:
        """
        LLM se response lo.
        provider = 'aiml'        → GPT-4o via AI/ML API
        provider = 'featherless' → Mistral-7B via Featherless AI
        """
        
        if self.mode == "demo":
            return self._mock_response(prompt, provider)
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt}
        ]
        
        if provider == "featherless":
            client = self.featherless_client
            model  = "mistralai/Mistral-7B-Instruct-v0.3"
        else:
            client = self.aiml_client
            model  = "gpt-4o"
        
        response = client.chat.completions.create(
            model      = model,
            messages   = messages,
            max_tokens = max_tokens
        )
        return response.choices[0].message.content

    def _mock_response(self, prompt: str, provider: str) -> str:
        """
        Demo mode ke liye fake responses.
        Bilkul real API jaisi structure hoti hai.
        """
        
        prompt_lower = prompt.lower()
        
        # Intake Agent ka mock response
        if "extract" in prompt_lower and "case" in prompt_lower:
            return json.dumps({
                "patient_age": 52,
                "diagnosis_code": "M54.5",
                "diagnosis_description": "Chronic lower back pain",
                "procedure_code": "72148",
                "procedure_description": "MRI Lumbar Spine with contrast",
                "insurance_plan": "Medicare Advantage Plan B",
                "doctor_notes_summary": "8 months back pain, 7/10 severity, radiating to left leg. NSAIDs failed.",
                "uploaded_documents": ["referral_letter.pdf", "diagnosis_report.pdf"],
                "missing_required_fields": [
                    "physical_therapy_history",
                    "conservative_treatment_records"
                ],
                "confidence_score": 0.92,
                "intake_status": "INCOMPLETE"
            }, indent=2)
        
        # Medical Necessity Agent ka mock response
        elif "medical" in prompt_lower or "necessity" in prompt_lower or "clinical" in prompt_lower:
            return json.dumps({
                "medical_necessity_assessment": "LIKELY_NECESSARY",
                "diagnosis_supports_procedure": True,
                "clinical_evidence_present": [
                    "ICD-10 M54.5 documented",
                    "Duration 8 months documented",
                    "Failed conservative treatment (NSAIDs) noted"
                ],
                "clinical_evidence_missing": [
                    "Physical therapy records",
                    "Previous imaging results",
                    "Neurological exam findings"
                ],
                "necessity_score": 0.75,
                "recommendation": "NEEDS_MORE_CLINICAL_EVIDENCE",
                "notes": "Diagnosis supports MRI request but clinical documentation is incomplete."
            }, indent=2)
        
        # Insurance Policy Agent ka mock response
        elif "policy" in prompt_lower or "insurance" in prompt_lower or "coverage" in prompt_lower:
            return json.dumps({
                "procedure_covered": True,
                "prerequisites_met": [
                    "Valid ICD-10 diagnosis code present",
                    "In-network physician referral present",
                    "NSAID trial documented"
                ],
                "prerequisites_missing": [
                    "6 weeks conservative treatment history NOT documented",
                    "Physical therapy records NOT submitted",
                    "PT provider notes NOT included"
                ],
                "policy_verdict": "NEEDS_MORE_INFO",
                "policy_reason": "Medicare Advantage Plan B requires minimum 6 weeks of conservative treatment including physical therapy before MRI approval. Physical therapy records are missing from submission.",
                "cited_policy_section": "Section 4.2.1 - Conservative Treatment Prerequisite",
                "confidence_score": 0.95
            }, indent=2)
        
        # Compliance Agent ka mock response
        elif "compliance" in prompt_lower or "risk" in prompt_lower or "audit" in prompt_lower:
            return json.dumps({
                "compliance_status": "COMPLIANT",
                "data_privacy_check": "PASS",
                "synthetic_data_confirmed": True,
                "hipaa_flags": [],
                "risk_level": "MEDIUM",
                "risk_factors": [
                    "Incomplete documentation increases denial risk",
                    "Missing PT records may indicate documentation gap"
                ],
                "human_review_required": True,
                "human_review_reason": "Missing prerequisite documentation requires human verification",
                "audit_trail_notes": [
                    "Case received: 2026-06-14",
                    "All agents reviewed case through Band room",
                    "Synthetic data verified - no real patient info",
                    "Decision pending human review"
                ],
                "compliance_score": 0.88
            }, indent=2)
        
        # Decision Coordinator ka mock response
        elif "final" in prompt_lower or "decision" in prompt_lower or "coordinator" in prompt_lower:
            return json.dumps({
                "final_status": "NEEDS_MORE_INFORMATION",
                "justification": "The prior authorization request for MRI Lumbar Spine (CPT 72148) cannot be approved at this time. While the diagnosis (M54.5) supports the procedure and referral documentation is present, the required 6-week conservative treatment history with physical therapy records is missing per Medicare Advantage Plan B policy requirements.",
                "missing_documents": [
                    "Physical therapy treatment records (minimum 6 weeks)",
                    "PT provider progress notes",
                    "Conservative treatment timeline documentation"
                ],
                "policy_reason": "Medicare Advantage Plan B Section 4.2.1 requires documented 6-week conservative treatment including PT before MRI approval.",
                "risk_level": "MEDIUM",
                "next_steps": [
                    "Request physical therapy records from treating PT provider",
                    "Submit updated prior auth with complete documentation",
                    "Human reviewer to verify documentation when received",
                    "Estimated resubmission timeline: 3-5 business days"
                ],
                "human_reviewer_note": "HUMAN REVIEW REQUIRED: Please verify PT documentation when submitted. Case shows legitimate medical need but requires complete documentation per policy.",
                "agents_consulted": [
                    "IntakeAgent", 
                    "MedicalNecessityAgent",
                    "InsurancePolicyAgent",
                    "ComplianceRiskAgent"
                ],
                "decision_confidence": 0.91,
                "disclaimer": "This recommendation is generated by AI for informational purposes only. Final authorization decision must be made by a licensed insurance reviewer. This is not medical advice."
            }, indent=2)
        
        # Default response
        return json.dumps({
            "status": "processed",
            "message": "Analysis complete",
            "confidence_score": 0.85
        }, indent=2)