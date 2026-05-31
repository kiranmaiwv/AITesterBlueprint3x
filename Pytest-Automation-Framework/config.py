# config.py

# Load environment variables from a .env file
import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    # Base URL for all API calls
    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Credentials (Should be loaded securely)
    API_KEY = os.getenv("API_KEY", "dummy_key_for_testing")
    
    # Define common resource paths
    RESERVATIONS_ENDPOINT = "/api/reservations"
