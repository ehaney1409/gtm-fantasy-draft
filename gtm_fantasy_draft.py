import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import base64
from pathlib import Path

# Page config
st.set_page_config(page_title="Kittil.io - GTM Fantasy Draft", layout="wide", page_icon="🐱")

# Custom CSS for modern light theme
st.markdown("""
<style>
    /* Base App Styling */
    .stApp { 
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    }
    .main { 
        background-color: transparent;
    }
    
    /* Header Logo Styling */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
        padding: 16px 0;
    }
    
    .logo-container img {
        height: 48px;
        width: auto;
    }
    
    .logo-text {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .logo-subtitle {
        font-size: 16px;
        color: #64748b;
        margin-top: 4px;
    }
    
    /* Card Components */
    .draft-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }
    
    .draft-card:hover {
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.08);
    }
    
    .ai-card {
        background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 2px solid #8b5cf6;
        box-shadow: 0 4px 16px 0 rgba(139, 92, 246, 0.15);
    }
    
    .account-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #8b5cf6;
        transition: all 0.2s ease;
    }
    
    .account-card:hover {
        border-left-color: #7c3aed;
        box-shadow: 0 2px 8px 0 rgba(139, 92, 246, 0.15);
        transform: translateX(4px);
    }
    
    .pick-card {
        background: linear-gradient(135deg, #faf5ff 0%, #ffffff 100%);
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
        border: 1px solid #e9d5ff;
        border-left: 3px solid #a78bfa;
    }
    
    .segment-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #8b5cf6;
    }
    
    /* Typography */
    h1, h2, h3, h4 { 
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    h1 { font-size: 32px !important; }
    h2 { font-size: 24px !important; }
    h3 { font-size: 20px !important; margin-top: 8px !important; }
    
    p, span, div, label { 
        color: #475569 !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white !important;
        border-radius: 10px;
        font-weight: 600;
        padding: 12px 24px;
        border: none;
        box-shadow: 0 2px 8px 0 rgba(139, 92, 246, 0.3);
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        box-shadow: 0 4px 12px 0 rgba(139, 92, 246, 0.4);
        transform: translateY(-1px);
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        box-shadow: 0 2px 8px 0 rgba(16, 185, 129, 0.3);
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 4px 12px 0 rgba(16, 185, 129, 0.4);
    }
    
    .stButton button[kind="secondary"] {
        background: #f1f5f9;
        color: #475569 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .stButton button[kind="secondary"]:hover {
        background: #e2e8f0;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: #1e293b !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #8b5cf6 !important;
        font-weight: 700 !important;
        font-size: 28px !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* On Clock Indicator */
    .on-clock {
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 16px 0 rgba(16, 185, 129, 0.15);
    }
    
    .on-clock h3 {
        color: #059669 !important;
    }
    
    /* Score Badges */
    .score-badge {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
        box-shadow: 0 2px 6px 0 rgba(139, 92, 246, 0.3);
    }
    
    .pick-number-badge {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white !important;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 11px;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Data Tables */
    .stDataFrame {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    /* Input Fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        background: #ffffff !important;
        color: #1e293b !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: #ffffff;
        border: 2px dashed #e2e8f0;
        border-radius: 12px;
        padding: 24px;
    }
    
    .stFileUploader:hover {
        border-color: #8b5cf6;
        background: #faf5ff;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        color: #64748b;
        font-weight: 600;
        padding: 12px 20px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #faf5ff;
        border-color: #8b5cf6;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
        color: white !important;
        border-color: #7c3aed !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #faf5ff;
        border-color: #8b5cf6;
    }
    
    /* Success/Warning/Error Messages */
    .stAlert {
        border-radius: 12px;
        border: none;
    }
    
    /* Custom spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 2px solid #e2e8f0;
        margin: 32px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MULTI-DRAFT STATE MANAGEMENT
# =============================================================================

# Initialize multi-draft system
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'territory_planning'  # territory_planning, draft_flow, manage_drafts
if 'all_drafts' not in st.session_state:
    st.session_state.all_drafts = {}
if 'current_draft_id' not in st.session_state:
    st.session_state.current_draft_id = None
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = None

# Legacy single-draft state (for compatibility with existing code)
if 'stage' not in st.session_state:
    st.session_state.stage = 'upload'
if 'accounts_df' not in st.session_state:
    st.session_state.accounts_df = None
if 'ae_list' not in st.session_state:
    st.session_state.ae_list = []
if 'draft_order' not in st.session_state:
    st.session_state.draft_order = []
if 'draft_picks' not in st.session_state:
    st.session_state.draft_picks = []
if 'current_pick' not in st.session_state:
    st.session_state.current_pick = 0
if 'available_accounts' not in st.session_state:
    st.session_state.available_accounts = []
if 'blacklisted_accounts' not in st.session_state:
    st.session_state.blacklisted_accounts = set()
if 'ae_books' not in st.session_state:
    st.session_state.ae_books = {}
if 'ae_keeper_selections' not in st.session_state:
    st.session_state.ae_keeper_selections = {}
if 'accounts_per_ae' not in st.session_state:
    st.session_state.accounts_per_ae = 20
if 'is_snake' not in st.session_state:
    st.session_state.is_snake = True

def sync_to_current_draft():
    """Save current session state to the active draft"""
    if st.session_state.current_draft_id and st.session_state.current_draft_id in st.session_state.all_drafts:
        draft = st.session_state.all_drafts[st.session_state.current_draft_id]
        draft['stage'] = st.session_state.stage
        draft['accounts_df'] = st.session_state.accounts_df
        draft['ae_list'] = st.session_state.ae_list
        draft['draft_order'] = st.session_state.draft_order
        draft['draft_picks'] = st.session_state.draft_picks
        draft['current_pick'] = st.session_state.current_pick
        draft['available_accounts'] = st.session_state.available_accounts
        draft['blacklisted_accounts'] = st.session_state.blacklisted_accounts
        draft['ae_books'] = st.session_state.ae_books
        draft['ae_keeper_selections'] = st.session_state.ae_keeper_selections
        draft['accounts_per_ae'] = st.session_state.accounts_per_ae
        draft['is_snake'] = st.session_state.is_snake

def sync_from_current_draft():
    """Load active draft into session state"""
    if st.session_state.current_draft_id and st.session_state.current_draft_id in st.session_state.all_drafts:
        draft = st.session_state.all_drafts[st.session_state.current_draft_id]
        st.session_state.stage = draft.get('stage', 'upload')
        st.session_state.accounts_df = draft.get('accounts_df')
        st.session_state.ae_list = draft.get('ae_list', [])
        st.session_state.draft_order = draft.get('draft_order', [])
        st.session_state.draft_picks = draft.get('draft_picks', [])
        st.session_state.current_pick = draft.get('current_pick', 0)
        st.session_state.available_accounts = draft.get('available_accounts', [])
        st.session_state.blacklisted_accounts = draft.get('blacklisted_accounts', set())
        st.session_state.ae_books = draft.get('ae_books', {})
        st.session_state.ae_keeper_selections = draft.get('ae_keeper_selections', {})
        st.session_state.accounts_per_ae = draft.get('accounts_per_ae', 20)
        st.session_state.is_snake = draft.get('is_snake', True)

def create_new_draft(segment_name):
    """Create a new draft for a segment"""
    draft_id = f"{segment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.all_drafts[draft_id] = {
        'segment_name': segment_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'stage': 'upload',
        'accounts_df': None,
        'ae_list': [],
        'draft_order': [],
        'draft_picks': [],
        'current_pick': 0,
        'available_accounts': [],
        'blacklisted_accounts': set(),
        'ae_books': {},
        'ae_keeper_selections': {},
        'accounts_per_ae': 20,
        'is_snake': True
    }
    return draft_id

# Sync on every run if we have an active draft
if st.session_state.view_mode == 'draft_flow' and st.session_state.current_draft_id:
    sync_from_current_draft()

# =============================================================================
# HEADER & LOGO
# =============================================================================

# Try to load and display logo
logo_path = "kittil_logo.jpg"
try:
    if Path(logo_path).exists():
        with open(logo_path, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div class='logo-container'>
                <img src='data:image/jpeg;base64,{logo_data}' alt='Kittil.io Logo'>
                <div>
                    <div class='logo-text'>GTM Fantasy Draft</div>
                    <div class='logo-subtitle'>Territory planning reimagined</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='logo-container'>
                <div>
                    <div class='logo-text'>🐱 GTM Fantasy Draft</div>
                    <div class='logo-subtitle'>Territory planning reimagined</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
except:
    st.markdown("""
        <div class='logo-container'>
            <div>
                <div class='logo-text'>🐱 GTM Fantasy Draft</div>
                <div class='logo-subtitle'>Territory planning reimagined</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# NAVIGATION
# =============================================================================

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button("🗺️ Territory Planning", use_container_width=True, 
                 type="primary" if st.session_state.view_mode == 'territory_planning' else "secondary"):
        sync_to_current_draft()
        st.session_state.view_mode = 'territory_planning'
        st.rerun()

with nav_col2:
    draft_count = len(st.session_state.all_drafts)
    current_segment = ""
    if st.session_state.current_draft_id and st.session_state.current_draft_id in st.session_state.all_drafts:
        current_segment = f" - {st.session_state.all_drafts[st.session_state.current_draft_id]['segment_name']}"
    
    if st.button(f"🎯 Active Draft ({draft_count}){current_segment}", use_container_width=True,
                 type="primary" if st.session_state.view_mode == 'draft_flow' else "secondary",
                 disabled=st.session_state.current_draft_id is None):
        sync_to_current_draft()
        st.session_state.view_mode = 'draft_flow'
        sync_from_current_draft()
        st.rerun()

with nav_col3:
    if st.button("📋 Manage Drafts", use_container_width=True,
                 type="primary" if st.session_state.view_mode == 'manage_drafts' else "secondary"):
        sync_to_current_draft()
        st.session_state.view_mode = 'manage_drafts'
        st.rerun()

st.markdown("---")

# =============================================================================
# MANAGE DRAFTS VIEW
# =============================================================================

if st.session_state.view_mode == 'manage_drafts':
    st.header("📋 Manage Drafts")
    
    if not st.session_state.all_drafts:
        st.markdown("""
            <div class='draft-card' style='text-align: center; padding: 60px;'>
                <h3>No drafts yet!</h3>
                <p style='color: #64748b;'>Start by creating segments in Territory Planning</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color: #64748b; margin-bottom: 20px;'>Managing {len(st.session_state.all_drafts)} draft(s)</p>", unsafe_allow_html=True)
        
        for draft_id, draft in st.session_state.all_drafts.items():
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            
            # Header
            col_h1, col_h2, col_h3 = st.columns([3, 2, 1])
            with col_h1:
                st.markdown(f"<h3 style='margin: 0; color: #8b5cf6;'>{draft['segment_name']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #64748b; margin: 4px 0;'>Created: {draft['created_at']}</p>", unsafe_allow_html=True)
            with col_h2:
                stage_emoji = {'upload': '📁', 'ae_config': '⚙️', 'keepers': '🔒', 'draft': '🎯', 'results': '📊'}
                st.markdown(f"<p style='color: #475569;'>Stage: {stage_emoji.get(draft['stage'], '•')} {draft['stage'].replace('_', ' ').title()}</p>", unsafe_allow_html=True)
            with col_h3:
                if st.button("Open", key=f"open_draft_{draft_id}", use_container_width=True):
                    st.session_state.current_draft_id = draft_id
                    st.session_state.view_mode = 'draft_flow'
                    sync_from_current_draft()
                    st.rerun()
            
            # Show draft details if data exists
            if draft['accounts_df'] is not None and draft['ae_list']:
                st.markdown("<hr style='border-color: #e2e8f0; margin: 16px 0;'>", unsafe_allow_html=True)
                
                # Summary metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Total Accounts", len(draft['accounts_df']))
                with col_m2:
                    st.metric("AEs", len(draft['ae_list']))
                with col_m3:
                    picks_made = len(draft.get('draft_picks', []))
                    st.metric("Picks Made", picks_made)
                with col_m4:
                    if draft['stage'] == 'results':
                        st.markdown("<p style='color: #10b981; font-weight: 600; margin-top: 20px;'>✅ Complete</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color: #f59e0b; font-weight: 600; margin-top: 20px;'>⏳ In Progress</p>", unsafe_allow_html=True)
                
                # Show AE books if draft has started
                if draft.get('ae_books') and any(len(book) > 0 for book in draft['ae_books'].values()):
                    st.markdown("<h4 style='margin-top: 16px;'>📚 AE Territory Assignments</h4>", unsafe_allow_html=True)
                    
                    # Create book assignments
                    ae_list_sorted = sorted(draft['ae_list'])
                    
                    for idx, ae in enumerate(ae_list_sorted, 1):
                        book_ids = draft['ae_books'].get(ae, [])
                        if book_ids:
                            # Generate book name
                            book_name = f"{draft['segment_name']}-Book_{idx}"
                            
                            # Get account details
                            ae_accounts = draft['accounts_df'][draft['accounts_df']['Account_ID'].isin(book_ids)]
                            
                            with st.expander(f"📖 {book_name} → **{ae}** ({len(book_ids)} accounts)", expanded=False):
                                if len(ae_accounts) > 0:
                                    col_s1, col_s2, col_s3 = st.columns(3)
                                    with col_s1:
                                        st.metric("Accounts", len(ae_accounts))
                                    with col_s2:
                                        st.metric("Avg Score", f"{ae_accounts['Account_Score'].mean():.1f}")
                                    with col_s3:
                                        st.metric("Total Score", f"{ae_accounts['Account_Score'].sum():.0f}")
                                    
                                    # Show accounts table
                                    display_df = ae_accounts[['Account_Name', 'Account_Score']].sort_values('Account_Score', ascending=False)
                                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                                    
                                    # Download button for this AE's book
                                    csv_data = ae_accounts.to_csv(index=False)
                                    st.download_button(
                                        f"📥 Download {book_name}",
                                        csv_data,
                                        f"{book_name}.csv",
                                        "text/csv",
                                        key=f"download_{draft_id}_{ae}",
                                        use_container_width=True
                                    )
            
            st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TERRITORY PLANNING VIEW
# =============================================================================

elif st.session_state.view_mode == 'territory_planning':
    st.header("🗺️ Territory Planning")
    
    st.markdown("""
        <div class='draft-card'>
            <p style='margin: 0; font-size: 16px;'>
                <strong>Plan your territory structure</strong> by defining segments and the number of AEs needed in each. 
                Each segment can have its own draft.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # AI TERRITORY PLANNER
    st.markdown("<div class='ai-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0; color: #7c3aed;'>🤖 AI Territory Planner</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Upload your accounts file and get AI-powered territory recommendations based on your chosen criteria.</p>", unsafe_allow_html=True)
    
    col_ai1, col_ai2, col_ai3, col_ai4, col_ai5 = st.columns([2, 1, 1, 1, 1])
    
    with col_ai1:
        ai_file = st.file_uploader("Upload accounts CSV for analysis", type=['csv'], key="ai_upload")
    with col_ai2:
        current_aes = st.number_input("Current # of AEs", 1, 1000, 20, key="current_aes")
    with col_ai3:
        target_accounts_per_rep = st.number_input("Target Accounts/Rep", 5, 100, 15, key="accounts_per_rep",
                                                   help="How many accounts should each rep manage?")
    with col_ai4:
        tier_criteria = st.selectbox("Tier By", 
                                      ["Account Score", "Revenue", "Employee Count", "Combined Score"],
                                      key="tier_criteria",
                                      help="How to determine Strategic vs Enterprise tiers")
    with col_ai5:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        analyze_button = st.button("🔮 Analyze", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if ai_file and analyze_button:
        with st.spinner("🤖 Analyzing your accounts..."):
            try:
                # Read the CSV
                df_ai = pd.read_csv(ai_file)
                
                # Create summary stats
                total_accounts = len(df_ai)
                
                # Try to find relevant columns
                cols = df_ai.columns.tolist()
                industry_col = next((c for c in cols if 'industry' in c.lower()), None)
                region_col = next((c for c in cols if any(x in c.lower() for x in ['region', 'state', 'country', 'geo', 'billing'])), None)
                score_col = next((c for c in cols if 'score' in c.lower()), None)
                revenue_col = next((c for c in cols if any(x in c.lower() for x in ['revenue', 'arr', 'value', 'acv'])), None)
                employee_col = next((c for c in cols if any(x in c.lower() for x in ['employee', 'employees', 'emp_count', 'headcount'])), None)
                
                # Determine which column to use for tiering
                tier_col = None
                tier_col_name = ""
                
                if tier_criteria == "Account Score" and score_col:
                    tier_col = score_col
                    tier_col_name = "Account Score"
                    df_ai[tier_col] = pd.to_numeric(df_ai[tier_col], errors='coerce')
                elif tier_criteria == "Revenue" and revenue_col:
                    tier_col = revenue_col
                    tier_col_name = "Revenue"
                    df_ai[tier_col] = pd.to_numeric(df_ai[tier_col], errors='coerce')
                elif tier_criteria == "Employee Count" and employee_col:
                    tier_col = employee_col
                    tier_col_name = "Employee Count"
                    df_ai[tier_col] = pd.to_numeric(df_ai[tier_col], errors='coerce')
                elif tier_criteria == "Combined Score":
                    # Create a combined score
                    df_ai['Combined_Tier_Score'] = 0
                    factors_used = []
                    
                    if score_col:
                        df_ai[score_col] = pd.to_numeric(df_ai[score_col], errors='coerce')
                        df_ai['norm_score'] = (df_ai[score_col] - df_ai[score_col].min()) / (df_ai[score_col].max() - df_ai[score_col].min()) * 100
                        df_ai['Combined_Tier_Score'] += df_ai['norm_score'].fillna(0)
                        factors_used.append("Score")
                    
                    if revenue_col:
                        df_ai[revenue_col] = pd.to_numeric(df_ai[revenue_col], errors='coerce')
                        df_ai['norm_revenue'] = (df_ai[revenue_col] - df_ai[revenue_col].min()) / (df_ai[revenue_col].max() - df_ai[revenue_col].min()) * 100
                        df_ai['Combined_Tier_Score'] += df_ai['norm_revenue'].fillna(0)
                        factors_used.append("Revenue")
                    
                    if employee_col:
                        df_ai[employee_col] = pd.to_numeric(df_ai[employee_col], errors='coerce')
                        df_ai['norm_employees'] = (df_ai[employee_col] - df_ai[employee_col].min()) / (df_ai[employee_col].max() - df_ai[employee_col].min()) * 100
                        df_ai['Combined_Tier_Score'] += df_ai['norm_employees'].fillna(0)
                        factors_used.append("Employees")
                    
                    if factors_used:
                        df_ai['Combined_Tier_Score'] = df_ai['Combined_Tier_Score'] / len(factors_used)
                        tier_col = 'Combined_Tier_Score'
                        tier_col_name = f"Combined ({', '.join(factors_used)})"
                
                # Generate recommendations
                recommendations = []
                
                if tier_col and tier_col in df_ai.columns:
                    # Calculate tiers
                    high_value_count = (df_ai[tier_col] > df_ai[tier_col].quantile(0.75)).sum()
                    mid_value_count = ((df_ai[tier_col] >= df_ai[tier_col].quantile(0.25)) & 
                                     (df_ai[tier_col] <= df_ai[tier_col].quantile(0.75))).sum()
                    
                    threshold_75 = df_ai[tier_col].quantile(0.75)
                    threshold_25 = df_ai[tier_col].quantile(0.25)
                    
                    # Strategic (top tier)
                    strat_accounts_per_rep = max(5, int(target_accounts_per_rep * 0.7))
                    strat_aes = max(2, int(high_value_count / strat_accounts_per_rep))
                    recommendations.append({
                        'name': 'Strategic',
                        'num_aes': strat_aes,
                        'accounts': high_value_count,
                        'accounts_per_rep': strat_accounts_per_rep,
                        'criteria': f'High {tier_col_name} (top 25%, >{threshold_75:.0f})',
                        'rationale': 'Strategic accounts need high-touch approach with smaller book sizes'
                    })
                    
                    # Enterprise (mid tier)
                    ent_accounts_per_rep = max(10, int(target_accounts_per_rep * 1.3))
                    ent_aes = max(3, int(mid_value_count / ent_accounts_per_rep))
                    recommendations.append({
                        'name': 'Enterprise',
                        'num_aes': ent_aes,
                        'accounts': mid_value_count,
                        'accounts_per_rep': ent_accounts_per_rep,
                        'criteria': f'Mid {tier_col_name} (25th-75th percentile, {threshold_25:.0f}-{threshold_75:.0f})',
                        'rationale': 'Enterprise accounts with scaled sales approach and larger territories'
                    })
                    
                    # Store for later
                    st.session_state.ai_tier_col = tier_col
                    st.session_state.ai_tier_col_name = tier_col_name
                else:
                    st.error(f"❌ Could not find {tier_criteria} column in your data.")
                    st.stop()
                
                # Regional splits if available
                if region_col and len(recommendations) > 0:
                    def get_high_level_region(location):
                        location = str(location).upper()
                        if any(x in location for x in ['US', 'USA', 'UNITED STATES', 'CANADA', 'CA', 'MEXICO', 'MX', 
                                                        'NY', 'TX', 'FL', 'IL', 'NORTH AMERICA']):
                            return 'NAMER'
                        elif any(x in location for x in ['UK', 'GB', 'GERMANY', 'DE', 'FRANCE', 'FR', 'SPAIN', 'ES', 
                                                          'ITALY', 'IT', 'NETHERLANDS', 'NL', 'EUROPE', 'EMEA', 
                                                          'MIDDLE EAST', 'AFRICA']):
                            return 'EMEA'
                        elif any(x in location for x in ['CHINA', 'CN', 'JAPAN', 'JP', 'INDIA', 'IN', 'AUSTRALIA', 'AU',
                                                          'SINGAPORE', 'SG', 'KOREA', 'KR', 'ASIA', 'APAC', 'PACIFIC']):
                            return 'APAC'
                        elif any(x in location for x in ['BRAZIL', 'BR', 'ARGENTINA', 'AR', 'CHILE', 'CL', 
                                                          'COLOMBIA', 'CO', 'LATIN AMERICA', 'LATAM']):
                            return 'LATAM'
                        return 'Other'
                    
                    df_ai['High_Level_Region'] = df_ai[region_col].apply(get_high_level_region)
                    region_counts = df_ai['High_Level_Region'].value_counts()
                    major_regions = [r for r in region_counts.index if r != 'Other' and region_counts[r] > 50]
                    
                    if major_regions:
                        regional_recs = []
                        for base_seg in recommendations[:]:
                            for region in major_regions:
                                if tier_col and tier_col in df_ai.columns:
                                    if base_seg['name'] == 'Strategic':
                                        region_accounts = df_ai[(df_ai['High_Level_Region'] == region) & 
                                                               (df_ai[tier_col] > df_ai[tier_col].quantile(0.75))]
                                    else:
                                        region_accounts = df_ai[(df_ai['High_Level_Region'] == region) & 
                                                               (df_ai[tier_col] >= df_ai[tier_col].quantile(0.25)) &
                                                               (df_ai[tier_col] <= df_ai[tier_col].quantile(0.75))]
                                else:
                                    region_accounts = df_ai[df_ai['High_Level_Region'] == region]
                                
                                account_count = len(region_accounts)
                                
                                if account_count > 20:
                                    if base_seg['name'] == 'Strategic':
                                        seg_name = f"Strat-{region}"
                                    else:
                                        seg_name = f"Ent-{region}"
                                    
                                    accounts_per_rep_for_seg = base_seg.get('accounts_per_rep', target_accounts_per_rep)
                                    recommended_aes = max(2, int(account_count / accounts_per_rep_for_seg))
                                    
                                    regional_recs.append({
                                        'name': seg_name,
                                        'num_aes': recommended_aes,
                                        'accounts': account_count,
                                        'accounts_per_rep': accounts_per_rep_for_seg,
                                        'criteria': f"{base_seg['name']} in {region}",
                                        'rationale': f"{base_seg['rationale']}, focused on {region} region"
                                    })
                        
                        if regional_recs:
                            recommendations = regional_recs
                
                # Display recommendations
                st.success(f"✅ Analysis complete! Generated {len(recommendations)} territory recommendations")
                
                total_recommended_aes = sum(r['num_aes'] for r in recommendations)
                col_sum1, col_sum2 = st.columns(2)
                with col_sum1:
                    st.metric("Total Accounts Analyzed", total_accounts)
                with col_sum2:
                    st.metric("Recommended Total AEs", total_recommended_aes, 
                             delta=f"{total_recommended_aes - current_aes:+d} vs current")
                
                # Display each recommendation
                for i, rec in enumerate(recommendations):
                    col_rec1, col_rec2 = st.columns([4, 1])
                    with col_rec1:
                        st.markdown(f"""
                            <div class='account-card' style='margin: 12px 0;'>
                                <h4 style='margin: 0; color: #8b5cf6;'>{rec['name']}</h4>
                                <p style='margin: 4px 0;'>
                                    <strong>AEs:</strong> {rec['num_aes']} | 
                                    <strong>Accounts:</strong> {rec.get('accounts', 'N/A')} | 
                                    <strong>Per Rep:</strong> {rec.get('accounts_per_rep', 'N/A')}
                                </p>
                                <p style='margin: 4px 0; color: #64748b; font-size: 13px;'><strong>Criteria:</strong> {rec['criteria']}</p>
                                <p style='margin: 4px 0; color: #475569; font-size: 12px;'>{rec['rationale']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with col_rec2:
                        st.markdown("<div style='padding-top: 20px;'>", unsafe_allow_html=True)
                        if st.button(f"➕ Add", key=f"add_ai_{i}", use_container_width=True):
                            if not any(s['name'] == rec['name'] for s in st.session_state.segments):
                                st.session_state.segments.append({
                                    'name': rec['name'],
                                    'num_aes': rec['num_aes'],
                                    'draft_id': None,
                                    'status': 'Not Started'
                                })
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Add all button
                if st.button("✨ Add All Recommended Segments", type="primary", use_container_width=True):
                    added = 0
                    for rec in recommendations:
                        if not any(s['name'] == rec['name'] for s in st.session_state.segments):
                            st.session_state.segments.append({
                                'name': rec['name'],
                                'num_aes': rec['num_aes'],
                                'draft_id': None,
                                'status': 'Not Started'
                            })
                            added += 1
                    if added > 0:
                        st.rerun()
            
            except Exception as e:
                st.error(f"Error analyzing file: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display segments
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.session_state.segments:
            st.markdown("<h3>📋 Your Segments</h3>", unsafe_allow_html=True)
            
            for idx, seg in enumerate(st.session_state.segments):
                st.markdown(f"""
                    <div class='segment-card'>
                        <h4 style='margin: 0;'>{seg['name']}</h4>
                        <p style='color: #64748b; margin: 4px 0;'>{seg['num_aes']} AEs | Status: {seg['status']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_x, col_y, col_z = st.columns([2, 2, 1])
                
                with col_x:
                    if seg['status'] == 'Not Started':
                        if st.button(f"🚀 Start Draft", key=f"start_{idx}", use_container_width=True):
                            draft_id = create_new_draft(seg['name'])
                            st.session_state.segments[idx]['draft_id'] = draft_id
                            st.session_state.segments[idx]['status'] = 'In Progress'
                            st.session_state.current_draft_id = draft_id
                            st.session_state.view_mode = 'draft_flow'
                            sync_from_current_draft()
                            st.rerun()
                    elif seg['status'] == 'In Progress':
                        if st.button(f"▶️ Continue", key=f"cont_{idx}", use_container_width=True):
                            st.session_state.current_draft_id = seg['draft_id']
                            st.session_state.view_mode = 'draft_flow'
                            sync_from_current_draft()
                            st.rerun()
                    else:
                        if st.button(f"👁️ View", key=f"view_{idx}", use_container_width=True):
                            st.session_state.current_draft_id = seg['draft_id']
                            st.session_state.view_mode = 'draft_flow'
                            sync_from_current_draft()
                            st.rerun()
                
                with col_y:
                    if seg.get('draft_id') and st.button(f"🔄 New Draft", key=f"new_{idx}", use_container_width=True):
                        draft_id = create_new_draft(seg['name'])
                        st.session_state.segments[idx]['draft_id'] = draft_id
                        st.session_state.segments[idx]['status'] = 'In Progress'
                        st.session_state.current_draft_id = draft_id
                        st.session_state.view_mode = 'draft_flow'
                        sync_from_current_draft()
                        st.rerun()
                
                with col_z:
                    if st.button("🗑️", key=f"del_{idx}", help="Delete segment"):
                        st.session_state.segments.pop(idx)
                        st.rerun()
    
    with col2:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>📊 Summary</h3>", unsafe_allow_html=True)
        
        total_segments = len(st.session_state.segments)
        total_aes = sum(s['num_aes'] for s in st.session_state.segments)
        completed = sum(1 for s in st.session_state.segments if s['status'] == 'Completed')
        
        st.metric("Segments", total_segments)
        st.metric("Total AEs", total_aes)
        st.metric("Drafts", len(st.session_state.all_drafts))
        
        if total_segments > 0:
            progress = completed / total_segments if total_segments > 0 else 0
            st.progress(progress)
            st.markdown(f"<p style='text-align: center; color: #64748b;'>{int(progress * 100)}% Complete</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# DRAFT FLOW VIEW
# =============================================================================

elif st.session_state.view_mode == 'draft_flow':
    
    # Sidebar - Draft Information
    with st.sidebar:
        if st.session_state.current_draft_id:
            current_draft = st.session_state.all_drafts.get(st.session_state.current_draft_id, {})
            st.markdown(f"""
                <div class='segment-card'>
                    <h4 style='margin-top: 0; color: #8b5cf6;'>Current Draft</h4>
                    <p style='margin: 4px 0;'><strong>Segment:</strong> {current_draft.get('segment_name', 'N/A')}</p>
                    <p style='margin: 4px 0;'><strong>Created:</strong> {current_draft.get('created_at', 'N/A')}</p>
                    <p style='margin: 4px 0;'><strong>Stage:</strong> {st.session_state.stage.replace('_', ' ').title()}</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📋 Draft Stages")
        
        stages = ['upload', 'ae_config', 'keepers', 'draft', 'results']
        stage_labels = {
            'upload': '1️⃣ Upload Data',
            'ae_config': '2️⃣ Configure AEs',
            'keepers': '3️⃣ Select Keepers',
            'draft': '4️⃣ Live Draft',
            'results': '5️⃣ Results'
        }
        
        current_stage_idx = stages.index(st.session_state.stage) if st.session_state.stage in stages else 0
        
        for idx, stage in enumerate(stages):
            if idx < current_stage_idx:
                st.markdown(f"✅ {stage_labels[stage]}")
            elif idx == current_stage_idx:
                st.markdown(f"**▶️ {stage_labels[stage]}**")
            else:
                st.markdown(f"⚪ {stage_labels[stage]}")
    
    # =============================================================================
    # Stage 1: Upload Accounts
    # =============================================================================
    
    if st.session_state.stage == 'upload':
        st.header("📤 Upload Account Data")
        
        st.markdown("""
            <div class='draft-card'>
                <p style='margin: 0; font-size: 16px;'>
                    Upload a CSV file containing your account data. Required columns: 
                    <strong>Account_ID</strong>, <strong>Account_Name</strong>, and <strong>Account_Score</strong>.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Validate required columns
                required_cols = ['Account_ID', 'Account_Name', 'Account_Score']
                if all(col in df.columns for col in required_cols):
                    st.session_state.accounts_df = df
                    
                    st.success(f"✅ Successfully loaded {len(df)} accounts!")
                    
                    # Preview data
                    st.subheader("📊 Data Preview")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Accounts", len(df))
                    with col2:
                        st.metric("Avg Score", f"{df['Account_Score'].mean():.2f}")
                    with col3:
                        st.metric("Max Score", f"{df['Account_Score'].max():.2f}")
                    
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    if st.button("➡️ Continue to AE Configuration", type="primary", use_container_width=True):
                        st.session_state.stage = 'ae_config'
                        st.rerun()
                else:
                    st.error(f"❌ Missing required columns. Found: {list(df.columns)}")
                    st.info(f"Required columns: {required_cols}")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        
        # Sample data option
        st.markdown("---")
        if st.button("🎲 Use Sample Data", use_container_width=True):
            sample_df = pd.DataFrame({
                'Account_ID': [f'ACC{str(i).zfill(4)}' for i in range(1, 101)],
                'Account_Name': [f'Account {i}' for i in range(1, 101)],
                'Account_Score': np.random.uniform(50, 100, 100).round(2)
            })
            st.session_state.accounts_df = sample_df
            st.rerun()
    
    # =============================================================================
    # Stage 2: AE Configuration
    # =============================================================================
    
    elif st.session_state.stage == 'ae_config':
        st.header("👥 Configure Account Executives")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
                <div class='draft-card'>
                    <h3 style='margin-top: 0;'>Add AEs to the Draft</h3>
                    <p style='margin: 0;'>Enter the names of Account Executives who will participate in this draft.</p>
                </div>
            """, unsafe_allow_html=True)
            
            ae_input = st.text_input("AE Name", placeholder="Enter AE name...")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ Add AE", use_container_width=True):
                    if ae_input and ae_input not in st.session_state.ae_list:
                        st.session_state.ae_list.append(ae_input)
                        st.session_state.ae_books[ae_input] = []
                        st.session_state.ae_keeper_selections[ae_input] = []
                        st.rerun()
                    elif ae_input in st.session_state.ae_list:
                        st.warning("AE already added!")
        
        with col2:
            st.markdown("""
                <div class='draft-card'>
                    <h4 style='margin-top: 0;'>Draft Settings</h4>
                </div>
            """, unsafe_allow_html=True)
            
            st.session_state.is_snake = st.checkbox("🐍 Snake Draft", value=st.session_state.is_snake, 
                help="In snake draft, the order reverses each round")
            
            st.session_state.accounts_per_ae = st.number_input(
                "Accounts per AE",
                min_value=1,
                max_value=50,
                value=st.session_state.accounts_per_ae
            )
        
        # Display current AEs
        if st.session_state.ae_list:
            st.markdown("---")
            st.subheader(f"📋 Current AEs ({len(st.session_state.ae_list)})")
            
            for idx, ae in enumerate(st.session_state.ae_list):
                col_x, col_y = st.columns([4, 1])
                with col_x:
                    st.markdown(f"""
                        <div class='account-card'>
                            <span style='font-weight: 600; color: #1e293b;'>{idx + 1}. {ae}</span>
                        </div>
                    """, unsafe_allow_html=True)
                with col_y:
                    if st.button("🗑️", key=f"remove_ae_{idx}"):
                        st.session_state.ae_list.pop(idx)
                        del st.session_state.ae_books[ae]
                        del st.session_state.ae_keeper_selections[ae]
                        st.rerun()
            
            st.markdown("---")
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Back to Upload", use_container_width=True):
                    st.session_state.stage = 'upload'
                    st.rerun()
            with col_next:
                if len(st.session_state.ae_list) >= 2:
                    if st.button("➡️ Continue to Keepers", type="primary", use_container_width=True):
                        st.session_state.stage = 'keepers'
                        st.rerun()
                else:
                    st.info("Add at least 2 AEs to continue")
        else:
            st.info("👆 Add your first AE to get started!")
    
    # =============================================================================
    # Stage 3: Keeper Selection
    # =============================================================================
    
    elif st.session_state.stage == 'keepers':
        st.header("🔒 Keeper Selection")
        
        st.markdown("""
            <div class='draft-card'>
                <p style='margin: 0; font-size: 16px;'>
                    Each AE can select accounts they want to keep from their existing book.
                    Keepers will be automatically assigned and won't be available in the draft pool.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Randomize draft order button
        if not st.session_state.draft_order:
            if st.button("🎲 Randomize Draft Order", type="primary", use_container_width=True):
                st.session_state.draft_order = st.session_state.ae_list.copy()
                np.random.shuffle(st.session_state.draft_order)
                st.success("Draft order randomized!")
                st.rerun()
        else:
            st.success("✅ Draft order set!")
            st.markdown("**Draft Order:**")
            for idx, ae in enumerate(st.session_state.draft_order):
                st.markdown(f"{idx + 1}. **{ae}**")
        
        st.markdown("---")
        
        # Keeper selection for each AE
        for ae in st.session_state.ae_list:
            with st.expander(f"🔒 {ae}'s Keepers", expanded=False):
                # Search/filter accounts
                search_term = st.text_input(f"Search accounts for {ae}", key=f"search_{ae}")
                
                if search_term:
                    filtered_accounts = st.session_state.accounts_df[
                        st.session_state.accounts_df['Account_Name'].str.contains(search_term, case=False, na=False)
                    ]
                else:
                    filtered_accounts = st.session_state.accounts_df.head(20)
                
                # Multi-select for keepers
                selected_keepers = st.multiselect(
                    f"Select keepers for {ae}",
                    options=filtered_accounts['Account_ID'].tolist(),
                    format_func=lambda x: st.session_state.accounts_df[
                        st.session_state.accounts_df['Account_ID'] == x
                    ]['Account_Name'].iloc[0],
                    key=f"keepers_{ae}",
                    default=st.session_state.ae_keeper_selections.get(ae, [])
                )
                
                st.session_state.ae_keeper_selections[ae] = selected_keepers
                
                if selected_keepers:
                    st.markdown(f"**Selected: {len(selected_keepers)} keepers**")
        
        st.markdown("---")
        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("⬅️ Back to AE Config", use_container_width=True):
                st.session_state.stage = 'ae_config'
                st.rerun()
        with col_next:
            if st.button("➡️ Start Draft", type="primary", use_container_width=True):
                # Process keepers
                for ae, keeper_ids in st.session_state.ae_keeper_selections.items():
                    st.session_state.ae_books[ae].extend(keeper_ids)
                    st.session_state.blacklisted_accounts.update(keeper_ids)
                
                # Initialize available accounts
                st.session_state.available_accounts = st.session_state.accounts_df[
                    ~st.session_state.accounts_df['Account_ID'].isin(st.session_state.blacklisted_accounts)
                ].sort_values('Account_Score', ascending=False).to_dict('records')
                
                st.session_state.stage = 'draft'
                st.session_state.current_pick = 0
                st.rerun()
    
    # =============================================================================
    # Stage 4: Live Draft
    # =============================================================================
    
    elif st.session_state.stage == 'draft':
        st.header("🎯 Live Draft")
        
        # Calculate draft progress
        num_aes = len(st.session_state.draft_order)
        accounts_per_ae = st.session_state.accounts_per_ae
        
        # Account for keepers
        total_keeper_picks = sum(len(keepers) for keepers in st.session_state.ae_keeper_selections.values())
        remaining_picks_needed = (num_aes * accounts_per_ae) - total_keeper_picks
        total_picks = remaining_picks_needed
        
        current_pick = st.session_state.current_pick
        
        # Check if draft is complete
        if current_pick >= total_picks:
            st.session_state.stage = 'results'
            st.rerun()
        
        # Calculate current picker
        current_round = (current_pick // num_aes) + 1
        pick_in_round = (current_pick % num_aes)
        
        if st.session_state.is_snake and current_round % 2 == 0:
            current_ae_index = num_aes - 1 - pick_in_round
        else:
            current_ae_index = pick_in_round
        
        current_ae = st.session_state.draft_order[current_ae_index]
        
        # Progress bar
        progress = current_pick / total_picks if total_picks > 0 else 0
        st.progress(progress)
        st.markdown(f"**Progress:** Pick {current_pick + 1} of {total_picks} ({progress * 100:.1f}%)")
        
        st.markdown("---")
        
        # Two column layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # On the clock
            st.markdown(f"""
                <div class='on-clock'>
                    <h3 style='margin-top: 0;'>⏰ On The Clock</h3>
                    <h2 style='color: #10b981; margin: 8px 0;'>{current_ae}</h2>
                    <p style='margin: 0;'>Round {current_round} | Pick {pick_in_round + 1}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Available accounts
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top: 0;'>🎯 Available Accounts</h3>", unsafe_allow_html=True)
            
            if len(st.session_state.available_accounts) > 0:
                available_df = pd.DataFrame(st.session_state.available_accounts)
                
                # Search filter
                search_query = st.text_input("🔍 Search accounts", placeholder="Type to filter...")
                if search_query:
                    available_df = available_df[
                        available_df['Account_Name'].str.contains(search_query, case=False, na=False)
                    ]
                
                # Draft button
                selected_account = st.selectbox(
                    f"Select account for {current_ae}",
                    options=range(len(available_df)),
                    format_func=lambda x: f"{available_df.iloc[x]['Account_Name']} ({available_df.iloc[x]['Account_Score']:.2f})"
                )
                
                col_draft, col_auto = st.columns(2)
                
                with col_draft:
                    if st.button("✅ Make Pick", type="primary", use_container_width=True):
                        picked_account = available_df.iloc[selected_account]
                        
                        # Record the pick
                        st.session_state.draft_picks.append({
                            'pick_number': current_pick + 1,
                            'round': current_round,
                            'ae': current_ae,
                            'account_name': picked_account['Account_Name'],
                            'account_id': picked_account['Account_ID'],
                            'account_score': picked_account['Account_Score']
                        })
                        
                        # Update AE's book
                        st.session_state.ae_books[current_ae].append(picked_account['Account_ID'])
                        
                        # Remove from available
                        st.session_state.available_accounts = [
                            acc for acc in st.session_state.available_accounts 
                            if acc['Account_ID'] != picked_account['Account_ID']
                        ]
                        
                        st.session_state.current_pick += 1
                        st.rerun()
                
                with col_auto:
                    if st.button("⚡ Auto-Draft Remaining", use_container_width=True):
                        # Auto-draft all remaining picks
                        temp_pick = current_pick
                        temp_available = st.session_state.available_accounts.copy()
                        
                        while temp_pick < total_picks and len(temp_available) > 0:
                            # Calculate who's picking
                            temp_round = (temp_pick // num_aes) + 1
                            temp_pick_in_round = (temp_pick % num_aes)
                            
                            if st.session_state.is_snake and temp_round % 2 == 0:
                                temp_ae_index = num_aes - 1 - temp_pick_in_round
                            else:
                                temp_ae_index = temp_pick_in_round
                            
                            temp_ae = st.session_state.draft_order[temp_ae_index]
                            
                            # Draft best available
                            best_account = temp_available[0]
                            
                            st.session_state.draft_picks.append({
                                'pick_number': temp_pick + 1,
                                'round': temp_round,
                                'ae': temp_ae,
                                'account_name': best_account['Account_Name'],
                                'account_id': best_account['Account_ID'],
                                'account_score': best_account['Account_Score']
                            })
                            
                            st.session_state.ae_books[temp_ae].append(best_account['Account_ID'])
                            temp_available.pop(0)
                            temp_pick += 1
                        
                        st.session_state.available_accounts = temp_available
                        st.session_state.current_pick = temp_pick
                        st.rerun()
                
                # Show available accounts list
                st.markdown("<h4 style='margin: 24px 0 12px 0;'>Top Available</h4>", unsafe_allow_html=True)
                for idx, row in available_df.head(15).iterrows():
                    st.markdown(f"""
                        <div class='account-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <span style='color: #1e293b; font-weight: 600;'>{row['Account_Name']}</span>
                                <span class='score-badge'>{row['Account_Score']:.2f}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No more accounts available!")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            # Recent picks
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top: 0;'>📜 Recent Picks</h3>", unsafe_allow_html=True)
            recent_picks = st.session_state.draft_picks[-8:][::-1]
            
            for pick in recent_picks:
                st.markdown(f"""
                    <div class='pick-card'>
                        <span class='pick-number-badge'>PICK {pick['pick_number']}</span>
                        <p style='margin: 8px 0 4px 0; color: #1e293b; font-weight: 600;'>{pick['ae']}</p>
                        <p style='margin: 4px 0; color: #475569; font-size: 14px;'>{pick['account_name']}</p>
                        <span class='score-badge' style='font-size: 12px; margin-top: 4px;'>{pick['account_score']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Current AE's book
            if current_ae and current_ae in st.session_state.ae_books:
                st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='margin-top: 0;'>{current_ae}'s Book</h3>", unsafe_allow_html=True)
                ae_account_ids = st.session_state.ae_books[current_ae]
                ae_book_df = st.session_state.accounts_df[
                    st.session_state.accounts_df['Account_ID'].isin(ae_account_ids)
                ][['Account_Name', 'Account_Score']]
                
                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("Accounts", len(ae_account_ids))
                with col_y:
                    if len(ae_account_ids) > 0:
                        st.metric("Avg Score", f"{ae_book_df['Account_Score'].mean():.2f}")
                
                if len(ae_book_df) > 0:
                    for _, row in ae_book_df.iterrows():
                        st.markdown(f"""
                            <div style='background: #faf5ff; padding: 10px; border-radius: 8px; margin: 6px 0; border: 1px solid #e9d5ff;'>
                                <div style='display: flex; justify-content: space-between;'>
                                    <span style='color: #475569; font-size: 13px;'>{row['Account_Name']}</span>
                                    <span style='color: #8b5cf6; font-weight: 700; font-size: 13px;'>{row['Account_Score']:.1f}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    
    # =============================================================================
    # Stage 5: Results & Reporting
    # =============================================================================
    
    elif st.session_state.stage == 'results':
        st.header("🏆 Draft Results")
        
        df = st.session_state.accounts_df
        
        # Create results dataframe
        results = []
        for ae in st.session_state.ae_list:
            ae_account_ids = st.session_state.ae_books[ae]
            ae_accounts = df[df['Account_ID'].isin(ae_account_ids)]
            
            results.append({
                'AE': ae,
                'Total Accounts': len(ae_accounts),
                'Avg Account Score': ae_accounts['Account_Score'].mean() if len(ae_accounts) > 0 else 0,
                'Total Score': ae_accounts['Account_Score'].sum() if len(ae_accounts) > 0 else 0,
                'Top Account Score': ae_accounts['Account_Score'].max() if len(ae_accounts) > 0 else 0
            })
        
        results_df = pd.DataFrame(results).sort_values('Avg Account Score', ascending=False)
        
        # Winner announcement
        winner = results_df.iloc[0]
        st.markdown(f"""
            <div class='draft-card' style='background: linear-gradient(135deg, #faf5ff 0%, #ffffff 100%); border: 2px solid #8b5cf6;'>
                <h2 style='margin: 0; color: #8b5cf6;'>🎉 Champion: {winner['AE']}</h2>
                <p style='margin: 8px 0 0 0; font-size: 18px;'>Average Score: <strong>{winner['Avg Account Score']:.2f}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.subheader("📊 Final Standings")
        st.dataframe(results_df, use_container_width=True)
        
        # Individual AE books
        st.markdown("---")
        st.subheader("📚 Account Books by AE")
        
        for ae in st.session_state.ae_list:
            ae_account_ids = st.session_state.ae_books[ae]
            ae_accounts = df[df['Account_ID'].isin(ae_account_ids)].sort_values('Account_Score', ascending=False)
            
            with st.expander(f"📖 {ae} - {len(ae_accounts)} accounts | Avg Score: {ae_accounts['Account_Score'].mean():.2f}", expanded=False):
                st.dataframe(
                    ae_accounts[['Account_Name', 'Account_Score']].reset_index(drop=True),
                    use_container_width=True
                )
        
        # Draft history
        st.markdown("---")
        st.subheader("📜 Complete Draft History")
        if st.session_state.draft_picks:
            draft_history_df = pd.DataFrame(st.session_state.draft_picks)
            st.dataframe(draft_history_df, use_container_width=True)
        
        # Export results
        st.markdown("---")
        st.subheader("💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create export CSV
            export_data = []
            for ae in st.session_state.ae_list:
                ae_account_ids = st.session_state.ae_books[ae]
                ae_accounts = df[df['Account_ID'].isin(ae_account_ids)]
                
                for _, row in ae_accounts.iterrows():
                    export_data.append({
                        'Account_ID': row['Account_ID'],
                        'Account_Name': row['Account_Name'],
                        'New_Owner': ae,
                        'Account_Score': row['Account_Score']
                    })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Assignment CSV",
                data=csv,
                file_name=f"draft_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Download draft history
            if st.session_state.draft_picks:
                draft_csv = pd.DataFrame(st.session_state.draft_picks).to_csv(index=False)
                st.download_button(
                    label="📥 Download Draft History",
                    data=draft_csv,
                    file_name=f"draft_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        if st.button("🔄 Start New Draft", use_container_width=True):
            st.session_state.view_mode = 'territory_planning'
            st.rerun()

# Save draft state before page closes
sync_to_current_draft()
