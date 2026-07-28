import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Page config
st.set_page_config(page_title="GTM Fantasy Draft", layout="wide", page_icon="🏈")

# Header
st.title("🏈 GTM Fantasy Draft")
st.markdown("*Territory planning made fun - draft your accounts like fantasy football*")

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
if 'pick_start_time' not in st.session_state:
    st.session_state.pick_start_time = None
if 'timer_seconds' not in st.session_state:
    st.session_state.timer_seconds = 30
if 'selected_account_idx' not in st.session_state:
    st.session_state.selected_account_idx = None
if 'filter_tier' not in st.session_state:
    st.session_state.filter_tier = 'all'

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

# Sidebar navigation
with st.sidebar:
    st.header("Draft Status")
    
    if st.session_state.accounts_df is not None:
        st.success(f"✅ Loaded: {len(st.session_state.accounts_df)} accounts")
    
    if st.session_state.stage in ['draft', 'results']:
        st.success(f"✅ {len(st.session_state.ae_list)} AEs")
        st.info(f"📊 {'Snake' if st.session_state.is_snake else 'Linear'} Draft")
        if st.session_state.current_pick > 0:
            st.metric("Current Pick", f"{st.session_state.current_pick} of {len(st.session_state.ae_list) * st.session_state.accounts_per_ae}")
    
    st.markdown("---")
    st.markdown("**Stage:**")
    stages = {
        'upload': '1️⃣ Upload CSV',
        'setup': '2️⃣ Setup',
        'cleanup': '3️⃣ Blacklist',
        'draft': '4️⃣ Live Draft',
        'results': '5️⃣ Results'
    }
    for key, label in stages.items():
        if st.session_state.stage == key:
            st.markdown(f"**→ {label}**")
        else:
            st.markdown(f"   {label}")

