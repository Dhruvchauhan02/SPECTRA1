# pages/deepfake.py
"""
Deepfake Detection page for SPECTRA-AI
"""

import streamlit as st
import requests
from PIL import Image
import io
import time

def show():
    """Display deepfake detection page"""
    
    st.markdown("# 🖼️ Deepfake Image Detection")
    st.markdown("Upload an image to analyze for AI-generated or manipulated content")
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png"],
        help="Upload a JPG or PNG image for analysis"
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if uploaded_file is not None:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Image info
            st.markdown(f"""
            **Image Details:**
            - Filename: `{uploaded_file.name}`
            - Size: {image.size[0]} x {image.size[1]} pixels
            image = Image.open(uploaded_file)
            file_ext = uploaded_file.name.rsplit(".", 1)[-1].upper() if "." in uploaded_file.name else "Unknown"
            - Format: {file_ext}
            """)
    
    with col2:
        if uploaded_file is not None:
            # Analyze button
            if st.button("🔍 Analyze Image", type="primary", use_container_width=True):
                analyze_image(uploaded_file)
    
    st.markdown("---")
    
    # Info section
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        ### Detection Process
        
        1. **Face Detection**: Identifies faces in the image
        2. **Feature Extraction**: Analyzes facial features using EfficientNet-B0
        3. **AI Analysis**: Classifies as REAL or FAKE with confidence score
        4. **Result Compilation**: Aggregates results across all detected faces
        
        ### Confidence Levels
        
        - **90-100%**: Very High Confidence
        - **70-89%**: High Confidence
        - **50-69%**: Medium Confidence
        - **< 50%**: Uncertain
        
        ### Best Practices
        
        - Use clear, well-lit images
        - Ensure faces are visible and not obscured
        - Higher resolution images yield better results
        - Multiple faces are supported
        """)


def analyze_image(uploaded_file):
    """Analyze uploaded image"""
    
    with st.spinner("🔄 Analyzing image..."):
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Prepare request
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            
            # Send request
            start_time = time.time()
            response = requests.post(
                f"{st.session_state.api_url}/analyze-image",
                files=files,
                timeout=30
            )
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                display_results(result, processing_time)
            elif response.status_code == 422:
                # Person gate rejection
                try:
                    detail = response.json().get("detail", {})
                    detected = detail.get("detected_objects", [])
                except Exception:
                    detail = {}
                    detected = []

                st.error("⚠️ No Person Detected")
                st.markdown(
                    """
                    This image does **not** appear to contain a person or human face.  
                    SPECTRA can only analyse images of real people for deepfake manipulation.
                    """
                )
                if detected:
                    st.info(f"**What was found in the image:** {', '.join(detected)}")

                st.markdown("### Tips for a valid upload")
                st.markdown(
                    "- Upload a photo that clearly shows a **human face or body**\n"
                    "- Avoid images of objects, animals, landscapes, or abstract art\n"
                    "- Make sure the image is well-lit and not heavily cropped\n"
                    "- Minimum image size is 80 × 80 px"
                )
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The server might be overloaded.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection error. Make sure the API server is running.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")


def display_results(result, client_time):
    """Display analysis results"""
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    verdict = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0)
    spectra_score = result.get("spectra_score", 0)
    processing_time = result.get("processing_time_ms", 0)
    faces_detected = result.get("faces_detected", 0)
    if faces_detected == 0:
        st.error("❌ No face detected in image")
        st.info("Please upload a clear human face image")
        return
    faces = result.get("faces", [])

    global_conf = 0.0
    if faces:
        p_fake = faces[0].get("final_p", 0)
        verdict = faces[0].get("verdict", "UNKNOWN")

    if verdict == "REAL":
        global_conf = 1 - p_fake
    else:
        global_conf = p_fake
    # Verdict display
    if verdict == "REAL":
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(f"### ✅ VERDICT: **REAL**")
        st.markdown("This image appears to be authentic.")
        st.markdown('</div>', unsafe_allow_html=True)
    elif verdict == "FAKE":
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown(f"### ⚠️ VERDICT: **FAKE**")
        st.markdown("This image appears to be AI-generated or manipulated.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown(f"### ❓ VERDICT: **UNCERTAIN**")
        st.markdown("Unable to determine with confidence.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Confidence", f"{confidence:.1%}")
    
    with col2:
        st.metric("📊 SPECTRA Score", f"{spectra_score}/100")
    
    with col3:
        st.metric("👤 Faces Detected", faces_detected)
    
    with col4:
        st.metric("⚡ Processing Time", f"{processing_time}ms")
    
    # Confidence bar
    st.markdown("### Confidence Level")
    st.progress(global_conf )
    
    # Detailed results
    if faces_detected > 0:
        st.markdown("### 👥 Face Analysis")
        
        faces = result.get("faces", [])
        for i, face in enumerate(faces):
            with st.expander(f"Face {i+1} Details"):
                p_fake = face.get("final_p", 0)
                face_verdict = face.get("verdict", "UNKNOWN")
                if face_verdict == "REAL":
                    face_conf = 1 - p_fake
                else:
                    face_conf = p_fake
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Verdict", face_verdict)
                    st.metric("Confidence", f"{face_conf:.3f}")
                
                with col2:
                    bbox = face.get("bbox", [])
                    if bbox:
                        st.write(f"**Position:** x={bbox[0]}, y={bbox[1]}")
                        st.write(f"**Size:** {bbox[2]}x{bbox[3]}")
    
    # Technical details
    with st.expander("🔬 Technical Details"):
        st.json(result)
    
    # Download results
    st.markdown("### 💾 Export Results")
    
    import json
    result_json = json.dumps(result, indent=2)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download JSON",
            data=result_json,
            file_name=f"spectra_result_{result.get('request_id', 'unknown')[:8]}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Create simple text report
        report = f"""
SPECTRA-AI Detection Report
==========================

Verdict: {verdict}
Confidence: {confidence:.1%}
SPECTRA Score: {spectra_score}/100
Faces Detected: {faces_detected}
Processing Time: {processing_time}ms

Request ID: {result.get('request_id', 'N/A')}
Timestamp: {result.get('timestamp', 'N/A')}

Analysis completed successfully.
        """
        
        st.download_button(
            label="📝 Download Report",
            data=report,
            file_name=f"spectra_report_{result.get('request_id', 'unknown')[:8]}.txt",
            mime="text/plain",
            use_container_width=True
        )