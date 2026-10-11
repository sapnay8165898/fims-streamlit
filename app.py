import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

from modules.hasher import scan_directory
from modules.baseline import (
    save_baseline, load_baseline, list_baselines,
    delete_baseline, diff_baseline,
)
from modules.alerts import load_alerts, clear_alerts, record_diff
from modules.watcher import Watcher
from modules.utils import ensure_dirs

# ------------------------------------------------------------------
st.set_page_config(page_title="FIMS Dashboard", page_icon="🛡️", layout="wide")
ensure_dirs()

# Session state
if 'watcher' not in st.session_state:
    st.session_state.watcher = Watcher()
if 'scan_result' not in st.session_state:
    st.session_state.scan_result = None
if 'diff_result' not in st.session_state:
    st.session_state.diff_result = None

watcher = st.session_state.watcher

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ FIMS Control Panel")

    target_dir = st.text_input(
        "Directory to monitor",
        value=os.getcwd(),
        help="Absolute path (e.g. D:\\fims-streamlit or C:\\Windows\\System32\\drivers\\etc)",
    )

    extensions_raw = st.text_input(
        "Filter by extensions (comma-separated, blank = all)",
        value="",
        placeholder=".py,.txt,.conf",
    )
    extensions = [e.strip() for e in extensions_raw.split(',') if e.strip()] or None

    exclude_raw = st.text_input(
        "Exclude directories (comma-separated)",
        value="venv,.git,__pycache__,node_modules",
    )
    exclude_dirs = [e.strip() for e in exclude_raw.split(',') if e.strip()]

    max_size = st.slider("Skip files larger than (MB)", 1, 500, 50)

    hash_algo = st.selectbox("Hash algorithm", ['sha256', 'sha1', 'md5', 'sha512'])

    st.divider()
    st.subheader("📸 Baseline")

    baseline_choices = list_baselines()
    selected_baseline = st.selectbox(
        "Active baseline",
        options=baseline_choices or ['(none)'],
    )

    new_baseline_name = st.text_input("New baseline name", value="default")

    if st.button("📸 Create / Overwrite Baseline", use_container_width=True):
        if not os.path.isdir(target_dir):
            st.error("Directory not found")
        else:
            prog = st.progress(0.0, text="Hashing files...")

            def cb(done, total):
                prog.progress(done / total, text=f"Hashing {done}/{total}")

            files = scan_directory(
                target_dir, algo=hash_algo,
                extensions=extensions, max_size_mb=max_size,
                exclude_dirs=exclude_dirs, progress_callback=cb,
            )
            path = save_baseline(files, name=new_baseline_name)
            prog.empty()
            st.success(f"Baseline '{new_baseline_name}' saved ({len(files)} files)")

    if selected_baseline and selected_baseline != '(none)':
        bl = load_baseline(selected_baseline)
        if bl:
            st.caption(f"Created: {bl['created_at']}")
            st.caption(f"Files: {bl['file_count']}")
        if st.button("🗑️ Delete baseline", use_container_width=True):
            delete_baseline(selected_baseline)
            st.warning("Deleted")
            st.rerun()

    st.divider()
    st.subheader("🔍 Scan")

    if st.button("▶️ Scan Now (Compare vs Baseline)", use_container_width=True):
        if not os.path.isdir(target_dir):
            st.error("Directory not found")
        elif not selected_baseline or selected_baseline == '(none)':
            st.error("Create a baseline first")
        else:
            bl = load_baseline(selected_baseline)
            prog = st.progress(0.0, text="Scanning...")

            def cb(done, total):
                prog.progress(done / total, text=f"Scanning {done}/{total}")

            current = scan_directory(
                target_dir, algo=hash_algo,
                extensions=extensions, max_size_mb=max_size,
                exclude_dirs=exclude_dirs, progress_callback=cb,
            )
            diff = diff_baseline(bl['files'], current)
            record_diff(diff)
            st.session_state.diff_result = diff
            st.session_state.scan_result = current
            prog.empty()
            st.rerun()

    st.divider()
    st.subheader("⚡ Real-Time Watch")

    if watcher.watching:
        st.success("Watching for changes...")
        if st.button("⏹️ Stop Watching", use_container_width=True):
            watcher.stop()
            st.rerun()
    else:
        if st.button("▶️ Start Real-Time Watch", use_container_width=True):
            if os.path.isdir(target_dir):
                watcher.start(target_dir, extensions, exclude_dirs)
                st.rerun()
            else:
                st.error("Directory not found")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
st.title("🛡️ File Integrity Monitoring System")

diff = st.session_state.diff_result
all_alerts = load_alerts()

