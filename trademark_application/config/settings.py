import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_VERSION = "2024-08-01-preview"

# AZURE_ENDPOINT = st.secrets["AZURE_ENDPOINT"]
# AZURE_API_KEY = st.secrets["AZURE_API_KEY"]


def get_azure_client() -> AzureOpenAI:
    """
    Get an Azure OpenAI client instance
    """
    return AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
    )


# ML Model Thresholds
SEMANTIC_SIMILARITY_THRESHOLD = 0.87
PHONETIC_SIMILARITY_THRESHOLD = 85
PARTIAL_PHONETIC_THRESHOLD = 55
GOODS_SERVICES_SIMILARITY_THRESHOLD = 0.3

# Document Processing Settings
MAX_TOKENS_PER_CHUNK = 1500
EXCLUDE_HEADER_FOOTER = True
