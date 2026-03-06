"""
FastAPI Tests for Mergington High School Management System

Tests follow the AAA (Arrange-Act-Assert) pattern for clarity and consistency.
Each test clearly separates setup, execution, and verification phases.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def fresh_activities(monkeypatch):
    """Fixture that provides fresh activity data for each test"""
    from app import activities
    
    # Store original state
    original = {key: {
        "description": value["description"],
        "schedule": value["schedule"],
        "max_participants": value["max_participants"],
        "participants": value["participants"].copy()
    } for key, value in activities.items()}
    
    yield
    
    # Restore original state after test
    for activity_name, activity_data in original.items():
        activities[activity_name]["participants"] = activity_data["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        # Arrange
        expected_redirect_url = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivitiesEndpoint:
    """Tests for retrieving all activities"""

    def test_get_all_activities_returns_dict(self, client):
        # Arrange
        # (activity data is pre-loaded in the app)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)

    def test_get_activities_contains_expected_activities(self, client):
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Debate Club",
            "Robotics Club",
            "Art Studio",
            "Music Ensemble"
        ]
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity in expected_activities:
            assert activity in activities_data

    def test_get_activities_returns_activity_details(self, client):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        first_activity = activities_data["Chess Club"]
        for field in required_fields:
            assert field in first_activity

    def test_get_activities_participants_is_list(self, client):
        # Arrange
        # (activity data is pre-loaded)
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity in activities_data.items():
            assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for signing up students for activities"""

    def test_signup_success(self, client, fresh_activities):
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"

    def test_signup_adds_participant_to_activity(self, client, fresh_activities):
        # Arrange
        from app import activities
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert new_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_activity_not_found(self, client):
        # Arrange
        nonexistent_activity = "Physics Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student_fails(self, client, fresh_activities):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client, fresh_activities):
        # Arrange
        email = "multiactivestudent@mergington.edu"
        activity_names = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        responses = [
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            for activity in activity_names
        ]
        
        # Assert
        from app import activities
        for response in responses:
            assert response.status_code == 200
        
        for activity_name in activity_names:
            assert email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for unregistering students from activities"""

    def test_unregister_success(self, client, fresh_activities):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email_to_remove} from {activity_name}"

    def test_unregister_removes_participant(self, client, fresh_activities):
        # Arrange
        from app import activities
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert email_to_remove not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_unregister_activity_not_found(self, client):
        # Arrange
        nonexistent_activity = "Physics Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_signed_up(self, client):
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": non_participant_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client, fresh_activities):
        # Arrange
        from app import activities
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # First signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert email in activities[activity_name]["participants"]
        
        # Act - unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act - signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios"""

    def test_full_student_lifecycle(self, client, fresh_activities):
        # Arrange
        from app import activities
        student_email = "lifecycle@mergington.edu"
        activity = "Programming Class"
        initial_participants = len(activities[activity]["participants"])
        
        # Act - Get activities
        get_response = client.get("/activities")
        assert get_response.status_code == 200
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student_email}
        )
        
        # Act - Verify signup
        activities_check = client.get("/activities").json()
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": student_email}
        )
        
        # Assert
        assert signup_response.status_code == 200
        assert student_email in activities_check[activity]["participants"]
        assert unregister_response.status_code == 200
        assert student_email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_participants

    def test_concurrent_signups_different_activities(self, client, fresh_activities):
        # Arrange
        from app import activities
        student_email = "concurrent@mergington.edu"
        activities_to_join = ["Chess Club", "Robotics Club", "Art Studio"]
        
        # Act
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # Assert
        for activity in activities_to_join:
            assert student_email in activities[activity]["participants"]
