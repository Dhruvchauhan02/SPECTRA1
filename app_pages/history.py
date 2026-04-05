# pages/history.py
"""
History page for SPECTRA-AI
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# FIX #3: Removed broken `from database import mongodb` — 'mongodb' does not
# exist in database.py (it was renamed to supabase_db). The history page
# communicates with the backend via HTTP, so no direct DB import is needed here.


def show():
    """Display history page"""

    st.markdown("# 📜 Analysis History")
    st.markdown("View and search past analyses")

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_type = st.selectbox(
            "Filter by Type:",
            ["All", "deepfake_image", "fake_news_text", "celebrity_verification"]
        )

    with col2:
        limit = st.number_input("Results:", min_value=5, max_value=100, value=20)

    with col3:
        if st.button("🔍 Search", use_container_width=True):
            st.rerun()

    # Fetch history
    try:
        type_filter = None if analysis_type == "All" else analysis_type

        params = {"limit": limit}
        if type_filter:
            params["type"] = type_filter

        response = requests.get(
            f"{st.session_state.api_url}/history/recent",
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            analyses = data.get("analyses", [])

            if analyses:
                display_history(analyses)
            else:
                st.info("📭 No analyses found")
        else:
            st.error("❌ Unable to fetch history")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def display_history(analyses):
    """Display history table"""

    st.markdown(f"### 📊 Results ({len(analyses)})")

    # Convert to DataFrame
    records = []
    for analysis in analyses:
        record = {
            "ID": analysis.get("request_id", "")[:8],
            "Type": analysis.get("type", "").replace("_", " ").title(),
            "Timestamp": analysis.get("timestamp", ""),
            "Verdict": analysis.get("result", {}).get("verdict", "N/A"),
            "Confidence": f"{analysis.get('result', {}).get('confidence', 0):.2f}",
            "Time (ms)": analysis.get("result", {}).get("processing_time_ms", 0),
        }
        records.append(record)

    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Details
    st.markdown("### 🔍 View Details")

    options = [f"{r['ID']} - {r['Type']}" for r in records]
    selected_label = st.selectbox("Select analysis:", options)

    if selected_label:
        # FIX #9: was `int(selected_id.split(" -")[0])` — converted the
        # 8-char hex string to int, then compared it against a string, so
        # the match was ALWAYS False and no details ever rendered.
        # Fix: extract the prefix as a string and compare as strings.
        selected_prefix = selected_label.split(" -")[0].strip()

        for analysis in analyses:
            if analysis.get("request_id", "")[:8] == selected_prefix:
                with st.expander("📄 Full Details", expanded=True):
                    st.json(analysis)
                break

    # Export
    st.markdown("### 💾 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Download CSV", use_container_width=True):
            download_csv()

    with col2:
        if st.button("📥 Download JSON", use_container_width=True):
            download_json()


def download_csv():
    """Download data as CSV"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/export/csv?limit=100",
            timeout=30
        )

        if response.status_code == 200:
            st.download_button(
                label="💾 Save CSV File",
                data=response.content,
                file_name=f"spectra_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Export failed")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def download_json():
    """Download data as JSON"""
    try:
        response = requests.get(
            f"{st.session_state.api_url}/export/json?limit=100",
            timeout=30
        )

        if response.status_code == 200:
            st.download_button(
                label="💾 Save JSON File",
                data=response.content,
                file_name=f"spectra_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        else:
            st.error("❌ Export failed")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
