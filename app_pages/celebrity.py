# pages/celebrity.py
"""
Celebrity Claim Verification page for SPECTRA-AI
"""

import streamlit as st
import requests
import time


def show():
    """Display celebrity verification page"""

    st.markdown("# ⭐ Celebrity Claim Verification")
    st.markdown("Verify celebrity-related claims against news sources")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        celebrity = st.text_input(
            "Celebrity Name:",
            placeholder="e.g., Elon Musk, Taylor Swift",
            help="Enter the name of the celebrity"
        )

    with col2:
        claim = st.text_input(
            "Claim to Verify:",
            placeholder="e.g., announced new product, won award",
            help="Enter the claim you want to verify"
        )

    if st.button(
        "🔍 Verify Claim",
        type="primary",
        use_container_width=True,
        disabled=not (celebrity and claim)
    ):
        verify_claim(celebrity, claim)

    st.markdown("---")

    # Quick Examples
    st.markdown("### 🔥 Quick Examples")

    examples = [
        ("Elon Musk", "launched new rocket"),
        ("Taylor Swift", "new album release"),
        ("Modi", "announced new policy"),
    ]

    cols = st.columns(len(examples))
    for i, (celeb, clm) in enumerate(examples):
        with cols[i]:
            if st.button(f"{celeb}\n{clm}", use_container_width=True):
                verify_claim(celeb, clm)

    with st.expander("ℹ️ How it works"):
        st.markdown("""
        ### Verification Process

        1. **News Aggregation**: Searches multiple news sources
        2. **Context Analysis**: Understands whether articles confirm or debunk the claim
        3. **Source Verification**: Weights trusted outlets (Reuters, BBC, AP, etc.) more heavily
        4. **Verdict Generation**: Determines verification status

        ### Verdict Types

        - **VERIFIED**: Claim confirmed by multiple trusted sources
        - **PARTIALLY_VERIFIED**: Found in one trusted source — await more coverage
        - **DISPUTED**: Conflicting information found
        - **FAKE**: Actively debunked by fact-checkers
        - **UNVERIFIED**: No reliable sources found
        """)


def verify_claim(celebrity, claim):
    """Verify celebrity claim via API"""

    with st.spinner(f"🔄 Verifying claim about {celebrity}..."):
        try:
            payload = {
                "celebrity": celebrity,
                "claim": claim,
            }

            start_time = time.time()
            response = requests.post(
                f"{st.session_state.api_url}/verify-celebrity-claim",
                json=payload,
                timeout=30,
            )
            processing_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                display_verification_results(result, processing_time)
            elif response.status_code == 422:
                # Pydantic validation error — show helpful message
                detail = response.json().get("detail", [])
                st.error(f"❌ Invalid input: {detail}")
            else:
                st.error(f"❌ Server error {response.status_code}: {response.text[:200]}")

        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The news search may be slow — try again.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_verification_results(result, processing_time):
    """Display verification results"""

    st.markdown("---")
    st.markdown("## 📊 Verification Results")

    # FIX: result["verification"] is a dict {verdict, confidence},
    # NOT a string. Previously code did .get("verdict") on a string → None always.
    verification = result.get("verification", {})
    if isinstance(verification, str):
        # Defensive: handle old API shape just in case
        verdict    = verification
        confidence = result.get("confidence", 0)
    else:
        verdict    = verification.get("verdict", "UNKNOWN")
        confidence = verification.get("confidence", result.get("confidence", 0))

    # FIX: sources list now comes from result["sources"] which
    # celebrity_verification.py populates from confirming/debunking_sources.
    sources      = result.get("sources", [])
    sources_found = len(sources)

    # ── Verdict banner ────────────────────────────────────────────────────────
    verdict_config = {
        "VERIFIED":           ("✅", "success", "green"),
        "PARTIALLY_VERIFIED": ("🟡", "info",    "orange"),
        "DISPUTED":           ("❓", "warning", "orange"),
        "FAKE":               ("🚫", "error",   "red"),
        "UNVERIFIED":         ("⚠️", "warning", "gray"),
        "UNKNOWN":            ("❔", "info",    "gray"),
    }
    icon, box_type, _ = verdict_config.get(verdict, ("❔", "info", "gray"))

    if box_type == "success":
        st.success(f"{icon} **VERDICT: {verdict}** — Claim supported by {sources_found} source(s)")
    elif box_type == "error":
        st.error(f"{icon} **VERDICT: {verdict}** — Claim has been debunked")
    elif box_type == "warning":
        st.warning(f"{icon} **VERDICT: {verdict}** — {result.get('explanation', 'Conflicting or missing information')}")
    else:
        st.info(f"{icon} **VERDICT: {verdict}** — {result.get('explanation', 'Unable to verify')}")

    # ── Key metrics ───────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🎯 Confidence", f"{confidence:.0%}")

    with col2:
        st.metric("📰 Sources Found", sources_found)

    with col3:
        st.metric("⚡ Time", f"{processing_time:.0f}ms")

    # ── Explanation ───────────────────────────────────────────────────────────
    explanation = result.get("explanation", "")
    if explanation:
        st.markdown(f"**Analysis:** {explanation}")

    # ── Recommendation ────────────────────────────────────────────────────────
    recommendation = result.get("recommendation", "")
    if recommendation:
        st.info(f"💡 **Recommendation:** {recommendation}")

    # ── Source cards ──────────────────────────────────────────────────────────
    if sources_found > 0:
        st.markdown("### 📰 News Sources")

        for i, source in enumerate(sources[:5]):
            title        = source.get("title", "Untitled")
            outlet       = source.get("source", "Unknown")
            published_at = source.get("published_at", "")
            url          = source.get("url", "")

            label = f"Source {i + 1}: {title[:60]}{'...' if len(title) > 60 else ''}"
            with st.expander(label):
                st.markdown(f"**Title:** {title}")
                st.markdown(f"**Outlet:** {outlet}")
                if published_at:
                    st.markdown(f"**Date:** {published_at}")
                if url:
                    st.markdown(f"[🔗 Read Article]({url})")
    else:
        st.info("📭 No individual source articles were returned for this claim.")

    # ── Evidence summary (debug / advanced) ───────────────────────────────────
    ev_summary = result.get("evidence_summary", {})
    if ev_summary:
        with st.expander("🔬 Evidence Summary (advanced)"):
            st.json(ev_summary)
