# pages/fake_news.py
"""
Fake News Detection page for SPECTRA-AI
"""

import streamlit as st
import requests
import time

def show():
    """Display fake news detection page"""
    
    st.markdown("# 📰 Fake News Detection")
    st.markdown("Analyze text content for misinformation and fake news patterns")
    
    st.markdown("---")
    
    # Load example text into textarea if one was selected
    default_text = st.session_state.pop("example_text", "")

    # Text input
    text_input = st.text_area(
        "Enter text to analyze:",
        value=default_text,
        height=200,
        placeholder="Paste news article, social media post, or any text content here...",
        help="Enter the text you want to check for fake news patterns"
    )
    
    # Character count
    char_count = len(text_input)
    st.caption(f"Characters: {char_count}")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        analyze_button = st.button(
            "🔍 Analyze Text",
            type="primary",
            use_container_width=True,
            disabled=(char_count < 10)
        )
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()
    
    if analyze_button and text_input:
        analyze_text(text_input)

    st.markdown("---")

    # Examples
    st.markdown("### 📝 Example Texts")

    examples = {
        "Breaking News": "BREAKING: Scientists discover cure for all diseases! Doctors don't want you to know this secret! Share before it's deleted!",
        "Product Ad": "This one weird trick will make you rich overnight! Click here to find out how millionaires don't want you to know this!",
        "Real News": "The World Health Organization released their annual report today, highlighting progress in global vaccination efforts and disease prevention strategies.",
    }

    for title, example_text in examples.items():
        if st.button(f"Try: {title}", use_container_width=True):
            st.session_state.example_text = example_text
            st.rerun()
    
    # Info section
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        ### Detection Methods
        
        **Pattern Recognition:**
        - Clickbait phrases
        - Emotional manipulation
        - Urgent language
        - Unverifiable claims
        
        **Indicators of Fake News:**
        - ALL CAPS text
        - Excessive punctuation!!!
        - Sensational language
        - Lack of credible sources
        - Too-good-to-be-true claims
        
        ### Confidence Levels
        
        - **High**: Strong indicators detected
        - **Medium**: Some suspicious patterns
        - **Low**: Appears legitimate
        
        ### Best Practices
        
        - Provide complete context
        - Include multiple paragraphs for better analysis
        - Check multiple sources
        - Verify with fact-checking websites
        """)


def analyze_text(text):
    """Analyze text for fake news"""
    
    with st.spinner("🔄 Analyzing text..."):
        try:
            # Prepare request
            payload = {"text": text}
            
            start_time = time.time()
            response = requests.post(
                f"{st.session_state.api_url}/analyze-text",
                json=payload,
                timeout=10
            )
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                display_results(result, processing_time)
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_results(result, processing_time):
    """Display analysis results"""
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    verdict = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0)
    patterns = result.get("patterns_detected", [])
    
    # Verdict display
    if verdict == "LIKELY FAKE":
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown(f"### ⚠️ VERDICT: **{verdict}**")
        st.markdown("This text shows strong indicators of fake news or misinformation.")
        st.markdown('</div>', unsafe_allow_html=True)
    elif verdict == "POSSIBLY FAKE":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown(f"### ❓ VERDICT: **{verdict}**")
        st.markdown("This text contains some suspicious patterns.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(f"### ✅ VERDICT: **{verdict}**")
        st.markdown("This text appears to be legitimate.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎯 Confidence", f"{confidence:.1%}")
    
    with col2:
        st.metric("🚩 Patterns Found", len(patterns))
    
    with col3:
        st.metric("⚡ Processing Time", f"{processing_time:.0f}ms")
    
    # Confidence bar
    st.markdown("### Confidence Level")
    st.progress(confidence)
    
    # Patterns detected
    if patterns:
        st.markdown("### 🚩 Detected Patterns")
        
        for pattern in patterns:
            st.markdown(f"- ⚠️ **{pattern}**")
    else:
        st.info("✅ No suspicious patterns detected")
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    
    if confidence > 0.7:
        st.warning("""
        **High risk of fake news detected:**
        - Verify with multiple credible sources
        - Check fact-checking websites
        - Look for original sources
        - Be skeptical of claims that seem too extreme
        """)
    elif confidence > 0.4:
        st.info("""
        **Some suspicious elements found:**
        - Cross-reference with other sources
        - Check the publication date
        - Verify the author's credibility
        - Look for supporting evidence
        """)
    else:
        st.success("""
        **Text appears legitimate:**
        - Still verify important claims
        - Check the source credibility
        - Look for citations and references
        """)
    
    # Download results
    st.markdown("### 💾 Export Results")
    
    import json
    result_json = json.dumps(result, indent=2)
    
    st.download_button(
        label="📥 Download JSON Report",
        data=result_json,
        file_name="fake_news_analysis.json",
        mime="application/json",
        use_container_width=True
    )
