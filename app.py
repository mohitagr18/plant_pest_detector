# app.py
# Production Streamlit app for Google Cloud Run

# ============================================================================
# CRITICAL: Load environment variables FIRST before any other imports
# ============================================================================
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from PIL import Image
from io import BytesIO
import os

# NOW import your modules (after .env is loaded)
from src.plant_pest_detector import PlantPestDetector
from src.qa_engine_agentic import (
    create_agentic_session,
    generate_brief_assessment,
    generate_treatment_recommendations,
    answer_menu_option,
    ask_custom_question,
    get_menu_options
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="🌱 Agricultural Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main > div {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Better spacing on mobile */
    .stButton button {
        width: 100%;
        margin-top: 0.5rem;
    }
    
    /* Compact file uploader */
    .uploadedFile {
        margin-bottom: 1rem;
    }
    
    /* Better readability */
    .stMarkdown {
        line-height: 1.6;
    }
    
    /* Product links styling */
    a {
        color: #FF9900;
        text-decoration: none;
        font-weight: 500;
    }
    
    /* Fix report header sizes - all h2 should be normal size */
    .stMarkdown h2 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Fix h1 in reports */
    .stMarkdown h1 {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    
    /* Tab labels should be bigger */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.1rem !important;
        padding: 0.75rem 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'stage' not in st.session_state:
    st.session_state.stage = 'upload'  # upload -> details -> recommendations

if 'detection_results' not in st.session_state:
    st.session_state.detection_results = None

if 'context' not in st.session_state:
    st.session_state.context = None

if 'treatment_shown' not in st.session_state:
    st.session_state.treatment_shown = False

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def load_detector():
    """Cache the detector model"""
    return PlantPestDetector()

def reset_session():
    """Reset the entire session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.title("🌱 Agricultural Assistant")
    st.markdown("*AI-powered pest & disease detection with personalized treatment recommendations*")
    
    # ========================================================================
    # STAGE 1: IMAGE UPLOAD
    # ========================================================================
    
    if st.session_state.stage == 'upload':
        st.markdown("---")
        st.subheader("📸 Upload Plant Image")
        st.markdown("Take a photo of your plant showing signs of pest or disease")
        
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=['jpg', 'jpeg', 'png'],
            help="Best results with clear, well-lit photos"
        )
        
        if uploaded_file:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Analyze button
            if st.button("🔍 Analyze Image", type="primary"):
                with st.spinner("Analyzing image..."):
                    # Convert to bytes
                    buffer = BytesIO()
                    image.save(buffer, format='JPEG')
                    image_bytes = buffer.getvalue()
                    
                    # Detect pest/disease
                    detector = load_detector()
                    pest, severity, plant, confidence, subject_type = detector.identify(image_bytes)
                    
                    # Generate brief assessment
                    brief_assessment = generate_brief_assessment(pest, severity, plant)
                    
                    # Store results
                    st.session_state.detection_results = {
                        'pest': pest,
                        'severity': severity,
                        'plant': plant,
                        'confidence': confidence,
                        'subject_type': subject_type,
                        'brief_assessment': brief_assessment,
                        'image': image
                    }
                    
                    # Move to next stage
                    st.session_state.stage = 'details'
                    st.rerun()
    
    # ========================================================================
    # STAGE 2: SHOW RESULTS & GET DETAILS
    # ========================================================================
    
    elif st.session_state.stage == 'details':
        results = st.session_state.detection_results
        
        # Show detection results
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(results['image'], use_container_width=True)
        
        with col2:
            st.markdown("### ✓ Detection Results")
            st.markdown(f"**Issue:** {results['pest']}")
            st.markdown(f"**Severity:** {results['severity']}")
            st.markdown(f"**Plant:** {results['plant'] if results['plant'] != 'Unknown' else 'Not identified'}")
            
            st.markdown("---")
            st.warning(f"⚠️ {results['brief_assessment']}")
        
        # Get personalized details
        st.markdown("---")
        st.subheader("📝 Get Personalized Treatment Plan")
        st.markdown("I can generate detailed treatment and product recommendations based on your soil and weather data")
        
        with st.form("details_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                plant_input = st.text_input(
                    "Plant/Crop",
                    value=results['plant'] if results['plant'] != 'Unknown' else '',
                    placeholder="e.g., tomato"
                )
            
            with col2:
                zipcode = st.text_input(
                    "Zip Code",
                    placeholder="e.g., 92336",
                    max_chars=5
                )
            
            with col3:
                infestation = st.selectbox(
                    "Infestation Level",
                    options=['low', 'medium', 'high'],
                    index=1
                )
            
            submitted = st.form_submit_button("Generate Treatment Plan", type="primary")
            
            if submitted:
                if not zipcode or len(zipcode) != 5:
                    st.error("Please enter a valid 5-digit zip code")
                elif not plant_input:
                    st.error("Please enter the plant type")
                else:
                    with st.spinner("Generating personalized treatment plan..."):
                        # Create agentic session
                        context = create_agentic_session(
                            pest_or_disease=results['pest'],
                            severity=results['severity'],
                            plant_type=plant_input,
                            infestation_level=infestation,
                            zipcode=zipcode
                        )
                        
                        # Generate treatment recommendations
                        treatment = generate_treatment_recommendations(context)
                        
                        # Store context and treatment
                        st.session_state.context = context
                        st.session_state.treatment = treatment
                        st.session_state.stage = 'recommendations'
                        st.rerun()
    
    # ========================================================================
    # STAGE 3: SHOW TREATMENT RECOMMENDATIONS + MENU
    # ========================================================================
    
    elif st.session_state.stage == 'recommendations':
        # Back button
        if st.button("← New Analysis"):
            reset_session()
        
        # Show detection results + image at top
        results = st.session_state.detection_results
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(results['image'], use_container_width=True)
        
        with col2:
            st.markdown("### ✓ Detection Results")
            st.markdown(f"**Issue:** {results['pest']}")
            st.markdown(f"**Severity:** {results['severity']}")
            st.markdown(f"**Plant:** {results['plant'] if results['plant'] != 'Unknown' else 'Not identified'}")
            
            st.markdown("---")
            st.warning(f"⚠️ {results['brief_assessment']}")
        
        st.markdown("---")
        
        # Display treatment recommendations
        st.markdown(st.session_state.treatment)
        
        st.markdown("---")
        
        # NOW show the menu
        st.subheader("What else would you like to know?")
        
        menu_options = get_menu_options()
        
        # Create tabs for different options
        tab_labels = [
            "🪨 Soil Impact",
            "🌤️ Weather Timing",
            "👀 Monitoring",
            "📄 Full Report",
            "💬 Ask Question"
        ]
        
        tabs = st.tabs(tab_labels)
        
        # Tab 1: Soil Impact
        with tabs[0]:
            if st.button("Show Soil Analysis", key="soil_btn"):
                with st.spinner("Analyzing soil impact..."):
                    answer = answer_menu_option(st.session_state.context, 2)
                    st.session_state.conversation_history.append(("Soil Impact", answer))
                    st.markdown(answer)
        
        # Tab 2: Weather Timing
        with tabs[1]:
            if st.button("Show Weather Timing", key="weather_btn"):
                with st.spinner("Analyzing weather conditions..."):
                    answer = answer_menu_option(st.session_state.context, 3)
                    st.session_state.conversation_history.append(("Weather Timing", answer))
                    st.markdown(answer)
        
        # Tab 3: Monitoring
        with tabs[2]:
            if st.button("Show Monitoring Guide", key="monitor_btn"):
                with st.spinner("Generating monitoring guide..."):
                    answer = answer_menu_option(st.session_state.context, 4)
                    st.session_state.conversation_history.append(("Monitoring", answer))
                    st.markdown(answer)
        
        # Tab 4: Full Report
        with tabs[3]:
            if st.button("Generate Full Report", key="report_btn"):
                with st.spinner("Generating comprehensive report..."):
                    answer = answer_menu_option(st.session_state.context, 5)
                    st.session_state.conversation_history.append(("Full Report", answer))
                    st.markdown(answer)
        
        # Tab 5: Custom Question
        with tabs[4]:
            question = st.text_input("Ask a custom question:", key="custom_q")
            if st.button("Ask", key="ask_btn") and question:
                with st.spinner("Thinking..."):
                    answer = ask_custom_question(st.session_state.context, question)
                    st.session_state.conversation_history.append((question, answer))
                    st.markdown(answer)
        
        # Show conversation history
        if st.session_state.conversation_history:
            st.markdown("---")
            st.subheader("📜 Conversation History")
            for q, a in st.session_state.conversation_history:
                with st.expander(f"💬 {q}"):
                    st.markdown(a)


if __name__ == "__main__":
    main()
