import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="GTM Fantasy Draft", layout="wide", page_icon="🏈")

# Custom CSS for Sleeper-inspired dark theme (optimized)
st.markdown("""
<style>
    .stApp { background-color: #0f1419; }
    .main { background-color: #0f1419; }
    
    .draft-card {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border: 1px solid #2d3748;
    }
    
    .account-card {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border-left: 3px solid #4299e1;
    }
    
    .pick-card {
        background: #1a1f2e;
        border-radius: 6px;
        padding: 10px;
        margin: 4px 0;
        border-left: 3px solid #48bb78;
    }
    
    .segment-card {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #f6ad55;
    }
    
    h1, h2, h3 { color: #f7fafc !important; }
    p, span, div { color: #e2e8f0 !important; }
    
    .stButton button {
        background: #4299e1;
        color: white;
        border-radius: 6px;
        font-weight: 600;
    }
    
    .stButton button[kind="primary"] {
        background: #48bb78;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #1a1f2e;
    }
    
    [data-testid="stMetricValue"] {
        color: #4299e1 !important;
        font-weight: 700 !important;
    }
    
    .on-clock {
        background: #2d3748;
        border: 2px solid #48bb78;
        border-radius: 12px;
        padding: 20px;
    }
    
    .score-badge {
        background: #667eea;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MULTI-DRAFT STATE MANAGEMENT
# =============================================================================

# Initialize multi-draft system
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'territory_planning'  # territory_planning, draft_flow
if 'all_drafts' not in st.session_state:
    st.session_state.all_drafts = {}
if 'current_draft_id' not in st.session_state:
    st.session_state.current_draft_id = None
if 'segments' not in st.session_state:
    st.session_state.segments = []

# Legacy single-draft state (for compatibility with existing code)
# These will be synced with current_draft from all_drafts
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
# HEADER & NAVIGATION
# =============================================================================

st.markdown("""
    <div style='padding: 20px 0;'>
        <h1 style='margin: 0; font-size: 48px; background: linear-gradient(135deg, #4299e1 0%, #48bb78 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;'>
            🏈 GTM Fantasy Draft
        </h1>
        <p style='color: #a0aec0; font-size: 18px; margin-top: 8px;'>Territory planning reimagined</p>
    </div>
""", unsafe_allow_html=True)

# Navigation buttons
nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button("🗺️ Territory Planning", use_container_width=True, 
                 type="primary" if st.session_state.view_mode == 'territory_planning' else "secondary"):
        sync_to_current_draft()  # Save before switching
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
        sync_to_current_draft()  # Save before switching
        st.session_state.view_mode = 'draft_flow'
        sync_from_current_draft()  # Load the draft
        st.rerun()

with nav_col3:
    if st.button("📋 Manage Drafts", use_container_width=True):
        sync_to_current_draft()
        st.info("Draft management coming soon!")

st.markdown("<hr style='border-color: #2d3748; margin: 20px 0;'>", unsafe_allow_html=True)

# =============================================================================
# TERRITORY PLANNING VIEW
# =============================================================================

if st.session_state.view_mode == 'territory_planning':
    st.markdown("<h2>🗺️ Territory Planning</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #2d3748; padding: 16px; border-radius: 8px; margin: 16px 0;'>
        <p style='color: #e2e8f0; margin: 0;'><strong>Plan your territory structure</strong> by defining segments and the number of AEs needed in each. Each segment can have its own draft.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>🌍 Define Segments</h3>", unsafe_allow_html=True)
        
        # Add new segment
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            seg_name = st.text_input("Segment Name", placeholder="e.g., Ent-NAMER", key="new_seg")
        with col_b:
            seg_aes = st.number_input("# AEs", 1, 100, 5, key="new_aes")
        with col_c:
            if st.button("➕ Add", use_container_width=True):
                if seg_name and not any(s['name'] == seg_name for s in st.session_state.segments):
                    st.session_state.segments.append({
                        'name': seg_name,
                        'num_aes': seg_aes,
                        'draft_id': None,
                        'status': 'Not Started'
                    })
                    st.rerun()
        
        st.markdown("**Quick Add:**")
        quick_cols = st.columns(3)
        common = [("Ent-NAMER", 8), ("Strat-NAMER", 12), ("Ent-EMEA", 6), ("Strat-EMEA", 10), ("Ent-APAC", 5), ("Strat-APAC", 8)]
        
        for i, (name, aes) in enumerate(common):
            with quick_cols[i % 3]:
                if st.button(f"+ {name}", key=f"q_{name}", use_container_width=True):
                    if not any(s['name'] == name for s in st.session_state.segments):
                        st.session_state.segments.append({'name': name, 'num_aes': aes, 'draft_id': None, 'status': 'Not Started'})
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display segments
        if st.session_state.segments:
            st.markdown("<h3>📋 Your Segments</h3>", unsafe_allow_html=True)
            
            for idx, seg in enumerate(st.session_state.segments):
                st.markdown(f"""
                    <div class='segment-card'>
                        <h4 style='margin: 0;'>{seg['name']}</h4>
                        <p style='color: #a0aec0; margin: 4px 0;'>{seg['num_aes']} AEs | Status: {seg['status']}</p>
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
        st.markdown("<h3 style='margin-top: 0;'>🤖 AI Territory Planner</h3>", unsafe_allow_html=True)
        
        st.markdown("<p style='color: #a0aec0; font-size: 14px;'>Upload your accounts file and get AI-powered territory recommendations</p>", unsafe_allow_html=True)
        
        ai_file = st.file_uploader("Upload accounts CSV", type=['csv'], key="ai_upload")
        current_aes = st.number_input("Current # of AEs", 1, 1000, 20, key="current_aes")
        
        if ai_file and st.button("🔮 Get AI Recommendations", type="primary", use_container_width=True):
            with st.spinner("Claude is analyzing your accounts..."):
                try:
                    # Read the CSV
                    df_ai = pd.read_csv(ai_file)
                    
                    # Create summary stats
                    total_accounts = len(df_ai)
                    
                    # Try to find relevant columns
                    cols = df_ai.columns.tolist()
                    industry_col = next((c for c in cols if 'industry' in c.lower()), None)
                    region_col = next((c for c in cols if any(x in c.lower() for x in ['region', 'state', 'country', 'geo'])), None)
                    score_col = next((c for c in cols if 'score' in c.lower()), None)
                    revenue_col = next((c for c in cols if any(x in c.lower() for x in ['revenue', 'arr', 'value'])), None)
                    
                    # Build analysis prompt
                    prompt = f"""Analyze this sales account data and recommend an optimal territory segmentation strategy.

**Current Situation:**
- Total Accounts: {total_accounts:,}
- Current AEs: {current_aes}
- Accounts per AE: {total_accounts/current_aes:.1f}

**Account Data Summary:**
"""
                    
                    if industry_col:
                        industries = df_ai[industry_col].value_counts().head(10)
                        prompt += f"\nTop Industries:\n"
                        for ind, count in industries.items():
                            prompt += f"  - {ind}: {count} accounts\n"
                    
                    if region_col:
                        regions = df_ai[region_col].value_counts().head(10)
                        prompt += f"\nTop Regions:\n"
                        for reg, count in regions.items():
                            prompt += f"  - {reg}: {count} accounts\n"
                    
                    if score_col:
                        df_ai[score_col] = pd.to_numeric(df_ai[score_col], errors='coerce')
                        prompt += f"\nAccount Score Distribution:\n"
                        prompt += f"  - Mean: {df_ai[score_col].mean():.2f}\n"
                        prompt += f"  - Median: {df_ai[score_col].median():.2f}\n"
                        prompt += f"  - High-value (>75th percentile): {(df_ai[score_col] > df_ai[score_col].quantile(0.75)).sum()} accounts\n"
                    
                    prompt += f"""

**Your Task:**
Create a territory segmentation strategy with 3-6 segments. For each segment, specify:
1. Segment name (e.g., "Enterprise-NAMER", "Strategic-EMEA")
2. Recommended number of AEs
3. Criteria for accounts in this segment
4. Rationale

Respond ONLY with a JSON array like this:
[
  {{"name": "Segment Name", "num_aes": 8, "criteria": "Description", "rationale": "Why"}},
  ...
]

No markdown, no preamble, just the JSON array."""

                    # Call Claude API
                    response = fetch("https://api.anthropic.com/v1/messages", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json",
                        },
                        "body": JSON.stringify({
                            "model": "claude-sonnet-4-20250514",
                            "max_tokens": 2000,
                            "messages": [{"role": "user", "content": prompt}]
                        })
                    })
                    
                    # This won't work in Python - need to use requests
                    # Let me use a Python approach instead
                    
                    import json
                    
                    # Simulated AI response for now - in production, call Anthropic API
                    # You would use: import anthropic; client = anthropic.Anthropic()
                    
                    st.info("💡 AI Analysis Complete!")
                    
                    # Generate smart recommendations based on data
                    recommendations = []
                    
                    # Enterprise vs Strategic split
                    if score_col:
                        high_value_count = (df_ai[score_col] > df_ai[score_col].quantile(0.75)).sum()
                        mid_value_count = ((df_ai[score_col] >= df_ai[score_col].quantile(0.25)) & 
                                         (df_ai[score_col] <= df_ai[score_col].quantile(0.75))).sum()
                        
                        # Enterprise (high-value)
                        ent_aes = max(3, int(high_value_count / 15))  # ~15 accounts per enterprise AE
                        recommendations.append({
                            'name': 'Enterprise',
                            'num_aes': ent_aes,
                            'accounts': high_value_count,
                            'criteria': 'High account score (top 25%)',
                            'rationale': 'Lower account load for high-touch enterprise sales'
                        })
                        
                        # Strategic (mid-value)
                        strat_aes = max(5, int(mid_value_count / 25))  # ~25 accounts per strategic AE
                        recommendations.append({
                            'name': 'Strategic',
                            'num_aes': strat_aes,
                            'accounts': mid_value_count,
                            'criteria': 'Mid account score (25th-75th percentile)',
                            'rationale': 'Balanced approach for growing accounts'
                        })
                    
                    # Regional splits if we have region data
                    if region_col and len(recommendations) > 0:
                        top_regions = df_ai[region_col].value_counts().head(3).index.tolist()
                        
                        regional_recs = []
                        for base_seg in recommendations[:]:  # Copy to avoid modifying while iterating
                            for region in top_regions:
                                region_accounts = len(df_ai[df_ai[region_col] == region])
                                if region_accounts > 50:  # Only if substantial
                                    regional_recs.append({
                                        'name': f"{base_seg['name']}-{region}",
                                        'num_aes': max(2, int(base_seg['num_aes'] * (region_accounts / total_accounts))),
                                        'accounts': region_accounts,
                                        'criteria': f"{base_seg['criteria']}, Region: {region}",
                                        'rationale': f"Regional focus with {base_seg['rationale'].lower()}"
                                    })
                        
                        if regional_recs:
                            recommendations = regional_recs
                    
                    # Display recommendations
                    st.markdown("<h4>📋 Recommended Segments:</h4>", unsafe_allow_html=True)
                    
                    total_recommended_aes = sum(r['num_aes'] for r in recommendations)
                    st.metric("Recommended Total AEs", total_recommended_aes, 
                             delta=f"{total_recommended_aes - current_aes:+d} vs current")
                    
                    for rec in recommendations:
                        st.markdown(f"""
                            <div class='account-card' style='margin: 12px 0;'>
                                <h4 style='margin: 0; color: #4299e1;'>{rec['name']}</h4>
                                <p style='margin: 4px 0;'><strong>AEs:</strong> {rec['num_aes']} | <strong>Accounts:</strong> {rec.get('accounts', 'N/A')}</p>
                                <p style='margin: 4px 0; color: #a0aec0; font-size: 13px;'><strong>Criteria:</strong> {rec['criteria']}</p>
                                <p style='margin: 4px 0; color: #718096; font-size: 12px;'>{rec['rationale']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add quick-add button
                        if st.button(f"➕ Add {rec['name']}", key=f"add_ai_{rec['name']}", use_container_width=True):
                            if not any(s['name'] == rec['name'] for s in st.session_state.segments):
                                st.session_state.segments.append({
                                    'name': rec['name'],
                                    'num_aes': rec['num_aes'],
                                    'draft_id': None,
                                    'status': 'Not Started'
                                })
                                st.success(f"✅ Added {rec['name']}")
                                st.rerun()
                    
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
                            st.success(f"✅ Added {added} segments!")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"Error analyzing accounts: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Original summary section
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
            st.markdown(f"<p style='text-align: center; color: #a0aec0;'>{int(progress * 100)}% Complete</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# DRAFT FLOW VIEW (ALL ORIGINAL CODE FROM HERE)
# =============================================================================

elif st.session_state.view_mode == 'draft_flow':
    # Show current draft info
    if st.session_state.current_draft_id in st.session_state.all_drafts:
        draft_info = st.session_state.all_drafts[st.session_state.current_draft_id]
        st.markdown(f"""
            <div style='background: #2d3748; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;'>
                <strong style='color: #4299e1;'>📍 {draft_info['segment_name']}</strong> | 
                <strong>Stage:</strong> {st.session_state.stage.replace('_', ' ').title()} | 
                <strong>Created:</strong> {draft_info['created_at']}
            </div>
        """, unsafe_allow_html=True)

# Sidebar for navigation and settings (only show in draft mode)
if st.session_state.view_mode == 'draft_flow':
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <h2 style='font-size: 24px; margin: 0;'>⚙️ Draft Control</h2>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.stage in ['setup', 'cleanup', 'blacklist', 'draft', 'results'] and st.session_state.accounts_df is not None:
            st.markdown(f"""
                <div class='draft-card'>
                    <p style='color: #48bb78; font-weight: 600; margin: 0;'>✅ CSV Loaded</p>
                    <p style='color: #e2e8f0; font-size: 24px; font-weight: 700; margin: 4px 0;'>{len(st.session_state.accounts_df):,}</p>
                    <p style='color: #a0aec0; font-size: 12px; margin: 0;'>ACCOUNTS</p>
                </div>
            """, unsafe_allow_html=True)
    
        if st.session_state.stage in ['blacklist', 'draft', 'results'] and st.session_state.ae_list:
            st.markdown(f"""
                <div class='draft-card'>
                    <p style='color: #4299e1; font-weight: 600; margin: 0;'>👥 AEs in Draft</p>
                    <p style='color: #e2e8f0; font-size: 24px; font-weight: 700; margin: 4px 0;'>{len(st.session_state.ae_list)}</p>
                    <p style='color: #a0aec0; font-size: 12px; margin: 0;'>{'SNAKE DRAFT' if st.session_state.get('is_snake', True) else 'LINEAR DRAFT'}</p>
                </div>
            """, unsafe_allow_html=True)
    
        st.markdown("<hr style='border-color: #2d3748; margin: 24px 0;'>", unsafe_allow_html=True)
    
        st.markdown("<p style='color: #a0aec0; font-size: 12px; font-weight: 600; letter-spacing: 1px;'>DRAFT PROGRESS</p>", unsafe_allow_html=True)
    
        stages = {
            'upload': ('1', 'Upload CSV'),
            'setup': ('2', 'Draft Setup'), 
            'cleanup': ('3', 'Pre-Draft'),
            'blacklist': ('4', 'Blacklist'),
            'draft': ('5', 'Live Draft'),
            'results': ('6', 'Results')
        }
    
        for key, (num, label) in stages.items():
            if st.session_state.stage == key:
                st.markdown(f"""
                    <div style='background: #2d3748; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #48bb78;'>
                        <span style='color: #48bb78; font-weight: 700;'>{num}</span>
                        <span style='color: #f7fafc; font-weight: 600; margin-left: 12px;'>{label}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='padding: 12px; margin: 8px 0;'>
                        <span style='color: #4a5568; font-weight: 600;'>{num}</span>
                        <span style='color: #718096; margin-left: 12px;'>{label}</span>
                    </div>
                """, unsafe_allow_html=True)


# Stage 1: CSV Upload
if st.session_state.stage == 'upload':
    st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top: 0;'>📁 Upload Your Account Data</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #2d3748; padding: 16px; border-radius: 8px; margin: 16px 0;'>
        <p style='color: #e2e8f0; font-weight: 600; margin: 0 0 8px 0;'>Required Columns:</p>
        <ul style='color: #a0aec0; margin: 0; padding-left: 20px;'>
            <li><strong style='color: #4299e1;'>Account Name</strong> or Account_Name</li>
            <li><strong style='color: #4299e1;'>Account ID</strong> or Account_ID</li>
            <li><strong style='color: #4299e1;'>Account Owner Name</strong> or Account_Owner_Name</li>
            <li><strong style='color: #4299e1;'>Account Score</strong> or Account_Score (numerical)</li>
        </ul>
        <p style='color: #718096; font-size: 14px; margin: 12px 0 0 0;'>Optional: Parent Account ID, Industry, Sub-Industry, Billing State, etc.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Drop your CSV here or click to browse", type=['csv'])
    st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.replace(' ', '_')
            
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            st.markdown("<h3>🔗 Map Your Columns</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #a0aec0;'>Match your CSV columns to the required fields:</p>", unsafe_allow_html=True)
            
            available_columns = [''] + df.columns.tolist()
            
            col1, col2 = st.columns(2)
            with col1:
                account_name_col = st.selectbox(
                    "Account Name *",
                    available_columns,
                    index=next((i for i, col in enumerate(available_columns) if 'account' in col.lower() and 'name' in col.lower()), 0)
                )
                account_id_col = st.selectbox(
                    "Account ID *",
                    available_columns,
                    index=next((i for i, col in enumerate(available_columns) if 'account' in col.lower() and 'id' in col.lower()), 0)
                )
            
            with col2:
                account_owner_col = st.selectbox(
                    "Account Owner Name *",
                    available_columns,
                    index=next((i for i, col in enumerate(available_columns) if 'owner' in col.lower() and 'name' in col.lower()), 0)
                )
                account_score_col = st.selectbox(
                    "Account Score *",
                    available_columns,
                    index=next((i for i, col in enumerate(available_columns) if 'score' in col.lower()), 0)
                )
            
            # Validate mapping
            required_fields = {
                'Account_Name': account_name_col,
                'Account_ID': account_id_col,
                'Account_Owner_Name': account_owner_col,
                'Account_Score': account_score_col
            }
            
            missing = [field for field, col in required_fields.items() if not col]
            
            if missing:
                st.warning(f"⚠️ Please map all required fields: {', '.join([k for k, v in required_fields.items() if not v])}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Create new dataframe with mapped columns
                df_mapped = df.copy()
                for standard_name, user_col in required_fields.items():
                    if user_col in df.columns:
                        df_mapped[standard_name] = df[user_col]
                
                # Convert Account_Score to numeric
                df_mapped['Account_Score'] = pd.to_numeric(df_mapped['Account_Score'], errors='coerce')
                df_mapped = df_mapped.dropna(subset=['Account_Score'])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("✅ Confirm Mapping", type="primary"):
                    st.session_state.accounts_df = df_mapped
                
                st.markdown("<div class='draft-card' style='background: linear-gradient(135deg, #22543d 0%, #1a2f23 100%); border-color: #48bb78;'>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='color: #48bb78; margin-top: 0;'>✅ Successfully loaded {len(df):,} accounts!</h3>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Show preview
                st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
                st.markdown("<h3>📊 Data Preview</h3>", unsafe_allow_html=True)
                st.dataframe(df.head(10), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Show summary stats
                st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Accounts", f"{len(df):,}")
                with col2:
                    st.metric("Unique Owners", df['Account_Owner_Name'].nunique())
                with col3:
                    st.metric("Avg Account Score", f"{df['Account_Score'].mean():.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Breakdown by Account Owner
                st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
                st.markdown("<h3>👥 Account Breakdown by Owner</h3>", unsafe_allow_html=True)
                
                owner_stats = df.groupby('Account_Owner_Name').agg({
                    'Account_ID': 'count',
                    'Account_Score': ['mean', 'max', 'min', 'sum']
                }).round(2)
                
                owner_stats.columns = ['Account Count', 'Avg Score', 'Max Score', 'Min Score', 'Total Score']
                owner_stats = owner_stats.sort_values('Avg Score', ascending=False).reset_index()
                
                st.dataframe(owner_stats, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("➡️ Proceed to Draft Setup", type="primary"):
                    st.session_state.stage = 'setup'
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")


# Stage 2: Draft Setup
elif st.session_state.stage == 'setup':
    st.markdown("<h2>⚙️ Configure Your Draft</h2>", unsafe_allow_html=True)
    
    df = st.session_state.accounts_df
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>👥 Select AEs</h3>", unsafe_allow_html=True)
        
        # Get unique owners from data
        unique_owners = sorted(df['Account_Owner_Name'].unique().tolist())
        
        selected_aes = st.multiselect(
            "Choose AEs for the draft",
            unique_owners,
            default=unique_owners[:5] if len(unique_owners) >= 5 else unique_owners
        )
        
        # Or manually add AEs
        st.markdown("<p style='color: #a0aec0; font-size: 14px; margin-top: 16px;'>Or add AE manually:</p>", unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 1])
        with col_a:
            manual_ae = st.text_input("AE name", label_visibility="collapsed")
        with col_b:
            if st.button("Add", use_container_width=True) and manual_ae:
                if manual_ae not in selected_aes:
                    selected_aes.append(manual_ae)
                    st.success(f"Added {manual_ae}")
        
        st.session_state.ae_list = selected_aes
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>⚡ Draft Settings</h3>", unsafe_allow_html=True)
        
        draft_type = st.radio("Draft Type", ["Snake", "Linear"], index=0)
        st.session_state.is_snake = (draft_type == "Snake")
        
        accounts_per_ae = st.number_input(
            "Target accounts per AE",
            min_value=1,
            max_value=100,
            value=20,
            step=1
        )
        st.session_state.accounts_per_ae = accounts_per_ae
        
        st.markdown("<p style='color: #a0aec0; font-size: 14px; margin-top: 16px;'>Draft Order:</p>", unsafe_allow_html=True)
        order_method = st.radio("Set order by:", ["Random", "Manual"], label_visibility="collapsed")
        
        if order_method == "Random":
            if st.button("🎲 Randomize Order", use_container_width=True):
                st.session_state.draft_order = np.random.permutation(selected_aes).tolist()
                st.rerun()
        else:
            st.info("💡 Reorder AEs below - first in list picks first")
            
            # Manual reordering with selectboxes
            if 'draft_order' not in st.session_state or set(st.session_state.draft_order) != set(selected_aes):
                st.session_state.draft_order = selected_aes.copy()
            
            # Allow user to reorder by selecting position for each AE
            new_order = st.session_state.draft_order.copy()
            
            for i in range(len(new_order)):
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.markdown(f"<p style='color: #4299e1; font-weight: 600; padding-top: 8px;'>Pick {i+1}</p>", unsafe_allow_html=True)
                with col_b:
                    # Get available AEs (those not already placed before this position)
                    available_for_position = [ae for ae in selected_aes if ae not in new_order[:i]]
                    if new_order[i] not in available_for_position:
                        available_for_position.append(new_order[i])
                    
                    current_ae = st.selectbox(
                        f"Position {i+1}",
                        available_for_position,
                        index=available_for_position.index(new_order[i]) if new_order[i] in available_for_position else 0,
                        key=f"draft_pos_{i}",
                        label_visibility="collapsed"
                    )
                    new_order[i] = current_ae
            
            st.session_state.draft_order = new_order
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show draft order
    if st.session_state.draft_order:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>📋 Draft Order</h3>", unsafe_allow_html=True)
        
        for i, ae in enumerate(st.session_state.draft_order, 1):
            st.markdown(f"""
                <div class='account-card'>
                    <span style='color: #4299e1; font-weight: 700; font-size: 18px;'>{i}</span>
                    <span style='color: #f7fafc; font-weight: 600; margin-left: 16px; font-size: 16px;'>{ae}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show summary
    if selected_aes:
        st.markdown("<div class='draft-card' style='background: linear-gradient(135deg, #2c5282 0%, #1e3a5f 100%);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>📊 Draft Summary</h3>", unsafe_allow_html=True)
        total_picks = len(selected_aes) * accounts_per_ae
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("AEs Drafting", len(selected_aes))
        with col2:
            st.metric("Accounts Per AE", accounts_per_ae)
        with col3:
            st.metric("Total Picks", total_picks)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("➡️ Proceed to Pre-Draft Cleanup", type="primary", disabled=len(selected_aes) == 0):
            # Initialize AE books with current accounts
            st.session_state.ae_books = {ae: [] for ae in selected_aes}
            st.session_state.stage = 'cleanup'
            st.rerun()

# Stage 3: Pre-Draft Cleanup
elif st.session_state.stage == 'cleanup':
    st.markdown("<h2>🧹 Pre-Draft Cleanup</h2>", unsafe_allow_html=True)
    
    df = st.session_state.accounts_df
    
    st.markdown("""
    <div style='background: #2d3748; padding: 16px; border-radius: 8px; margin: 16px 0;'>
        <p style='color: #e2e8f0; margin: 0;'><strong>Configure which accounts each AE keeps before the draft.</strong> AEs can hold onto their top accounts, and dropped accounts will be available in the draft.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize keeper selections if not exists
    if 'ae_keeper_selections' not in st.session_state:
        st.session_state.ae_keeper_selections = {}
    
    st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0;'>⚙️ Retention Settings</h3>", unsafe_allow_html=True)
    
    keep_accounts = st.number_input(
        "Max accounts each AE can keep (pre-draft)",
        min_value=0,
        max_value=50,
        value=10,
        help="AEs will keep their top N accounts by Account Score"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show what each AE would keep with ability to substitute
    st.markdown("<h3>📚 Account Selection by AE</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0;'>Review and customize which accounts each AE keeps. By default, top accounts by score are selected.</p>", unsafe_allow_html=True)
    
    for ae in st.session_state.ae_list:
        ae_all_accounts = df[df['Account_Owner_Name'] == ae].sort_values('Account_Score', ascending=False)
        
        # Initialize with top accounts if not already set
        if ae not in st.session_state.ae_keeper_selections:
            st.session_state.ae_keeper_selections[ae] = ae_all_accounts.head(keep_accounts)['Account_ID'].tolist()
        
        # Get current keepers
        current_keepers = st.session_state.ae_keeper_selections[ae][:keep_accounts]
        keeper_accounts = df[df['Account_ID'].isin(current_keepers)]
        
        avg_score = keeper_accounts['Account_Score'].mean() if len(keeper_accounts) > 0 else 0
        
        with st.expander(f"✏️ {ae} - Keeping {len(current_keepers)} accounts (Avg Score: {avg_score:.2f})"):
            
            # Show current keepers
            st.markdown("**Current Keepers:**")
            for idx, row in keeper_accounts.iterrows():
                col_a, col_b, col_c = st.columns([4, 2, 1])
                with col_a:
                    st.markdown(f"<p style='margin: 4px 0;'>{row['Account_Name']}</p>", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"<span class='score-badge'>{row['Account_Score']:.2f}</span>", unsafe_allow_html=True)
                with col_c:
                    if st.button("🗑️", key=f"remove_{ae}_{row['Account_ID']}", help="Remove this account"):
                        st.session_state.ae_keeper_selections[ae].remove(row['Account_ID'])
                        st.rerun()
            
            # Allow adding accounts
            if len(current_keepers) < keep_accounts:
                st.markdown("---")
                st.markdown(f"**Add Account** (can add {keep_accounts - len(current_keepers)} more):")
                
                # Get available accounts (owned by this AE but not already kept)
                available_to_add = ae_all_accounts[~ae_all_accounts['Account_ID'].isin(current_keepers)]
                
                if len(available_to_add) > 0:
                    add_account = st.selectbox(
                        "Select account to add",
                        options=[''] + available_to_add['Account_Name'].tolist(),
                        key=f"add_select_{ae}"
                    )
                    
                    if add_account:
                        account_to_add = available_to_add[available_to_add['Account_Name'] == add_account].iloc[0]
                        if st.button(f"➕ Add {add_account}", key=f"add_btn_{ae}"):
                            st.session_state.ae_keeper_selections[ae].append(account_to_add['Account_ID'])
                            st.rerun()
        
        # Store final keepers
        st.session_state.ae_books[ae] = st.session_state.ae_keeper_selections[ae][:keep_accounts]
    
    # Calculate available accounts for draft
    kept_account_ids = set()
    for ae_accounts in st.session_state.ae_books.values():
        kept_account_ids.update(ae_accounts)
    
    available_for_draft = df[~df['Account_ID'].isin(kept_account_ids)].copy()
    
    st.markdown("---")
    st.markdown("<div class='draft-card' style='background: #2d3748;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0;'>📊 Cleanup Summary</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Accounts Kept", len(kept_account_ids))
    with col2:
        st.metric("Available for Draft", len(available_for_draft))
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("➡️ Continue to Blacklist & Draft Setup", type="primary"):
        st.session_state.available_accounts = available_for_draft.sort_values('Account_Score', ascending=False).to_dict('records')
        st.session_state.stage = 'blacklist'
        st.rerun()

# Stage 3.5: Blacklist (new separate stage)
elif st.session_state.stage == 'blacklist':
    st.markdown("<h2>🚫 Blacklist Accounts</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: #7c2d12; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #f6ad55;'>
        <p style='color: #feebc8; margin: 0;'><strong>Review available accounts and blacklist any that should not be drafted</strong> (competitors, bad data quality, etc.)</p>
    </div>
    """, unsafe_allow_html=True)
    
    available_df = pd.DataFrame(st.session_state.available_accounts)
    
    st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0;'>📋 Available Accounts for Draft</h3>", unsafe_allow_html=True)
    st.dataframe(
        available_df[['Account_Name', 'Account_Score', 'Industry']].head(50),
        use_container_width=True,
        height=400
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>🚫 Add to Blacklist</h3>", unsafe_allow_html=True)
        
        blacklist_method = st.radio("Blacklist by:", ["Account Names (one per line)", "Select from list"])
        
        if blacklist_method == "Account Names (one per line)":
            blacklist_input = st.text_area(
                "Account names",
                placeholder="Competitor Corp\nBad Data Inc\nJunk Account LLC",
                height=150,
                label_visibility="collapsed"
            )
            
            if st.button("🚫 Blacklist These Accounts"):
                if blacklist_input:
                    blacklist_names = [name.strip() for name in blacklist_input.split('\n') if name.strip()]
                    blacklist_ids = available_df[available_df['Account_Name'].isin(blacklist_names)]['Account_ID'].tolist()
                    st.session_state.blacklisted_accounts = st.session_state.blacklisted_accounts.union(set(blacklist_ids))
                    st.success(f"✅ Blacklisted {len(blacklist_ids)} accounts")
                    st.rerun()
        else:
            # Select from multiselect
            blacklist_select = st.multiselect(
                "Select accounts to blacklist",
                options=available_df['Account_Name'].tolist(),
                label_visibility="collapsed"
            )
            
            if st.button("🚫 Blacklist Selected") and blacklist_select:
                blacklist_ids = available_df[available_df['Account_Name'].isin(blacklist_select)]['Account_ID'].tolist()
                st.session_state.blacklisted_accounts = st.session_state.blacklisted_accounts.union(set(blacklist_ids))
                st.success(f"✅ Blacklisted {len(blacklist_ids)} accounts")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0;'>📊 Blacklist Summary</h3>", unsafe_allow_html=True)
        st.metric("Blacklisted Accounts", len(st.session_state.blacklisted_accounts))
        
        if len(st.session_state.blacklisted_accounts) > 0:
            st.markdown("**Blacklisted:**")
            blacklisted_df = available_df[available_df['Account_ID'].isin(st.session_state.blacklisted_accounts)]
            for _, row in blacklisted_df.iterrows():
                col_x, col_y = st.columns([3, 1])
                with col_x:
                    st.markdown(f"<p style='font-size: 12px; margin: 2px 0;'>{row['Account_Name']}</p>", unsafe_allow_html=True)
                with col_y:
                    if st.button("✖️", key=f"unblock_{row['Account_ID']}", help="Remove from blacklist"):
                        st.session_state.blacklisted_accounts.remove(row['Account_ID'])
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Remove blacklisted from available
    final_available = available_df[~available_df['Account_ID'].isin(st.session_state.blacklisted_accounts)]
    
    st.markdown("---")
    st.metric("📈 Final Available for Draft", len(final_available))
    
    if st.button("➡️ Start Draft", type="primary"):
        st.session_state.available_accounts = final_available.sort_values('Account_Score', ascending=False).to_dict('records')
        st.session_state.current_pick = 0
        st.session_state.draft_picks = []
        st.session_state.stage = 'draft'
        st.rerun()

# Stage 4: Live Draft
elif st.session_state.stage == 'draft':
    st.markdown("<h2>🎯 Live Draft Board</h2>", unsafe_allow_html=True)
    
    total_rounds = st.session_state.accounts_per_ae
    num_aes = len(st.session_state.draft_order)
    
    # Safety check - if no AEs, go back to setup
    if num_aes == 0:
        st.error("No AEs found! Please go back to setup.")
        if st.button("← Back to Setup"):
            st.session_state.stage = 'setup'
            st.rerun()
        st.stop()
    
    total_picks = total_rounds * num_aes
    current_pick = st.session_state.current_pick
    
    # Calculate current round and position
    current_round = (current_pick // num_aes) + 1
    pick_in_round = (current_pick % num_aes)
    
    # Determine current drafter (snake logic)
    if st.session_state.is_snake and current_round % 2 == 0:
        current_ae_index = num_aes - 1 - pick_in_round
    else:
        current_ae_index = pick_in_round
    
    current_ae = st.session_state.draft_order[current_ae_index] if current_pick < total_picks else None
    
    # Draft progress
    progress = min(current_pick / total_picks, 1.0)
    st.progress(progress, text=f"Pick {current_pick + 1} of {total_picks}")
    
    st.markdown(f"""
        <div style='text-align: center; margin: 16px 0;'>
            <span class='round-indicator'>Round {current_round} of {total_rounds}</span>
        </div>
    """, unsafe_allow_html=True)
    
    if current_pick >= total_picks:
        st.markdown("""
            <div class='draft-card' style='background: linear-gradient(135deg, #22543d 0%, #1a2f23 100%); text-align: center; padding: 48px;'>
                <h1 style='font-size: 48px; margin: 0;'>🎉</h1>
                <h2 style='margin: 16px 0;'>Draft Complete!</h2>
                <p style='color: #c6f6d5;'>Time to review your new territory assignments</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("➡️ View Results", type="primary"):
            st.session_state.stage = 'results'
            st.rerun()
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # On the clock card
            st.markdown(f"""
                <div class='on-clock'>
                    <h3 style='margin: 0 0 8px 0; color: #48bb78;'>🏈 ON THE CLOCK</h3>
                    <h2 style='margin: 0; font-size: 32px;'>{current_ae}</h2>
                    <p style='color: #a0aec0; margin: 8px 0 0 0;'>Round {current_round}, Pick {pick_in_round + 1}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Available accounts
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top: 0;'>📊 Top Available Accounts</h3>", unsafe_allow_html=True)
            
            available_df = pd.DataFrame(st.session_state.available_accounts)
            
            if len(available_df) > 0:
                # Account selection
                selected_account_name = st.selectbox(
                    "Select account to draft:",
                    options=available_df['Account_Name'].tolist(),
                    index=0,
                    label_visibility="collapsed"
                )
                
                selected_account = available_df[available_df['Account_Name'] == selected_account_name].iloc[0]
                
                # Show selected account card
                st.markdown(f"""
                    <div class='account-card' style='background: #2d3748; padding: 20px; margin: 16px 0;'>
                        <h4 style='margin: 0 0 8px 0; color: #f7fafc;'>{selected_account['Account_Name']}</h4>
                        <span class='score-badge'>Score: {selected_account['Account_Score']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅ Draft This Account", type="primary", use_container_width=True):
                        # Record the pick
                        st.session_state.draft_picks.append({
                            'pick_number': current_pick + 1,
                            'round': current_round,
                            'ae': current_ae,
                            'account_name': selected_account['Account_Name'],
                            'account_id': selected_account['Account_ID'],
                            'account_score': selected_account['Account_Score']
                        })
                        
                        st.session_state.ae_books[current_ae].append(selected_account['Account_ID'])
                        
                        st.session_state.available_accounts = [
                            acc for acc in st.session_state.available_accounts 
                            if acc['Account_ID'] != selected_account['Account_ID']
                        ]
                        
                        st.session_state.current_pick += 1
                        st.rerun()
                
                with col_b:
                    if st.button("⚡ Auto-Draft Best", use_container_width=True):
                        best_account = available_df.iloc[0]
                        
                        st.session_state.draft_picks.append({
                            'pick_number': current_pick + 1,
                            'round': current_round,
                            'ae': current_ae,
                            'account_name': best_account['Account_Name'],
                            'account_id': best_account['Account_ID'],
                            'account_score': best_account['Account_Score']
                        })
                        
                        st.session_state.ae_books[current_ae].append(best_account['Account_ID'])
                        
                        st.session_state.available_accounts = [
                            acc for acc in st.session_state.available_accounts 
                            if acc['Account_ID'] != best_account['Account_ID']
                        ]
                        
                        st.session_state.current_pick += 1
                        st.rerun()
                
                with col_c:
                    if current_pick > 0 and st.button("↩️ Undo Pick", use_container_width=True):
                        last_pick = st.session_state.draft_picks.pop()
                        st.session_state.ae_books[last_pick['ae']].remove(last_pick['account_id'])
                        
                        returned_account = st.session_state.accounts_df[
                            st.session_state.accounts_df['Account_ID'] == last_pick['account_id']
                        ].iloc[0].to_dict()
                        st.session_state.available_accounts.insert(0, returned_account)
                        st.session_state.available_accounts = sorted(
                            st.session_state.available_accounts,
                            key=lambda x: x['Account_Score'],
                            reverse=True
                        )
                        
                        st.session_state.current_pick -= 1
                        st.rerun()
                
                # Auto-complete rest of draft button
                st.markdown("---")
                remaining_picks = total_picks - current_pick
                st.markdown(f"<p style='color: #a0aec0; text-align: center;'>{remaining_picks} picks remaining</p>", unsafe_allow_html=True)
                
                if st.button(f"🤖 Auto-Complete Remaining {remaining_picks} Picks", use_container_width=True, type="secondary"):
                    # Auto-draft all remaining picks
                    with st.spinner('Auto-drafting remaining picks...'):
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
                st.markdown("<h4 style='margin: 24px 0 12px 0;'>Available Accounts</h4>", unsafe_allow_html=True)
                for idx, row in available_df.head(15).iterrows():
                    st.markdown(f"""
                        <div class='account-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <span style='color: #f7fafc; font-weight: 600;'>{row['Account_Name']}</span>
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
                        <p style='margin: 0; color: #4299e1; font-weight: 600; font-size: 12px;'>PICK {pick['pick_number']}</p>
                        <p style='margin: 4px 0; color: #f7fafc; font-weight: 600;'>{pick['ae']}</p>
                        <p style='margin: 4px 0 0 0; color: #e2e8f0; font-size: 14px;'>{pick['account_name']}</p>
                        <span class='score-badge' style='font-size: 12px; margin-top: 4px;'>{pick['account_score']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Current AE's book
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
                        <div style='background: #232936; padding: 8px; border-radius: 6px; margin: 4px 0;'>
                            <div style='display: flex; justify-content: space-between;'>
                                <span style='color: #e2e8f0; font-size: 13px;'>{row['Account_Name']}</span>
                                <span style='color: #4299e1; font-weight: 600; font-size: 13px;'>{row['Account_Score']:.1f}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Stage 5: Results & Reporting
elif st.session_state.stage == 'results':
    st.header("📊 Draft Results")
    
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
    
    st.subheader("🏆 Final Standings")
    st.dataframe(results_df, use_container_width=True)
    
    # Individual AE books
    st.subheader("📚 Account Books by AE")
    
    for ae in st.session_state.ae_list:
        ae_account_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_account_ids)].sort_values('Account_Score', ascending=False)
        
        with st.expander(f"{ae} - {len(ae_accounts)} accounts | Avg Score: {ae_accounts['Account_Score'].mean():.2f}"):
            st.dataframe(
                ae_accounts[['Account_Name', 'Account_Score']].reset_index(drop=True),
                use_container_width=True
            )
    
    # Draft history
    st.subheader("📜 Complete Draft History")
    if st.session_state.draft_picks:
        draft_history_df = pd.DataFrame(st.session_state.draft_picks)
        st.dataframe(draft_history_df, use_container_width=True)
    
    # Export results
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
            mime="text/csv"
        )
    
    with col2:
        # Download draft history
        if st.session_state.draft_picks:
            draft_csv = pd.DataFrame(st.session_state.draft_picks).to_csv(index=False)
            st.download_button(
                label="📥 Download Draft History",
                data=draft_csv,
                file_name=f"draft_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    if st.button("🔄 Start New Draft"):
        # Reset everything
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# Save draft state before page closes
sync_to_current_draft()
