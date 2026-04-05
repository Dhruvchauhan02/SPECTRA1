# pages/admin.py
"""
Admin page for SPECTRA-AI
"""

import streamlit as st
import requests


def show():
    """Display admin page"""

    st.markdown("# ⚙️ Admin Panel")
    st.markdown("Database management and system utilities")

    st.markdown("---")

    # Storage Info
    st.markdown("### 💾 Storage Information")

    try:
        response = requests.get(
            f"{st.session_state.api_url}/admin/storage-info",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            storage = data.get("storage_info", {})

            # FIX #8: Supabase doesn't expose size/index metrics via anon key.
            # Show record counts instead of misleading 0.00 MB metrics.
            counts = storage.get("counts", {})
            total_records = counts.get("total", 0)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Records", f"{total_records:,}")

            with col2:
                st.metric("Collections", storage.get("collections", 3))

            with col3:
                st.metric("Database", storage.get("database", "Supabase"))

            # Show per-table breakdown
            if counts:
                st.markdown("**Records per table:**")
                for table_name, count in counts.items():
                    if table_name != "total":
                        st.markdown(f"- `{table_name}`: {count:,}")

    except Exception as e:
        st.error(f"❌ Error fetching storage info: {str(e)}")

    st.markdown("---")

    # Data Validation
    st.markdown("### ✅ Data Validation")

    if st.button("🔍 Validate Database", use_container_width=True):
        validate_database()

    st.markdown("---")

    # Cleanup
    st.markdown("### 🗑️ Data Cleanup")

    st.warning("⚠️ **Warning:** This will permanently delete old data!")

    col1, col2 = st.columns(2)

    with col1:
        days = st.number_input(
            "Delete data older than (days):",
            min_value=7,
            max_value=365,
            value=90
        )

    with col2:
        dry_run = st.checkbox("Dry run (simulate only)", value=True)

    if st.button("🗑️ Run Cleanup", type="primary", use_container_width=True):
        cleanup_data(days, dry_run)

    st.markdown("---")

    # Backup Info
    st.markdown("### 💾 Backup Information")

    try:
        response = requests.get(
            f"{st.session_state.api_url}/admin/backup-info",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            methods = data.get("backup_methods", {})

            st.markdown("#### Recommended Backup Methods:")

            for method_name, method_info in methods.items():
                with st.expander(f"📦 {method_name}"):
                    st.markdown(f"**Description:** {method_info.get('description')}")
                    if 'command' in method_info:
                        st.code(method_info['command'], language='bash')
                    if 'endpoint' in method_info:
                        st.markdown(f"**Endpoint:** `{method_info['endpoint']}`")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def validate_database():
    """Validate database integrity"""

    with st.spinner("Validating database..."):
        try:
            response = requests.get(
                f"{st.session_state.api_url}/admin/validate",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                validation = data.get("validation", {})

                # FIX #7: API returns 'total_rows' and 'healthy' (bool), not
                # 'total_documents', 'status', or 'issues' list.
                total_rows = validation.get("total_rows", 0)
                is_healthy = validation.get("healthy", False)

                missing_request_id = validation.get("missing_request_id", 0)
                missing_result     = validation.get("missing_result", 0)
                missing_type       = validation.get("missing_type", 0)

                if is_healthy:
                    st.success(f"✅ Database is healthy! ({total_rows:,} records)")
                else:
                    problems = []
                    if missing_request_id:
                        problems.append(f"**missing_request_id**: {missing_request_id} records")
                    if missing_result:
                        problems.append(f"**missing_result**: {missing_result} records")
                    if missing_type:
                        problems.append(f"**missing_type**: {missing_type} records")

                    st.warning(f"⚠️ Found {len(problems)} issue(s) across {total_rows:,} records")
                    for p in problems:
                        st.markdown(f"- {p}")
            else:
                st.error("❌ Validation failed")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def cleanup_data(days, dry_run):
    """Cleanup old data"""

    action = "Simulating" if dry_run else "Executing"

    with st.spinner(f"{action} cleanup..."):
        try:
            response = requests.post(
                f"{st.session_state.api_url}/admin/cleanup",
                params={"days": days, "dry_run": dry_run},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                if dry_run:
                    # FIX #6: API returns 'would_delete', not 'documents_to_delete'
                    to_delete = data.get("would_delete", 0)
                    st.info(f"📊 Simulation: Would delete {to_delete:,} documents")
                    st.markdown(f"**Cutoff Date:** {data.get('cutoff_date', 'N/A')}")

                    if to_delete > 0:
                        st.warning("To actually delete, uncheck 'Dry run' and run again.")
                else:
                    # FIX #6: API returns 'deleted', not 'documents_deleted'
                    deleted = data.get("deleted", 0)
                    st.success(f"✅ Deleted {deleted:,} documents")
            else:
                st.error("❌ Cleanup failed")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
