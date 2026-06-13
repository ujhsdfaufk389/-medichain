import streamlit as st
import json
import time
from band_client import BandClient
from agents import (
    IntakeAgent,
    MedicalNecessityAgent,
    InsurancePolicyAgent,
    ComplianceRiskAgent,
    DecisionCoordinatorAgent
)
from report_generator import generate_report

# ── Page Config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "MediChain AI",
    page_icon  = "🏥",
    layout     = "wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
.agent-box {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 6px 0;
    border-left: 4px solid;
}
.approved   { background: #F0FDF4; border-color: #059669; }
.denied     { background: #FEF2F2; border-color: #DC2626; }
.needs-more { background: #FFFBEB; border-color: #D97706; }
.escalate   { background: #FEF2F2; border-color: #DC2626; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.title("🏥 MediChain AI")
st.markdown(
    "**Band-Powered Multi-Agent Prior Authorization Review System** | "
    "Track 3: Regulated & High-Stakes Workflows"
)

st.info(
    "⚠️ This system assists human reviewers ONLY. "
    "It does NOT make final medical or insurance decisions. "
    "All data is synthetic. Always requires human review.",
    icon="🛡️"
)

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    
    app_mode = st.selectbox(
        "Mode",
        ["demo", "live"],
        help="Demo = no API keys needed. Live = real AI responses."
    )
    
    import os
    os.environ["APP_MODE"] = app_mode
    
    st.divider()
    st.header("📁 Case Selection")
    
    case_option = st.selectbox(
        "Select Sample Case",
        ["case_001.json — MRI Request (Missing PT History)"]
    )
    
    st.divider()
    st.markdown("**🤖 Agents**")
    st.markdown("1. 🔵 IntakeAgent — GPT-4o")
    st.markdown("2. 🟢 MedicalNecessityAgent — GPT-4o")
    st.markdown("3. 🟡 InsurancePolicyAgent — Mistral-7B")
    st.markdown("4. 🔴 ComplianceRiskAgent — GPT-4o")
    st.markdown("5. ⚫ DecisionCoordinator — GPT-4o")
    
    st.divider()
    st.markdown("**🔗 Band Integration**")
    st.markdown("✅ Shared room per case")
    st.markdown("✅ Agents read Band history")
    st.markdown("✅ Persistent context")
    st.markdown("✅ Human escalation via Band")

# ── Load Data ─────────────────────────────────────────────────────────────
try:
    case_data   = json.load(open("sample_data/case_001.json"))
    policy_data = json.load(open("sample_data/policy_mri.json"))
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}")
    st.stop()

# ── Case Summary ──────────────────────────────────────────────────────────
st.subheader("📋 Case Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Case ID",   case_data["case_id"])
col2.metric("Patient Age", case_data["patient"]["age"])
col3.metric("Diagnosis", case_data["diagnosis"]["icd10_code"])
col4.metric("Procedure", case_data["requested_procedure"]["cpt_code"])

with st.expander("📄 View Full Case Details"):
    st.json(case_data)

with st.expander("📋 View Insurance Policy Rules"):
    st.json(policy_data)

st.divider()

# ── Start Review Button ───────────────────────────────────────────────────
if st.button(
    "🚀 Start Multi-Agent Review",
    type             = "primary",
    use_container_width = True
):
    band    = BandClient()
    results = {}

    # Agent Timeline
    st.subheader("🔄 Agent Timeline")
    
    progress_bar = st.progress(0, text="Starting review...")
    status_area  = st.empty()
    
    agent_steps = [
        ("🔵 IntakeAgent",            IntakeAgent(),               "aiml",        20),
        ("🟢 MedicalNecessityAgent",  MedicalNecessityAgent(),     "aiml",        40),
        ("🟡 InsurancePolicyAgent",   InsurancePolicyAgent(),      "featherless", 60),
        ("🔴 ComplianceRiskAgent",    ComplianceRiskAgent(),       "aiml",        80),
        ("⚫ DecisionCoordinator",    DecisionCoordinatorAgent(),  "aiml",        100),
    ]

    timeline_messages = []
    room_id           = None

    for agent_label, agent_obj, provider, progress in agent_steps:
        status_area.info(f"⏳ {agent_label} is working...")
        progress_bar.progress(
            progress - 15,
            text=f"Running {agent_label}..."
        )
        time.sleep(0.3)

        try:
            if isinstance(agent_obj, IntakeAgent):
                out     = agent_obj.run(case_data, band)
                room_id = out["room_id"]
                result  = out["result"]
                
            elif isinstance(agent_obj, InsurancePolicyAgent):
                out    = agent_obj.run(room_id, policy_data, band)
                result = out["result"]
                
            else:
                out    = agent_obj.run(room_id, band)
                result = out["result"]

            results[agent_label] = result
            timeline_messages.append({
                "agent":  agent_label,
                "status": "✅ Complete",
                "result": result
            })

        except Exception as e:
            st.error(f"Error in {agent_label}: {str(e)}")
            results[agent_label] = {"error": str(e)}
            timeline_messages.append({
                "agent":  agent_label,
                "status": f"❌ Error: {str(e)}",
                "result": {}
            })

        progress_bar.progress(progress, text=f"{agent_label} done!")
        time.sleep(0.2)

    status_area.success("✅ All agents completed!")

    st.divider()

    # Show Timeline
    st.subheader("📊 Agent Results")
    for item in timeline_messages:
        with st.expander(f"{item['agent']} — {item['status']}"):
            st.json(item["result"])

    st.divider()

    # Final Decision
    st.subheader("🎯 Final Recommendation")
    
    decision_result = results.get("⚫ DecisionCoordinator", {})
    final_status    = decision_result.get("final_status", "UNKNOWN")

    status_colors = {
        "APPROVED":               "green",
        "DENIED":                 "red",
        "NEEDS_MORE_INFORMATION": "orange",
        "ESCALATE_TO_HUMAN":      "red",
    }
    color = status_colors.get(final_status, "gray")
    st.markdown(f"## :{color}[{final_status}]")

    if decision_result.get("justification"):
        st.write(decision_result["justification"])

    # Missing Documents
    missing_docs = decision_result.get("missing_documents", [])
    if missing_docs:
        st.warning("📋 Missing Documents Required:")
        for doc in missing_docs:
            st.markdown(f"- 📄 {doc}")

    # Risk Level
    risk = decision_result.get("risk_level", "UNKNOWN")
    risk_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
    st.markdown(
        f"**Risk Level:** {risk_colors.get(risk, '⚪')} {risk}")

    # Human Reviewer Note
    if decision_result.get("human_reviewer_note"):
        st.error(
            f"👤 **Human Reviewer Note:** "
            f"{decision_result['human_reviewer_note']}"
        )

    # Next Steps
    next_steps = decision_result.get("next_steps", [])
    if next_steps:
        st.subheader("📌 Next Steps")
        for i, step in enumerate(next_steps, 1):
            st.markdown(f"{i}. {step}")

    st.divider()

    # Audit Trail
    st.subheader("🔗 Band Room Audit Trail")
    st.caption(f"Room ID: {room_id}")

    band_messages = band.get_messages(room_id) if room_id else []
    for msg in band_messages:
        with st.expander(
            f"**{msg.get('sender')}** — {msg.get('timestamp')}"
        ):
            st.code(msg.get("content", ""), language="json")

    st.divider()

    # Download Report
    st.subheader("📥 Download Report")
    
    if decision_result and room_id:
        try:
            pdf_bytes = generate_report(
                case_data     = case_data,
                decision      = decision_result,
                band_messages = band_messages
            )
            st.download_button(
                label            = "📥 Download PDF Report",
                data             = pdf_bytes,
                file_name        = f"medichain_{case_data['case_id']}.pdf",
                mime             = "application/pdf",
                use_container_width = True
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    # Disclaimer
    st.caption(
        "⚠️ DISCLAIMER: This is AI-assisted analysis only. "
        "Final decisions must be made by licensed professionals. "
        "All data is synthetic."
    )