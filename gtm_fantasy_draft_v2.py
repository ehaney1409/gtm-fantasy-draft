import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="GTM Fantasy Draft", layout="wide", page_icon="🏈")

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0f1419; }
    .main { background-color: #0f1419; }
    .draft-card { background: #1a1f2e; border-radius: 12px; padding: 20px; margin: 12px 0; border: 1px solid #2d3748; }
    .account-card { background: #1a1f2e; border-radius: 8px; padding: 12px; margin: 6px 0; border-left: 3px solid #4299e1; }
    .pick-card { background: #1a1f2e; border-radius: 6px; padding: 10px; margin: 4px 0; border-left: 3px solid #48bb78; }
    .segment-card { background: #1a1f2e; border-radius: 8px; padding: 16px; margin: 8px 0; border-left: 4px solid #f6ad55; }
    h1, h2, h3 { color: #f7fafc !important; }
    p, span, div { color: #e2e8f0 !important; }
    .stButton button { background: #4299e1; color: white; border-radius: 6px; font-weight: 600; }
    .stButton button[kind="primary"] { background: #48bb78; }
    section[data-testid="stSidebar"] { background-color: #1a1f2e; }
    [data-testid="stMetricValue"] { color: #4299e1 !important; font-weight: 700 !important; }
    .on-clock { background: #2d3748; border: 2px solid #48bb78; border-radius: 12px; padding: 20px; }
    .score-badge { background: #667eea; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 13px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# Initialize multi-draft state
if 'all_drafts' not in st.session_state:
    st.session_state.all_drafts = {}
if 'current_draft_id' not in st.session_state:
    st.session_state.current_draft_id = None
if 'segments' not in st.session_state:
    st.session_state.segments = []

# Create a new draft or get existing
def get_or_create_draft(draft_id):
    if draft_id not in st.session_state.all_drafts:
        st.session_state.all_drafts[draft_id] = {
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
            'is_snake': True,
            'segment_name': '',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    return st.session_state.all_drafts[draft_id]

# Helper to get current draft
def d(key):
    """Get value from current draft"""
    if st.session_state.current_draft_id:
        return st.session_state.all_drafts[st.session_state.current_draft_id].get(key)
    return None

def set_d(key, value):
    """Set value in current draft"""
    if st.session_state.current_draft_id:
        st.session_state.all_drafts[st.session_state.current_draft_id][key] = value

# Header
st.markdown("""
    <div style='padding: 20px 0;'>
        <h1 style='margin: 0; font-size: 48px; background: linear-gradient(135deg, #4299e1 0%, #48bb78 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;'>
            🏈 GTM Fantasy Draft
        </h1>
        <p style='color: #a0aec0; font-size: 18px; margin-top: 8px;'>Territory planning reimagined</p>
    </div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["🗺️ Territory Planning", "📋 Manage Drafts", "🎯 Active Draft"])

# TAB 1: Territory Planning
with tab1:
    st.markdown("<h2>🗺️ Territory Planning</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🌍 Define Segments</h3>", unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            seg_name = st.text_input("Segment Name", placeholder="e.g., Ent-NAMER", key="new_seg_name")
        with col_b:
            seg_aes = st.number_input("# AEs", 1, 100, 5, key="new_seg_aes")
        with col_c:
            if st.button("➕ Add"):
                if seg_name and not any(s['name'] == seg_name for s in st.session_state.segments):
                    st.session_state.segments.append({
                        'name': seg_name,
                        'num_aes': seg_aes,
                        'draft_ids': [],
                        'status': 'Not Started'
                    })
                    st.rerun()
        
        st.markdown("**Quick Add Common Segments:**")
        quick_segs = st.columns(3)
        for i, (name, aes) in enumerate([("Ent-NAMER", 8), ("Strat-NAMER", 12), ("Ent-EMEA", 6), ("Strat-EMEA", 10), ("Ent-APAC", 5), ("Strat-APAC", 8)]):
            with quick_segs[i % 3]:
                if st.button(f"+ {name}", key=f"q_{name}"):
                    if not any(s['name'] == name for s in st.session_state.segments):
                        st.session_state.segments.append({'name': name, 'num_aes': aes, 'draft_ids': [], 'status': 'Not Started'})
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display segments
        if st.session_state.segments:
            st.markdown("<h3>📋 Your Segments</h3>", unsafe_allow_html=True)
            for idx, seg in enumerate(st.session_state.segments):
                st.markdown(f"""
                    <div class='segment-card'>
                        <h4 style='margin: 0;'>{seg['name']}</h4>
                        <p style='color: #a0aec0; margin: 4px 0;'>{seg['num_aes']} AEs | {len(seg['draft_ids'])} draft(s)</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_x, col_y, col_z = st.columns([2, 2, 1])
                with col_x:
                    if st.button(f"🚀 New Draft for {seg['name']}", key=f"new_draft_{idx}"):
                        draft_id = f"{seg['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        get_or_create_draft(draft_id)
                        st.session_state.all_drafts[draft_id]['segment_name'] = seg['name']
                        st.session_state.segments[idx]['draft_ids'].append(draft_id)
                        st.session_state.current_draft_id = draft_id
                        st.rerun()
                
                with col_y:
                    if seg['draft_ids']:
                        latest_draft = seg['draft_ids'][-1]
                        if st.button(f"▶️ Continue Latest", key=f"cont_{idx}"):
                            st.session_state.current_draft_id = latest_draft
                            st.rerun()
                
                with col_z:
                    if st.button("🗑️", key=f"del_seg_{idx}"):
                        st.session_state.segments.pop(idx)
                        st.rerun()
    
    with col2:
        st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📊 Summary</h3>", unsafe_allow_html=True)
        st.metric("Segments", len(st.session_state.segments))
        st.metric("Total AEs", sum(s['num_aes'] for s in st.session_state.segments))
        st.metric("Total Drafts", len(st.session_state.all_drafts))
        st.markdown("</div>", unsafe_allow_html=True)

# TAB 2: Manage Drafts
with tab2:
    st.markdown("<h2>📋 All Drafts</h2>", unsafe_allow_html=True)
    
    if not st.session_state.all_drafts:
        st.info("No drafts yet! Create segments in Territory Planning to get started.")
    else:
        for draft_id, draft in st.session_state.all_drafts.items():
            st.markdown("<div class='draft-card'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"<h3 style='margin:0;'>{draft['segment_name']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#a0aec0;'>Stage: {draft['stage'].title()} | Created: {draft['created_at']}</p>", unsafe_allow_html=True)
            
            with col2:
                if draft['accounts_df'] is not None:
                    st.metric("Accounts", len(draft['accounts_df']))
                if draft['ae_list']:
                    st.metric("AEs", len(draft['ae_list']))
            
            with col3:
                if st.button("Open", key=f"open_{draft_id}"):
                    st.session_state.current_draft_id = draft_id
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# TAB 3: Active Draft (complete draft flow)
with tab3:
    if not st.session_state.current_draft_id:
        st.markdown("""
            <div class='draft-card' style='text-align: center; padding: 60px;'>
                <h2>No Active Draft</h2>
                <p style='color: #a0aec0;'>Create or select a draft from Territory Planning or Manage Drafts tabs</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Get current draft
        draft = get_or_create_draft(st.session_state.current_draft_id)
        stage = draft['stage']
        
        # Show draft header
        st.markdown(f"""
            <div style='background: #2d3748; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;'>
                <strong style='color: #4299e1;'>📍 {draft['segment_name']}</strong> | 
                <strong>Stage:</strong> {stage.replace('_', ' ').title()}
            </div>
        """, unsafe_allow_html=True)
        
        # Stage progress indicator
        stages_list = ['upload', 'setup', 'cleanup', 'blacklist', 'draft', 'results']
        stage_names = ['Upload CSV', 'Draft Setup', 'Pre-Draft', 'Blacklist', 'Live Draft', 'Results']
        
        progress_cols = st.columns(6)
        for i, (s, name) in enumerate(zip(stages_list, stage_names)):
            with progress_cols[i]:
                if s == stage:
                    st.markdown(f"<div style='background: #48bb78; padding: 8px; border-radius: 6px; text-align: center;'><strong>{i+1}. {name}</strong></div>", unsafe_allow_html=True)
                elif stages_list.index(s) < stages_list.index(stage):
                    st.markdown(f"<div style='background: #2d3748; padding: 8px; border-radius: 6px; text-align: center; color: #718096;'>{i+1}. {name}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='padding: 8px; text-align: center; color: #4a5568;'>{i+1}. {name}</div>", unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #2d3748; margin: 20px 0;'>", unsafe_allow_html=True)
        
        # STAGE 1: CSV UPLOAD
        if stage == 'upload':
            st.markdown("<h2>📁 Upload Account Data</h2>", unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
            
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                df.columns = df.columns.str.strip().str.replace(' ', '_')
                
                st.markdown("<h3>🔗 Map Columns</h3>", unsafe_allow_html=True)
                available_cols = [''] + df.columns.tolist()
                
                col1, col2 = st.columns(2)
                with col1:
                    name_col = st.selectbox("Account Name", available_cols, index=next((i for i, c in enumerate(available_cols) if 'name' in c.lower() and 'account' in c.lower()), 0))
                    id_col = st.selectbox("Account ID", available_cols, index=next((i for i, c in enumerate(available_cols) if 'id' in c.lower()), 0))
                with col2:
                    owner_col = st.selectbox("Account Owner", available_cols, index=next((i for i, c in enumerate(available_cols) if 'owner' in c.lower()), 0))
                    score_col = st.selectbox("Account Score", available_cols, index=next((i for i, c in enumerate(available_cols) if 'score' in c.lower()), 0))
                
                if name_col and id_col and owner_col and score_col:
                    if st.button("✅ Confirm Mapping", type="primary"):
                        df_mapped = df.copy()
                        df_mapped['Account_Name'] = df[name_col]
                        df_mapped['Account_ID'] = df[id_col]
                        df_mapped['Account_Owner_Name'] = df[owner_col]
                        df_mapped['Account_Score'] = pd.to_numeric(df[score_col], errors='coerce')
                        df_mapped = df_mapped.dropna(subset=['Account_Score'])
                        
                        draft['accounts_df'] = df_mapped
                        draft['stage'] = 'setup'
                        st.rerun()
        
        # STAGE 2: DRAFT SETUP
        elif stage == 'setup':
            st.markdown("<h2>⚙️ Draft Setup</h2>", unsafe_allow_html=True)
            
            df = draft['accounts_df']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3>👥 Select AEs</h3>", unsafe_allow_html=True)
                unique_owners = sorted(df['Account_Owner_Name'].unique().tolist())
                selected_aes = st.multiselect("Choose AEs", unique_owners, default=unique_owners[:5] if len(unique_owners) >= 5 else unique_owners)
                draft['ae_list'] = selected_aes
            
            with col2:
                st.markdown("<h3>⚙️ Settings</h3>", unsafe_allow_html=True)
                draft['is_snake'] = st.radio("Draft Type", ["Snake", "Linear"]) == "Snake"
                draft['accounts_per_ae'] = st.number_input("Accounts per AE", 1, 100, 20)
                
                if st.button("🎲 Randomize Order"):
                    draft['draft_order'] = np.random.permutation(selected_aes).tolist()
                    st.rerun()
            
            if not draft.get('draft_order'):
                draft['draft_order'] = selected_aes
            
            st.markdown("<h3>📋 Draft Order</h3>", unsafe_allow_html=True)
            for i, ae in enumerate(draft['draft_order'], 1):
                st.write(f"{i}. {ae}")
            
            if selected_aes and st.button("➡️ Continue", type="primary"):
                draft['ae_books'] = {ae: [] for ae in selected_aes}
                draft['ae_keeper_selections'] = {}
                draft['stage'] = 'cleanup'
                st.rerun()
        
        # STAGE 3: PRE-DRAFT CLEANUP
        elif stage == 'cleanup':
            st.markdown("<h2>🧹 Pre-Draft Cleanup</h2>", unsafe_allow_html=True)
            
            df = draft['accounts_df']
            keep_accounts = st.number_input("Max accounts to keep per AE", 0, 50, 10)
            
            for ae in draft['ae_list']:
                ae_accounts = df[df['Account_Owner_Name'] == ae].nlargest(keep_accounts, 'Account_Score')
                if ae not in draft['ae_keeper_selections']:
                    draft['ae_keeper_selections'][ae] = ae_accounts['Account_ID'].tolist()
                draft['ae_books'][ae] = draft['ae_keeper_selections'][ae][:keep_accounts]
            
            kept_ids = set()
            for book in draft['ae_books'].values():
                kept_ids.update(book)
            
            available = df[~df['Account_ID'].isin(kept_ids)]
            
            st.metric("Available for Draft", len(available))
            
            if st.button("➡️ Continue to Blacklist", type="primary"):
                draft['available_accounts'] = available.sort_values('Account_Score', ascending=False).to_dict('records')
                draft['stage'] = 'blacklist'
                st.rerun()
        
        # STAGE 4: BLACKLIST
        elif stage == 'blacklist':
            st.markdown("<h2>🚫 Blacklist Accounts</h2>", unsafe_allow_html=True)
            
            available_df = pd.DataFrame(draft['available_accounts'])
            st.dataframe(available_df[['Account_Name', 'Account_Score']].head(30), use_container_width=True)
            
            blacklist_names = st.text_area("Account names to blacklist (one per line)", height=100)
            
            if st.button("🚫 Add to Blacklist") and blacklist_names:
                names = [n.strip() for n in blacklist_names.split('\n') if n.strip()]
                blacklist_ids = available_df[available_df['Account_Name'].isin(names)]['Account_ID'].tolist()
                draft['blacklisted_accounts'] = draft['blacklisted_accounts'].union(set(blacklist_ids))
                st.rerun()
            
            st.metric("Blacklisted", len(draft['blacklisted_accounts']))
            
            if st.button("➡️ Start Draft", type="primary"):
                final_available = available_df[~available_df['Account_ID'].isin(draft['blacklisted_accounts'])]
                draft['available_accounts'] = final_available.sort_values('Account_Score', ascending=False).to_dict('records')
                draft['current_pick'] = 0
                draft['draft_picks'] = []
                draft['stage'] = 'draft'
                st.rerun()
        
        # STAGE 5: LIVE DRAFT
        elif stage == 'draft':
            st.markdown("<h2>🎯 Live Draft</h2>", unsafe_allow_html=True)
            
            total_rounds = draft['accounts_per_ae']
            num_aes = len(draft['draft_order'])
            
            if num_aes == 0:
                st.error("No AEs! Go back to setup.")
                st.stop()
            
            total_picks = total_rounds * num_aes
            current_pick = draft['current_pick']
            
            if current_pick >= total_picks:
                st.success("🎉 Draft Complete!")
                if st.button("➡️ View Results", type="primary"):
                    draft['stage'] = 'results'
                    st.rerun()
            else:
                current_round = (current_pick // num_aes) + 1
                pick_in_round = (current_pick % num_aes)
                
                if draft['is_snake'] and current_round % 2 == 0:
                    current_ae_index = num_aes - 1 - pick_in_round
                else:
                    current_ae_index = pick_in_round
                
                current_ae = draft['draft_order'][current_ae_index]
                
                st.progress(current_pick / total_picks, text=f"Pick {current_pick + 1} of {total_picks}")
                st.markdown(f"<h3 style='color: #48bb78;'>🏈 ON THE CLOCK: {current_ae}</h3>", unsafe_allow_html=True)
                
                available_df = pd.DataFrame(draft['available_accounts'])
                
                if len(available_df) > 0:
                    selected_name = st.selectbox("Select account", available_df['Account_Name'].tolist())
                    selected = available_df[available_df['Account_Name'] == selected_name].iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Draft", type="primary", use_container_width=True):
                            draft['draft_picks'].append({'pick_number': current_pick + 1, 'round': current_round, 'ae': current_ae, 'account_name': selected['Account_Name'], 'account_id': selected['Account_ID'], 'account_score': selected['Account_Score']})
                            draft['ae_books'][current_ae].append(selected['Account_ID'])
                            draft['available_accounts'] = [a for a in draft['available_accounts'] if a['Account_ID'] != selected['Account_ID']]
                            draft['current_pick'] += 1
                            st.rerun()
                    
                    with col2:
                        if st.button("⚡ Auto Best", use_container_width=True):
                            best = available_df.iloc[0]
                            draft['draft_picks'].append({'pick_number': current_pick + 1, 'round': current_round, 'ae': current_ae, 'account_name': best['Account_Name'], 'account_id': best['Account_ID'], 'account_score': best['Account_Score']})
                            draft['ae_books'][current_ae].append(best['Account_ID'])
                            draft['available_accounts'] = [a for a in draft['available_accounts'] if a['Account_ID'] != best['Account_ID']]
                            draft['current_pick'] += 1
                            st.rerun()
                    
                    with col3:
                        remaining = total_picks - current_pick
                        if st.button(f"🤖 Auto {remaining}", use_container_width=True):
                            # Auto-complete rest
                            temp_pick = current_pick
                            temp_available = draft['available_accounts'].copy()
                            
                            while temp_pick < total_picks and temp_available:
                                temp_round = (temp_pick // num_aes) + 1
                                temp_pick_in_round = (temp_pick % num_aes)
                                if draft['is_snake'] and temp_round % 2 == 0:
                                    temp_ae_idx = num_aes - 1 - temp_pick_in_round
                                else:
                                    temp_ae_idx = temp_pick_in_round
                                temp_ae = draft['draft_order'][temp_ae_idx]
                                
                                best = temp_available[0]
                                draft['draft_picks'].append({'pick_number': temp_pick + 1, 'round': temp_round, 'ae': temp_ae, 'account_name': best['Account_Name'], 'account_id': best['Account_ID'], 'account_score': best['Account_Score']})
                                draft['ae_books'][temp_ae].append(best['Account_ID'])
                                temp_available.pop(0)
                                temp_pick += 1
                            
                            draft['available_accounts'] = temp_available
                            draft['current_pick'] = temp_pick
                            st.rerun()
                    
                    st.dataframe(available_df[['Account_Name', 'Account_Score']].head(15), use_container_width=True)
        
        # STAGE 6: RESULTS
        elif stage == 'results':
            st.markdown("<h2>📊 Draft Results</h2>", unsafe_allow_html=True)
            
            df = draft['accounts_df']
            results = []
            
            for ae in draft['ae_list']:
                ae_accounts = df[df['Account_ID'].isin(draft['ae_books'][ae])]
                results.append({
                    'AE': ae,
                    'Accounts': len(ae_accounts),
                    'Avg Score': ae_accounts['Account_Score'].mean() if len(ae_accounts) > 0 else 0,
                    'Total Score': ae_accounts['Account_Score'].sum() if len(ae_accounts) > 0 else 0
                })
            
            results_df = pd.DataFrame(results).sort_values('Avg Score', ascending=False)
            st.dataframe(results_df, use_container_width=True)
            
            # Export
            export_data = []
            for ae in draft['ae_list']:
                ae_accounts = df[df['Account_ID'].isin(draft['ae_books'][ae])]
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
                "📥 Download Results",
                csv,
                f"draft_results_{draft['segment_name']}_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
            
            # Mark segment as complete
            for seg in st.session_state.segments:
                if draft['segment_name'] in seg.get('draft_ids', []) or seg.get('name') == draft['segment_name']:
                    seg['status'] = 'Completed'
            
            if st.button("🔄 Start New Draft"):
                st.session_state.current_draft_id = None
                st.rerun()

st.markdown("<hr style='border-color:#2d3748; margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#718096;'>GTM Fantasy Draft v2.0 - Multi-Draft Edition</p>", unsafe_allow_html=True)
