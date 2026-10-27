import json
import requests
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Contract Risk Analyzer Pro", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
.hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg,#101827,#1e3a5f); color: white; margin-bottom: 1.2rem;}
.hero h1 {margin: 0 0 .35rem 0; font-size: 2.1rem;}
.hero p {margin: 0; color: #dbeafe; font-size: 1rem;}
</style>
""", unsafe_allow_html=True)
st.markdown("""<div class="hero"><h1>AI- Based Contract Risk Analyzer <span style="color:#93c5fd">Pro</span></h1><p>Review contract clauses, spot potential issues, and get a structured screening report.</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API base URL", value=DEFAULT_API_URL).strip().rstrip("/")
    contract_type = st.selectbox("Contract type", ["general", "employment", "software", "service", "vendor", "lease", "nda"])
    st.divider()
    st.caption("Keep the FastAPI server running in a separate terminal.")

api_online = False
try:
    api_online = requests.get(f"{api_url}/health", timeout=3).ok
except requests.RequestException:
    pass

if api_online:
    st.success("API connected")
else:
    st.warning("API not detected. Start FastAPI, then refresh or rerun this page.")

st.subheader("1. Add a contract")
mode = st.radio("Choose input method", ["Upload a document", "Paste contract text"], horizontal=True)
uploaded_file = None
contract_text = ""

if mode == "Upload a document":
    uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    st.caption("The current API has a 15 MB upload limit.")
    if uploaded_file:
        st.info(f"Selected: {uploaded_file.name} · {uploaded_file.size / 1024:.1f} KB")
else:
    contract_text = st.text_area("Paste contract text", height=220, placeholder="Paste the contract or clauses you want to screen...")

if st.button("Analyze contract", type="primary", use_container_width=True, disabled=not api_online):
    try:
        with st.spinner("Analyzing contract clauses..."):
            if mode == "Upload a document":
                if uploaded_file is None:
                    st.error("Upload a PDF, DOCX, or TXT file first.")
                    st.stop()
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                response = requests.post(f"{api_url}/v1/analyze/file", files=files, params={"contract_type": contract_type}, timeout=180)
            else:
                if not contract_text.strip():
                    st.error("Paste some contract text first.")
                    st.stop()
                response = requests.post(f"{api_url}/v1/analyze", json={"text": contract_text, "contract_type": contract_type}, timeout=180)

        if not response.ok:
            st.error(f"API error ({response.status_code})")
            st.code(response.text[:4000])
            st.stop()
        st.session_state["analysis_result"] = response.json()
    except requests.RequestException as exc:
        st.error(f"Could not reach the API: {exc}")
    except ValueError:
        st.error("The API response was not valid JSON.")

result = st.session_state.get("analysis_result")
if result:
    st.divider()
    st.subheader("2. Screening report")
    score = int(result.get("overall_risk_score", 0))
    stats = result.get("statistics", {})
    findings = result.get("findings", [])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk score", f"{score}/100")
    c2.metric("Risk level", str(result.get("risk_level", "unknown")).upper())
    c3.metric("Clauses detected", stats.get("clauses_detected", 0))
    c4.metric("Potential issues", len(findings))
    st.progress(max(0, min(100, score)) / 100)
    st.write(result.get("summary", ""))

    st.subheader("Potential issues")
    if not findings:
        st.info("No issues were flagged by the current rules. This does not prove the contract is low-risk.")
    for i, finding in enumerate(findings, start=1):
        title = finding.get("clause_type", "Unclassified").replace("_", " ").title()
        with st.expander(f"{i}. {title} · {str(finding.get('risk_level', 'unknown')).upper()}", expanded=i == 1):
            st.markdown("**Evidence**")
            st.write(finding.get("evidence", "No evidence returned."))
            st.markdown("**Why it was flagged**")
            st.write(finding.get("reason", "No reason returned."))
            st.markdown("**Suggested review**")
            st.write(finding.get("recommendation", "No recommendation returned."))
            st.caption(f"Source: {finding.get('source', 'unknown')} · Confidence: {finding.get('confidence', 'N/A')}")

    st.subheader("LegalBERT clause classifications")
    classifications = result.get("clause_classifications", [])
    if classifications:
        st.dataframe([{
            "Clause category": item.get("label", "unknown"),
            "Confidence": round(float(item.get("confidence", 0)), 4),
            "Clause text": item.get("text", ""),
        } for item in classifications], use_container_width=True, hide_index=True)
    else:
        st.info("No model classifications were returned.")

    st.subheader("Clauses to verify")
    missing = result.get("missing_clause_checks", [])
    if missing:
        for item in missing:
            st.markdown(f"- {item}")
    else:
        st.write("No missing-clause checks were returned.")

    with st.expander("Contract statistics and full JSON"):
        st.json(stats)
        st.json(result)

    st.download_button("Download report as JSON", data=json.dumps(result, indent=2, ensure_ascii=False),
                       file_name="contract_risk_report.json", mime="application/json", use_container_width=True)
    st.caption(result.get("disclaimer", "AI-assisted screening only. Not legal advice."))
    st.caption("The risk score comes from baseline rules. LegalBERT classifies clause types; its confidence is not a legal-risk probability.")
else:
    st.info("Your report will appear here after you analyze a contract.")
