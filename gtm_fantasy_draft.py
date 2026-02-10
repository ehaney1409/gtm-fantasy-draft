import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="GTM Fantasy Draft", layout="wide", page_icon="🏈")

# Custom CSS for Sleeper-inspired dark theme
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background-color: #0f1419;
    }
    
    /* Main content area */
    .main {
        background-color: #0f1419;
    }
    
    /* Custom card styling */
    .draft-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16191f 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid #2d3748;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .account-card {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #4299e1;
        transition: all 0.3s ease;
    }
    
    .account-card:hover {
        background: #232936;
        transform: translateX(4px);
        border-left-color: #63b3ed;
    }
    
    /* Pick card for draft board */
    .pick-card {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border-left: 3px solid #48bb78;
        font-size: 14px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f7fafc !important;
        font-weight: 700 !important;
    }
    
    /* Text colors */
    p, span, div {
        color: #e2e8f0 !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(66, 153, 225, 0.4);
    }
    
    /* Primary button special styling */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        box-shadow: 0 6px 12px rgba(72, 187, 120, 0.4);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1f2e;
        border-right: 1px solid #2d3748;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #1a1f2e;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #4299e1 !important;
        font-size: 32px !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0 !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #48bb78;
    }
    
    /* Dataframe */
    .stDataFrame {
        background-color: #1a1f2e;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #1a1f2e;
        border-radius: 12px;
        border: 2px dashed #4299e1;
        padding: 24px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a1f2e;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #a0aec0;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2d3748;
        color: #4299e1;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess {
        background-color: #22543d;
        border-left: 4px solid #48bb78;
        border-radius: 8px;
        color: #c6f6d5;
    }
    
    .stInfo {
        background-color: #2c5282;
        border-left: 4px solid #4299e1;
        border-radius: 8px;
        color: #bee3f8;
    }
    
    .stWarning {
        background-color: #7c2d12;
        border-left: 4px solid #f6ad55;
        border-radius: 8px;
        color: #feebc8;
    }
    
    /* On the clock highlight */
    .on-clock {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border: 2px solid #48bb78;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 0 20px rgba(72, 187, 120, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 20px rgba(72, 187, 120, 0.3);
        }
        50% {
            box-shadow: 0 0 30px rgba(72, 187, 120, 0.5);
        }
    }
    
    /* Score badge */
    .score-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
    }
    
    /* Round indicator */
    .round-indicator {
        background: #2d3748;
        color: #4299e1;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
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

# Header with Sleeper-style branding
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
        <div style='padding: 20px 0;'>
            <h1 style='margin: 0; font-size: 48px; background: linear-gradient(135deg, #4299e1 0%, #48bb78 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;'>
                🏈 GTM Fantasy Draft
            </h1>
            <p style='color: #a0aec0; font-size: 18px; margin-top: 8px;'>Territory planning reimagined</p>
        </div>
    """, unsafe_allow_html=True)


# Sidebar for navigation and settings
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h2 style='font-size: 24px; margin: 0;'>⚙️ Draft Control</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.stage in ['setup', 'cleanup', 'draft', 'results']:
        st.markdown(f"""
            <div class='draft-card'>
                <p style='color: #48bb78; font-weight: 600; margin: 0;'>✅ CSV Loaded</p>
                <p style='color: #e2e8f0; font-size: 24px; font-weight: 700; margin: 4px 0;'>{len(st.session_state.accounts_df):,}</p>
                <p style='color: #a0aec0; font-size: 12px; margin: 0;'>ACCOUNTS</p>
            </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.stage in ['draft', 'results']:
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
        'draft': ('4', 'Live Draft'),
        'results': ('5', 'Results')
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
            
            # Check for required columns (flexible naming)
            required_mappings = {
                'Account_Name': ['Account_Name', 'Account Name', 'account_name', 'AccountName'],
                'Account_ID': ['Account_ID', 'Account ID', 'account_id', 'AccountID', 'Id', 'ID'],
                'Account_Owner_Name': ['Account_Owner_Name', 'Account Owner Name', 'account_owner_name', 'Owner_Name', 'Owner'],
                'Account_Score': ['Account_Score', 'Account Score', 'account_score', 'Score']
            }
            
            # Rename columns to standard names
            for standard_name, possible_names in required_mappings.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        df.rename(columns={possible_name: standard_name}, inplace=True)
                        break
            
            # Verify we have required columns
            missing = [col for col in required_mappings.keys() if col not in df.columns]
            
            if missing:
                st.error(f"❌ Missing required columns: {', '.join(missing)}")
                st.info("Available columns in your file: " + ", ".join(df.columns.tolist()))
            else:
                # Convert Account_Score to numeric
                df['Account_Score'] = pd.to_numeric(df['Account_Score'], errors='coerce')
                df = df.dropna(subset=['Account_Score'])
                
                st.session_state.accounts_df = df
                
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
        order_method = st.radio("Set order by:", ["Random", "Manual (by tenure/selection)"], label_visibility="collapsed")
        
        if order_method == "Random":
            if st.button("🎲 Randomize Order", use_container_width=True):
                st.session_state.draft_order = np.random.permutation(selected_aes).tolist()
                st.rerun()
        else:
            st.session_state.draft_order = selected_aes.copy()
        
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
    st.header("🧹 Step 3: Pre-Draft Cleanup")
    
    df = st.session_state.accounts_df
    
    st.markdown("""
    **Configure which accounts each AE keeps before the draft:**
    - Set how many accounts each AE can hold onto
    - Review and blacklist any bad accounts (competitors, poor data quality)
    - Dropped accounts will be available in the draft
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Account Retention")
        
        keep_accounts = st.number_input(
            "Max accounts each AE can keep (pre-draft)",
            min_value=0,
            max_value=50,
            value=10,
            help="AEs will keep their top N accounts by Account Score"
        )
        
        # Show what each AE would keep
        st.markdown("**Preview: Accounts Being Kept**")
        
        for ae in st.session_state.ae_list:
            ae_accounts = df[df['Account_Owner_Name'] == ae].nlargest(keep_accounts, 'Account_Score')
            
            with st.expander(f"{ae} - Keeping {len(ae_accounts)} accounts (Avg Score: {ae_accounts['Account_Score'].mean():.2f})"):
                st.dataframe(
                    ae_accounts[['Account_Name', 'Account_Score']].reset_index(drop=True),
                    use_container_width=True
                )
                # Store kept accounts
                st.session_state.ae_books[ae] = ae_accounts['Account_ID'].tolist()
    
    with col2:
        st.subheader("Blacklist Accounts")
        
        st.markdown("Flag accounts to exclude from draft:")
        
        blacklist_input = st.text_area(
            "Account names (one per line)",
            placeholder="Competitor Corp\nBad Data Inc\nJunk Account LLC",
            height=150
        )
        
        if blacklist_input:
            blacklist_names = [name.strip() for name in blacklist_input.split('\n') if name.strip()]
            blacklist_ids = df[df['Account_Name'].isin(blacklist_names)]['Account_ID'].tolist()
            st.session_state.blacklisted_accounts = set(blacklist_ids)
            st.info(f"🚫 {len(st.session_state.blacklisted_accounts)} accounts blacklisted")
    
    # Calculate available accounts for draft
    kept_account_ids = set()
    for ae_accounts in st.session_state.ae_books.values():
        kept_account_ids.update(ae_accounts)
    
    available_for_draft = df[
        (~df['Account_ID'].isin(kept_account_ids)) & 
        (~df['Account_ID'].isin(st.session_state.blacklisted_accounts))
    ].copy()
    
    st.markdown("---")
    st.subheader("📊 Cleanup Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Accounts Kept", len(kept_account_ids))
    with col2:
        st.metric("Blacklisted", len(st.session_state.blacklisted_accounts))
    with col3:
        st.metric("Available for Draft", len(available_for_draft))
    
    if st.button("➡️ Start Draft", type="primary"):
        st.session_state.available_accounts = available_for_draft.sort_values('Account_Score', ascending=False).to_dict('records')
        st.session_state.current_pick = 0
        st.session_state.draft_picks = []
        st.session_state.stage = 'draft'
        st.rerun()

# Stage 4: Live Draft
elif st.session_state.stage == 'draft':
    st.markdown("<h2>🎯 Live Draft Board</h2>", unsafe_allow_html=True)
    
    total_rounds = st.session_state.accounts_per_ae
    num_aes = len(st.session_state.draft_order)
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
