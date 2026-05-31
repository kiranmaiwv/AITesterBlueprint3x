# conftest.py
import pytest
import requests
import responses
import json
from config import APIConfig

# Global counter for reservation IDs
_reservation_counter = 1000


@pytest.fixture(scope="session", autouse=True)
def mock_api():
    """
    Automatically mock all API endpoints for testing without a real server.
    This fixture is automatically used by all tests.
    """
    global _reservation_counter
    _reservation_counter = 1000  # Reset counter
    
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()
    
    # Mock authentication endpoint
    rsps.add(
        responses.POST,
        f"{APIConfig.BASE_URL}/api/v1/auth/login",
        json={"access_token": "MOCK_JWT_TOKEN_12345", "token_type": "Bearer"},
        status=200
    )
    
    # Mock POST /api/reservations (create reservation)
    def post_reservation_callback(request):
        global _reservation_counter
        payload = json.loads(request.body)
        
        # Validate required fields for error cases
        if "check_in_date" not in payload:
            return (400, {}, json.dumps({"Error": "Missing required field: check_in_date"}))
        
        # Check for conflict scenario
        if payload.get("check_in_date") == payload.get("check_out_date"):
            return (409, {}, json.dumps({"Error": "Check-in and check-out dates cannot be the same"}))
        
        _reservation_counter += 1
        reservation_id = _reservation_counter
        response_data = {
            "id": reservation_id,
            "check_in_date": payload.get("check_in_date"),
            "check_out_date": payload.get("check_out_date"),
            "guest_name": payload.get("guest_name"),
            "room_type": payload.get("room_type"),
            "status": "CONFIRMED",
            "created_at": "2025-05-30T10:00:00Z"
        }
        return (201, {}, json.dumps(response_data))
    
    rsps.add_callback(
        responses.POST,
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}",
        callback=post_reservation_callback,
        content_type="application/json"
    )
    
    # Mock GET /api/reservations/detail/{id} (get reservation)
    def get_reservation_callback(request):
        reservation_id = request.url.split("/")[-1]
        response_data = {
            "id": int(reservation_id),
            "check_in_date": "2025-10-01",
            "check_out_date": "2025-10-03",
            "guest_name": "Test User",
            "room_type": "Standard",
            "status": "CONFIRMED",
            "created_at": "2025-05-30T10:00:00Z"
        }
        return (200, {}, json.dumps(response_data))
    
    rsps.add_callback(
        responses.GET,
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/detail/",
        callback=get_reservation_callback,
        content_type="application/json"
    )
    
    # Also add regex pattern for GET with ID
    import re
    rsps.add_callback(
        responses.GET,
        re.compile(f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/detail/\\d+"),
        callback=get_reservation_callback,
        content_type="application/json"
    )
    
    # Mock PUT /api/reservations/{id} (update reservation)
    def put_reservation_callback(request):
        reservation_id = request.url.split("/")[-1]
        payload = json.loads(request.body)
        response_data = {
            "id": int(reservation_id),
            "check_in_date": "2025-10-01",
            "check_out_date": "2025-10-03",
            "guest_name": "Test User",
            "room_type": "Standard",
            "status": payload.get("status", "UPDATED"),
            "notes": payload.get("notes", ""),
            "reason": payload.get("reason", ""),
            "updated_at": "2025-05-30T11:00:00Z"
        }
        return (200, {}, json.dumps(response_data))
    
    rsps.add_callback(
        responses.PUT,
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/",
        callback=put_reservation_callback,
        content_type="application/json"
    )
    
    # Also add pattern for PUT with ID (for dynamic IDs)
    import re
    rsps.add_callback(
        responses.PUT,
        re.compile(f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/\\d+"),
        callback=put_reservation_callback,
        content_type="application/json"
    )
    
    # Mock DELETE /api/reservations/{id}
    rsps.add(
        responses.DELETE,
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/",
        json={},
        status=204,
        match_querystring=False
    )
    
    # Also add regex pattern for DELETE with ID
    rsps.add_callback(
        responses.DELETE,
        re.compile(f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}/\\d+"),
        callback=lambda request: (204, {}, ""),
        content_type="application/json"
    )
    
    yield
    rsps.stop()
    rsps.reset()


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
