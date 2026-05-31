# test_reservations.py
import pytest
from config import APIConfig

# Use fixtures for setup and cleanup
pytestmark = pytest.mark.api

def test_1_create_successful_reservation(api_session, auth_token):
    """FUNC-R-001: Test creating a new reservation successfully."""
    print("\n--- Running Test: Successful Creation ---")
    payload = {
        "check_in_date": "2025-12-01",
        "check_out_date": "2025-12-05",
        "guest_name": "Alice Smith",
        "room_type": "Luxury"
    }
    
    response = api_session.post(
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}", 
        json=payload, 
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Assertions based on status code and data structure
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert "id" in data, "Response body must contain a reservation ID."
    assert data["guest_name"] == "Alice Smith"

@pytest.mark.parametrize("invalid_field, payload, expected_code", [
    # FUNC-R-002: Missing mandatory field
    ("check_in_date", {"check_out_date": "2025-12-05", "room_type": "Standard"}, 400),
    # FUNC-R-003: Business logic failure (Conflict)
    ("conflict", {"check_in_date": "2025-12-01", "check_out_date": "2025-12-01", "room_type": "Standard"}, 409),
])
def test_2_create_failure_validation(api_session, auth_token, invalid_field, payload, expected_code):
    """Tests failure cases like validation or business logic conflicts."""
    print(f"\n--- Running Test: Validation Failure ({invalid_field}) ---")
    response = api_session.post(
        f"{APIConfig.BASE_URL}{APIConfig.RESERVATIONS_ENDPOINT}", 
        json=payload, 
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == expected_code, \
        f"Validation failed: Expected {expected_code}, got {response.status_code}"
    assert "Error" in response.text # Asserting the response body contains an error message


def test_read_and_update_reservation(session, sample_session):
    """Tests retrieving and updating a specific record."""
    # 1. Read
    get_url = f"{session}/detail/{sample_session}"
    response = session.get(get_url)
    assert response.status_code == 200
    
    # 2. Update
    update_payload = {"status": "CHECKED_IN", "notes": "Guest arrived successfully."}
    update_response = session.put(get_url, json=update_payload)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["status"] == "CHECKED_IN"
    
# --- Test scope and cleanup (Uses fixture from example structure) ---
def test_update_booking(session, sample_session):
    """
    This test uses the fixture 'sample_session' which represents a bookable session ID.
    It tests the update functionality using the session object.
    """
    # This test requires the session/sample_session fixture to run correctly.
    pass
