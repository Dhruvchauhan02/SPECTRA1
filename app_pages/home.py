# pages/home.py
"""
Home page for SPECTRA-AI Streamlit Dashboard
"""

import streamlit as st
import requests

def show():
    """Display home page"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 SPECTRA-AI Detection System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Advanced Multimodal AI Detection Platform</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🖼️ Deepfake Detection
        Analyze images for AI-generated or manipulated content using EfficientNet-B0 model.
        
        **Features:**
        - Face detection & analysis
        - Confidence scoring
        - Multi-face support
        - Processing time < 2s
        """)
    
    with col2:
        st.markdown("""
        ### 📰 Fake News Detection
        Identify misinformation using pattern recognition and cross-referencing.
        
        **Features:**
        - Pattern-based analysis
        - News source verification
        - Confidence scoring
        - Real-time processing
        """)
    
    with col3:
        st.markdown("""
        ### ⭐ Celebrity Verification
        Verify celebrity-related claims against news sources.
        
        **Features:**
        - News aggregation
        - Source credibility check
        - Context-aware analysis
        - Trending detection
        """)
    
    st.markdown("---")
    
    # System Statistics
    st.markdown("## 📊 System Overview")
    
    try:
        # Get statistics from API
        response = requests.get(
            f"{st.session_state.api_url}/history/stats",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get("analysis_stats", {})
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = stats.get("total_analyses", 0)
                st.metric("📈 Total Analyses", f"{total:,}")
            
            with col2:
                deepfake = stats.get("by_type", {}).get("deepfake_image", 0)
                st.metric("🖼️ Deepfake Scans", f"{deepfake:,}")
            
            with col3:
                fake_news = stats.get("by_type", {}).get("fake_news_text", 0)
                st.metric("📰 Fake News Checks", f"{fake_news:,}")
            
            with col4:
                celebrity = stats.get("by_type", {}).get("celebrity_verification", 0)
                st.metric("⭐ Celebrity Verifications", f"{celebrity:,}")
            
            # Verdicts
            st.markdown("### 🎯 Detection Results")
            verdicts = stats.get("deepfake_verdicts", {})
            
            col1, col2 = st.columns(2)
            with col1:
                real = verdicts.get("real", 0)
                st.metric("✅ Verified REAL", f"{real:,}", delta="Authentic")
            
            with col2:
                fake = verdicts.get("fake", 0)
                st.metric("⚠️ Detected FAKE", f"{fake:,}", delta="Manipulated", delta_color="inverse")
            
        else:
            st.warning("⚠️ Unable to fetch statistics. Check API connection.")
    
    except Exception as e:
        st.error(f"❌ Error connecting to API: {str(e)}")
        st.info("💡 Make sure your FastAPI server is running on http://localhost:8000")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🖼️ Analyze Image", use_container_width=True):
            st.session_state.navigate_to = "🖼️ Deepfake Detection"
            st.rerun()
    
    with col2:
        if st.button("📰 Check News", use_container_width=True):
            st.session_state.navigate_to = "📰 Fake News Detection"
            st.rerun()
    
    with col3:
        if st.button("⭐ Verify Celebrity Claim", use_container_width=True):
            st.session_state.navigate_to = "⭐ Celebrity Verification"
            st.rerun()
    
    st.markdown("---")
    
    # Features
    st.markdown("## ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔬 Advanced AI Models**
        - EfficientNet-B0 for deepfake detection
        - Pattern recognition for fake news
        - News aggregation for fact-checking
        
        **💾 Data Persistence**
        - MongoDB database integration
        - Complete analysis history
        - Export capabilities (CSV/JSON)
        
        **📊 Analytics Dashboard**
        - Real-time statistics
        - Trending detection
        - Performance monitoring
        """)
    
    with col2:
        st.markdown("""
        **⚡ High Performance**
        - Sub-2 second processing
        - Batch processing support
        - Optimized face detection
        
        **🔐 Secure & Reliable**
        - Data validation
        - Error handling
        - Audit trail
        
        **📈 Comprehensive Reporting**
        - Hourly activity analysis
        - Anomaly detection
        - Confidence distribution
        """)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    ### 💡 Getting Started
    
    1. **Select a detection type** from the sidebar
    2. **Upload your content** (image, text, or claim)
    3. **Get instant results** with confidence scores
    4. **View analytics** and historical data
    5. **Export reports** for further analysis
    
    *Need help? Check the documentation or contact support.*
    """)
