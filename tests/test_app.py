"""
Test suite for the Mergington High School Management System API
Using AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from src.app import activities
    
    # Save original state
    original_activities = {
        activity: {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy()
        }
        for activity, activity_data in activities.items()
    }
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Basketball Team"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Soccer Club"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signup fails if student is already registered"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_multiple_activities_signup(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        # Arrange
        email = "versatile_student@mergington.edu"
        
        # Act - Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Act - Sign up for second activity
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Art Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
    
    def test_remove_participant_actually_removes(self, client, reset_activities):
        """Test that remove actually removes the participant"""
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_remove_nonexistent_activity(self, client, reset_activities):
        """Test removal from non-existent activity returns 404"""
        # Arrange - No special setup needed
        
        # Act
        response = client.delete(
            "/activities/Nonexistent Club/participants/student@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_remove_nonexistent_participant(self, client, reset_activities):
        """Test removal of non-existent participant returns 400"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Participant not found" in data["detail"]
    
    def test_remove_then_readd(self, client, reset_activities):
        """Test that a student can be removed and re-added"""
        # Arrange
        email = "testuser@mergington.edu"
        activity_name = "Debate Club"
        
        # Act - Add
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Remove
        response1 = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Act - Re-add
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"