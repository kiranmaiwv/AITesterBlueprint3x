# conftest.py
import pytest
import requests
from config import APIConfig

@pytest.fixture(scope="session")
def api_session():
    """
    Fixture providing a robust requests session object.
    It sets up base headers like Content-Type and Base URL.
    """
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-Key': APIConfig.API_KEY
    })
    yield session
    # Teardown: Ensure the session is closed after all tests run
    session.close()


@pytest.fixture(scope="module")
def auth_token(api_session):
    """
    Fixture to obtain a valid authentication token before testing.
    This simulates the initial login handshake.
    """
    print("\n--- 🔑 Acquiring Authentication Token ---")
    # Hypothetical login call to get a JWT token
    login_url = f"{APIConfig.BASE_URL}/api/v1/auth/login"
    payload = {"username": "testuser", "password": "password123"}
    
    response = api_session.post(login_url, json=payload)
    response.raise_for_status() # Fails the test if status is 4xx/5xx
    
    data = response.json()
    token = data.get("access_token", "MOCK_DUMMY_TOKEN")
    
    # Yield the token, which subsequent tests will use
    yield token
    
    print("--- ✅ Token session ended ---")


@pytest.fixture(scope="function")
def sample_reservation_id(api_session, auth_token):
    """
    Fixture to ensure a clean, reusable resource ID for testing.
    It performs the creation (POST) and yields the ID, 
    and then cleans up (DELETE) after the test finishes.
    """
    # 1. Setup: Create a known resource
    initial_payload = {
        "check_in_date": "2025-10-01",
        "check_out_date": "2025-10-03",
        "guest_name": "Test User",
        "room_type": "Standard"
    }
    
    # Use the dedicated API client helper
    response = api_session.post(
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}", 
        json=initial_payload, 
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    response.raise_for_status()
    
    reservation_id = response.json().get("id")
    
    # 2. Yield the resource for use in the test
    yield reservation_id
    
    # 3. Teardown: Clean up the created resource
    api_session.delete(
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/{reservation_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
