import streamlit as st

# Page config
st.set_page_config(
    page_title="SwackTech API Hub",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .api-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    .centered-text {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='centered-text'>SwackTech API Hub</h1>", unsafe_allow_html=True)
st.markdown("<p class='centered-text'>Enterprise-Grade Blockchain Analytics APIs</p>", unsafe_allow_html=True)

# Main API Section
st.markdown("## Available APIs")

# Ethereum Loan Analytics API
with st.container():
    st.markdown("<div class='api-card'>", unsafe_allow_html=True)
    st.subheader("📊 Ethereum Loan Analytics API")
    st.markdown("""
    Comprehensive analytics for Ethereum lending protocols, providing real-time insights into:
    - Vault statistics and performance metrics
    - User position tracking and analysis
    - Multi-token support with USD value calculations
    - Historical data access
    
    **Key Features:**
    - Real-time data updates
    - Comprehensive error handling
    - Automatic data validation
    - High-performance caching
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[📚 API Documentation](https://ethereum.swacktech.com/api/docs)")
    with col2:
        st.markdown("[🔍 API Reference](https://ethereum.swacktech.com/api/redoc)")
    with col3:
        st.markdown("[⚙️ OpenAPI Spec](https://ethereum.swacktech.com/api/openapi.json)")
    st.markdown("</div>", unsafe_allow_html=True)

# Integration Section
st.markdown("## Quick Integration")
st.code("""
# Example: Fetch vault statistics
import requests

VAULT_ADDRESS = "0x..."  # Your vault address
response = requests.get(
    f"https://ethereum.swacktech.com/api/v1/vaults/{VAULT_ADDRESS}/stats"
)
stats = response.json()
""", language="python")

# Features Overview
st.markdown("## Why Choose SwackTech APIs?")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### Technical Excellence
    - RESTful API design
    - Comprehensive documentation
    - Production-ready endpoints
    - Enterprise-grade reliability
    """)

with col2:
    st.markdown("""
    #### Developer Experience
    - Easy integration
    - Clear documentation
    - Predictable responses
    - Helpful error messages
    """)

# Footer
st.markdown("---")
st.markdown("""
<div class='centered-text'>
    <p>© 2025 SwackTech. All rights reserved.</p>
    <p>For support or inquiries, please visit our <a href="https://ethereum.swacktech.com/api/docs">documentation</a>.</p>
</div>
""", unsafe_allow_html=True)
