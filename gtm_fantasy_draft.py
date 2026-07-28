import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(page_title="GTM Fantasy Draft", layout="wide", page_icon="🏈")

# =============================================================================
# SESSION STATE
# =============================================================================
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
if 'ae_books' not in st.session_state:
    st.session_state.ae_books = {}
if 'blacklisted_accounts' not in st.session_state:
    st.session_state.blacklisted_accounts = set()
if 'accounts_per_ae' not in st.session_state:
    st.session_state.accounts_per_ae = 20
if 'is_snake' not in st.session_state:
    st.session_state.is_snake = True
if 'filter_tier' not in st.session_state:
    st.session_state.filter_tier = 'all'
if 'accounts_shown' not in st.session_state:
    st.session_state.accounts_shown = 50

# AE SALESFORCE ID MAPPING
AE_SFDC_IDS = {
    'Alexa Pass': '005Vr00000QYPh1IAH',
    'Lindsay Kelvie': '005Vr00000QYQWVIA5',
    'Paul Kellum': '005Vr00000QYQWqIAP',
    'Travis Pederson': '005Vr00000QYQXDIA5'
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tier_rank(tier_value):
    """Return numeric rank for sorting (higher = better)"""
    if pd.isna(tier_value) or tier_value == '' or tier_value == 'nan':
        return 0
    tier_str = str(tier_value).lower()
    if 'tier 1' in tier_str:
        return 2
    elif 'tier 2' in tier_str:
        return 1
    return 0

def sort_accounts_by_tier(accounts_list):
    """Sort accounts by Tier (1 > 2 > Unranked), then by ICP Score (descending)"""
    return sorted(
        accounts_list,
        key=lambda x: (-get_tier_rank(x.get('CXP_Swat_Tier', '')), -float(x.get('ICP_score', 0)))
    )

def get_current_ae():
    """Determine which AE is picking now"""
    if not st.session_state.draft_order:
        return None
    num_aes = len(st.session_state.draft_order)
    pick_in_round = st.session_state.current_pick % num_aes
    round_num = st.session_state.current_pick // num_aes
    
    if st.session_state.is_snake and round_num % 2 == 1:
        ae_index = num_aes - 1 - pick_in_round
    else:
        ae_index = pick_in_round
    
    return st.session_state.draft_order[ae_index]

def tier_badge(tier_val):
    """Return visual badge for tier"""
    if pd.isna(tier_val) or tier_val == '' or tier_val == 'nan':
        return '⚪'
    tier_str = str(tier_val).lower()
    if 'tier 1' in tier_str:
        return '🟡'
    elif 'tier 2' in tier_str:
        return '🟢'
    return '⚪'

def tier_name(tier_val):
    """Return tier name"""
    if pd.isna(tier_val) or tier_val == '' or tier_val == 'nan':
        return 'Unranked'
    tier_str = str(tier_val).lower()
    if 'tier 1' in tier_str:
        return 'Tier 1'
    elif 'tier 2' in tier_str:
        return 'Tier 2'
    return 'Unranked'

# Sidebar - draft status
with st.sidebar:
    st.header("📊 Draft Status")
    
    if st.session_state.stage == 'draft':
        num_aes = len(st.session_state.ae_list)
        total_picks = num_aes * st.session_state.accounts_per_ae
        current = st.session_state.current_pick
        current_round = (current // num_aes) + 1
        picks_in_round = (current % num_aes) + 1
        
        st.metric("Current Pick", f"{current + 1} of {total_picks}")
        st.metric("Round", current_round)
        st.metric("Pick in Round", f"{picks_in_round} of {num_aes}")
        
        current_ae = get_current_ae()
        if current_ae:
            st.info(f"**Now Picking:** {current_ae}")
            ae_picks = len(st.session_state.ae_books[current_ae])
            st.metric(f"{current_ae}'s Picks", ae_picks)
        
        st.markdown("---")
        st.metric("Accounts Left", len(st.session_state.available_accounts))
    
    if st.session_state.stage in ['draft', 'results']:
        st.metric("AEs", len(st.session_state.ae_list))
        st.metric("Type", "Snake" if st.session_state.is_snake else "Linear")

# =============================================================================
# STAGE 1: CSV UPLOAD
# =============================================================================
if st.session_state.stage == 'upload':
    st.header("📁 Step 1: Upload Account Data")

    st.markdown("""
    Upload your SWAT CSV file. Required columns:
    - **Company name** — Account Name
    - **Salesforce ID** — Account ID
    - **ICP score** — Account Score (numeric)
    - **CXP Swat Tier** — Tier (Tier 1, Tier 2, or blank)
    """)

    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.replace(' ', '_')

            st.subheader("Map Columns")
            available_columns = [''] + df.columns.tolist()

            col1, col2 = st.columns(2)
            with col1:
                account_name_col = st.selectbox(
                    "Account Name",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'company' in c.lower() and 'name' in c.lower()), 0)
                )
                account_id_col = st.selectbox(
                    "Account ID",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'salesforce' in c.lower() and 'id' in c.lower()), 0)
                )
            with col2:
                account_score_col = st.selectbox(
                    "ICP Score",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'icp' in c.lower() and 'score' in c.lower()), 0)
                )
                tier_col = st.selectbox(
                    "CXP Swat Tier",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'cxp' in c.lower() and 'tier' in c.lower()), 0)
                )
            
            col3, col4 = st.columns(2)
            with col3:
                reasoning_col = st.selectbox(
                    "ICP Reasoning (optional)",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'reasoning' in c.lower()), 0)
                )

            required = {'Account_Name': account_name_col, 'Account_ID': account_id_col, 'ICP_score': account_score_col, 'CXP_Swat_Tier': tier_col}
            missing = [k for k, v in required.items() if not v]

            if missing:
                st.warning(f"⚠️ Map all fields: {', '.join(missing)}")
            else:
                df_mapped = df.copy()
                for std_name, user_col in required.items():
                    df_mapped[std_name] = df[user_col]
                
                # Map optional reasoning column
                if reasoning_col:
                    df_mapped['ICP_Reasoning'] = df[reasoning_col]
                else:
                    df_mapped['ICP_Reasoning'] = ''

                df_mapped['ICP_score'] = pd.to_numeric(df_mapped['ICP_score'], errors='coerce')
                df_mapped = df_mapped.dropna(subset=['ICP_score'])
                df_mapped['CXP_Swat_Tier'] = df_mapped['CXP_Swat_Tier'].fillna('')

                st.session_state.accounts_df = df_mapped
                st.success(f"✅ Loaded {len(df_mapped)} accounts")

                st.subheader("Preview")
                st.dataframe(df_mapped[['Account_Name', 'Account_ID', 'ICP_score', 'CXP_Swat_Tier']].head(10), use_container_width=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(df_mapped))
                with col2:
                    t1 = (df_mapped['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
                    st.metric("Tier 1", t1)
                with col3:
                    t2 = (df_mapped['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
                    st.metric("Tier 2", t2)
                with col4:
                    unranked = len(df_mapped) - t1 - t2
                    st.metric("Unranked", unranked)

                if st.button("➡️ Next: Setup", type="primary"):
                    st.session_state.stage = 'setup'
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# =============================================================================
# STAGE 2: SETUP
# =============================================================================
elif st.session_state.stage == 'setup':
    st.header("⚙️ Step 2: Configure Draft")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Enter AE Names")
        st.markdown("Quick start: Use the default team or paste AE names (one per line):")
        
        # Default AEs button
        if st.button("📋 Use Default Team (Alexa Pass, Lindsay Kelvie, Paul Kellum, Travis Pederson)", use_container_width=True, key="default_aes"):
            st.session_state.ae_list = list(AE_SFDC_IDS.keys())
            st.rerun()
        
        ae_input = st.text_area(
            "AE Names",
            value='\n'.join(st.session_state.ae_list) if st.session_state.ae_list else "",
            height=120,
            label_visibility="collapsed"
        )
        
        if ae_input:
            ae_list = [line.strip() for line in ae_input.split('\n') if line.strip()]
            st.session_state.ae_list = ae_list
            for ae in ae_list:
                if ae not in st.session_state.ae_books:
                    st.session_state.ae_books[ae] = []
            st.success(f"✅ {len(ae_list)} AEs ready")

    with col2:
        st.subheader("Settings")
        draft_type = st.radio("Draft Type", ["Snake", "Linear"])
        st.session_state.is_snake = (draft_type == "Snake")
        
        st.session_state.accounts_per_ae = st.number_input(
            "Accounts per AE",
            min_value=1,
            max_value=100,
            value=st.session_state.accounts_per_ae
        )

    st.markdown("---")

    if st.session_state.ae_list and len(st.session_state.ae_list) >= 2:
        if st.button("🎲 Generate Draft Order & Continue", type="primary", use_container_width=True):
            st.session_state.draft_order = np.random.permutation(st.session_state.ae_list).tolist()
            accounts_list = st.session_state.accounts_df.to_dict('records')
            st.session_state.available_accounts = sort_accounts_by_tier(accounts_list)
            st.session_state.draft_picks = []
            st.session_state.current_pick = 0
            st.session_state.stage = 'cleanup'
            st.rerun()
    else:
        st.warning("⚠️ Enter at least 2 AEs")

# =============================================================================
# STAGE 3: BLACKLIST (OPTIONAL)
# =============================================================================
elif st.session_state.stage == 'cleanup':
    st.header("🚫 Step 3: Blacklist Accounts (Optional)")
    st.markdown("Review top 50 accounts and exclude any with poor data quality. Or skip to start drafting immediately.")

    # SKIP BUTTON AT TOP
    if st.button("⏭️ Skip Blacklist → Start Draft", type="primary", use_container_width=True):
        st.session_state.stage = 'draft'
        st.rerun()
    
    st.markdown("---")

    st.info(f"**Draft Order:** {' → '.join(st.session_state.draft_order)}")
    st.metric("Available Accounts", len(st.session_state.available_accounts))

    st.markdown("---")

    available_df = pd.DataFrame(st.session_state.available_accounts)
    display_df = available_df[['Account_Name', 'Account_ID', 'ICP_score', 'CXP_Swat_Tier']].head(50).copy()
    display_df['Remove'] = False

    st.subheader("Top 50 Accounts (Optional Blacklist)")
    st.caption("Check accounts to remove from draft, or skip this step entirely.")
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        column_config={'Remove': st.column_config.CheckboxColumn("Blacklist?")},
        hide_index=True
    )

    for idx, row in edited_df.iterrows():
        if row['Remove']:
            st.session_state.blacklisted_accounts.add(row['Account_ID'])

    st.session_state.available_accounts = [
        acc for acc in st.session_state.available_accounts
        if acc['Account_ID'] not in st.session_state.blacklisted_accounts
    ]

    st.metric("Blacklisted", len(st.session_state.blacklisted_accounts))

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.stage = 'setup'
            st.rerun()
    with col2:
        if st.button("⏭️ Skip", use_container_width=True):
            st.session_state.stage = 'draft'
            st.rerun()
    with col3:
        if st.button("▶️ Start Draft", type="primary", use_container_width=True):
            st.session_state.stage = 'draft'
            st.rerun()

# =============================================================================
# STAGE 4: LIVE DRAFT - SLEEPER/YAHOO STYLE
# =============================================================================
elif st.session_state.stage == 'draft':
    st.header("🎯 Live Draft")

    num_aes = len(st.session_state.ae_list)
    total_picks = num_aes * st.session_state.accounts_per_ae
    current_pick = st.session_state.current_pick
    current_round = (current_pick // num_aes) + 1
    current_ae = get_current_ae()

    # TOP STATUS BAR - Professional layout with better hierarchy
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #1f77b4;">🔴 {current_ae if current_ae else 'TBD'} is Picking</h3>
                <p style="margin: 5px 0; color: #555; font-size: 14px;">Round {current_round} • Pick {current_pick + 1} of {total_picks}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; font-size: 24px; font-weight: bold; color: #1f77b4;">{len(st.session_state.available_accounts)}</p>
                <p style="margin: 5px 0; color: #555; font-size: 14px;">Accounts Available</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if current_pick < total_picks and len(st.session_state.available_accounts) > 0:
        
        # MAIN DRAFT BOARD
        col_board, col_sidebar = st.columns([3, 1])
        
        # ===== LEFT: MAIN BOARD =====
        with col_board:
            st.subheader("📋 Available Accounts", divider="blue")
            
            # SEARCH BOX
            search_query = st.text_input(
                "🔍 Search by name or ID",
                placeholder="e.g., 'Shapellx' or '001Vr000'",
                label_visibility="collapsed"
            )
            
            # FILTER TABS - with better styling
            available_df = pd.DataFrame(st.session_state.available_accounts)
            
            # Apply search first if provided
            if search_query:
                search_lower = search_query.lower()
                search_df = available_df[
                    (available_df['Account_Name'].str.lower().str.contains(search_lower, na=False)) |
                    (available_df['Account_ID'].str.lower().str.contains(search_lower, na=False))
                ]
            else:
                search_df = available_df
            
            tier1_count = (search_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
            tier2_count = (search_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
            unranked_count = len(search_df) - tier1_count - tier2_count
            
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4, gap="small")
            
            with filter_col1:
                if st.button(f"📊 All ({len(search_df)})", use_container_width=True, key="filter_all"):
                    st.session_state.filter_tier = 'all'
            with filter_col2:
                if st.button(f"🟡 Tier 1 ({tier1_count})", use_container_width=True, key="filter_t1"):
                    st.session_state.filter_tier = 'tier1'
            with filter_col3:
                if st.button(f"🟢 Tier 2 ({tier2_count})", use_container_width=True, key="filter_t2"):
                    st.session_state.filter_tier = 'tier2'
            with filter_col4:
                if st.button(f"⚪ Unranked ({unranked_count})", use_container_width=True, key="filter_unr"):
                    st.session_state.filter_tier = 'unranked'
            
            st.markdown("---")
            
            # Apply tier filter on top of search
            if st.session_state.filter_tier == 'tier1':
                filtered_df = search_df[search_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)]
            elif st.session_state.filter_tier == 'tier2':
                filtered_df = search_df[search_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)]
            elif st.session_state.filter_tier == 'unranked':
                filtered_df = search_df[
                    (search_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False) == False) &
                    (search_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False) == False)
                ]
            else:
                filtered_df = search_df
            
            # Show first N accounts (growing with Load More button)
            display_df = filtered_df.head(st.session_state.accounts_shown)
            
            # Info message
            if search_query:
                st.caption(f"🔍 Found {len(filtered_df)} account(s) matching '{search_query}'")
            if len(filtered_df) > st.session_state.accounts_shown:
                st.caption(f"📌 Showing {len(display_df)} of {len(filtered_df)} accounts")
            
            # ACCOUNT TABLE with clickable draft buttons - improved connection
            for idx, (_, acc) in enumerate(display_df.iterrows()):
                badge = tier_badge(acc['CXP_Swat_Tier'])
                tier_text = tier_name(acc['CXP_Swat_Tier'])
                
                # Account header with pick button in same row
                col_rank, col_info, col_button = st.columns([0.5, 4, 1.2], gap="small")
                
                with col_rank:
                    st.markdown(f"<span style='font-size: 16px; font-weight: bold; color: #1f77b4;'>{idx + 1}</span>", unsafe_allow_html=True)
                
                with col_info:
                    st.markdown(f"{badge} **{acc['Account_Name']}**")
                    st.caption(f"Score: {acc['ICP_score']:.0f} | {tier_text} | ID: {acc['Account_ID']}")
                
                with col_button:
                    if st.button(f"📍 PICK", key=f"draft_{idx}_{acc['Account_ID']}", use_container_width=True):
                        st.session_state.draft_picks.append({
                            'pick_number': current_pick + 1,
                            'round': current_round,
                            'ae': current_ae,
                            'account_name': acc['Account_Name'],
                            'account_id': acc['Account_ID'],
                            'icp_score': acc['ICP_score'],
                            'tier': acc.get('CXP_Swat_Tier', '')
                        })
                        st.session_state.ae_books[current_ae].append(acc['Account_ID'])
                        st.session_state.available_accounts = [
                            a for a in st.session_state.available_accounts
                            if a['Account_ID'] != acc['Account_ID']
                        ]
                        st.session_state.current_pick += 1
                        st.rerun()
                
                # Show ICP reasoning if available
                if acc.get('ICP_Reasoning', ''):
                    st.caption(f"💡 {acc['ICP_Reasoning']}")
                
                st.divider()
            
            # Load More button if there are more accounts
            if len(filtered_df) > st.session_state.accounts_shown:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button(f"📂 Load More ({len(filtered_df) - st.session_state.accounts_shown} remaining)", use_container_width=True):
                        st.session_state.accounts_shown += 50
                        st.rerun()
        
        # ===== RIGHT SIDEBAR =====
        with col_sidebar:
            # ON THE CLOCK - Show upcoming picks
            st.subheader("🕐 On the Clock", divider="orange")
            
            next_picks_count = 0
            for upcoming_pick_num in range(current_pick, min(current_pick + 10, total_picks)):
                if next_picks_count >= 5:  # Show next 5
                    break
                
                upcoming_round = (upcoming_pick_num // num_aes) + 1
                pick_in_round = upcoming_pick_num % num_aes
                
                if st.session_state.is_snake and upcoming_round % 2 == 0:
                    ae_idx = num_aes - 1 - pick_in_round
                else:
                    ae_idx = pick_in_round
                
                upcoming_ae = st.session_state.draft_order[ae_idx]
                is_now = (upcoming_pick_num == current_pick)
                
                if is_now:
                    st.markdown(f"**🔴 NOW: #{upcoming_pick_num + 1} {upcoming_ae}** (Rd {upcoming_round})")
                else:
                    st.markdown(f"→ #{upcoming_pick_num + 1} {upcoming_ae} (Rd {upcoming_round})")
                
                next_picks_count += 1
            
            st.markdown("---")
            st.subheader("📚 Roster", divider="blue")
            
            if current_ae and current_ae in st.session_state.ae_books:
                ae_ids = st.session_state.ae_books[current_ae]
                
                # Metrics with better styling
                col_picks, col_avg = st.columns(2)
                with col_picks:
                    st.metric("Picks", len(ae_ids))
                with col_avg:
                    ae_book_df = st.session_state.accounts_df[
                        st.session_state.accounts_df['Account_ID'].isin(ae_ids)
                    ].sort_values('ICP_score', ascending=False)
                    if len(ae_book_df) > 0:
                        st.metric("Avg", f"{ae_book_df['ICP_score'].mean():.0f}")
                
                # Drafted accounts list
                if len(ae_book_df) > 0:
                    st.markdown("**Recently Drafted:**")
                    for _, row in ae_book_df.head(5).iterrows():
                        badge = tier_badge(row['CXP_Swat_Tier'])
                        st.markdown(f"  {badge} {row['Account_Name'][:18]} — {row['ICP_score']:.0f}")
                    
                    if len(ae_book_df) > 5:
                        st.caption(f"...and {len(ae_book_df) - 5} more")
            
            st.markdown("---")
            st.subheader("⚡ Quick Actions", divider="orange")
            
            col_undo, col_auto = st.columns(2)
            with col_undo:
                if current_pick > 0 and st.button("↩️ Undo", use_container_width=True):
                    last = st.session_state.draft_picks.pop()
                    st.session_state.ae_books[last['ae']].remove(last['account_id'])
                    undo_acc = st.session_state.accounts_df[
                        st.session_state.accounts_df['Account_ID'] == last['account_id']
                    ].iloc[0].to_dict()
                    st.session_state.available_accounts.insert(0, undo_acc)
                    st.session_state.available_accounts = sort_accounts_by_tier(st.session_state.available_accounts)
                    st.session_state.current_pick -= 1
                    st.rerun()
            
            with col_auto:
                if st.button("⚡ Auto-Best", use_container_width=True):
                    best = st.session_state.available_accounts[0]
                    st.session_state.draft_picks.append({
                        'pick_number': current_pick + 1,
                        'round': current_round,
                        'ae': current_ae,
                        'account_name': best['Account_Name'],
                        'account_id': best['Account_ID'],
                        'icp_score': best['ICP_score'],
                        'tier': best.get('CXP_Swat_Tier', '')
                    })
                    st.session_state.ae_books[current_ae].append(best['Account_ID'])
                    st.session_state.available_accounts.pop(0)
                    st.session_state.current_pick += 1
                    st.rerun()
        
        st.markdown("---")
        
        # ACTION BUTTONS AT BOTTOM
        st.markdown("### ⚙️ Draft Control")
        col_done, col_complete = st.columns(2, gap="small")
        with col_done:
            if st.button("🏁 Done Picking", use_container_width=True, help="Finish manual picks and review auto-complete"):
                st.session_state.stage = 'autocomplete'
                st.rerun()
        
        with col_complete:
            remaining = total_picks - current_pick
            if st.button(f"🤖 Auto-Complete All {remaining}", type="primary", use_container_width=True, help="Simulate remaining picks instantly"):
                with st.spinner(f"Auto-drafting {remaining} accounts..."):
                    temp_pick = current_pick
                    temp_available = st.session_state.available_accounts.copy()

                    while temp_pick < total_picks and len(temp_available) > 0:
                        round_num = (temp_pick // num_aes) + 1
                        pick_in_round = temp_pick % num_aes

                        if st.session_state.is_snake and round_num % 2 == 0:
                            ae_idx = num_aes - 1 - pick_in_round
                        else:
                            ae_idx = pick_in_round

                        ae = st.session_state.draft_order[ae_idx]
                        best = temp_available[0]

                        st.session_state.draft_picks.append({
                            'pick_number': temp_pick + 1,
                            'round': round_num,
                            'ae': ae,
                            'account_name': best['Account_Name'],
                            'account_id': best['Account_ID'],
                            'icp_score': best['ICP_score'],
                            'tier': best.get('CXP_Swat_Tier', '')
                        })
                        st.session_state.ae_books[ae].append(best['Account_ID'])
                        temp_available.pop(0)
                        temp_pick += 1

                    st.session_state.available_accounts = temp_available
                    st.session_state.current_pick = temp_pick
                    st.success(f"✅ Auto-drafted {temp_pick - current_pick} accounts!")
                    
                st.session_state.stage = 'results'
                st.rerun()
        
        st.markdown("---")
        if len(st.session_state.available_accounts) == 0:
            st.warning("❌ No more accounts available!")
        if current_pick >= total_picks:
            st.success("✅ All manual picks complete!")
        
        st.markdown("---")
        
        # DRAFT PICKS STREAM - Show all picks organized by round
        st.subheader("📜 Draft History", divider="gray")
        
        if st.session_state.draft_picks:
            # Group picks by round
            picks_by_round = {}
            for pick in st.session_state.draft_picks:
                round_num = pick['round']
                if round_num not in picks_by_round:
                    picks_by_round[round_num] = []
                picks_by_round[round_num].append(pick)
            
            # Display rounds in reverse order (most recent at top)
            for round_num in sorted(picks_by_round.keys(), reverse=True):
                round_picks = picks_by_round[round_num]
                is_current = (round_num == current_round)
                round_label = f"Round {round_num}" + (" ← Currently Picking" if is_current else "")
                
                with st.expander(f"**{round_label}** ({len(round_picks)} picks)", expanded=is_current):
                    for pick in round_picks:
                        badge = tier_badge(pick['tier'])
                        st.markdown(
                            f"**#{pick['pick_number']}** {pick['ae']:15} — {badge} {pick['account_name']} **{pick['icp_score']:.0f}**"
                        )
        else:
            st.info("📭 No picks yet - draft starting soon!")
        
        if st.button("▶️ Go to Results"):
            st.session_state.stage = 'results'
            st.rerun()

# =============================================================================
# STAGE 4B: AUTO-COMPLETE (kept for flow, but can be skipped)
# =============================================================================
elif st.session_state.stage == 'autocomplete':
    st.header("🤖 Auto-Complete Remaining Picks")
    
    num_aes = len(st.session_state.ae_list)
    total_picks = num_aes * st.session_state.accounts_per_ae
    current_pick = st.session_state.current_pick
    remaining = total_picks - current_pick
    available = len(st.session_state.available_accounts)

    st.info(f"**{remaining} picks remaining** | **{available} accounts available**")
    
    st.markdown("---")
    
    if st.button("✅ Auto-Complete Draft", type="primary", use_container_width=True):
        with st.spinner(f"Auto-drafting {remaining} picks..."):
            temp_pick = current_pick
            temp_available = st.session_state.available_accounts.copy()

            while temp_pick < total_picks and len(temp_available) > 0:
                round_num = (temp_pick // num_aes) + 1
                pick_in_round = temp_pick % num_aes

                if st.session_state.is_snake and round_num % 2 == 0:
                    ae_idx = num_aes - 1 - pick_in_round
                else:
                    ae_idx = pick_in_round

                ae = st.session_state.draft_order[ae_idx]
                best = temp_available[0]

                st.session_state.draft_picks.append({
                    'pick_number': temp_pick + 1,
                    'round': round_num,
                    'ae': ae,
                    'account_name': best['Account_Name'],
                    'account_id': best['Account_ID'],
                    'icp_score': best['ICP_score'],
                    'tier': best.get('CXP_Swat_Tier', '')
                })
                st.session_state.ae_books[ae].append(best['Account_ID'])
                temp_available.pop(0)
                temp_pick += 1

            st.session_state.available_accounts = temp_available
            st.session_state.current_pick = temp_pick
            st.success(f"✅ Auto-drafted {temp_pick - current_pick} picks!")
            
        st.session_state.stage = 'results'
        st.rerun()
    
    if st.button("⬅️ Back to Draft"):
        st.session_state.stage = 'draft'
        st.rerun()

# =============================================================================
# STAGE 5: RESULTS
# =============================================================================
elif st.session_state.stage == 'results':
    st.header("📊 Draft Results")

    df = st.session_state.accounts_df

    results = []
    for ae in st.session_state.ae_list:
        ae_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_ids)]
        
        tier1 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
        tier2 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
        
        results.append({
            'AE': ae,
            'Total': len(ae_accounts),
            'Tier 1': tier1,
            'Tier 2': tier2,
            'Avg Score': ae_accounts['ICP_score'].mean() if len(ae_accounts) > 0 else 0,
            'Total Score': ae_accounts['ICP_score'].sum() if len(ae_accounts) > 0 else 0,
        })

    results_df = pd.DataFrame(results).sort_values('Avg Score', ascending=False)

    st.subheader("🏆 Final Standings")
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("📚 Account Books")
    for ae in st.session_state.ae_list:
        ae_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_ids)].sort_values('ICP_score', ascending=False)
        avg = ae_accounts['ICP_score'].mean() if len(ae_accounts) > 0 else 0
        t1 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
        t2 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()

        with st.expander(f"**{ae}** - {len(ae_accounts)} accounts | Avg: {avg:.0f} | T1: {t1} | T2: {t2}"):
            display_cols = ['Account_Name', 'ICP_score', 'CXP_Swat_Tier']
            if 'ICP_Reasoning' in ae_accounts.columns:
                display_cols.append('ICP_Reasoning')
            
            st.dataframe(
                ae_accounts[display_cols],
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")
    st.subheader("📜 Draft History")
    if st.session_state.draft_picks:
        picks_df = pd.DataFrame(st.session_state.draft_picks)
        st.dataframe(picks_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💾 Export")

    col1, col2 = st.columns(2)

    with col1:
        export_data = []
        for ae in st.session_state.ae_list:
            ae_ids = st.session_state.ae_books[ae]
            ae_accounts = df[df['Account_ID'].isin(ae_ids)]
            # Get Salesforce ID for this AE (if it exists in our mapping)
            ae_sfdc_id = AE_SFDC_IDS.get(ae, '')
            for _, row in ae_accounts.iterrows():
                export_data.append({
                    'Account_ID': row['Account_ID'],
                    'Account_Name': row['Account_Name'],
                    'New_Owner': ae,
                    'Owner_SFDC_ID': ae_sfdc_id,
                    'ICP_Score': row['ICP_score'],
                    'CXP_Swat_Tier': row['CXP_Swat_Tier']
                })
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Assignments (with SFDC IDs)",
            data=csv,
            file_name=f"draft_assignments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col2:
        if st.session_state.draft_picks:
            draft_csv = pd.DataFrame(st.session_state.draft_picks).to_csv(index=False)
            st.download_button(
                label="📥 Download History",
                data=draft_csv,
                file_name=f"draft_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    st.markdown("---")
    if st.button("🔄 New Draft"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