# =============================================================================
# STAGE 1: CSV UPLOAD
# =============================================================================
if st.session_state.stage == 'upload':
    st.header("📁 Step 1: Upload Account Data")

    st.markdown("""
    Upload your SWAT accounts CSV. Required columns:
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
# STAGE 2: SETUP (AEs + DRAFT ORDER)
# =============================================================================
elif st.session_state.stage == 'setup':
    st.header("⚙️ Step 2: Configure Draft")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Enter AE Names")
        st.markdown("Paste AE names (one per line):")
        ae_input = st.text_area(
            "AE Names",
            value='\n'.join(st.session_state.ae_list) if st.session_state.ae_list else "",
            height=150,
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
        draft_type = st.radio("Type", ["Snake", "Linear"])
        st.session_state.is_snake = (draft_type == "Snake")
        
        st.session_state.accounts_per_ae = st.number_input(
            "Accounts per AE",
            min_value=1,
            max_value=100,
            value=st.session_state.accounts_per_ae
        )
        
        st.session_state.timer_seconds = st.number_input(
            "Timer (seconds)",
            min_value=10,
            max_value=120,
            value=30
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
# STAGE 3: BLACKLIST CLEANUP
# =============================================================================
elif st.session_state.stage == 'cleanup':
    st.header("🚫 Step 3: Blacklist Accounts")
    st.markdown("Review and exclude any accounts with poor data quality before draft starts.")

    st.info(f"**Draft Order:** {' → '.join(st.session_state.draft_order)}")
    st.metric("Available Accounts", len(st.session_state.available_accounts))

    st.markdown("---")

    available_df = pd.DataFrame(st.session_state.available_accounts)
    display_df = available_df[['Account_Name', 'Account_ID', 'ICP_score', 'CXP_Swat_Tier']].head(50).copy()
    display_df['Remove'] = False

    st.subheader("Top 50 Accounts - Check to Blacklist")
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.stage = 'setup'
            st.rerun()
    with col2:
        if st.button("▶️ Start Draft", type="primary", use_container_width=True):
            st.session_state.stage = 'draft'
            st.session_state.pick_start_time = datetime.now()
            st.rerun()

# =============================================================================
# STAGE 4: LIVE DRAFT
# =============================================================================
elif st.session_state.stage == 'draft':
    st.header("🎯 Live Draft - Pick from the Board")

    num_aes = len(st.session_state.ae_list)
    total_picks = num_aes * st.session_state.accounts_per_ae
    current_pick = st.session_state.current_pick

    current_round = (current_pick // num_aes) + 1
    current_ae = get_current_ae()

    # Top status bar
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pick", f"{current_pick + 1}/{total_picks}")
    with col2:
        st.metric("Round", current_round)
    with col3:
        st.metric("Current AE", current_ae if current_ae else "N/A")
    with col4:
        st.metric("Available", len(st.session_state.available_accounts))

    st.markdown("---")

    if current_pick < total_picks and len(st.session_state.available_accounts) > 0:
        
        # TIMER SECTION with auto-draft
        timer_placeholder = st.empty()
        time_is_up = False
        
        if st.session_state.pick_start_time is None:
            st.session_state.pick_start_time = datetime.now()
        
        elapsed = (datetime.now() - st.session_state.pick_start_time).total_seconds()
        remaining = max(0, st.session_state.timer_seconds - elapsed)
        
        # Display timer
        if remaining > 10:
            timer_color = "green"
        elif remaining > 5:
            timer_color = "orange"
        else:
            timer_color = "red"
        
        timer_placeholder.markdown(
            f"<h2 style='text-align: center; color: {timer_color};'>⏱️ {int(remaining)} seconds</h2>",
            unsafe_allow_html=True
        )
        
        # If time expired, auto-draft best
        if remaining <= 0:
            with st.spinner("⏰ Time expired - auto-drafting best available..."):
                time.sleep(0.5)
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
                st.session_state.pick_start_time = None
                st.rerun()
        
        st.markdown("---")

        # DRAFT BOARD with FILTERS
        st.subheader("📋 Available Accounts")
        
        # Filter tabs
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        available_df = pd.DataFrame(st.session_state.available_accounts)
        
        with filter_col1:
            if st.button(f"📊 All ({len(available_df)})"):
                st.session_state.filter_tier = 'all'
        with filter_col2:
            tier1_count = (available_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
            if st.button(f"🟡 Tier 1 ({tier1_count})"):
                st.session_state.filter_tier = 'tier1'
        with filter_col3:
            tier2_count = (available_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
            if st.button(f"🟢 Tier 2 ({tier2_count})"):
                st.session_state.filter_tier = 'tier2'
        with filter_col4:
            unranked_count = ((available_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False) == False) & 
                            (available_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False) == False)).sum()
            if st.button(f"⚪ Unranked ({unranked_count})"):
                st.session_state.filter_tier = 'unranked'
        
        # Apply filter
        if st.session_state.filter_tier == 'tier1':
            filtered_df = available_df[available_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)]
        elif st.session_state.filter_tier == 'tier2':
            filtered_df = available_df[available_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)]
        elif st.session_state.filter_tier == 'unranked':
            filtered_df = available_df[
                (available_df['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False) == False) &
                (available_df['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False) == False)
            ]
        else:
            filtered_df = available_df
        
        st.info(f"Showing {len(filtered_df)} accounts")
        
        st.markdown("---")
        
        # Display as expandable cards with reasoning
        for idx, acc in filtered_df.iterrows():
            badge = tier_badge(acc['CXP_Swat_Tier'])
            col_title, col_draft = st.columns([4, 1])
            
            with col_title:
                with st.expander(f"{badge} {acc['Account_Name']} — Score: {acc['ICP_score']:.0f}"):
                    st.write(f"**Account ID:** {acc['Account_ID']}")
                    st.write(f"**Tier:** {acc['CXP_Swat_Tier']}")
                    st.write(f"**Score:** {acc['ICP_score']:.0f}")
                    
                    if acc.get('ICP_Reasoning', ''):
                        st.write(f"**Reasoning:** {acc['ICP_Reasoning']}")
            
            with col_draft:
                # Draft button next to account name
                if st.button(f"📍 Draft", key=f"draft_{acc['Account_ID']}"):
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
                    st.session_state.pick_start_time = None
                    st.rerun()

        st.markdown("---")

        # Quick action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⚡ Auto-Draft Best"):
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
                st.session_state.pick_start_time = None
                st.rerun()
        
        with col2:
            if current_pick > 0 and st.button("↩️ Undo"):
                last = st.session_state.draft_picks.pop()
                st.session_state.ae_books[last['ae']].remove(last['account_id'])
                undo_acc = st.session_state.accounts_df[
                    st.session_state.accounts_df['Account_ID'] == last['account_id']
                ].iloc[0].to_dict()
                st.session_state.available_accounts.insert(0, undo_acc)
                st.session_state.available_accounts = sort_accounts_by_tier(st.session_state.available_accounts)
                st.session_state.current_pick -= 1
                st.session_state.pick_start_time = None
                st.rerun()
        
        with col3:
            if st.button("🏁 Done Picking", use_container_width=True):
                st.session_state.stage = 'autocomplete'
                st.rerun()

        st.markdown("---")
        st.subheader("📜 Recent Picks")
        recent = st.session_state.draft_picks[-5:][::-1]
        for pick in recent:
            st.write(f"**Pick {pick['pick_number']}** — {pick['ae']} → {pick['account_name']} ({pick['icp_score']:.0f})")

    else:
        if len(st.session_state.available_accounts) == 0:
            st.warning("No more accounts available!")
        if current_pick >= total_picks:
            st.success("All manual picks complete!")
        
        if st.button("▶️ Done - Go to Results"):
            st.session_state.stage = 'results'
            st.rerun()

# =============================================================================
# STAGE 4B: AUTO-COMPLETE
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
    
    st.subheader("Auto-draft summary:")
    st.write(f"Will auto-draft the best available accounts (sorted by Tier + Score) until draft is complete or accounts run out.")
    
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
            
            time.sleep(1)
            st.session_state.stage = 'results'
            st.rerun()
    
    if st.button("⬅️ Back to Draft"):
        st.session_state.stage = 'draft'
        st.session_state.pick_start_time = None
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
            for _, row in ae_accounts.iterrows():
                export_data.append({
                    'Account_ID': row['Account_ID'],
                    'Account_Name': row['Account_Name'],
                    'New_Owner': ae,
                    'ICP_Score': row['ICP_score'],
                    'CXP_Swat_Tier': row['CXP_Swat_Tier']
                })
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Assignments",
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
