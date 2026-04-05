# streamlit_app.py
"""
SPECTRA-AI Streamlit Dashboard
Main application with multipage navigation
"""

import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SPECTRA-AI Detection",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: 600;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# Sidebar
with st.sidebar:
    st.markdown("# 🎯 SPECTRA-AI")
    st.markdown("**Multimodal Detection System**")
    st.markdown("---")
    
    # API Configuration
    st.markdown("### ⚙️ Configuration")
    api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="FastAPI backend URL"
    )
    st.session_state.api_url = api_url
    
    # Test connection
    if st.button("🔍 Test Connection"):
        import requests
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected!")
            else:
                st.error(f"❌ Error: {response.status_code}")
        except Exception as e:
            import traceback 
            st.code(traceback.format_exc())
            st.error(f"❌ Connection failed: {str(e)}")
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 📑 Navigation")
    
    # Initialize session state for page
    if 'page_selector' not in st.session_state:
        st.session_state.page_selector = "🏠 Home"

    if "navigate_to" in st.session_state:
        st.session_state.page_selector = st.session_state.navigate_to
        del st.session_state.navigate_to
    page = st.radio(
        "Go to:",
        ["🏠 Home", "🖼️ Deepfake Detection", "📰 Fake News Detection",
         "⭐ Celebrity Verification", "📊 Analytics", "📜 History", "⚙️ Admin"],
        key="page_selector",
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    # System Info
    st.markdown("### 📈 System Status")
    import requests
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            st.metric("Status", "🟢 Online")
            st.metric("Version", data.get("version", "2.0.0"))
        else:
            st.metric("Status", "🔴 Offline")
    except:
        st.metric("Status", "🔴 Offline")
    
    st.markdown("---")
    st.markdown("**Built with ❤️ by SPECTRA-AI**")
    st.markdown(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')} IST*")

# Main content based on navigation
try:
    if st.session_state.page_selector == "🏠 Home":
        from app_pages import home
        home.show()
    elif st.session_state.page_selector == "🖼️ Deepfake Detection":
        from app_pages import deepfake
        deepfake.show()
    elif st.session_state.page_selector == "📰 Fake News Detection":
        from app_pages import fake_news
        fake_news.show()
    elif st.session_state.page_selector == "⭐ Celebrity Verification":
        from app_pages import celebrity
        celebrity.show()
    elif st.session_state.page_selector == "📊 Analytics":
        from app_pages import analytics
        analytics.show()
    elif st.session_state.page_selector == "📜 History":
        from app_pages import history
        history.show()
    elif st.session_state.page_selector == "⚙️ Admin":
        from app_pages import admin
        admin.show()
except Exception as e:
    import traceback
    st.error(f"❌ Error loading page:")
    st.code(traceback.format_exc())
    st.error("Make sure all page files are in the 'app_pages/' folder")
    
    # Debug info
    with st.expander("🔍 Debug Information"):
        import sys
        import os
        st.write("**Python Path:**")
        st.code("\n".join(sys.path))
        st.write("**Current Directory:**")
        st.code(os.getcwd())
        st.write("**Files in current directory:**")
        st.code("\n".join(os.listdir(".")))
        if os.path.exists("app_pages"):
            st.write("**Files in app_pages/ directory:**")
            st.code("\n".join(os.listdir("app_pages")))
