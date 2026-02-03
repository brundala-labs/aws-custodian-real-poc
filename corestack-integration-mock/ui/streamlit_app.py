"""Streamlit UI: CoreStack – Unified Policy Compliance (POC)."""

import json
import os
import requests
import streamlit as st

API_BASE = os.environ.get("CORESTACK_API_URL", "http://localhost:8080")

st.set_page_config(
    page_title="CoreStack – Unified Policy Compliance",
    page_icon="🛡️",  # noqa
    layout="wide",
)

# ── Styles ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; }
    .kpi-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
    }
    .kpi-value { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .kpi-label { font-size: 0.85rem; color: #6c757d; margin: 0; }
    .status-pass { color: #198754; font-weight: 600; }
    .status-fail { color: #dc3545; font-weight: 600; }
    .source-badge {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.75rem; font-weight: 600;
    }
    .source-cloudcustodian { background: #e3f2fd; color: #1565c0; }
    .source-corestack { background: #fce4ec; color: #c62828; }
    .severity-high { color: #dc3545; }
    .severity-medium { color: #fd7e14; }
    .severity-low { color: #6c757d; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE}. Is the API server running?")
        st.stop()
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()


def api_post(path: str, params: dict = None):
    try:
        r = requests.post(f"{API_BASE}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE}. Is the API server running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def status_html(status: str) -> str:
    cls = "status-pass" if status == "PASS" else "status-fail"
    return f'<span class="{cls}">{status}</span>'


def source_html(source: str) -> str:
    cls = f"source-{source}"
    label = "Cloud Custodian" if source == "cloudcustodian" else "CoreStack"
    return f'<span class="source-badge {cls}">{label}</span>'


def severity_html(sev: str) -> str:
    return f'<span class="severity-{sev}">{sev.upper()}</span>'


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("## CoreStack – Unified Policy Compliance (POC)")
st.caption("Real Cloud Custodian findings + CoreStack native policies in one view")

# ── Re-Ingest ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Data Ingestion")
    default_path = os.environ.get("CUSTODIAN_RUN_DIR", "")
    ingest_path = st.text_input("Custodian Run Directory", value=default_path)
    if st.button("Re-Ingest", type="primary", use_container_width=True):
        if ingest_path:
            with st.spinner("Ingesting..."):
                result = api_post("/ingest", params={"path": ingest_path})
            if result and result.get("status") == "ok":
                st.success(
                    f"Ingested run **{result['run_id']}**: "
                    f"{result['policies_ingested']} policies, "
                    f"{result['findings_ingested']} findings, "
                    f"{result['resources_ingested']} resources"
                )
                st.rerun()
            elif result:
                st.error(f"Ingest failed: {result}")
        else:
            st.warning("Enter a path to the custodian run directory.")

    st.markdown("---")
    st.markdown("### Filters")
    source_filter = st.selectbox("Source", ["All", "cloudcustodian", "corestack"])
    status_filter = st.selectbox("Status", ["All", "FAIL", "PASS"])
    severity_filter = st.selectbox("Severity", ["All", "high", "medium", "low"])

# ── KPIs ─────────────────────────────────────────────────────────────────────

summary = api_get("/summary")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value">{summary['total_policies']}</p>
        <p class="kpi-label">Total Policies</p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value status-pass">{summary['passing']}</p>
        <p class="kpi-label">Passing</p>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value status-fail">{summary['failing']}</p>
        <p class="kpi-label">Failing</p>
    </div>""", unsafe_allow_html=True)
with c4:
    last_eval = summary.get("last_evaluated") or "N/A"
    st.markdown(f"""<div class="kpi-card">
        <p class="kpi-value" style="font-size:1.1rem;">{last_eval}</p>
        <p class="kpi-label">Last Evaluated</p>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ── Source breakdown ─────────────────────────────────────────────────────────

with st.expander("Breakdown by Source & Severity", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**By Source**")
        for src, counts in summary.get("by_source", {}).items():
            label = "Cloud Custodian" if src == "cloudcustodian" else "CoreStack" if src == "corestack" else src
            parts = ", ".join(f"{s}: {c}" for s, c in counts.items())
            st.markdown(f"- **{label}**: {parts}")
    with col_b:
        st.markdown("**By Severity**")
        for sev, counts in summary.get("by_severity", {}).items():
            parts = ", ".join(f"{s}: {c}" for s, c in counts.items())
            st.markdown(f"- **{sev.upper()}**: {parts}")

# ── Findings table ───────────────────────────────────────────────────────────

st.markdown("### Policy Findings")

params = {}
if source_filter != "All":
    params["source"] = source_filter
if status_filter != "All":
    params["status"] = status_filter
if severity_filter != "All":
    params["severity"] = severity_filter

findings = api_get("/findings", params=params)

if not findings:
    st.info("No findings match the current filters.")
else:
    # Build HTML table
    table_html = """
    <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
    <thead>
        <tr style="border-bottom:2px solid #dee2e6; text-align:left;">
            <th style="padding:8px;">Policy Name</th>
            <th style="padding:8px;">Source</th>
            <th style="padding:8px;">Status</th>
            <th style="padding:8px;">Violations</th>
            <th style="padding:8px;">Severity</th>
            <th style="padding:8px;">Category</th>
            <th style="padding:8px;">Resource Type</th>
            <th style="padding:8px;">Last Evaluated</th>
        </tr>
    </thead>
    <tbody>
    """
    for f in findings:
        table_html += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:8px;">{f['policy_name']}</td>
            <td style="padding:8px;">{source_html(f['source'])}</td>
            <td style="padding:8px;">{status_html(f['status'])}</td>
            <td style="padding:8px;">{f['violations_count']}</td>
            <td style="padding:8px;">{severity_html(f['severity'])}</td>
            <td style="padding:8px;">{f['category']}</td>
            <td style="padding:8px;"><code>{f['resource_types']}</code></td>
            <td style="padding:8px; font-size:0.8rem;">{f['last_evaluated']}</td>
        </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

# ── Drill-down ───────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Policy Drill-Down")

policy_options = {f["policy_name"]: f["policy_id"] for f in findings} if findings else {}
if policy_options:
    selected_name = st.selectbox("Select a policy to inspect", list(policy_options.keys()))
    selected_id = policy_options[selected_name]

    # Resources
    resources = api_get("/policies/resources", params={"policy_id": selected_id})
    if resources:
        st.markdown(f"**Violating Resources** ({len(resources)})")
        res_rows = []
        for r in resources:
            res_rows.append({
                "Resource Key": r["resource_key"],
                "Type": r["type"],
                "Raw ID": r["raw_id"],
                "Region": r["region"],
                "Account": r["account_id"],
            })
        st.dataframe(res_rows, use_container_width=True)
    else:
        st.success("No violating resources (policy passed).")

    # Evidence
    evidence_list = api_get("/policies/evidence", params={"policy_id": selected_id})
    if evidence_list:
        with st.expander("Raw Evidence JSON", expanded=False):
            for ev in evidence_list:
                st.markdown(f"**Run**: `{ev['run_id']}`")
                try:
                    parsed = json.loads(ev["evidence_json"])
                    st.json(parsed)
                except json.JSONDecodeError:
                    st.code(ev["evidence_json"])
    else:
        st.info("No evidence available for this policy.")
else:
    st.info("Select filters above to view findings, then drill down here.")
