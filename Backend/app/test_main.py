import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app, get_course_service, get_rating_service
from app.services.course_service import CourseService
from app.services.rating_service import RatingService


# Mock data according to the contracts
MOCK_COURSES_LIST = [
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Aprende React desde cero",
        "thumbnail": "https://via.placeholder.com/150",
        "slug": "curso-de-react",
        "average_rating": 4.5,
        "total_ratings": 2
    },
    {
        "id": 2,
        "name": "Curso de Python",
        "description": "Domina Python paso a paso",
        "thumbnail": "https://via.placeholder.com/200",
        "slug": "curso-de-python",
        "average_rating": None,
        "total_ratings": 0
    }
]

MOCK_COURSE_DETAIL = {
    "id": 1,
    "name": "Curso de React",
    "description": "Aprende React desde cero",
    "thumbnail": "https://via.placeholder.com/150",
    "slug": "curso-de-react",
    "teacher_id": [1, 2],
    "average_rating": 4.5,
    "total_ratings": 2,
    "classes": [
        {
            "id": 1,
            "name": "Introducción a React",
            "description": "Conceptos básicos de React",
            "slug": "introduccion-a-react"
        },
        {
            "id": 2,
            "name": "Componentes en React",
            "description": "Aprende a crear componentes",
            "slug": "componentes-en-react"
        }
    ]
}


@pytest.fixture
def mock_course_service():
    """Create a mock CourseService for testing"""
    return Mock(spec=CourseService)


@pytest.fixture
def client(mock_course_service):
    """Create test client with mocked CourseService dependency"""
    
    def get_mock_course_service():
        return mock_course_service
    
    # Override the dependency
    app.dependency_overrides[get_course_service] = get_mock_course_service
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up after test
    app.dependency_overrides.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_returns_welcome_message(self, client):
        """Test that root endpoint returns expected welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Bienvenido a Platziflix API"}


class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns expected structure"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields are present
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "database" in data
        
        # Verify field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["database"], bool)


class TestCoursesEndpoints:
    """Tests for courses related endpoints"""
    
    def test_get_all_courses_success(self, client, mock_course_service):
        """Test GET /courses returns list of courses matching contract"""
        # Configure mock
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST
        
        response = client.get("/courses")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify each course has required fields according to contract
        for course in data:
            assert "id" in course
            assert "name" in course
            assert "description" in course
            assert "thumbnail" in course
            assert "slug" in course
            
            # Verify field types
            assert isinstance(course["id"], int)
            assert isinstance(course["name"], str)
            assert isinstance(course["description"], str)
            assert isinstance(course["thumbnail"], str)
            assert isinstance(course["slug"], str)
        
        # Verify mock was called
        mock_course_service.get_all_courses.assert_called_once()
    
    def test_get_all_courses_empty_list(self, client, mock_course_service):
        """Test GET /courses when no courses exist"""
        # Configure mock to return empty list
        mock_course_service.get_all_courses.return_value = []
        
        response = client.get("/courses")
        assert response.status_code == 200
        assert response.json() == []
        
        mock_course_service.get_all_courses.assert_called_once()
    
    def test_get_course_by_slug_success(self, client, mock_course_service):
        """Test GET /courses/{slug} returns course details matching contract"""
        # Configure mock
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-react")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields according to contract
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "thumbnail" in data
        assert "slug" in data
        assert "teacher_id" in data
        assert "classes" in data
        
        # Verify field types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["thumbnail"], str)
        assert isinstance(data["slug"], str)
        assert isinstance(data["teacher_id"], list)
        assert isinstance(data["classes"], list)
        
        # Verify teacher_id contains integers
        for teacher_id in data["teacher_id"]:
            assert isinstance(teacher_id, int)
        
        # Verify classes structure
        for class_item in data["classes"]:
            assert "id" in class_item
            assert "name" in class_item
            assert "description" in class_item
            assert "slug" in class_item
            
            assert isinstance(class_item["id"], int)
            assert isinstance(class_item["name"], str)
            assert isinstance(class_item["description"], str)
            assert isinstance(class_item["slug"], str)
        
        # Verify mock was called with correct slug
        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-react")
    
    def test_get_course_by_slug_not_found(self, client, mock_course_service):
        """Test GET /courses/{slug} when course doesn't exist"""
        # Configure mock to return None
        mock_course_service.get_course_by_slug.return_value = None
        
        response = client.get("/courses/nonexistent-course")
        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}
        
        mock_course_service.get_course_by_slug.assert_called_once_with("nonexistent-course")
    
    def test_get_course_by_slug_with_special_characters(self, client, mock_course_service):
        """Test GET /courses/{slug} with special characters in slug"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-c++")
        assert response.status_code == 200
        
        mock_course_service.get_course_by_slug.assert_called_once_with("curso-de-c++")


class TestContractCompliance:
    """Additional tests to ensure strict contract compliance"""
    
    def test_courses_list_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses response contains only contract-specified fields"""
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST
        
        response = client.get("/courses")
        data = response.json()
        
        expected_fields = {"id", "name", "description", "thumbnail", "slug", "average_rating", "total_ratings"}
        
        for course in data:
            # Verify no extra fields beyond contract
            actual_fields = set(course.keys())
            assert actual_fields == expected_fields, f"Expected {expected_fields}, got {actual_fields}"
    
    def test_course_detail_contract_fields_only(self, client, mock_course_service):
        """Ensure GET /courses/{slug} response contains only contract-specified fields"""
        mock_course_service.get_course_by_slug.return_value = MOCK_COURSE_DETAIL
        
        response = client.get("/courses/curso-de-react")
        data = response.json()
        
        # Verify main course fields
        expected_course_fields = {
            "id", "name", "description", "thumbnail", "slug", "teacher_id", "average_rating", "total_ratings", "classes"
        }
        actual_course_fields = set(data.keys())
        assert actual_course_fields == expected_course_fields
        
        # Verify classes fields
        expected_class_fields = {"id", "name", "description", "slug"}
        for class_item in data["classes"]:
            actual_class_fields = set(class_item.keys())
            assert actual_class_fields == expected_class_fields
    
    def test_courses_response_data_matches_contract_examples(self, client, mock_course_service):
        """Test that response structure exactly matches contract examples"""
        mock_course_service.get_all_courses.return_value = [
            {
                "id": 1,
                "name": "Curso de React",
                "description": "Curso de React",
                "thumbnail": "https://via.placeholder.com/150",
                "slug": "curso-de-react",
                "average_rating": 4.5,
                "total_ratings": 2
            }
        ]
        
        response = client.get("/courses")
        data = response.json()
        
        # Verify the response matches the exact contract structure
        assert len(data) == 1
        course = data[0]
        assert course["id"] == 1
        assert course["name"] == "Curso de React"
        assert course["description"] == "Curso de React"
        assert course["thumbnail"] == "https://via.placeholder.com/150"
        assert course["slug"] == "curso-de-react"
        assert course["average_rating"] == 4.5
        assert course["total_ratings"] == 2

    def test_course_without_ratings_has_null_average(self, client, mock_course_service):
        """Courses without ratings return average_rating null and total_ratings 0"""
        mock_course_service.get_all_courses.return_value = MOCK_COURSES_LIST

        response = client.get("/courses")
        course = response.json()[1]

        assert course["average_rating"] is None
        assert course["total_ratings"] == 0


