import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
if 'ae_keeper_selections' not in st.session_state:
    st.session_state.ae_keeper_selections = {}
if 'accounts_per_ae' not in st.session_state:
    st.session_state.accounts_per_ae = 20
if 'is_snake' not in st.session_state:
    st.session_state.is_snake = True

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
        'setup': '2️⃣ Draft Setup',
        'cleanup': '3️⃣ Pre-Draft Cleanup',
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
    Upload a CSV file with your account data. Required columns:
    - **Account Name** (or Account_Name)
    - **Account ID** (or Account_ID)
    - **Account Owner Name** (or Account_Owner_Name)
    - **Account Score** (or Account_Score) — numerical
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
                    index=next((i for i, c in enumerate(available_columns) if 'account' in c.lower() and 'name' in c.lower()), 0)
                )
                account_id_col = st.selectbox(
                    "Account ID *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'account' in c.lower() and 'id' in c.lower()), 0)
                )
            with col2:
                account_owner_col = st.selectbox(
                    "Account Owner Name *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'owner' in c.lower() and 'name' in c.lower()), 0)
                )
                account_score_col = st.selectbox(
                    "Account Score *",
                    available_columns,
                    index=next((i for i, c in enumerate(available_columns) if 'score' in c.lower()), 0)
                )

            required_fields = {
                'Account_Name': account_name_col,
                'Account_ID': account_id_col,
                'Account_Owner_Name': account_owner_col,
                'Account_Score': account_score_col
            }
            missing = [k for k, v in required_fields.items() if not v]

            if missing:
                st.warning(f"⚠️ Please map all required fields: {', '.join(missing)}")
            else:
                df_mapped = df.copy()
                for standard_name, user_col in required_fields.items():
                    df_mapped[standard_name] = df[user_col]

                df_mapped['Account_Score'] = pd.to_numeric(df_mapped['Account_Score'], errors='coerce')
                df_mapped = df_mapped.dropna(subset=['Account_Score'])

                st.session_state.accounts_df = df_mapped

                st.success(f"✅ Successfully loaded {len(df_mapped)} accounts!")

                st.subheader("Data Preview")
                st.dataframe(df_mapped.head(10), use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Accounts", len(df_mapped))
                with col2:
                    st.metric("Unique Owners", df_mapped['Account_Owner_Name'].nunique())
                with col3:
                    st.metric("Avg Account Score", f"{df_mapped['Account_Score'].mean():.2f}")

                if st.button("➡️ Proceed to Draft Setup", type="primary"):
                    st.session_state.stage = 'setup'
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")

# =============================================================================
# STAGE 2: DRAFT SETUP
# =============================================================================
elif st.session_state.stage == 'setup':
    st.header("⚙️ Step 2: Configure Your Draft")

    df = st.session_state.accounts_df

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Account Owners (AEs)")
        unique_owners = sorted(df['Account_Owner_Name'].unique().tolist())

        st.markdown("Select which AEs will participate in the draft:")
        selected_aes = st.multiselect(
            "Select AEs",
            unique_owners,
            default=st.session_state.ae_list if st.session_state.ae_list else (unique_owners[:5] if len(unique_owners) >= 5 else unique_owners)
        )
        st.session_state.ae_list = selected_aes

    with col2:
        st.subheader("Draft Settings")

        draft_type = st.radio("Draft Type", ["Snake", "Linear"], index=0 if st.session_state.is_snake else 1)
        st.session_state.is_snake = (draft_type == "Snake")

        st.session_state.accounts_per_ae = st.number_input(
            "Target accounts per AE",
            min_value=1,
            max_value=100,
            value=st.session_state.accounts_per_ae,
            step=1
        )

        st.markdown("**Draft Order:**")
        if st.button("🎲 Randomize Order") and selected_aes:
            st.session_state.draft_order = np.random.permutation(selected_aes).tolist()

    if not st.session_state.draft_order or set(st.session_state.draft_order) != set(selected_aes):
        st.session_state.draft_order = selected_aes.copy()

    if st.session_state.draft_order:
        st.success("**Draft Order:**")
        for i, ae in enumerate(st.session_state.draft_order, 1):
            st.write(f"{i}. {ae}")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back to Upload"):
            st.session_state.stage = 'upload'
            st.rerun()
    with col_next:
        if len(selected_aes) >= 2:
            if st.button("➡️ Continue to Cleanup", type="primary"):
                st.session_state.ae_books = {ae: [] for ae in selected_aes}
                st.session_state.ae_keeper_selections = {}
                st.session_state.stage = 'cleanup'
                st.rerun()
        else:
            st.info("Select at least 2 AEs to continue")

# =============================================================================
# STAGE 3: PRE-DRAFT CLEANUP
# =============================================================================
elif st.session_state.stage == 'cleanup':
    st.header("🧹 Step 3: Pre-Draft Cleanup")

    df = st.session_state.accounts_df

    st.markdown("Configure which accounts each AE keeps before the draft. AEs keep their top accounts, and everything else becomes available in the draft pool.")

    keep_accounts = st.number_input(
        "Max accounts each AE can keep (pre-draft)",
        min_value=0,
        max_value=50,
        value=10,
        help="AEs will keep their top N accounts by Account Score"
    )

    st.subheader("📚 Keepers by AE")

    for ae in st.session_state.ae_list:
        ae_accounts = df[df['Account_Owner_Name'] == ae].nlargest(keep_accounts, 'Account_Score')
        if ae not in st.session_state.ae_keeper_selections:
            st.session_state.ae_keeper_selections[ae] = ae_accounts['Account_ID'].tolist()
        st.session_state.ae_books[ae] = st.session_state.ae_keeper_selections[ae][:keep_accounts]

        kept_ids = st.session_state.ae_books[ae]
        kept_df = df[df['Account_ID'].isin(kept_ids)]
        avg_score = kept_df['Account_Score'].mean() if len(kept_df) > 0 else 0

        with st.expander(f"{ae} - Keeping {len(kept_ids)} accounts (Avg Score: {avg_score:.2f})"):
            st.dataframe(kept_df[['Account_Name', 'Account_Score']], use_container_width=True, hide_index=True)

    kept_all_ids = set()
    for book in st.session_state.ae_books.values():
        kept_all_ids.update(book)

    available_for_draft = df[~df['Account_ID'].isin(kept_all_ids)].copy()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Accounts Kept", len(kept_all_ids))
    with col2:
        st.metric("Available for Draft", len(available_for_draft))

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Back to Setup"):
            st.session_state.stage = 'setup'
            st.rerun()
    with col_next:
        if st.button("➡️ Start Draft", type="primary"):
            st.session_state.available_accounts = available_for_draft.sort_values('Account_Score', ascending=False).to_dict('records')
            st.session_state.current_pick = 0
            st.session_state.draft_picks = []
            st.session_state.stage = 'draft'
            st.rerun()

# =============================================================================
# STAGE 4: LIVE DRAFT
# =============================================================================
elif st.session_state.stage == 'draft':
    st.header("🎯 Step 4: Live Draft")

    total_rounds = st.session_state.accounts_per_ae
    num_aes = len(st.session_state.draft_order)

    if num_aes == 0:
        st.error("No AEs found! Please go back to setup.")
        if st.button("← Back to Setup"):
            st.session_state.stage = 'setup'
            st.rerun()
        st.stop()

    total_picks = total_rounds * num_aes
    current_pick = st.session_state.current_pick

    current_round = (current_pick // num_aes) + 1
    pick_in_round = current_pick % num_aes

    if st.session_state.is_snake and current_round % 2 == 0:
        current_ae_index = num_aes - 1 - pick_in_round
    else:
        current_ae_index = pick_in_round

    current_ae = st.session_state.draft_order[current_ae_index] if current_pick < total_picks else None

    progress = min(current_pick / total_picks, 1.0) if total_picks else 1.0
    st.progress(progress, text=f"Pick {min(current_pick + 1, total_picks)} of {total_picks}")

    if current_pick >= total_picks:
        st.success("🎉 Draft Complete! Time to review your new territory assignments.")
        if st.button("➡️ View Results", type="primary"):
            st.session_state.stage = 'results'
            st.rerun()
    else:
        st.markdown(f"### 🏈 On the Clock: **{current_ae}**")
        st.caption(f"Round {current_round}, Pick {pick_in_round + 1}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📊 Available Accounts")
            available_df = pd.DataFrame(st.session_state.available_accounts)

            if len(available_df) > 0:
                selected_account_name = st.selectbox(
                    "Select account to draft:",
                    options=available_df['Account_Name'].tolist(),
                    index=0
                )
                selected_account = available_df[available_df['Account_Name'] == selected_account_name].iloc[0].to_dict()

                st.info(f"**{selected_account['Account_Name']}** — Score: {selected_account['Account_Score']:.2f}")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅ Draft This Account", type="primary", use_container_width=True):
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

                st.markdown("---")
                remaining_picks = total_picks - current_pick
                if st.button(f"🤖 Auto-Complete Remaining {remaining_picks} Picks", use_container_width=True):
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
                            'account_score': best_account['Account_Score']
                        })
                        st.session_state.ae_books[temp_ae].append(best_account['Account_ID'])
                        temp_available.pop(0)
                        temp_pick += 1

                    st.session_state.available_accounts = temp_available
                    st.session_state.current_pick = temp_pick
                    st.rerun()

                st.subheader("Top Available Accounts")
                st.dataframe(
                    available_df[['Account_Name', 'Account_Score']].head(15),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No more accounts available!")

        with col2:
            st.subheader("📜 Recent Picks")
            recent_picks = st.session_state.draft_picks[-8:][::-1]
            for pick in recent_picks:
                st.markdown(f"**Pick {pick['pick_number']}** — {pick['ae']}")
                st.caption(f"{pick['account_name']} ({pick['account_score']:.2f})")

            if current_ae and current_ae in st.session_state.ae_books:
                st.markdown("---")
                st.subheader(f"{current_ae}'s Book")
                ae_ids = st.session_state.ae_books[current_ae]
                ae_book_df = st.session_state.accounts_df[
                    st.session_state.accounts_df['Account_ID'].isin(ae_ids)
                ][['Account_Name', 'Account_Score']]

                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("Accounts", len(ae_ids))
                with col_y:
                    if len(ae_ids) > 0:
                        st.metric("Avg Score", f"{ae_book_df['Account_Score'].mean():.2f}")

                st.dataframe(ae_book_df, use_container_width=True, hide_index=True)

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
        results.append({
            'AE': ae,
            'Total Accounts': len(ae_accounts),
            'Avg Account Score': ae_accounts['Account_Score'].mean() if len(ae_accounts) > 0 else 0,
            'Total Score': ae_accounts['Account_Score'].sum() if len(ae_accounts) > 0 else 0,
            'Top Account Score': ae_accounts['Account_Score'].max() if len(ae_accounts) > 0 else 0
        })

    results_df = pd.DataFrame(results).sort_values('Avg Account Score', ascending=False)

    st.subheader("🏆 Final Standings")
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.subheader("📚 Account Books by AE")
    for ae in st.session_state.ae_list:
        ae_ids = st.session_state.ae_books[ae]
        ae_accounts = df[df['Account_ID'].isin(ae_ids)].sort_values('Account_Score', ascending=False)
        avg = ae_accounts['Account_Score'].mean() if len(ae_accounts) > 0 else 0
        with st.expander(f"{ae} - {len(ae_accounts)} accounts | Avg Score: {avg:.2f}"):
            st.dataframe(
                ae_accounts[['Account_Name', 'Account_Score']].reset_index(drop=True),
                use_container_width=True
            )

    st.subheader("📜 Complete Draft History")
    if st.session_state.draft_picks:
        st.dataframe(pd.DataFrame(st.session_state.draft_picks), use_container_width=True)

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