# KPI row
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Changes Logged", len(all_alerts))
if diff:
    k2.metric("✏️ Modified", len(diff['modified']))
    k3.metric("➕ Added", len(diff['added']))
    k4.metric("➖ Deleted", len(diff['deleted']))
    k5.metric("🔐 Perms", len(diff['permission_changed']))
else:
    k2.metric("✏️ Modified", 0)
    k3.metric("➕ Added", 0)
    k4.metric("➖ Deleted", 0)
    k5.metric("🔐 Perms", 0)

st.caption(f"Target: `{target_dir}`  |  Baseline: `{selected_baseline}`  |  "
           f"Real-time: {'🟢 ON' if watcher.watching else '🔴 OFF'}")

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Last Scan", "🚨 Change Log", "📈 Analytics", "🗂️ Files"]
)

# --- Tab 1: Last Scan ---
with tab1:
    if not diff:
        st.info("Run a scan to see changes vs baseline.")
    else:
        st.subheader(f"Scan at {diff['scanned_at']}")

        if diff['modified']:
            st.error(f"✏️ {len(diff['modified'])} modified files")
            st.dataframe(pd.DataFrame(diff['modified']), use_container_width=True)

        if diff['added']:
            st.warning(f"➕ {len(diff['added'])} new files")
            st.dataframe(pd.DataFrame(diff['added']), use_container_width=True)

        if diff['deleted']:
            st.error(f"➖ {len(diff['deleted'])} deleted files")
            st.dataframe(pd.DataFrame(diff['deleted']), use_container_width=True)

        if diff['permission_changed']:
            st.warning(f"🔐 {len(diff['permission_changed'])} permission changes")
            st.dataframe(pd.DataFrame(diff['permission_changed']),
                         use_container_width=True)

        if not any([diff['modified'], diff['added'],
                    diff['deleted'], diff['permission_changed']]):
            st.success("✅ No changes detected — integrity intact")

# --- Tab 2: Change Log ---
with tab2:
    c1, c2 = st.columns([3, 1])
    with c1:
        types = st.multiselect(
            "Filter change type",
            options=['modified', 'added', 'deleted', 'permission'],
            default=['modified', 'added', 'deleted', 'permission'],
        )
    with c2:
        if st.button("Clear All Logs", use_container_width=True):
            clear_alerts()
            st.rerun()

    filtered = [a for a in all_alerts if a.get('change_type') in types]
    if filtered:
        df = pd.DataFrame(filtered).iloc[::-1]
        st.dataframe(df, use_container_width=True, height=450)
        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name=f"fims_changes_{datetime.now():%Y%m%d_%H%M%S}.csv",
            mime="text/csv",
        )
    else:
        st.success("No changes logged yet 🎉")

# --- Tab 3: Analytics ---
with tab3:
    if all_alerts:
        df = pd.DataFrame(all_alerts)
        c1, c2 = st.columns(2)
        with c1:
            counts = df['change_type'].value_counts().reset_index()
            counts.columns = ['Type', 'Count']
            color_map = {'modified': 'orange', 'added': 'green',
                         'deleted': 'red', 'permission': 'purple'}
            fig = px.pie(counts, names='Type', values='Count',
                         title="Changes by Type", color='Type',
                         color_discrete_map=color_map)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'timestamp' in df.columns:
                df['ts'] = pd.to_datetime(df['timestamp'], errors='coerce')
                tl = df.dropna(subset=['ts']).set_index('ts').resample('1min').size()
                tl = tl.reset_index(name='count')
                if not tl.empty:
                    fig = px.line(tl, x='ts', y='count',
                                  title="Changes Over Time", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet")

# --- Tab 4: Files ---
with tab4:
    scan = st.session_state.scan_result
    if not scan:
        st.info("Run a scan to see file inventory.")
    else:
        df = pd.DataFrame(list(scan.values()))
        c1, c2, c3 = st.columns(3)
        with c1:
            q = st.text_input("Filter path contains")
        with c2:
            sort_by = st.selectbox("Sort by", ['path', 'size', 'mtime'])
        with c3:
            algo_label = st.text_input("Filter by hash prefix")

        if q:
            df = df[df['path'].str.contains(q, case=False, na=False)]
        if algo_label:
            df = df[df['hash'].astype(str).str.startswith(algo_label)]
        df = df.sort_values(sort_by, ascending=(sort_by == 'path'))

        st.dataframe(df, use_container_width=True, height=500)
        st.download_button(
            "⬇️ Download Inventory (CSV)",
            data=df.to_csv(index=False),
            file_name=f"fims_inventory_{datetime.now():%Y%m%d_%H%M%S}.csv",
            mime="text/csv",
        )