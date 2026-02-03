"""Streamlit UI: CoreStack – Unified Policy Compliance (POC).

Standalone version that reads directly from SQLite for Streamlit Cloud deployment.
"""

import json
import os
import sqlite3
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

# ── CoreStack Brand Colors (Darker for better visibility) ────────────────────
CORESTACK_BLUE = "#0066cc"
CORESTACK_DARK_BLUE = "#003d7a"
CORESTACK_LIGHT_BG = "#EDF2F7"
CORESTACK_CARD_BG = "#FFFFFF"
CORESTACK_TEXT_DARK = "#1A202C"
CORESTACK_TEXT_MID = "#2D3748"
CORESTACK_SUCCESS = "#276749"  # Darker green
CORESTACK_DANGER = "#C53030"   # Darker red
CORESTACK_WARNING = "#C05621"  # Darker orange

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

    /* Force light theme with explicit text colors */
    .stApp {{
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }}

    .main {{
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }}

    [data-testid="stHeader"] {{
        background-color: #FFFFFF !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #F7FAFC !important;
        color: #1A202C !important;
    }}

    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }}

    /* Force dark text on all Streamlit elements */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {{
        color: #1A202C !important;
    }}

    /* Tabs text color */
    .stTabs [data-baseweb="tab"] {{
        color: {CORESTACK_DARK_BLUE} !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: {CORESTACK_BLUE} !important;
        font-weight: 700 !important;
    }}

    /* Tab indicator line */
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {CORESTACK_BLUE} !important;
    }}

    /* Radio button labels */
    .stRadio > label {{
        color: {CORESTACK_BLUE} !important;
        font-weight: 600 !important;
    }}

    .stRadio span {{
        color: {CORESTACK_DARK_BLUE} !important;
    }}

    /* Selectbox and other inputs */
    .stSelectbox label, .stTextInput label {{
        color: {CORESTACK_BLUE} !important;
        font-weight: 600 !important;
    }}

    /* Container text and borders */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        color: #1A202C !important;
    }}

    /* Make container borders visible with blue color */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border: 2px solid {CORESTACK_BLUE} !important;
        border-radius: 8px !important;
    }}

    /* Info/warning boxes */
    .stAlert {{
        color: #1A202C !important;
    }}

    /* Expander text */
    .streamlit-expanderHeader {{
        color: #1A202C !important;
    }}

    /* Caption text */
    .stCaption {{
        color: #4A5568 !important;
    }}

    /* Dataframe text colors */
    [data-testid="stDataFrame"] {{
        color: #1A202C !important;
    }}

    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {{
        color: #1A202C !important;
        background-color: #FFFFFF !important;
    }}

    /* Table headers */
    [data-testid="stDataFrame"] th {{
        background-color: #0076e1 !important;
        color: white !important;
    }}

    /* Bordered containers background */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }}

    /* Bold text */
    strong, b {{
        color: inherit !important;
    }}

    /* Links */
    a {{
        color: {CORESTACK_BLUE} !important;
    }}

    /* Headings - exclude header-banner which needs white text */
    h1:not(.header-banner h1), h2, h3, h4, h5, h6 {{
        color: {CORESTACK_BLUE} !important;
    }}

    /* Material icons in headings */
    h3 .material-symbols-outlined, h4 .material-symbols-outlined {{
        color: {CORESTACK_BLUE} !important;
    }}

    /* Ensure header banner text stays white */
    .header-banner, .header-banner * {{
        color: white !important;
    }}

    /* Mobile Responsive - Tablet */
    @media (max-width: 992px) {{
        .kpi-container, .kpi-6-cols {{
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 0.75rem !important;
        }}

        /* Stack 4 columns into 2 */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: 0 0 48% !important;
            min-width: 48% !important;
            margin-bottom: 0.5rem !important;
        }}
    }}

    /* Mobile Responsive - Phone */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 0.5rem !important;
        }}

        /* Force all text dark on mobile */
        body, .stApp, .main, [data-testid="stAppViewContainer"] {{
            color: #1A202C !important;
            background-color: #FFFFFF !important;
        }}

        /* All text elements dark */
        p, span, li, div, label {{
            color: #1A202C !important;
        }}

        /* Bold text */
        strong, b {{
            color: #1A202C !important;
        }}

        /* Captions */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: #4A5568 !important;
        }}

        /* KPI cards - 2 columns on phone */
        .kpi-container, .kpi-6-cols {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 0.5rem !important;
        }}

        .kpi-card {{
            padding: 0.75rem !important;
            background: #FFFFFF !important;
            color: #1A202C !important;
        }}

        .kpi-value {{
            font-size: 1.5rem !important;
            color: #1A202C !important;
        }}

        .kpi-label {{
            font-size: 0.75rem !important;
            color: #2D3748 !important;
        }}

        .kpi-icon {{
            width: 36px !important;
            height: 36px !important;
            font-size: 1rem !important;
            margin-bottom: 0.5rem !important;
        }}

        .kpi-trend {{
            font-size: 0.65rem !important;
            padding: 0.15rem 0.4rem !important;
        }}

        /* Header - keep white text */
        .header-banner {{
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }}

        .header-banner, .header-banner h1, .header-banner p, .header-banner * {{
            color: white !important;
        }}

        /* Stack ALL Streamlit columns vertically */
        [data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
        }}

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 0.75rem !important;
        }}

        /* Scrollable dataframes */
        [data-testid="stDataFrame"] > div {{
            overflow-x: auto !important;
        }}

        /* Graphviz chart - make scrollable */
        [data-testid="stGraphvizChart"] {{
            overflow-x: auto !important;
            max-width: 100% !important;
        }}

        [data-testid="stGraphvizChart"] svg {{
            min-width: 500px !important;
            height: auto !important;
        }}

        /* Smaller text in containers */
        .stMarkdown p, .stMarkdown li {{
            font-size: 0.85rem !important;
        }}

        /* Plotly charts - responsive */
        [data-testid="stPlotlyChart"] {{
            overflow-x: auto !important;
        }}

        /* Radio buttons - wrap on mobile */
        [data-testid="stRadio"] > div {{
            flex-wrap: wrap !important;
            gap: 0.25rem !important;
        }}

        /* Tabs - smaller on mobile */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0 !important;
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 0.5rem 0.75rem !important;
            font-size: 0.85rem !important;
        }}
    }}

    /* Mobile Responsive - Small Phone */
    @media (max-width: 480px) {{
        /* Force all text dark */
        p, span, li, div, label, strong, b {{
            color: #1A202C !important;
        }}

        .kpi-container, .kpi-6-cols {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 0.5rem !important;
        }}

        .kpi-card {{
            display: flex !important;
            align-items: center !important;
            gap: 1rem !important;
            padding: 0.75rem 1rem !important;
            background: #FFFFFF !important;
        }}

        .kpi-icon {{
            margin-bottom: 0 !important;
        }}

        .kpi-value {{
            font-size: 1.3rem !important;
            color: #1A202C !important;
        }}

        .kpi-label {{
            color: #2D3748 !important;
        }}

        /* Header banner - keep white */
        .header-banner, .header-banner h1, .header-banner p, .header-banner * {{
            color: white !important;
        }}

        .header-banner h1 {{
            font-size: 1rem !important;
        }}

        .header-banner p {{
            font-size: 0.7rem !important;
            line-height: 1.3 !important;
        }}

        h4, .stMarkdown h4 {{
            font-size: 0.9rem !important;
            color: {CORESTACK_BLUE} !important;
        }}

        h3, .stMarkdown h3 {{
            font-size: 1rem !important;
            color: {CORESTACK_BLUE} !important;
        }}

        /* Smaller text overall */
        .stMarkdown p, .stMarkdown li {{
            font-size: 0.8rem !important;
            color: #1A202C !important;
        }}

        /* Dataframe smaller on very small screens */
        [data-testid="stDataFrame"] {{
            font-size: 0.7rem !important;
            color: #1A202C !important;
        }}

        /* Container borders - less padding */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 0.5rem !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            background-color: #FFFFFF !important;
            color: #1A202C !important;
        }}

        /* Material icons smaller */
        .material-symbols-outlined {{
            font-size: 20px !important;
        }}

        /* Graphviz even more compact */
        [data-testid="stGraphvizChart"] svg {{
            min-width: 400px !important;
        }}
    }}

    /* Bordered containers */
    .bordered-box {{
        border: 2px solid {CORESTACK_BLUE};
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
        border: 2px solid {CORESTACK_BLUE};
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
        border-bottom: 1px solid {CORESTACK_BLUE}40;
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
        background: linear-gradient(135deg, {CORESTACK_BLUE} 0%, {CORESTACK_DARK_BLUE} 100%) !important;
        color: white !important;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 118, 225, 0.3);
    }}
    .header-banner h1 {{
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: white !important;
    }}
    .header-banner p {{
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
        color: white !important;
    }}

    /* KPI Cards */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}

    /* 6-column KPI layout for dashboard */
    .kpi-6-cols {{
        grid-template-columns: repeat(6, 1fr);
    }}
    .kpi-card {{
        background: {CORESTACK_CARD_BG} !important;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 2px solid {CORESTACK_BLUE};
        transition: transform 0.2s, box-shadow 0.2s;
        color: {CORESTACK_TEXT_DARK} !important;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        border-color: {CORESTACK_DARK_BLUE};
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
    .kpi-icon.blue {{ background: rgba(0, 102, 204, 0.2) !important; color: {CORESTACK_BLUE} !important; }}
    .kpi-icon.green {{ background: rgba(39, 103, 73, 0.2) !important; color: {CORESTACK_SUCCESS} !important; }}
    .kpi-icon.red {{ background: rgba(197, 48, 48, 0.2) !important; color: {CORESTACK_DANGER} !important; }}
    .kpi-icon.orange {{ background: rgba(192, 86, 33, 0.2) !important; color: {CORESTACK_WARNING} !important; }}
    .kpi-value {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {CORESTACK_TEXT_DARK} !important;
        line-height: 1;
        margin-bottom: 0.25rem;
    }}
    .kpi-label {{
        font-size: 0.9rem;
        color: {CORESTACK_TEXT_MID} !important;
        font-weight: 600;
    }}
    .kpi-trend {{
        font-size: 0.8rem;
        margin-top: 0.5rem;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }}
    .kpi-trend.up {{ background: rgba(39, 103, 73, 0.2) !important; color: {CORESTACK_SUCCESS} !important; }}
    .kpi-trend.down {{ background: rgba(197, 48, 48, 0.2) !important; color: {CORESTACK_DANGER} !important; }}

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
        border: 2px solid {CORESTACK_BLUE};
    }}
    .data-table thead {{
        background: linear-gradient(180deg, #F8FAFC 0%, #EDF2F7 100%);
    }}
    .data-table th {{
        padding: 1rem;
        text-align: left;
        font-weight: 700;
        color: {CORESTACK_BLUE};
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid {CORESTACK_BLUE};
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
        border-bottom: 2px solid {CORESTACK_BLUE};
    }}
    .section-header h3 {{
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: {CORESTACK_BLUE};
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


def db_get_filtered_summary(source=None, status=None, severity=None):
    """Get summary statistics with optional filters."""
    conn = get_db()
    cursor = conn.cursor()

    # Build WHERE clause
    where_clauses = ["(f.policy_id, f.run_id) IN (SELECT policy_id, MAX(run_id) FROM findings GROUP BY policy_id)"]
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

    # Total policies (filtered)
    cursor.execute(f"""
        SELECT COUNT(DISTINCT f.policy_id) FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE {where_sql}
    """, params)
    total = cursor.fetchone()[0]

    # Passing/Failing counts (filtered)
    cursor.execute(f"""
        SELECT f.status, COUNT(*) FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE {where_sql}
        GROUP BY f.status
    """, params)
    status_counts = dict(cursor.fetchall())
    passing = status_counts.get("PASS", 0)
    failing = status_counts.get("FAIL", 0)

    # Last evaluated (filtered)
    cursor.execute(f"""
        SELECT MAX(f.last_evaluated) FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE {where_sql}
    """, params)
    last_eval = cursor.fetchone()[0]

    # By source breakdown (filtered)
    cursor.execute(f"""
        SELECT p.source, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE {where_sql}
        GROUP BY p.source, f.status
    """, params)
    by_source = {}
    for src, stat, count in cursor.fetchall():
        if src not in by_source:
            by_source[src] = {}
        by_source[src][stat] = count

    # By severity breakdown (filtered)
    cursor.execute(f"""
        SELECT p.severity, f.status, COUNT(*)
        FROM findings f
        JOIN policies p ON f.policy_id = p.policy_id
        WHERE {where_sql}
        GROUP BY p.severity, f.status
    """, params)
    by_severity = {}
    for sev, stat, count in cursor.fetchall():
        if sev not in by_severity:
            by_severity[sev] = {}
        by_severity[sev][stat] = count

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


# ── Hide Sidebar ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header Banner ────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-banner" style="color: white !important;">
    <h1 style="color: white !important;">◈ CoreStack – Unified Policy Compliance</h1>
    <p style="color: white !important;">Real-time cloud governance across multiple policy engines • Cloud Custodian + CoreStack Native</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_executive, tab_dashboard = st.tabs(["Executive Summary", "Dashboard"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

with tab_dashboard:
    # ── Clickable Filters ─────────────────────────────────────────────────────

    st.markdown("**Select Filters:**")

    filter_cols = st.columns(3)

    with filter_cols[0]:
        with st.container(border=True):
            source_filter = st.radio(
                "Source",
                ["All", "Cloud Custodian", "CoreStack"],
                horizontal=True,
                key="source_radio"
            )
        # Convert display value to db value
        source_param = None
        if source_filter == "Cloud Custodian":
            source_param = "cloudcustodian"
        elif source_filter == "CoreStack":
            source_param = "corestack"

    with filter_cols[1]:
        with st.container(border=True):
            status_filter = st.radio(
                "Status",
                ["All", "PASS", "FAIL"],
                horizontal=True,
                key="status_radio"
            )
        status_param = None if status_filter == "All" else status_filter

    with filter_cols[2]:
        with st.container(border=True):
            severity_filter = st.radio(
                "Severity",
                ["All", "High", "Medium", "Low"],
                horizontal=True,
                key="severity_radio"
            )
        severity_param = None if severity_filter == "All" else severity_filter.lower()

    # ── Get Filtered Data ─────────────────────────────────────────────────────

    summary = db_get_filtered_summary(source=source_param, status=status_param, severity=severity_param)

    compliance_rate = round((summary['passing'] / max(summary['total_policies'], 1)) * 100)

    # Calculate source counts
    custodian_data = summary.get('by_source', {}).get('cloudcustodian', {})
    custodian_count = custodian_data.get('PASS', 0) + custodian_data.get('FAIL', 0)

    corestack_data = summary.get('by_source', {}).get('corestack', {})
    corestack_count = corestack_data.get('PASS', 0) + corestack_data.get('FAIL', 0)

    st.markdown(f"""
    <div class="kpi-container kpi-6-cols">
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined">policy</span></div>
            <div class="kpi-value">{summary['total_policies']}</div>
            <div class="kpi-label">Total Policies</div>
            <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">visibility</span> Unified View</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined">cloud</span></div>
            <div class="kpi-value" style="color:#1565C0;">{custodian_count}</div>
            <div class="kpi-label">Cloud Custodian</div>
            <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">security</span> Open Source</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon blue"><span class="material-symbols-outlined">domain</span></div>
            <div class="kpi-value" style="color:{CORESTACK_BLUE};">{corestack_count}</div>
            <div class="kpi-label">CoreStack Native</div>
            <div class="kpi-trend up"><span class="material-symbols-outlined" style="font-size:14px;">verified</span> Enterprise</div>
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

    # ── Breakdown Section ────────────────────────────────────────────────────

    st.markdown(f'<h4 style="color: {CORESTACK_DARK_BLUE}; margin-bottom: 0.5rem;">Compliance Breakdown</h4>', unsafe_allow_html=True)

    # Side by side bar charts
    col_source, col_severity = st.columns(2)

    # By Policy Source (Left) - Bar Chart
    with col_source:
        with st.container(border=True):
            st.markdown(f'<p style="color: {CORESTACK_BLUE}; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">By Policy Source</p>', unsafe_allow_html=True)

            source_labels = []
            source_pass = []
            source_fail = []

            for src, counts in summary.get("by_source", {}).items():
                label = "Cloud Custodian" if src == "cloudcustodian" else "CoreStack"
                source_labels.append(label)
                source_pass.append(counts.get("PASS", 0))
                source_fail.append(counts.get("FAIL", 0))

            if source_labels:
                fig_source = go.Figure()
                fig_source.add_trace(go.Bar(
                    name='Pass',
                    x=source_labels,
                    y=source_pass,
                    marker_color='#4DA6FF',  # Light CoreStack blue
                    text=source_pass,
                    textposition='auto',
                    textfont=dict(color='white', size=14, family='Nunito Sans')
                ))
                fig_source.add_trace(go.Bar(
                    name='Fail',
                    x=source_labels,
                    y=source_fail,
                    marker_color='#FF8C66',  # Light coral/orange
                    text=source_fail,
                    textposition='auto',
                    textfont=dict(color='white', size=14, family='Nunito Sans')
                ))
                fig_source.update_layout(
                    barmode='group',
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Nunito Sans", size=12),
                    xaxis=dict(title=""),
                    yaxis=dict(title="Policies", gridcolor='#E2E8F0')
                )
                st.plotly_chart(fig_source, use_container_width=True)
            else:
                st.caption("No data available")

    # By Severity Level (Right) - Bar Chart
    with col_severity:
        with st.container(border=True):
            st.markdown(f'<p style="color: {CORESTACK_BLUE}; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">By Severity Level</p>', unsafe_allow_html=True)

            severity_labels = []
            severity_pass = []
            severity_fail = []

            for sev in ["high", "medium", "low"]:
                counts = summary.get("by_severity", {}).get(sev, {})
                pass_count = counts.get("PASS", 0)
                fail_count = counts.get("FAIL", 0)
                if pass_count > 0 or fail_count > 0:
                    severity_labels.append(sev.upper())
                    severity_pass.append(pass_count)
                    severity_fail.append(fail_count)

            if severity_labels:
                fig_severity = go.Figure()
                fig_severity.add_trace(go.Bar(
                    name='Pass',
                    x=severity_labels,
                    y=severity_pass,
                    marker_color='#4DA6FF',  # Light CoreStack blue
                    text=severity_pass,
                    textposition='auto',
                    textfont=dict(color='white', size=14, family='Nunito Sans')
                ))
                fig_severity.add_trace(go.Bar(
                    name='Fail',
                    x=severity_labels,
                    y=severity_fail,
                    marker_color='#FF8C66',  # Light coral/orange
                    text=severity_fail,
                    textposition='auto',
                    textfont=dict(color='white', size=14, family='Nunito Sans')
                ))
                fig_severity.update_layout(
                    barmode='group',
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Nunito Sans", size=12),
                    xaxis=dict(title=""),
                    yaxis=dict(title="Policies", gridcolor='#E2E8F0')
                )
                st.plotly_chart(fig_severity, use_container_width=True)
            else:
                st.caption("No data available")

    st.markdown(f'<h4 style="color: {CORESTACK_DARK_BLUE}; margin-top: 1.5rem; margin-bottom: 0.5rem;">Policy Compliance Findings</h4>', unsafe_allow_html=True)
    findings = db_get_findings(source=source_param, status=status_param, severity=severity_param)

    if not findings:
        st.info("No findings match the current filters. Try adjusting your filter criteria.")
    else:
        # Build dataframe with display values
        table_data = []
        for f in findings:
            source_label = "Cloud Custodian" if f['source'] == "cloudcustodian" else "CoreStack"
            table_data.append({
                "Policy": f['policy_name'],
                "Source": source_label,
                "Status": f['status'],
                "Violations": int(f['violations_count']),
                "Severity": f['severity'].upper(),
                "Category": f['category'],
                "Resource": f['resource_types']
            })

        df = pd.DataFrame(table_data)

        # Style function for the dataframe
        def color_status(val):
            if val == "PASS":
                return 'color: #38A169; font-weight: bold'
            elif val == "FAIL":
                return 'color: #E53E3E; font-weight: bold'
            return ''

        def color_violations(val):
            if val > 0:
                return 'color: #E53E3E; font-weight: bold'
            return 'color: #38A169; font-weight: bold'

        def color_severity(val):
            if val == "HIGH":
                return 'color: #E53E3E; font-weight: bold'
            elif val == "MEDIUM":
                return 'color: #DD6B20; font-weight: bold'
            elif val == "LOW":
                return 'color: #3182CE; font-weight: bold'
            return ''

        # Apply styling
        styled_df = df.style\
            .applymap(color_status, subset=['Status'])\
            .applymap(color_violations, subset=['Violations'])\
            .applymap(color_severity, subset=['Severity'])\
            .set_properties(**{'border': '1px solid #0066cc', 'padding': '10px'})\
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#0066cc'), ('color', 'white'), ('font-weight', 'bold'), ('padding', '12px'), ('border', '1px solid #003d7a')]},
                {'selector': 'td', 'props': [('border', '1px solid #0066cc40')]},
            ])

        with st.container(border=True):
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )

    # ── Drill-down Section ─────────────────────────────────────────────────────

    st.markdown(f'<h4 style="color: {CORESTACK_DARK_BLUE}; margin-top: 1.5rem; margin-bottom: 0.5rem;">Policy Deep Dive & Evidence</h4>', unsafe_allow_html=True)

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
                st.markdown("**Violating Resources**")
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
                st.success("No violations found — this policy is compliant!")

        with col2:
            # Quick stats for selected policy
            selected_finding = next((f for f in findings if f["policy_id"] == selected_id), None)
            if selected_finding:
                with st.container(border=True):
                    st.markdown("**Quick Stats**")

                    # Violations with color
                    viol_count = selected_finding["violations_count"]
                    if viol_count > 0:
                        st.error(f"Violations: {viol_count}")
                    else:
                        st.success(f"Violations: {viol_count}")

                    # Severity with color
                    sev = selected_finding["severity"].upper()
                    if sev == "HIGH":
                        st.error(f"Severity: {sev}")
                    elif sev == "MEDIUM":
                        st.warning(f"Severity: {sev}")
                    else:
                        st.info(f"Severity: {sev}")

                    # Status with color
                    status = selected_finding["status"]
                    if status == "PASS":
                        st.success(f"Status: {status}")
                    else:
                        st.error(f"Status: {status}")

                    st.caption(f"Category: {selected_finding['category'].title()}")

        # Evidence
        evidence_list = db_get_evidence(selected_id)
        if evidence_list:
            with st.expander("Raw Evidence JSON (Click to expand)", expanded=False):
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
        st.info("Select filters above to view findings, then choose a policy to drill down.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

with tab_executive:
    # ── Executive Summary Header ─────────────────────────────────────────────
    st.markdown(f'<h3 style="color: {CORESTACK_DARK_BLUE};">Executive Summary</h3>', unsafe_allow_html=True)

    st.markdown("""
    This POC demonstrates **CoreStack's unified cloud governance platform** that aggregates compliance findings
    from multiple policy engines into a single dashboard. The solution ingests real Cloud Custodian scan results
    from live AWS resources and presents them alongside CoreStack-native policies.
    """)

    # ── Business Challenge ────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;"><span class="material-symbols-outlined" style="vertical-align: middle;">warning</span> Business Challenge</h4>', unsafe_allow_html=True)

    with st.container(border=True):
        challenge_cols = st.columns([1, 1])

        with challenge_cols[0]:
            st.markdown("""
            **The Problem**

            Organizations today face significant challenges in cloud governance:

            - **Tool Fragmentation**: Multiple security tools generate siloed reports
            - **Visibility Gaps**: No unified view across policy engines
            - **Manual Correlation**: Teams spend hours consolidating findings
            - **Compliance Fatigue**: Difficult to track overall security posture
            - **Delayed Response**: Slow detection of policy violations
            """)

        with challenge_cols[1]:
            st.markdown("""
            **The Impact**

            Without unified governance, organizations experience:

            - Increased security risk from missed violations
            - Higher operational costs from manual processes
            - Audit failures due to incomplete evidence
            - Slower time-to-remediation for issues
            - Difficulty demonstrating compliance to stakeholders
            """)

    # ── Solution Overview ─────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;"><span class="material-symbols-outlined" style="vertical-align: middle;">lightbulb</span> Solution Overview</h4>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""
        **CoreStack Unified Governance** solves these challenges by providing:

        - **Single Pane of Glass**: Aggregate findings from Cloud Custodian, AWS Config, Azure Policy, and more
        - **Normalized Data Model**: Consistent schema across all policy engines
        - **Real-Time Visibility**: Continuous compliance monitoring and alerting
        - **Evidence Collection**: Automated capture of violation details for audits
        - **Flexible Output**: API, embeddable links, and interactive dashboards
        """)

    # ── Key Benefits ──────────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;"><span class="material-symbols-outlined" style="vertical-align: middle;">verified</span> Key Benefits</h4>', unsafe_allow_html=True)

    benefit_cols = st.columns(4)

    with benefit_cols[0]:
        with st.container(border=True):
            st.markdown(f'<div style="text-align: center;"><span class="material-symbols-outlined" style="font-size: 48px; color: {CORESTACK_SUCCESS};">speed</span></div>', unsafe_allow_html=True)
            st.markdown("**80% Faster**")
            st.caption("Reduce time spent on compliance reporting")

    with benefit_cols[1]:
        with st.container(border=True):
            st.markdown(f'<div style="text-align: center;"><span class="material-symbols-outlined" style="font-size: 48px; color: {CORESTACK_BLUE};">visibility</span></div>', unsafe_allow_html=True)
            st.markdown("**100% Visibility**")
            st.caption("Complete view across all policy engines")

    with benefit_cols[2]:
        with st.container(border=True):
            st.markdown(f'<div style="text-align: center;"><span class="material-symbols-outlined" style="font-size: 48px; color: {CORESTACK_DARK_BLUE};">security</span></div>', unsafe_allow_html=True)
            st.markdown("**Reduced Risk**")
            st.caption("Catch violations before they become incidents")

    with benefit_cols[3]:
        with st.container(border=True):
            st.markdown(f'<div style="text-align: center;"><span class="material-symbols-outlined" style="font-size: 48px; color: {CORESTACK_SUCCESS};">savings</span></div>', unsafe_allow_html=True)
            st.markdown("**Cost Savings**")
            st.caption("Eliminate manual consolidation work")

    # ── Use Cases ─────────────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;"><span class="material-symbols-outlined" style="vertical-align: middle;">cases</span> Use Cases</h4>', unsafe_allow_html=True)

    with st.container(border=True):
        usecase_cols = st.columns(3)

        with usecase_cols[0]:
            st.markdown(f'<span class="material-symbols-outlined" style="color: {CORESTACK_BLUE};">gavel</span> **Compliance Audits**', unsafe_allow_html=True)
            st.markdown("""
            - Generate audit-ready reports
            - Provide evidence for SOC2, HIPAA, PCI-DSS
            - Track compliance trends over time
            """)

        with usecase_cols[1]:
            st.markdown(f'<span class="material-symbols-outlined" style="color: {CORESTACK_BLUE};">shield</span> **Security Operations**', unsafe_allow_html=True)
            st.markdown("""
            - Monitor security posture in real-time
            - Prioritize remediation by severity
            - Integrate with SIEM/SOAR platforms
            """)

        with usecase_cols[2]:
            st.markdown(f'<span class="material-symbols-outlined" style="color: {CORESTACK_BLUE};">account_tree</span> **DevSecOps**', unsafe_allow_html=True)
            st.markdown("""
            - Shift-left security in CI/CD
            - Automate policy checks in pipelines
            - Provide developer-friendly feedback
            """)

    # ── Supported Integrations ────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;"><span class="material-symbols-outlined" style="vertical-align: middle;">hub</span> Supported Integrations</h4>', unsafe_allow_html=True)

    with st.container(border=True):
        int_cols = st.columns(4)

        with int_cols[0]:
            st.markdown("**Policy Engines**")
            st.markdown("""
            - Cloud Custodian
            - AWS Config Rules
            - Azure Policy
            - GCP Organization Policy
            - Open Policy Agent
            """)

        with int_cols[1]:
            st.markdown("**Cloud Providers**")
            st.markdown("""
            - Amazon Web Services
            - Microsoft Azure
            - Google Cloud Platform
            - Multi-cloud environments
            """)

        with int_cols[2]:
            st.markdown("**Compliance Frameworks**")
            st.markdown("""
            - CIS Benchmarks
            - SOC 2 Type II
            - HIPAA
            - PCI-DSS
            - NIST 800-53
            """)

        with int_cols[3]:
            st.markdown("**Integrations**")
            st.markdown("""
            - Jira / ServiceNow
            - Slack / Teams
            - Splunk / Datadog
            - Terraform / Pulumi
            """)

    # ── Output Options ───────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;">Output Options</h4>', unsafe_allow_html=True)

    output_cols = st.columns(3)

    with output_cols[0]:
        with st.container(border=True):
            st.markdown(f'<h3><span class="material-symbols-outlined" style="color: {CORESTACK_BLUE}; vertical-align: middle;">api</span> API</h3>', unsafe_allow_html=True)
            st.markdown("""
            **RESTful API Access**

            Programmatic access to compliance data for integration with:
            - CI/CD pipelines
            - SIEM systems
            - Custom applications
            - Automation workflows

            **Endpoints:**
            - `GET /summary` - KPIs
            - `GET /findings` - Policy results
            - `GET /policies` - Policy details
            """)

    with output_cols[1]:
        with st.container(border=True):
            st.markdown(f'<h3><span class="material-symbols-outlined" style="color: {CORESTACK_BLUE}; vertical-align: middle;">link</span> Embeddable Link</h3>', unsafe_allow_html=True)
            st.markdown("""
            **Shareable Dashboard URL**

            Embed compliance views directly into:
            - Internal portals
            - Confluence/Wiki pages
            - Executive reports
            - Slack/Teams channels

            **Features:**
            - No login required
            - Real-time updates
            - Mobile responsive
            """)

    with output_cols[2]:
        with st.container(border=True):
            st.markdown(f'<h3><span class="material-symbols-outlined" style="color: {CORESTACK_BLUE}; vertical-align: middle;">dashboard</span> Dashboard</h3>', unsafe_allow_html=True)
            st.markdown("""
            **Interactive Web Interface**

            Full-featured compliance dashboard with:
            - KPI cards & metrics
            - Filterable reports
            - Drill-down analysis
            - Evidence viewer

            **Capabilities:**
            - Multi-source aggregation
            - Severity breakdown
            - Policy deep-dive
            """)

    # ── Data Flow Diagram ────────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;">Data Flow Architecture</h4>', unsafe_allow_html=True)

    with st.container(border=True):
        # Visual dataflow using Graphviz
        st.graphviz_chart('''
            digraph G {
                rankdir=LR;
                bgcolor="transparent";
                node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, margin="0.3,0.2"];
                edge [fontname="Helvetica", fontsize=9, color="#718096"];

                // AWS Resources
                aws [label="AWS Cloud\\nS3 • EC2 • EBS", fillcolor="#FF9900", fontcolor="white"];

                // Cloud Custodian
                custodian [label="Cloud Custodian\\nPolicy Engine", fillcolor="#6C63FF", fontcolor="white"];

                // JSON Outputs
                json [label="JSON Outputs\\nresources.json", fillcolor="#4A5568", fontcolor="white"];

                // Ingestion
                ingest [label="Ingestion Layer\\nNormalize + Store", fillcolor="#0066cc", fontcolor="white"];

                // CoreStack Native
                native [label="CoreStack Native\\nIAM • CloudTrail • Budget", fillcolor="#276749", fontcolor="white"];

                // CoreStack DB
                db [label="CoreStack DB\\nUnified Schema", fillcolor="#003d7a", fontcolor="white"];

                // CoreStack Recommendation Dashboard
                dashboard [label="CoreStack\\nRecommendation Dashboard", fillcolor="#E53E3E", fontcolor="white"];

                // Flow
                aws -> custodian [label="scan"];
                custodian -> json [label="output"];
                json -> ingest [label="read"];
                native -> ingest [label="seed"];
                ingest -> db [label="store"];
                db -> dashboard [label="query"];
            }
        ''')

    # ── Data Flow Steps Table ────────────────────────────────────────────────
    st.markdown(f'<h4 style="color: {CORESTACK_BLUE}; margin-top: 2rem;">Data Flow Steps</h4>', unsafe_allow_html=True)

    flow_data = [
        {"Step": "1", "Component": "AWS Resources", "Description": "S3 buckets, EC2 instances, EBS volumes scanned via AWS APIs"},
        {"Step": "2", "Component": "Cloud Custodian", "Description": "Executes policy YAML files against AWS resources"},
        {"Step": "3", "Component": "JSON Outputs", "Description": "Generates resources.json and metadata.json per policy"},
        {"Step": "4", "Component": "Ingestion Layer", "Description": "Reads Custodian output directories"},
        {"Step": "5", "Component": "Normalizer", "Description": "Converts findings to unified schema (policy_id, status, violations)"},
        {"Step": "6", "Component": "Native Policies", "Description": "Seeds CoreStack-specific policies (IAM MFA, CloudTrail, Budget)"},
        {"Step": "7", "Component": "CoreStack DB", "Description": "Stores policies, findings, resources, and evidence"},
        {"Step": "8", "Component": "CoreStack Recommendation Dashboard", "Description": "Presents unified compliance view to end users"},
    ]

    flow_df = pd.DataFrame(flow_data)
    st.dataframe(flow_df, use_container_width=True, hide_index=True)


# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:{CORESTACK_TEXT_MID}; font-size:0.8rem; padding:1rem 0;">
    <div><strong>◈ CoreStack</strong> – AI-Powered Cloud Governance Platform</div>
    <div style="margin-top:0.25rem;">Unified compliance visibility across Cloud Custodian, AWS Config, Azure Policy, and more</div>
    <div style="margin-top:0.5rem; color:#A0AEC0;">POC Demo • Not for Production Use</div>
</div>
""", unsafe_allow_html=True)