MOCK_RATING = {
    "id": 1,
    "course_id": 1,
    "user_id": 1,
    "rating": 5,
    "created_at": "2026-09-30T12:00:00",
    "updated_at": "2026-09-30T12:00:00"
}


@pytest.fixture
def mock_rating_service():
    """Create a mock RatingService for testing"""
    service = Mock(spec=RatingService)
    service.course_exists.return_value = True
    return service


@pytest.fixture
def rating_client(mock_rating_service):
    """Create test client with mocked RatingService dependency"""
    app.dependency_overrides[get_rating_service] = lambda: mock_rating_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestRatingsEndpoints:
    """Tests for course rating endpoints"""

    def test_create_rating_returns_201(self, rating_client, mock_rating_service):
        mock_rating_service.upsert_rating.return_value = (MOCK_RATING, True)

        response = rating_client.post("/courses/1/ratings", json={"user_id": 1, "rating": 5})

        assert response.status_code == 201
        assert set(response.json().keys()) == {"id", "course_id", "user_id", "rating", "created_at", "updated_at"}
        mock_rating_service.upsert_rating.assert_called_once_with(1, 1, 5)

    def test_update_existing_rating_returns_200(self, rating_client, mock_rating_service):
        mock_rating_service.upsert_rating.return_value = ({**MOCK_RATING, "rating": 3}, False)

        response = rating_client.post("/courses/1/ratings", json={"user_id": 1, "rating": 3})

        assert response.status_code == 200
        assert response.json()["rating"] == 3

    @pytest.mark.parametrize("invalid_rating", [0, 6, -1, 4.5, "5", None])
    def test_invalid_rating_returns_422(self, rating_client, mock_rating_service, invalid_rating):
        response = rating_client.post("/courses/1/ratings", json={"user_id": 1, "rating": invalid_rating})

        assert response.status_code == 422
        mock_rating_service.upsert_rating.assert_not_called()

    @pytest.mark.parametrize("invalid_user_id", [0, 2_147_483_648, 3_000_000_000])
    def test_out_of_range_user_id_returns_422(self, rating_client, mock_rating_service, invalid_user_id):
        response = rating_client.post("/courses/1/ratings", json={"user_id": invalid_user_id, "rating": 5})

        assert response.status_code == 422
        mock_rating_service.upsert_rating.assert_not_called()

    def test_missing_user_id_returns_422(self, rating_client, mock_rating_service):
        response = rating_client.post("/courses/1/ratings", json={"rating": 5})

        assert response.status_code == 422

    def test_rate_nonexistent_course_returns_404(self, rating_client, mock_rating_service):
        mock_rating_service.course_exists.return_value = False

        response = rating_client.post("/courses/999/ratings", json={"user_id": 1, "rating": 5})

        assert response.status_code == 404
        assert response.json() == {"detail": "Course not found"}
        mock_rating_service.upsert_rating.assert_not_called()

    def test_get_user_rating_success(self, rating_client, mock_rating_service):
        mock_rating_service.get_user_rating.return_value = MOCK_RATING

        response = rating_client.get("/courses/1/ratings/user/1")

        assert response.status_code == 200
        assert response.json()["rating"] == 5
        mock_rating_service.get_user_rating.assert_called_once_with(1, 1)

    def test_get_user_rating_not_found(self, rating_client, mock_rating_service):
        mock_rating_service.get_user_rating.return_value = None

        response = rating_client.get("/courses/1/ratings/user/2")

        assert response.status_code == 404
        assert response.json() == {"detail": "Rating not found"}

    def test_delete_user_rating_returns_204(self, rating_client, mock_rating_service):
        mock_rating_service.delete_user_rating.return_value = True

        response = rating_client.delete("/courses/1/ratings/user/1")

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_missing_rating_returns_404(self, rating_client, mock_rating_service):
        mock_rating_service.delete_user_rating.return_value = False

        response = rating_client.delete("/courses/1/ratings/user/1")

        assert response.status_code == 404
