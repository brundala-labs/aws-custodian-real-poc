"""Streamlit UI: CoreStack – Unified Policy Compliance (POC).

Standalone version that reads directly from SQLite for Streamlit Cloud deployment.
"""

import json
import os
import sqlite3
from pathlib import Path
import streamlit as st

# ── Database Path ─────────────────────────────────────────────────────────────
# Look for database in multiple locations for flexibility
def get_db_path():
    candidates = [
        Path(__file__).parent.parent / "corestack.db",  # ../corestack.db from ui/
        Path.cwd() / "corestack.db",
        Path.cwd() / "corestack-integration-mock" / "corestack.db",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])  # Default to first candidate

DB_PATH = get_db_path()

st.set_page_config(
    page_title="CoreStack – Unified Policy Compliance",
    page_icon="https://www.corestack.io/wp-content/uploads/2021/09/cropped-favicon-32x32.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CoreStack Brand Colors ───────────────────────────────────────────────────
CORESTACK_BLUE = "#0076e1"
CORESTACK_DARK_BLUE = "#004789"
CORESTACK_LIGHT_BG = "#F7FAFC"
CORESTACK_CARD_BG = "#FFFFFF"
CORESTACK_TEXT_DARK = "#1A202C"
CORESTACK_TEXT_MID = "#495974"
CORESTACK_SUCCESS = "#38A169"
CORESTACK_DANGER = "#E53E3E"
CORESTACK_WARNING = "#DD6B20"

# ── Custom CSS with CoreStack Branding ───────────────────────────────────────

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0');

    .material-symbols-outlined {{
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }}

    * {{
        font-family: 'Nunito Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    /* Bordered containers */
    .bordered-box {{
        border: 2px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}

    /* Findings Table */
    .findings-table {{
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
        margin-top: 1rem;
    }}
    .findings-table th {{
        background: linear-gradient(135deg, {CORESTACK_BLUE} 0%, {CORESTACK_DARK_BLUE} 100%);
        color: white;
        padding: 12px 16px;
        text-align: left;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .findings-table td {{
        padding: 12px 16px;
        border-bottom: 1px solid #E2E8F0;
        font-size: 0.9rem;
    }}
    .findings-table tr:last-child td {{
        border-bottom: none;
    }}
    .findings-table tr.row-pass {{
        background-color: #F0FFF4;
    }}
    .findings-table tr.row-fail {{
        background-color: #FFF5F5;
    }}
    .findings-table tr:hover {{
        filter: brightness(0.97);
    }}

    /* Status badges */
    .badge-pass {{
        background: #38A169;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }}
    .badge-fail {{
        background: #E53E3E;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }}

    /* Severity badges */
    .badge-high {{
        color: #E53E3E;
        font-weight: 700;
    }}
    .badge-medium {{
        color: #DD6B20;
        font-weight: 700;
    }}
    .badge-low {{
        color: #3182CE;
        font-weight: 700;
    }}

    /* Violations count */
    .violations-count {{
        display: inline-block;
        min-width: 28px;
        text-align: center;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
    }}
    .violations-red {{
        background: #FED7D7;
        color: #C53030;
    }}
    .violations-green {{
        background: #C6F6D5;
        color: #276749;
    }}

    /* Header Banner */
    .header-banner {{
        background: linear-gradient(135deg, {CORESTACK_BLUE} 0%, {CORESTACK_DARK_BLUE} 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 118, 225, 0.3);
    }}
    .header-banner h1 {{
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }}
    .header-banner p {{
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }}

    /* KPI Cards */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}
    .kpi-card {{
        background: {CORESTACK_CARD_BG};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }}
    .kpi-icon {{
        width: 48px;
        height: 48px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }}
    .kpi-icon.blue {{ background: rgba(0, 118, 225, 0.1); color: {CORESTACK_BLUE}; }}
    .kpi-icon.green {{ background: rgba(56, 161, 105, 0.1); color: {CORESTACK_SUCCESS}; }}
    .kpi-icon.red {{ background: rgba(229, 62, 62, 0.1); color: {CORESTACK_DANGER}; }}
    .kpi-icon.orange {{ background: rgba(221, 107, 32, 0.1); color: {CORESTACK_WARNING}; }}
    .kpi-value {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {CORESTACK_TEXT_DARK};
        line-height: 1;
        margin-bottom: 0.25rem;
    }}
    .kpi-label {{
        font-size: 0.9rem;
        color: {CORESTACK_TEXT_MID};
        font-weight: 600;
    }}
    .kpi-trend {{
        font-size: 0.8rem;
        margin-top: 0.5rem;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }}
    .kpi-trend.up {{ background: rgba(56, 161, 105, 0.1); color: {CORESTACK_SUCCESS}; }}
    .kpi-trend.down {{ background: rgba(229, 62, 62, 0.1); color: {CORESTACK_DANGER}; }}

    /* Status Badges */
    .status-pass {{
        background: linear-gradient(135deg, {CORESTACK_SUCCESS} 0%, #2F855A 100%);
        color: white;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .status-fail {{
        background: linear-gradient(135deg, {CORESTACK_DANGER} 0%, #C53030 100%);
        color: white;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* Source Badges */
    .source-badge {{
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    .source-cloudcustodian {{
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        color: #1565C0;
        border: 1px solid #90CAF9;
    }}
    .source-corestack {{
        background: linear-gradient(135deg, {CORESTACK_BLUE}15 0%, {CORESTACK_BLUE}25 100%);
        color: {CORESTACK_BLUE};
        border: 1px solid {CORESTACK_BLUE}50;
    }}

    /* Severity Badges */
    .severity-high {{
        color: {CORESTACK_DANGER};
        font-weight: 700;
    }}
    .severity-medium {{
        color: {CORESTACK_WARNING};
        font-weight: 700;
    }}
    .severity-low {{
        color: {CORESTACK_TEXT_MID};
        font-weight: 600;
    }}

    /* Data Table */
    .data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: {CORESTACK_CARD_BG};
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #E2E8F0;
    }}
    .data-table thead {{
        background: linear-gradient(180deg, #F8FAFC 0%, #EDF2F7 100%);
    }}
    .data-table th {{
        padding: 1rem;
        text-align: left;
        font-weight: 700;
        color: {CORESTACK_TEXT_DARK};
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #E2E8F0;
    }}
    .data-table td {{
        padding: 1rem;
        border-bottom: 1px solid #EDF2F7;
        color: {CORESTACK_TEXT_DARK};
        font-size: 0.9rem;
    }}
    .data-table tbody tr {{
        transition: background 0.15s;
    }}
    .data-table tbody tr:hover {{
        background: #F7FAFC;
    }}
    .data-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    /* Section Headers */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #E2E8F0;
    }}
    .section-header h3 {{
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: {CORESTACK_TEXT_DARK};
    }}
    .section-icon {{
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, {CORESTACK_BLUE} 0%, {CORESTACK_DARK_BLUE} 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1rem;
    }}

    /* Diff-style Breakdown */
    .diff-container {{
        background: {CORESTACK_CARD_BG};
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .diff-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #E2E8F0;
    }}
    .diff-header h4 {{
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: {CORESTACK_TEXT_DARK};
    }}
    .diff-row {{
        display: flex;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #F1F5F9;
    }}
    .diff-row:last-child {{
        border-bottom: none;
    }}
    .diff-label {{
        width: 140px;
        font-weight: 600;
        color: {CORESTACK_TEXT_DARK};
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .diff-label .material-symbols-outlined {{
        font-size: 20px;
    }}
    .diff-bar-container {{
        flex: 1;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        height: 28px;
    }}
    .diff-bar {{
        height: 100%;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        color: white;
        min-width: 36px;
        transition: width 0.3s ease;
    }}
    .diff-bar.pass {{
        background: linear-gradient(135deg, {CORESTACK_SUCCESS} 0%, #2F855A 100%);
    }}
    .diff-bar.fail {{
        background: linear-gradient(135deg, {CORESTACK_DANGER} 0%, #C53030 100%);
    }}
    .diff-bar.empty {{
        background: #E2E8F0;
        color: #A0AEC0;
    }}
    .diff-stats {{
        display: flex;
        gap: 1rem;
        margin-left: auto;
        min-width: 120px;
        justify-content: flex-end;
    }}
    .diff-stat {{
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .diff-stat.pass {{
        color: {CORESTACK_SUCCESS};
    }}
    .diff-stat.fail {{
        color: {CORESTACK_DANGER};
    }}
    .diff-stat .material-symbols-outlined {{
        font-size: 18px;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FAFBFC 0%, #F1F5F9 100%);
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 2rem;
    }}

    /* Custom Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {CORESTACK_BLUE} 0%, {CORESTACK_DARK_BLUE} 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        font-size: 0.9rem;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(0, 118, 225, 0.3);
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(0, 118, 225, 0.4);
    }}

    /* Metrics styling override */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 800;
    }}

    /* Expander styling */
    .streamlit-expanderHeader {{
        background: #F7FAFC;
        border-radius: 8px;
        font-weight: 600;
    }}

    /* Code blocks */
    code {{
        background: #EDF2F7;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: {CORESTACK_DARK_BLUE};
    }}
</style>
""", unsafe_allow_html=True)


# ── Database Functions ────────────────────────────────────────────────────────

def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def db_get_summary():
    """Get summary statistics from database."""
    conn = get_db()
    cursor = conn.cursor()

    # Total policies
    cursor.execute("SELECT COUNT(*) FROM policies")
    total = cursor.fetchone()[0]

    # Passing/Failing counts
    cursor.execute("""
        SELECT status, COUNT(*) FROM findings
        WHERE (policy_id, run_id) IN (
            SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id
        )
        GROUP BY status
    """)
    status_counts = dict(cursor.fetchall())
    passing = status_counts.get("PASS", 0)
    failing = status_counts.get("FAIL", 0)

    # Last evaluated
    cursor.execute("SELECT MAX(last_evaluated) FROM findings")
    last_eval = cursor.fetchone()[0]

    # By source breakdown
    cursor.execute("""
        SELECT p.source, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (
            SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id
        )
        GROUP BY p.source, f.status
    """)
    by_source = {}
    for source, status, count in cursor.fetchall():
        if source not in by_source:
            by_source[source] = {}
        by_source[source][status] = count

    # By severity breakdown
    cursor.execute("""
        SELECT p.severity, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (
            SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id
        )
        GROUP BY p.severity, f.status
    """)
    by_severity = {}
    for severity, status, count in cursor.fetchall():
        if severity not in by_severity:
            by_severity[severity] = {}
        by_severity[severity][status] = count

    conn.close()

    return {
        "total_policies": total,
        "passing": passing,
        "failing": failing,
        "last_evaluated": last_eval,
        "by_source": by_source,
        "by_severity": by_severity
    }


def db_get_findings(source=None, status=None, severity=None):
    """Get findings with optional filters."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            f.policy_id,
            p.name as policy_name,
            p.source,
            f.status,
            f.violations_count,
            p.severity,
            p.category,
            p.resource_types,
            f.last_evaluated
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (
            SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id
        )
    """
    params = []

    if source:
        query += " AND p.source = ?"
        params.append(source)
    if status:
        query += " AND f.status = ?"
        params.append(status)
    if severity:
        query += " AND p.severity = ?"
        params.append(severity)

    query += " ORDER BY f.status DESC, p.severity DESC, p.name"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "policy_id": r[0],
            "policy_name": r[1],
            "source": r[2],
            "status": r[3],
            "violations_count": r[4],
            "severity": r[5],
            "category": r[6],
            "resource_types": r[7],
            "last_evaluated": r[8]
        }
        for r in rows
    ]


def db_get_resources(policy_id):
    """Get resources for a policy."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT resource_key, raw_id, type, region, account_id, tags_json
        FROM resources
        WHERE policy_id = ?
        ORDER BY resource_key
    """, (policy_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "resource_key": r[0],
            "raw_id": r[1],
            "type": r[2],
            "region": r[3],
            "account_id": r[4],
            "tags_json": r[5]
        }
        for r in rows
    ]


def db_get_evidence(policy_id):
    """Get evidence for a policy."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT run_id, evidence_json
        FROM evidence
        WHERE policy_id = ?
        ORDER BY run_id DESC
    """, (policy_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "run_id": r[0],
            "evidence_json": r[1]
        }
        for r in rows
    ]


# ── HTML Helpers ──────────────────────────────────────────────────────────────

def status_html(status: str) -> str:
    cls = "status-pass" if status == "PASS" else "status-fail"
    icon = "✓" if status == "PASS" else "✗"
    return f'<span class="{cls}">{icon} {status}</span>'


def source_html(source: str) -> str:
    cls = f"source-{source}"
    if source == "cloudcustodian":
        label = "Cloud Custodian"
        icon = "☁"
    else:
        label = "CoreStack"
        icon = "◈"
    return f'<span class="source-badge {cls}">{icon} {label}</span>'


def severity_html(sev: str) -> str:
    icons = {"high": "●", "medium": "◐", "low": "○"}
    return f'<span class="severity-{sev}">{icons.get(sev, "○")} {sev.upper()}</span>'


# ── Check Database Exists ─────────────────────────────────────────────────────

if not Path(DB_PATH).exists():
    st.error(f"""
    **Database not found at:** `{DB_PATH}`

    Please run the ingestion script first:
    ```bash
    cd corestack-integration-mock
    python scripts/ingest_once.py
    ```
    """)
    st.stop()


# ── Header Banner ────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-banner">
    <h1>◈ CoreStack – Unified Policy Compliance</h1>
    <p>Real-time cloud governance across multiple policy engines • Cloud Custodian + CoreStack Native</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">◈</div>
        <div style="font-weight:700; color:#0076e1; font-size:1.1rem;">CoreStack</div>
        <div style="font-size:0.75rem; color:#495974;">Cloud Governance Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Filters")

    source_filter = st.selectbox(
        "Policy Source",
        ["All Sources", "cloudcustodian", "corestack"],
        format_func=lambda x: "All Sources" if x == "All Sources" else ("☁ Cloud Custodian" if x == "cloudcustodian" else "◈ CoreStack")
    )

    status_filter = st.selectbox(
        "Compliance Status",
        ["All Statuses", "FAIL", "PASS"],
        format_func=lambda x: "All Statuses" if x == "All Statuses" else ("✗ Failing" if x == "FAIL" else "✓ Passing")
    )

    severity_filter = st.selectbox(
        "Severity Level",
        ["All Severities", "high", "medium", "low"],
        format_func=lambda x: "All Severities" if x == "All Severities" else f"{'●' if x=='high' else '◐' if x=='medium' else '○'} {x.title()}"
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem; color:#718096; text-align:center;">
        <div>Powered by CoreStack</div>
        <div style="margin-top:0.25rem;">AI-Powered Cloud Governance</div>
    </div>
    """, unsafe_allow_html=True)

# ── KPI Cards ────────────────────────────────────────────────────────────────

summary = db_get_summary()

compliance_rate = round((summary['passing'] / max(summary['total_policies'], 1)) * 100)

st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-icon blue"><span class="material-symbols-outlined">policy</span></div>
        <div class="kpi-value">{summary['total_policies']}</div>
        <div class="kpi-label">Total Policies</div>
        <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">visibility</span> Unified View</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon green"><span class="material-symbols-outlined">check_circle</span></div>
        <div class="kpi-value" style="color:{CORESTACK_SUCCESS};">{summary['passing']}</div>
        <div class="kpi-label">Compliant</div>
        <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">trending_up</span> {compliance_rate}% Rate</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon red"><span class="material-symbols-outlined">cancel</span></div>
        <div class="kpi-value" style="color:{CORESTACK_DANGER};">{summary['failing']}</div>
        <div class="kpi-label">Non-Compliant</div>
        <div class="kpi-trend down"><span class="material-symbols-outlined" style="font-size:14px;">priority_high</span> Requires Action</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon orange"><span class="material-symbols-outlined">schedule</span></div>
        <div class="kpi-value" style="font-size:1rem;">{summary.get('last_evaluated', 'N/A')[:10] if summary.get('last_evaluated') else 'N/A'}</div>
        <div class="kpi-label">Last Evaluated</div>
        <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">sync</span> Auto-Sync</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Breakdown Section ────────────────────────────────────────────────────────

st.markdown("#### Compliance Breakdown")

col_a, col_b = st.columns(2)

with col_a:
    with st.container(border=True):
        st.markdown("**By Policy Source**")
        for src, counts in summary.get("by_source", {}).items():
            label = "Cloud Custodian" if src == "cloudcustodian" else "CoreStack"
            pass_count = counts.get("PASS", 0)
            fail_count = counts.get("FAIL", 0)
            total = pass_count + fail_count
            pass_pct = int((pass_count / total * 100)) if total > 0 else 0

            st.markdown(f"**{label}**")
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                st.metric("Pass", pass_count, delta=None)
            with c2:
                st.metric("Fail", fail_count, delta=None)
            with c3:
                st.progress(pass_pct / 100 if pass_pct > 0 else 0.01, text=f"{pass_pct}% compliant")
            st.divider()

with col_b:
    with st.container(border=True):
        st.markdown("**By Severity Level**")
        for sev in ["high", "medium", "low"]:
            counts = summary.get("by_severity", {}).get(sev, {})
            pass_count = counts.get("PASS", 0)
            fail_count = counts.get("FAIL", 0)
            total = pass_count + fail_count
            pass_pct = int((pass_count / total * 100)) if total > 0 else 0

            if sev == "high":
                st.markdown(f":red[**{sev.upper()}**]")
            elif sev == "medium":
                st.markdown(f":orange[**{sev.upper()}**]")
            else:
                st.markdown(f":blue[**{sev.upper()}**]")

            if total > 0:
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.metric("Pass", pass_count, delta=None)
                with c2:
                    st.metric("Fail", fail_count, delta=None)
                with c3:
                    st.progress(pass_pct / 100 if pass_pct > 0 else 0.01, text=f"{pass_pct}% compliant")
            else:
                st.caption("No policies")
            st.divider()

# ── Findings Table ───────────────────────────────────────────────────────────

st.markdown("#### Policy Compliance Findings")

# Apply filters
source_param = None if source_filter == "All Sources" else source_filter
status_param = None if status_filter == "All Statuses" else status_filter
severity_param = None if severity_filter == "All Severities" else severity_filter

findings = db_get_findings(source=source_param, status=status_param, severity=severity_param)

if not findings:
    st.info("No findings match the current filters. Try adjusting your filter criteria.")
else:
    import pandas as pd

    # Build dataframe
    table_data = []
    for f in findings:
        source_label = "Cloud Custodian" if f['source'] == "cloudcustodian" else "CoreStack"
        table_data.append({
            "Policy": f['policy_name'],
            "Source": source_label,
            "Status": f['status'],
            "Violations": f['violations_count'],
            "Severity": f['severity'].upper(),
            "Category": f['category'],
            "Resource Type": f['resource_types']
        })

    df = pd.DataFrame(table_data)

    # Use st.dataframe with column_config for styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Policy": st.column_config.TextColumn("Policy", width="large"),
            "Source": st.column_config.TextColumn("Source", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Violations": st.column_config.NumberColumn(
                "Violations",
                width="small",
                format="%d",
            ),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Resource Type": st.column_config.TextColumn("Resource Type", width="medium"),
        }
    )

    # Add legend
    st.caption("Legend: PASS = Compliant | FAIL = Non-compliant | Violations bar shows count")

# ── Drill-down Section ───────────────────────────────────────────────────────

st.markdown("#### Policy Deep Dive & Evidence")

policy_options = {f["policy_name"]: f["policy_id"] for f in findings} if findings else {}

if policy_options:
    selected_name = st.selectbox(
        "Select a policy to inspect",
        list(policy_options.keys()),
        help="Choose a policy to view detailed violation information and raw evidence"
    )
    selected_id = policy_options[selected_name]

    col1, col2 = st.columns([2, 1])

    with col1:
        # Resources
        resources = db_get_resources(selected_id)
        if resources:
            st.markdown(f"#### 🎯 Violating Resources ({len(resources)})")
            res_data = []
            for r in resources:
                res_data.append({
                    "Resource Key": r["resource_key"],
                    "Type": r["type"],
                    "ID": r["raw_id"],
                    "Region": r["region"],
                })
            st.dataframe(res_data, use_container_width=True, hide_index=True)
        else:
            st.success("✓ No violations found — this policy is compliant!")

    with col2:
        # Quick stats for selected policy
        selected_finding = next((f for f in findings if f["policy_id"] == selected_id), None)
        if selected_finding:
            st.markdown("#### 📊 Quick Stats")
            st.metric("Violations", selected_finding["violations_count"])
            st.metric("Severity", selected_finding["severity"].upper())
            st.metric("Category", selected_finding["category"].title())

    # Evidence
    evidence_list = db_get_evidence(selected_id)
    if evidence_list:
        with st.expander("📄 Raw Evidence JSON (Click to expand)", expanded=False):
            for ev in evidence_list:
                st.markdown(f"**Run ID**: `{ev['run_id']}`")
                try:
                    parsed = json.loads(ev["evidence_json"])
                    st.json(parsed)
                except json.JSONDecodeError:
                    st.code(ev["evidence_json"], language="json")
    else:
        st.info("No evidence data available for this policy.")
else:
    st.info("👆 Select filters above to view findings, then choose a policy to drill down.")

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:{CORESTACK_TEXT_MID}; font-size:0.8rem; padding:1rem 0;">
    <div><strong>◈ CoreStack</strong> – AI-Powered Cloud Governance Platform</div>
    <div style="margin-top:0.25rem;">Unified compliance visibility across Cloud Custodian, AWS Config, Azure Policy, and more</div>
    <div style="margin-top:0.5rem; color:#A0AEC0;">POC Demo • Not for Production Use</div>
</div>
""", unsafe_allow_html=True)
