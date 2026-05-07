"""
Test suite for the Mergington High School Activities API using the AAA testing pattern.

AAA Pattern:
- Arrange: Set up test data and initial state
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        # Arrange
        # (No setup needed; app has predefined activities)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_returns_correct_structure(self, client):
        """Test that each activity has required fields"""
        # Arrange
        # (No setup needed)

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


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        # Arrange
        # (No setup needed)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successfully signing up for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

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

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity list"""
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up the same email twice returns 400"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_activity_full_fails(self, client):
        """Test that signing up to a full activity returns 400"""
        # Arrange
        # Find an activity with max_participants == current participants count
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Tennis Club has max 12 and 2 participants, so it's not full
        # Let's sign up 11 new people to fill it, then test the 12th
        activity_name = "Tennis Club"
        activity = activities[activity_name]
        max_cap = activity["max_participants"]
        current_count = len(activity["participants"])

        for i in range(max_cap - current_count):
            email = f"student{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )

        # Act - Try to sign up one more when activity is full
        final_email = "final@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": final_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_success(self, client):
        """Test successfully unregistering a participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering non-existent participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_frees_up_spot(self, client):
        """Test that unregistering frees up a spot for new signups"""
        # Arrange
        activity_name = "Drama Club"
        participant_to_remove = "jacob@mergington.edu"
        new_participant = "newstudent@mergington.edu"

        # Act - Remove existing participant
        response1 = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": participant_to_remove}
        )

        # Act - Sign up new participant
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_participant}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert new_participant in activities[activity_name]["participants"]
        assert participant_to_remove not in activities[activity_name]["participants"]
