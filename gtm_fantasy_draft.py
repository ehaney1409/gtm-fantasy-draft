import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random

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
if 'draft_complete' not in st.session_state:
    st.session_state.draft_complete = False

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tier_rank(tier_value):
    """Return numeric rank for sorting (higher = better)"""
    if pd.isna(tier_value) or tier_value == '':
        return 0  # Unranked
    tier_str = str(tier_value).lower()
    if 'tier 1' in tier_str:
        return 2
    elif 'tier 2' in tier_str:
        return 1
    return 0

def sort_accounts(accounts_list):
    """Sort accounts by Tier (1 > 2 > Unranked), then by ICP Score (descending)"""
    return sorted(
        accounts_list,
        key=lambda x: (-get_tier_rank(x.get('CXP_Swat_Tier')), -x.get('ICP_score', 0))
    )

def generate_draft_order(ae_list, is_snake=True):
    """Generate draft order (randomized, optionally snake)"""
    order = ae_list.copy()
    random.shuffle(order)
    return order

def get_current_ae():
    """Determine which AE is picking"""
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

# Sidebar navigation / status
with st.sidebar:
    st.header("Draft Settings")

    if st.session_state.accounts_df is not None:
        st.success(f"✅ CSV Loaded: {len(st.session_state.accounts_df)} accounts")

    if st.session_state.stage in ['draft', 'results']:
        st.success(f"✅ {len(st.session_state.ae_list)} AEs in draft")
        st.info(f"📊 Draft Type: {'Snake' if st.session_state.is_snake else 'Linear'}")

    st.markdown("---")
    st.markdown("**Current Stage:**")
    stages = {
        'upload': '1️⃣ Upload CSV',
        'setup': '2️⃣ AE Input',
        'blacklist': '3️⃣ Blacklist Accounts',
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
    Upload a CSV file with your SWAT accounts data. Required columns:
    - **Company name** - Account Name
    - **Salesforce ID** - Account ID
    - **ICP score** - Account Score (numeric)
    - **CXP Swat Tier** - Tier classification (Tier 1, Tier 2, or blank/unranked)
    """)

    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.replace(' ', '_')

            st.subheader("🔗 Map Your Columns")
            st.markdown("Match your CSV columns to the required fields:")

            available_columns = [''] + df.columns.tolist()

            col1, col2 = st.columns(2)
            with col1:
                account_name_col = st.selectbox(
                    "Account Name *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'company' in c.lower() and 'name' in c.lower()), 0)
                )
                account_id_col = st.selectbox(
                    "Account ID *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'salesforce' in c.lower() and 'id' in c.lower()), 0)
                )
            with col2:
                account_score_col = st.selectbox(
                    "Account Score (ICP) *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'icp' in c.lower() and 'score' in c.lower()), 0)
                )
                tier_col = st.selectbox(
                    "Swat Tier *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'cxp' in c.lower() and 'tier' in c.lower()), 0)
                )

            required_fields = {
                'Account_Name': account_name_col,
                'Account_ID': account_id_col,
                'ICP_score': account_score_col,
                'CXP_Swat_Tier': tier_col
            }
            missing = [k for k, v in required_fields.items() if not v]

            if missing:
                st.warning(f"⚠️ Please map all required fields: {', '.join(missing)}")
            else:
                df_mapped = df.copy()
                for standard_name, user_col in required_fields.items():
                    df_mapped[standard_name] = df[user_col]

                # Convert score to numeric and handle null tiers
                df_mapped['ICP_score'] = pd.to_numeric(df_mapped['ICP_score'], errors='coerce')
                df_mapped = df_mapped.dropna(subset=['ICP_score'])
                
                # Treat empty/NaN tiers as unranked (keep them, don't drop)
                df_mapped['CXP_Swat_Tier'] = df_mapped['CXP_Swat_Tier'].fillna('')

                st.session_state.accounts_df = df_mapped

                st.success(f"✅ Successfully loaded {len(df_mapped)} accounts!")

                st.subheader("Data Preview")
                preview_cols = ['Account_Name', 'Account_ID', 'ICP_score', 'CXP_Swat_Tier']
                st.dataframe(df_mapped[preview_cols].head(15), use_container_width=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Accounts", len(df_mapped))
                with col2:
                    tier1_count = (df_mapped['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
                    st.metric("Tier 1", tier1_count)
                with col3:
                    tier2_count = (df_mapped['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
                    st.metric("Tier 2", tier2_count)
                with col4:
                    unranked = len(df_mapped) - tier1_count - tier2_count
                    st.metric("Unranked", unranked)

                if st.button("➡️ Proceed to AE Input", type="primary"):
                    st.session_state.stage = 'setup'
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")

# =============================================================================
# STAGE 2: AE INPUT & DRAFT ORDER GENERATION
# =============================================================================
elif st.session_state.stage == 'setup':
    st.header("⚙️ Step 2: Enter AE Names & Generate Draft Order")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Add AEs to Draft")
        st.markdown("Enter the names of AEs who will participate. Add one per line:")
        
        ae_input = st.text_area(
            "AE Names (one per line)",
            value='\n'.join(st.session_state.ae_list) if st.session_state.ae_list else "",
            height=200,
            label_visibility="collapsed"
        )
        
        if ae_input:
            ae_list = [line.strip() for line in ae_input.split('\n') if line.strip()]
            st.session_state.ae_list = ae_list
            
            st.success(f"✅ {len(ae_list)} AEs ready to draft")
            
            # Initialize AE books
            for ae in ae_list:
                if ae not in st.session_state.ae_books:
                    st.session_state.ae_books[ae] = []

    with col2:
        st.subheader("Draft Settings")
        
        draft_type = st.radio("Draft Type", ["Snake", "Linear"])
        st.session_state.is_snake = (draft_type == "Snake")
        
        st.session_state.accounts_per_ae = st.number_input(
            "Target accounts per AE",
            min_value=1,
            max_value=100,
            value=st.session_state.accounts_per_ae
        )
        
        st.session_state.timer_seconds = st.number_input(
            "Seconds per pick",
            min_value=10,
            max_value=120,
            value=30
        )

    st.markdown("---")

    if st.session_state.ae_list and len(st.session_state.ae_list) >= 2:
        if st.button("🎲 Generate Draft Order", type="primary", use_container_width=True):
            st.session_state.draft_order = generate_draft_order(
                st.session_state.ae_list,
                st.session_state.is_snake
            )
            
            # Populate available accounts (sorted by tier + score)
            accounts_list = st.session_state.accounts_df.to_dict('records')
            st.session_state.available_accounts = sort_accounts(accounts_list)
            
            # Reset draft state
            st.session_state.draft_picks = []
            st.session_state.current_pick = 0
            st.session_state.pick_start_time = None
            
            st.session_state.stage = 'blacklist'
            st.rerun()
    else:
        st.warning("⚠️ Please enter at least 2 AEs to generate draft order")

# =============================================================================
# STAGE 3: BLACKLIST / PRE-DRAFT CLEANUP
# =============================================================================
elif st.session_state.stage == 'blacklist':
    st.header("🚫 Step 3: Blacklist Poor-Quality Accounts")
    st.markdown(
        "Review the top accounts and blacklist any with data quality issues. "
        "Blacklisted accounts will be excluded from the draft."
    )

    st.subheader(f"Draft Order: {' → '.join(st.session_state.draft_order)}")
    st.info(f"Total accounts available: {len(st.session_state.available_accounts)}")

    st.markdown("---")

    # Display available accounts for blacklisting
    available_df = pd.DataFrame(st.session_state.available_accounts)
    
    # Create a selection dataframe
    display_df = available_df[['Account_Name', 'Account_ID', 'ICP_score', 'CXP_Swat_Tier']].copy()
    display_df['Blacklist'] = display_df['Account_ID'].apply(
        lambda x: x in st.session_state.blacklisted_accounts
    )

    st.subheader("Top 50 Accounts")
    edited_df = st.data_editor(
        display_df.head(50),
        use_container_width=True,
        column_config={
            'Blacklist': st.column_config.CheckboxColumn(
                "Blacklist?",
                default=False
            )
        },
        hide_index=True
    )

    # Update blacklist from editor
    for idx, row in edited_df.iterrows():
        account_id = row['Account_ID']
        if row['Blacklist']:
            st.session_state.blacklisted_accounts.add(account_id)
        else:
            st.session_state.blacklisted_accounts.discard(account_id)

    # Remove blacklisted accounts from available list
    st.session_state.available_accounts = [
        acc for acc in st.session_state.available_accounts
        if acc['Account_ID'] not in st.session_state.blacklisted_accounts
    ]

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Accounts to Draft", len(st.session_state.available_accounts))
    with col2:
        st.metric("Blacklisted", len(st.session_state.blacklisted_accounts))

    st.markdown("---")
    
    if st.button("✅ Start Live Draft", type="primary", use_container_width=True):
        st.session_state.stage = 'draft'
        st.session_state.pick_start_time = datetime.now()
        st.rerun()

# =============================================================================
# STAGE 4: LIVE DRAFT
# =============================================================================
elif st.session_state.stage == 'draft':
    st.header("🎯 Step 4: Live Draft")

    df = st.session_state.accounts_df
    num_aes = len(st.session_state.ae_list)
    total_picks = num_aes * st.session_state.accounts_per_ae
    current_pick = st.session_state.current_pick

    # Determine current round and AE
    current_round = (current_pick // num_aes) + 1
    current_ae = get_current_ae()

    # Status bar at top
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Pick", f"{current_pick + 1} of {total_picks}")
    with col2:
        st.metric("Round", current_round)
    with col3:
        st.metric("Current AE", current_ae if current_ae else "N/A")
    with col4:
        remaining = len(st.session_state.available_accounts)
        st.metric("Accounts Left", remaining)

    if current_pick < total_picks and len(st.session_state.available_accounts) > 0:
        
        # Timer
        st.markdown("---")
        timer_col, spacer = st.columns([1, 4])
        
        with timer_col:
            if st.session_state.pick_start_time is None:
                st.session_state.pick_start_time = datetime.now()
            
            elapsed = (datetime.now() - st.session_state.pick_start_time).total_seconds()
            remaining_secs = max(0, st.session_state.timer_seconds - elapsed)
            
            # Display timer with color coding
            if remaining_secs > 10:
                timer_color = "green"
            elif remaining_secs > 5:
                timer_color = "orange"
            else:
                timer_color = "red"
            
            st.markdown(f"<h2 style='color: {timer_color};'>⏱️ {int(remaining_secs)}s</h2>", unsafe_allow_html=True)
            
            if remaining_secs <= 0:
                st.warning("⏰ Time's up! Auto-drafting best available account...")
                time.sleep(1)
        
        st.markdown("---")

        # Display available accounts
        available_df = pd.DataFrame(st.session_state.available_accounts)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Available Accounts")
            
            # Color-code by tier
            def tier_badge(tier_val):
                if pd.isna(tier_val) or tier_val == '':
                    return '⚪ Unranked'
                elif 'Tier 1' in str(tier_val):
                    return '🟡 Tier 1'
                elif 'Tier 2' in str(tier_val):
                    return '🟢 Tier 2'
                return '⚪ Unranked'
            
            display_cols = ['Account_Name', 'ICP_score', 'CXP_Swat_Tier']
            display_data = available_df[display_cols].head(20).copy()
            display_data['Tier'] = display_data['CXP_Swat_Tier'].apply(tier_badge)
            
            st.dataframe(
                display_data[['Account_Name', 'ICP_score', 'Tier']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # Selection interface
            st.subheader("Make Your Pick")
            selected_idx = st.selectbox(
                "Select account to draft",
                range(len(available_df.head(50))),
                format_func=lambda i: f"{available_df.iloc[i]['Account_Name']} ({available_df.iloc[i]['ICP_score']:.0f})"
            )

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if st.button("✅ Confirm Pick", use_container_width=True):
                    selected_account = available_df.iloc[selected_idx]
                    st.session_state.draft_picks.append({
                        'pick_number': current_pick + 1,
                        'round': current_round,
                        'ae': current_ae,
                        'account_name': selected_account['Account_Name'],
                        'account_id': selected_account['Account_ID'],
                        'icp_score': selected_account['ICP_score'],
                        'tier': selected_account['CXP_Swat_Tier']
                    })
                    st.session_state.ae_books[current_ae].append(selected_account['Account_ID'])
                    st.session_state.available_accounts = [
                        acc for acc in st.session_state.available_accounts
                        if acc['Account_ID'] != selected_account['Account_ID']
                    ]
                    st.session_state.current_pick += 1
                    st.session_state.pick_start_time = None
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
                        'icp_score': best_account['ICP_score'],
                        'tier': best_account['CXP_Swat_Tier']
                    })
                    st.session_state.ae_books[current_ae].append(best_account['Account_ID'])
                    st.session_state.available_accounts = [
                        acc for acc in st.session_state.available_accounts
                        if acc['Account_ID'] != best_account['Account_ID']
                    ]
                    st.session_state.current_pick += 1
                    st.session_state.pick_start_time = None
                    st.rerun()

            with col_c:
                if current_pick > 0 and st.button("↩️ Undo Pick", use_container_width=True):
                    last_pick = st.session_state.draft_picks.pop()
                    st.session_state.ae_books[last_pick['ae']].remove(last_pick['account_id'])
                    returned_account = st.session_state.accounts_df[
                        st.session_state.accounts_df['Account_ID'] == last_pick['account_id']
                    ].iloc[0].to_dict()
                    st.session_state.available_accounts.insert(0, returned_account)
                    st.session_state.available_accounts = sort_accounts(st.session_state.available_accounts)
                    st.session_state.current_pick -= 1
                    st.session_state.pick_start_time = None
                    st.rerun()

        with col2:
            st.subheader("📜 Recent Picks")
            recent_picks = st.session_state.draft_picks[-8:][::-1]
            for pick in recent_picks:
                st.markdown(f"**Pick {pick['pick_number']}** — {pick['ae']}")
                st.caption(f"{pick['account_name']}")
                st.caption(f"Score: {pick['icp_score']:.0f} | {pick['tier'] if pick['tier'] else 'Unranked'}")

            if current_ae and current_ae in st.session_state.ae_books:
                st.markdown("---")
                st.subheader(f"{current_ae}'s Book")
                ae_ids = st.session_state.ae_books[current_ae]
                ae_book_df = st.session_state.accounts_df[
                    st.session_state.accounts_df['Account_ID'].isin(ae_ids)
                ][['Account_Name', 'ICP_score', 'CXP_Swat_Tier']].sort_values('ICP_score', ascending=False)

                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("Accounts", len(ae_ids))
                with col_y:
                    if len(ae_ids) > 0:
                        st.metric("Avg Score", f"{ae_book_df['ICP_score'].mean():.0f}")

                st.dataframe(ae_book_df, use_container_width=True, hide_index=True)

    else:
        st.success("✅ Draft complete!")
        
        st.markdown("---")
        remaining_picks = total_picks - current_pick
        
        if remaining_picks > 0 and len(st.session_state.available_accounts) > 0:
            st.subheader("🤖 Auto-Complete Draft")
            st.info(f"Auto-draft {remaining_picks} remaining picks")
            
            if st.button(f"🚀 Auto-Complete All {remaining_picks} Picks", type="primary", use_container_width=True):
                temp_pick = current_pick
                temp_available = st.session_state.available_accounts.copy()

                while temp_pick < total_picks and len(temp_available) > 0:
                    temp_round = (temp_pick // num_aes) + 1
                    temp_pick_in_round = temp_pick % num_aes

                    if st.session_state.is_snake and temp_round % 2 == 0:
                        temp_ae_index = num_aes - 1 - temp_pick_in_round
                    else:
                        temp_ae_index = temp_pick_in_round

                    temp_ae = st.session_state.draft_order[temp_ae_index]
                    best_account = temp_available[0]

                    st.session_state.draft_picks.append({
                        'pick_number': temp_pick + 1,
                        'round': temp_round,
                        'ae': temp_ae,
                        'account_name': best_account['Account_Name'],
                        'account_id': best_account['Account_ID'],
                        'icp_score': best_account['ICP_score'],
                        'tier': best_account.get('CXP_Swat_Tier', '')
                    })
                    st.session_state.ae_books[temp_ae].append(best_account['Account_ID'])
                    temp_available.pop(0)
                    temp_pick += 1

                st.session_state.available_accounts = temp_available
                st.session_state.current_pick = temp_pick
                st.rerun()
        else:
            if st.button("➡️ Go to Results", type="primary", use_container_width=True):
                st.session_state.stage = 'results'
                st.rerun()

# =============================================================================
# STAGE 5: RESULTS & REPORTING
# =============================================================================
elif st.session_state.stage == 'results':
    st.header("📊 Draft Results")

    df = st.session_state.accounts_df

    results = []
    for ae in st.session_state.ae_list:
        ae_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_ids)]
        
        # Count tier 1 and tier 2
        tier1 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
        tier2 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
        
        results.append({
            'AE': ae,
            'Total Accounts': len(ae_accounts),
            'Tier 1': tier1,
            'Tier 2': tier2,
            'Avg ICP Score': ae_accounts['ICP_score'].mean() if len(ae_accounts) > 0 else 0,
            'Total Score': ae_accounts['ICP_score'].sum() if len(ae_accounts) > 0 else 0,
        })

    results_df = pd.DataFrame(results).sort_values('Avg ICP Score', ascending=False)

    st.subheader("🏆 Final Standings")
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📚 Account Books by AE")
    for ae in st.session_state.ae_list:
        ae_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_ids)].sort_values('ICP_score', ascending=False)
        avg = ae_accounts['ICP_score'].mean() if len(ae_accounts) > 0 else 0
        
        tier1 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 1', case=False, na=False)).sum()
        tier2 = (ae_accounts['CXP_Swat_Tier'].str.contains('Tier 2', case=False, na=False)).sum()
        
        with st.expander(f"{ae} - {len(ae_accounts)} accounts | Avg Score: {avg:.0f} | Tier 1: {tier1} | Tier 2: {tier2}"):
            st.dataframe(
                ae_accounts[['Account_Name', 'ICP_score', 'CXP_Swat_Tier']].reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")
    st.subheader("📜 Complete Draft History")
    if st.session_state.draft_picks:
        picks_df = pd.DataFrame(st.session_state.draft_picks)
        st.dataframe(picks_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💾 Export Results")
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
            label="📥 Download Assignment CSV",
            data=csv,
            file_name=f"draft_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    with col2:
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
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
