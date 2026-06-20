"""FORGE-inspired dark theme CSS for Streamlit."""

from src.config import FORGE_COLORS

FORGE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {{
    --bg: {FORGE_COLORS['bg']};
    --surface: {FORGE_COLORS['surface']};
    --border: {FORGE_COLORS['border']};
    --text: {FORGE_COLORS['text']};
    --text-muted: {FORGE_COLORS['text_muted']};
    --accent: {FORGE_COLORS['accent']};
    --green: {FORGE_COLORS['green']};
    --amber: {FORGE_COLORS['amber']};
}}

.stApp {{
    background-color: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}}

#MainMenu, footer, header {{visibility: hidden;}}

.block-container {{
    padding-top: 1rem;
    max-width: 1400px;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] .stMarkdown {{
    color: var(--text);
}}

/* Metric cards */
.forge-metric-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.5rem;
}}
.forge-metric-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}}
.forge-metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.2;
}}
.forge-metric-sub {{
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}}

/* Header */
.forge-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}}
.forge-logo {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: 0.15em;
}}
.forge-live {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--accent);
    margin-left: 1rem;
}}
.forge-live-dot {{
    width: 6px;
    height: 6px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}

/* Section labels */
.forge-section-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.25rem;
}}
.forge-section-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 1rem;
}}

/* Alert cards */
.forge-alert {{
    background: var(--surface);
    border-left: 3px solid var(--accent);
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 4px 4px 0;
}}
.forge-alert-critical {{ border-left-color: {FORGE_COLORS['red']}; }}
.forge-alert-warning {{ border-left-color: var(--amber); }}
.forge-alert-info {{ border-left-color: var(--text-muted); }}
.forge-alert-severity {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.forge-alert-critical .forge-alert-severity {{ color: {FORGE_COLORS['red']}; }}
.forge-alert-warning .forge-alert-severity {{ color: var(--amber); }}
.forge-alert-message {{
    font-size: 0.85rem;
    color: var(--text);
    margin-top: 0.15rem;
}}

/* P&L table */
.forge-pl-row {{
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.85rem;
}}
.forge-pl-row.section {{
    font-weight: 600;
    color: var(--accent);
    padding-top: 1rem;
    border-bottom: none;
}}
.forge-pl-row.total {{
    font-weight: 700;
    border-top: 2px solid var(--border);
    padding-top: 0.75rem;
}}

/* Status badges */
.forge-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    padding: 0.15rem 0.5rem;
    border-radius: 2px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.forge-badge-green {{ background: rgba(34,197,94,0.15); color: var(--green); }}
.forge-badge-orange {{ background: rgba(255,87,34,0.15); color: var(--accent); }}
.forge-badge-amber {{ background: rgba(245,158,11,0.15); color: var(--amber); }}

/* Buttons */
.stButton > button {{
    background-color: var(--accent) !important;
    color: white !important;
    border: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    border-radius: 2px !important;
}}
.stButton > button:hover {{
    background-color: {FORGE_COLORS['accent_dim']} !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    background: transparent;
    border-radius: 2px;
}}
.stTabs [aria-selected="true"] {{
    background: var(--accent) !important;
    color: white !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    border: 1px dashed var(--border);
    border-radius: 4px;
    padding: 0.5rem;
}}

/* Hide streamlit branding elements */
.stDeployButton {{display: none;}}
</style>
"""


def inject_forge_theme():
    """Return CSS string for injection into Streamlit."""
    return FORGE_CSS
