"""CoreStack – Unified Policy Compliance Dashboard (Mobile-First).

Mobile-first responsive design for optimal viewing on all devices.
"""

import json
import sqlite3
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Database Path ─────────────────────────────────────────────────────────────
def get_db_path():
    candidates = [
        Path(__file__).parent.parent / "corestack.db",
        Path.cwd() / "corestack.db",
        Path.cwd() / "corestack-integration-mock" / "corestack.db",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])

DB_PATH = get_db_path()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CoreStack – Unified Policy Compliance",
    page_icon="https://www.corestack.io/wp-content/uploads/2021/09/cropped-favicon-32x32.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Brand Colors ──────────────────────────────────────────────────────────────
BLUE = "#0066cc"
DARK_BLUE = "#003d7a"
SUCCESS = "#276749"
DANGER = "#C53030"
WARNING = "#C05621"
TEXT = "#1A202C"
TEXT_LIGHT = "#4A5568"
BG = "#FFFFFF"
BORDER = "#E2E8F0"

# ── Mobile-First CSS ──────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,1,0');

    /* Base - Mobile First - Apply Inter to text elements only */
    * {{
        box-sizing: border-box;
    }}

    body, p, span, div, label, li, h1, h2, h3, h4, h5, h6,
    button, input, select, textarea, td, th {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .material-symbols-outlined {{
        font-family: 'Material Symbols Outlined' !important;
        font-size: 24px;
        vertical-align: middle;
        color: {DARK_BLUE};
    }}

    /* Custom Expander Styling */
    .custom-expander {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin: 0.5rem 1rem;
        background: {BG};
    }}

    .custom-expander summary {{
        padding: 0.75rem 1rem;
        cursor: pointer;
        font-weight: 500;
        color: {TEXT};
        list-style: none;
        display: flex;
        align-items: center;
    }}

    .custom-expander summary::-webkit-details-marker {{
        display: none;
    }}

    .custom-expander summary::before {{
        content: "▶";
        font-size: 0.7rem;
        margin-right: 0.75rem;
        transition: transform 0.2s;
        color: {DARK_BLUE};
    }}

    .custom-expander[open] summary::before {{
        transform: rotate(90deg);
    }}

    .custom-expander .expander-content {{
        padding: 0 1rem 1rem 2rem;
        color: {TEXT_LIGHT};
    }}

    .custom-expander ul {{
        margin: 0;
        padding-left: 1rem;
    }}

    .custom-expander li {{
        margin: 0.25rem 0;
        color: {TEXT_LIGHT} !important;
    }}

    /* Detail section headers */
    .detail-section {{
        padding: 0.75rem 1rem;
        margin: 0.5rem 1rem;
        border: 1px solid {BORDER};
        border-radius: 8px;
        background: {BG};
        color: {TEXT} !important;
    }}

    .detail-section strong {{
        color: {DARK_BLUE} !important;
    }}

    /* Hide Streamlit elements */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}

    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    /* Force light theme and dark text */
    .stApp, .main, [data-testid="stAppViewContainer"] {{
        background: {BG} !important;
        color: {TEXT} !important;
    }}

    /* All text dark by default */
    p, span, div, label, li {{
        color: {TEXT} !important;
    }}

    /* Remove default padding */
    .main .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}

    /* Header Banner */
    .header {{
        background: linear-gradient(135deg, {BLUE} 0%, {DARK_BLUE} 100%);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }}

    .header h1, .header p, .header * {{
        color: #FFFFFF !important;
    }}

    .header h1 {{
        font-size: 1.75rem !important;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        color: #FFFFFF !important;
    }}

    .header p {{
        font-size: 0.9rem;
        margin: 0;
        color: #FFFFFF !important;
    }}

    /* Section Titles */
    .section-title {{
        color: {DARK_BLUE} !important;
        font-size: 1rem;
        font-weight: 600;
        margin: 1rem 0 0.5rem 0;
        padding: 0 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* KPI Grid - Mobile: 2 columns */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
        padding: 0 0.5rem;
        margin-bottom: 1rem;
    }}

    .kpi-card {{
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        border: 1px solid {BORDER};
    }}

    .kpi-icon {{
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.5rem;
    }}

    .kpi-icon.blue {{ background: rgba(0,102,204,0.1); }}
    .kpi-icon.green {{ background: rgba(39,103,73,0.1); }}
    .kpi-icon.red {{ background: rgba(197,48,48,0.1); }}
    .kpi-icon.orange {{ background: rgba(192,86,33,0.1); }}

    .kpi-icon .material-symbols-outlined {{
        font-size: 18px;
    }}

    .kpi-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {TEXT} !important;
        line-height: 1;
    }}

    .kpi-label {{
        font-size: 0.7rem;
        color: {TEXT_LIGHT} !important;
        margin-top: 0.25rem;
    }}

    .kpi-badge {{
        display: inline-block;
        font-size: 0.6rem;
        padding: 0.15rem 0.4rem;
        border-radius: 10px;
        margin-top: 0.25rem;
    }}

    .kpi-badge.up {{
        background: rgba(39,103,73,0.1);
        color: {SUCCESS} !important;
    }}

    .kpi-badge.down {{
        background: rgba(197,48,48,0.1);
        color: {DANGER} !important;
    }}

    /* Content Padding */
    .content {{
        padding: 0 1rem;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        padding: 0 1rem;
        background: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        color: {TEXT_LIGHT} !important;
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        color: {BLUE} !important;
        font-weight: 600;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {BLUE} !important;
    }}

    /* Radio Buttons - Force dark text */
    .stRadio > label {{
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: {DARK_BLUE} !important;
    }}

    .stRadio [role="radiogroup"] {{
        gap: 0.5rem !important;
        flex-wrap: wrap !important;
    }}

    .stRadio label[data-baseweb="radio"] {{
        padding: 0.4rem 0.6rem !important;
        background: white !important;
        border: 1px solid {BORDER} !important;
        border-radius: 6px !important;
        font-size: 0.75rem !important;
        color: {TEXT} !important;
    }}

    .stRadio label[data-baseweb="radio"] span {{
        color: {TEXT} !important;
    }}

    .stRadio label[data-baseweb="radio"] div {{
        color: {TEXT} !important;
    }}

    /* Charts */
    .chart-container {{
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0 0.5rem 1rem 0.5rem;
        border: 1px solid {BORDER};
    }}

    .chart-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {DARK_BLUE} !important;
        margin-bottom: 0.5rem;
    }}

    /* Data Table */
    [data-testid="stDataFrame"] {{
        font-size: 0.75rem !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
    }}

    [data-testid="stDataFrame"] > div {{
        overflow-x: auto !important;
    }}

    /* Selectbox */
    .stSelectbox label {{
        color: {DARK_BLUE} !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }}

    .stSelectbox > div > div {{
        border: 1px solid {BORDER} !important;
        border-radius: 6px !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: {DARK_BLUE} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        background: white !important;
    }}

    details {{
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        margin-bottom: 0.5rem !important;
    }}

    /* Benefits Grid */
    .benefits-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
        padding: 0 0.5rem;
    }}

    .benefit-card {{
        background: white;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid {BORDER};
    }}

    .benefit-icon {{
        font-size: 2rem;
        color: {DARK_BLUE} !important;
        margin-bottom: 0.5rem;
    }}

    .benefit-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {TEXT} !important;
        margin-bottom: 0.25rem;
    }}

    .benefit-desc {{
        font-size: 0.7rem;
        color: {TEXT_LIGHT} !important;
    }}

    /* Info Box */
    .info-box {{
        background: #F7FAFC;
        border-radius: 8px;
        padding: 1rem;
        margin: 0 0.5rem 1rem 0.5rem;
        border: 1px solid {BORDER};
    }}

    .info-box p {{
        font-size: 0.85rem;
        color: {TEXT} !important;
        margin: 0;
        line-height: 1.5;
    }}

    /* Output Options */
    .output-grid {{
        display: grid;
        grid-template-columns: repeat(1, 1fr);
        gap: 0.5rem;
        padding: 0 0.5rem;
    }}

    .output-card {{
        background: white;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid {BORDER};
    }}

    .output-card h4 {{
        color: {DARK_BLUE} !important;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .output-card p {{
        font-size: 0.8rem;
        color: {TEXT_LIGHT} !important;
        margin: 0;
        line-height: 1.4;
    }}

    .output-card ul {{
        margin: 0.5rem 0 0 0;
        padding-left: 1.25rem;
        font-size: 0.75rem;
        color: {TEXT} !important;
    }}

    .output-card li {{
        margin-bottom: 0.25rem;
        color: {TEXT} !important;
    }}

    /* Markdown content */
    .stMarkdown {{
        color: {TEXT} !important;
    }}

    .stMarkdown p, .stMarkdown li, .stMarkdown span {{
        color: {TEXT} !important;
        font-size: 0.85rem;
    }}

    .stMarkdown strong {{
        color: {TEXT} !important;
    }}

    /* Columns containers */
    [data-testid="column"] {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 0.5rem !important;
        background: white;
    }}

    /* Filter container */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        background: white !important;
    }}

    /* Footer */
    .footer {{
        text-align: center;
        padding: 1.5rem 1rem;
        color: {TEXT_LIGHT} !important;
        font-size: 0.75rem;
        border-top: 1px solid {BORDER};
        margin-top: 2rem;
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       TABLET (min-width: 640px)
       ═══════════════════════════════════════════════════════════════════════ */
    @media (min-width: 640px) {{
        .header {{
            padding: 1.25rem 1.5rem;
        }}

        .header h1 {{
            font-size: 1.5rem !important;
        }}

        .header p {{
            font-size: 0.9rem;
        }}

        .kpi-grid {{
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
            padding: 0 1rem;
        }}

        .kpi-value {{
            font-size: 1.75rem;
        }}

        .section-title {{
            font-size: 1.1rem;
        }}

        .benefits-grid {{
            grid-template-columns: repeat(4, 1fr);
            padding: 0 1rem;
        }}

        .output-grid {{
            grid-template-columns: repeat(3, 1fr);
            padding: 0 1rem;
        }}
    }}

    /* ═══════════════════════════════════════════════════════════════════════
       DESKTOP (min-width: 1024px)
       ═══════════════════════════════════════════════════════════════════════ */
    @media (min-width: 1024px) {{
        .main .block-container {{
            max-width: 1200px !important;
            margin: 0 auto;
            padding: 0 1rem !important;
        }}

        .header {{
            padding: 1.5rem 2rem;
            border-radius: 0 0 12px 12px;
        }}

        .header h1 {{
            font-size: 1.75rem !important;
        }}

        .kpi-grid {{
            grid-template-columns: repeat(6, 1fr);
            gap: 1rem;
            padding: 0;
        }}

        .kpi-card {{
            padding: 1rem;
        }}

        .kpi-value {{
            font-size: 2rem;
        }}

        .kpi-label {{
            font-size: 0.8rem;
        }}

        .chart-container {{
            margin: 0 0 1rem 0;
        }}

        .benefits-grid {{
            padding: 0;
        }}

        .output-grid {{
            padding: 0;
        }}

        .info-box {{
            margin: 0 0 1rem 0;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ── Database Functions ────────────────────────────────────────────────────────
def get_db():
    return sqlite3.connect(DB_PATH)

def db_get_summary(source=None, status=None, severity=None):
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if source:
        where_clauses.append("p.source = ?")
        params.append(source)
    if status:
        where_clauses.append("f.status = ?")
        params.append(status)
    if severity:
        where_clauses.append("p.severity = ?")
        params.append(severity)

    where_sql = " AND ".join(where_clauses)

    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT f.policy_id),
            SUM(CASE WHEN f.status = 'PASS' THEN 1 ELSE 0 END),
            SUM(CASE WHEN f.status = 'FAIL' THEN 1 ELSE 0 END),
            MAX(f.last_evaluated)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id)
        AND {where_sql}
    """, params)

    row = cursor.fetchone()
    total = row[0] or 0
    passing = row[1] or 0
    failing = row[2] or 0
    last_eval = row[3]

    cursor.execute(f"""
        SELECT p.source, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id)
        AND {where_sql}
        GROUP BY p.source, f.status
    """, params)

    by_source = {}
    for src, stat, count in cursor.fetchall():
        if src not in by_source:
            by_source[src] = {}
        by_source[src][stat] = count

    cursor.execute(f"""
        SELECT p.severity, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id)
        AND {where_sql}
        GROUP BY p.severity, f.status
    """, params)

    by_severity = {}
    for sev, stat, count in cursor.fetchall():
        if sev not in by_severity:
            by_severity[sev] = {}
        by_severity[sev][stat] = count

    conn.close()

    return {
        "total": total,
        "passing": passing,
        "failing": failing,
        "last_evaluated": last_eval,
        "by_source": by_source,
        "by_severity": by_severity
    }

def db_get_findings(source=None, status=None, severity=None):
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT f.policy_id, p.name, p.source, f.status, f.violations_count,
               p.severity, p.category, p.resource_types, f.last_evaluated
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE (f.policy_id, f.run_id) IN (SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id)
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

    return [{
        "policy_id": r[0], "policy_name": r[1], "source": r[2],
        "status": r[3], "violations_count": r[4], "severity": r[5],
        "category": r[6], "resource_types": r[7], "last_evaluated": r[8]
    } for r in rows]

def db_get_resources(policy_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT resource_key, raw_id, type, region, account_id, tags_json
        FROM resources WHERE policy_id = ? ORDER BY resource_key
    """, (policy_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"resource_key": r[0], "raw_id": r[1], "type": r[2],
             "region": r[3], "account_id": r[4], "tags_json": r[5]} for r in rows]

def db_get_evidence(policy_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT run_id, evidence_json FROM evidence
        WHERE policy_id = ? ORDER BY run_id DESC
    """, (policy_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"run_id": r[0], "evidence_json": r[1]} for r in rows]

# ── Check Database ────────────────────────────────────────────────────────────
if not Path(DB_PATH).exists():
    st.error(f"Database not found: `{DB_PATH}`\n\nRun: `python scripts/ingest_once.py`")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="header">
    <h1>◈ CoreStack – Unified Policy Compliance</h1>
    <p>Real-time cloud governance • Cloud Custodian + CoreStack Native</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS - Executive Summary FIRST
# ══════════════════════════════════════════════════════════════════════════════
tab_summary, tab_dashboard = st.tabs(["Executive Summary", "Dashboard"])

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_summary:

    st.markdown('<div class="section-title"><span class="material-symbols-outlined">summarize</span>Overview</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        <p>This POC demonstrates <strong>CoreStack's unified cloud governance platform</strong> that aggregates
        compliance findings from multiple policy engines into a single dashboard. The solution ingests real
        Cloud Custodian scan results from live AWS resources and presents them alongside CoreStack-native policies.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Key Benefits ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">verified</span>Key Benefits</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="benefits-grid">
        <div class="benefit-card">
            <div class="benefit-icon"><span class="material-symbols-outlined" style="font-size:2rem;color:{DARK_BLUE};">speed</span></div>
            <div class="benefit-title">80% Faster</div>
            <div class="benefit-desc">Reduce compliance reporting time</div>
        </div>
        <div class="benefit-card">
            <div class="benefit-icon"><span class="material-symbols-outlined" style="font-size:2rem;color:{DARK_BLUE};">visibility</span></div>
            <div class="benefit-title">100% Visibility</div>
            <div class="benefit-desc">Complete view across engines</div>
        </div>
        <div class="benefit-card">
            <div class="benefit-icon"><span class="material-symbols-outlined" style="font-size:2rem;color:{DARK_BLUE};">security</span></div>
            <div class="benefit-title">Reduced Risk</div>
            <div class="benefit-desc">Catch violations early</div>
        </div>
        <div class="benefit-card">
            <div class="benefit-icon"><span class="material-symbols-outlined" style="font-size:2rem;color:{DARK_BLUE};">savings</span></div>
            <div class="benefit-title">Cost Savings</div>
            <div class="benefit-desc">Eliminate manual work</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Output Options ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">output</span>Output Options</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="output-grid">
        <div class="output-card">
            <h4><span class="material-symbols-outlined" style="font-size:1.25rem;color:{BLUE};">api</span> API</h4>
            <p>RESTful API access for programmatic integration</p>
            <ul>
                <li>CI/CD pipelines</li>
                <li>SIEM systems</li>
                <li>Custom applications</li>
            </ul>
        </div>
        <div class="output-card">
            <h4><span class="material-symbols-outlined" style="font-size:1.25rem;color:{BLUE};">link</span> Embeddable Link</h4>
            <p>Shareable dashboard URL for easy access</p>
            <ul>
                <li>Internal portals</li>
                <li>Confluence/Wiki</li>
                <li>Slack/Teams</li>
            </ul>
        </div>
        <div class="output-card">
            <h4><span class="material-symbols-outlined" style="font-size:1.25rem;color:{BLUE};">dashboard</span> Dashboard</h4>
            <p>Interactive web interface with full features</p>
            <ul>
                <li>KPI cards & metrics</li>
                <li>Filterable reports</li>
                <li>Evidence viewer</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Solution Overview ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">lightbulb</span>Solution Overview</div>', unsafe_allow_html=True)

    st.markdown("""
    **CoreStack Unified Governance** provides:
    - **Single Pane of Glass**: Aggregate findings from Cloud Custodian, AWS Config, Azure Policy
    - **Normalized Data Model**: Consistent schema across all policy engines
    - **Real-Time Visibility**: Continuous compliance monitoring
    - **Evidence Collection**: Automated capture of violation details
    """)

    # ── Data Flow ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">account_tree</span>Data Flow Architecture</div>', unsafe_allow_html=True)

    st.graphviz_chart('''
        digraph G {
            rankdir=TB;
            bgcolor="transparent";
            node [shape=box, style="rounded,filled", fontname="Inter", fontsize=10, margin="0.2"];
            edge [fontname="Inter", fontsize=8, color="#718096"];

            aws [label="AWS Cloud", fillcolor="#FF9900", fontcolor="white"];
            custodian [label="Cloud Custodian", fillcolor="#6C63FF", fontcolor="white"];
            ingest [label="Ingestion Layer", fillcolor="#0066cc", fontcolor="white"];
            db [label="CoreStack DB", fillcolor="#003d7a", fontcolor="white"];
            dashboard [label="Recommendation Dashboard", fillcolor="#276749", fontcolor="white"];

            aws -> custodian -> ingest -> db -> dashboard;
        }
    ''')

    # ── Integrations ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">hub</span>Supported Integrations</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Policy Engines**
        - Cloud Custodian
        - AWS Config Rules
        - Azure Policy
        - Open Policy Agent
        """)

    with col2:
        st.markdown("""
        **Cloud Providers**
        - Amazon Web Services
        - Microsoft Azure
        - Google Cloud Platform
        """)

    # ── Use Cases ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">cases</span>Use Cases</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <details class="custom-expander">
        <summary>Compliance Audits</summary>
        <div class="expander-content">
            <ul>
                <li>Generate audit-ready reports</li>
                <li>Provide evidence for SOC2, HIPAA, PCI-DSS</li>
                <li>Track compliance trends over time</li>
            </ul>
        </div>
    </details>
    <details class="custom-expander">
        <summary>Security Operations</summary>
        <div class="expander-content">
            <ul>
                <li>Monitor security posture in real-time</li>
                <li>Prioritize remediation by severity</li>
                <li>Integrate with SIEM/SOAR platforms</li>
            </ul>
        </div>
    </details>
    <details class="custom-expander">
        <summary>DevSecOps</summary>
        <div class="expander-content">
            <ul>
                <li>Shift-left security in CI/CD</li>
                <li>Automate policy checks in pipelines</li>
                <li>Provide developer-friendly feedback</li>
            </ul>
        </div>
    </details>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_dashboard:

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">filter_alt</span>Filters</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        source_opt = st.radio("Source", ["All", "Cloud Custodian", "CoreStack"],
                              horizontal=True, key="src")
        source_param = None
        if source_opt == "Cloud Custodian":
            source_param = "cloudcustodian"
        elif source_opt == "CoreStack":
            source_param = "corestack"

    with col2:
        status_opt = st.radio("Status", ["All", "PASS", "FAIL"],
                              horizontal=True, key="stat")
        status_param = None if status_opt == "All" else status_opt

    with col3:
        severity_opt = st.radio("Severity", ["All", "High", "Medium", "Low"],
                                horizontal=True, key="sev")
        severity_param = None if severity_opt == "All" else severity_opt.lower()

    # ── Get Data ──────────────────────────────────────────────────────────────
    summary = db_get_summary(source=source_param, status=status_param, severity=severity_param)
    compliance_rate = round((summary['passing'] / max(summary['total'], 1)) * 100)

    custodian_data = summary.get('by_source', {}).get('cloudcustodian', {})
    custodian_count = custodian_data.get('PASS', 0) + custodian_data.get('FAIL', 0)

    corestack_data = summary.get('by_source', {}).get('corestack', {})
    corestack_count = corestack_data.get('PASS', 0) + corestack_data.get('FAIL', 0)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">analytics</span>Overview</div>', unsafe_allow_html=True)

    last_eval_display = summary.get('last_evaluated', 'N/A')
    if last_eval_display and last_eval_display != 'N/A':
        last_eval_display = last_eval_display[:10]

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined" style="color:{BLUE};">policy</span></div>
            <div class="kpi-value">{summary['total']}</div>
            <div class="kpi-label">Total Policies</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined" style="color:{BLUE};">cloud</span></div>
            <div class="kpi-value">{custodian_count}</div>
            <div class="kpi-label">Cloud Custodian</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined" style="color:{BLUE};">domain</span></div>
            <div class="kpi-value">{corestack_count}</div>
            <div class="kpi-label">CoreStack</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon green"><span class="material-symbols-outlined" style="color:{SUCCESS};">check_circle</span></div>
            <div class="kpi-value" style="color:{SUCCESS};">{summary['passing']}</div>
            <div class="kpi-label">Compliant</div>
            <div class="kpi-badge up">{compliance_rate}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon red"><span class="material-symbols-outlined" style="color:{DANGER};">cancel</span></div>
            <div class="kpi-value" style="color:{DANGER};">{summary['failing']}</div>
            <div class="kpi-label">Non-Compliant</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon orange"><span class="material-symbols-outlined" style="color:{WARNING};">schedule</span></div>
            <div class="kpi-value" style="font-size:1rem;">{last_eval_display}</div>
            <div class="kpi-label">Last Evaluated</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">bar_chart</span>Compliance Breakdown</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(f'<div class="chart-title">By Source</div>', unsafe_allow_html=True)

        source_labels, source_pass, source_fail = [], [], []
        for src, counts in summary.get("by_source", {}).items():
            label = "Cloud Custodian" if src == "cloudcustodian" else "CoreStack"
            source_labels.append(label)
            source_pass.append(counts.get("PASS", 0))
            source_fail.append(counts.get("FAIL", 0))

        if source_labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Pass', x=source_labels, y=source_pass,
                                marker_color=SUCCESS, text=source_pass, textposition='auto'))
            fig.add_trace(go.Bar(name='Fail', x=source_labels, y=source_fail,
                                marker_color=DANGER, text=source_fail, textposition='auto'))
            fig.update_layout(barmode='group', height=250, margin=dict(l=0,r=0,t=10,b=30),
                            legend=dict(orientation="h", y=1.15), showlegend=True,
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.markdown(f'<div class="chart-title">By Severity</div>', unsafe_allow_html=True)

        sev_labels, sev_pass, sev_fail = [], [], []
        for sev in ["high", "medium", "low"]:
            counts = summary.get("by_severity", {}).get(sev, {})
            if counts.get("PASS", 0) > 0 or counts.get("FAIL", 0) > 0:
                sev_labels.append(sev.upper())
                sev_pass.append(counts.get("PASS", 0))
                sev_fail.append(counts.get("FAIL", 0))

        if sev_labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Pass', x=sev_labels, y=sev_pass,
                                marker_color=SUCCESS, text=sev_pass, textposition='auto'))
            fig.add_trace(go.Bar(name='Fail', x=sev_labels, y=sev_fail,
                                marker_color=DANGER, text=sev_fail, textposition='auto'))
            fig.update_layout(barmode='group', height=250, margin=dict(l=0,r=0,t=10,b=30),
                            legend=dict(orientation="h", y=1.15), showlegend=True,
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

    # ── Findings Table ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title"><span class="material-symbols-outlined">list_alt</span>Policy Findings</div>', unsafe_allow_html=True)

    findings = db_get_findings(source=source_param, status=status_param, severity=severity_param)

    if not findings:
        st.info("No findings match the current filters.")
    else:
        table_data = []
        for f in findings:
            src_label = "Custodian" if f['source'] == "cloudcustodian" else "CoreStack"
            table_data.append({
                "Policy": f['policy_name'],
                "Source": src_label,
                "Status": f['status'],
                "Violations": int(f['violations_count']),
                "Severity": f['severity'].upper()
            })

        df = pd.DataFrame(table_data)

        def style_status(val):
            if val == "PASS":
                return f'color: {SUCCESS}; font-weight: 600'
            elif val == "FAIL":
                return f'color: {DANGER}; font-weight: 600'
            return ''

        styled = df.style.applymap(style_status, subset=['Status'])
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Policy Details ────────────────────────────────────────────────────────
    if findings:
        st.markdown('<div class="section-title"><span class="material-symbols-outlined">search</span>Policy Details</div>', unsafe_allow_html=True)

        policy_options = {f["policy_name"]: f["policy_id"] for f in findings}
        selected = st.selectbox("Select a policy", list(policy_options.keys()))

        if selected:
            policy_id = policy_options[selected]
            resources = db_get_resources(policy_id)
            evidence = db_get_evidence(policy_id)

            if resources:
                st.markdown(f'<div class="detail-section"><strong>▶ Resources ({len(resources)})</strong></div>', unsafe_allow_html=True)
                res_df = pd.DataFrame(resources)[['resource_key', 'type', 'region']]
                st.dataframe(res_df, use_container_width=True, hide_index=True)

            if evidence:
                st.markdown('<div class="detail-section"><strong>▶ Evidence</strong></div>', unsafe_allow_html=True)
                for ev in evidence[:2]:
                    st.code(ev['evidence_json'][:500] + "..." if len(ev['evidence_json']) > 500 else ev['evidence_json'])

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="footer">
    <strong>◈ CoreStack</strong> – AI-Powered Cloud Governance Platform<br>
    <span style="color:{TEXT_LIGHT};">POC Demo</span>
</div>
""", unsafe_allow_html=True)
