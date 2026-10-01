from fastapi import FastAPI, HTTPException, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import engine, get_db
from app.schemas.rating import RatingCreate
from app.services.course_service import CourseService
from app.services.rating_service import RatingService

app = FastAPI(title=settings.project_name, version=settings.version)


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """
    Dependency to get CourseService instance
    """
    return CourseService(db)


def get_rating_service(db: Session = Depends(get_db)) -> RatingService:
    """
    Dependency to get RatingService instance
    """
    return RatingService(db)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Bienvenido a Platziflix API"}


@app.get("/health")
def health() -> dict[str, str | bool | int]:
    """
    Health check endpoint that verifies:
    - Service status
    - Database connectivity
    """
    health_status = {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
        "database": False,
    }

    # Check database connectivity and verify migration
    try:
        with engine.connect() as connection:
            # Execute COUNT on courses table to verify migration was executed
            result = connection.execute(text("SELECT COUNT(*) FROM courses"))
            row = result.fetchone()
            if row:
                count = row[0]
                health_status["database"] = True
                health_status["courses_count"] = count
            else:
                health_status["database"] = True
                health_status["courses_count"] = 0
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database_error"] = str(e)

    return health_status


@app.get("/courses")
def get_courses(course_service: CourseService = Depends(get_course_service)) -> list:
    """
    Get all courses.
    Returns a list of courses with basic information: id, name, description, thumbnail, slug
    """
    return course_service.get_all_courses()


@app.get("/courses/{slug}")
def get_course_by_slug(slug: str, course_service: CourseService = Depends(get_course_service)) -> dict:
    """
    Get course details by slug.
    Returns course information including teachers and classes.
    """
    course = course_service.get_course_by_slug(slug)
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course


@app.get("/courses/{slug}/classes/{class_id}")
def get_course_class(slug: str, class_id: int, course_service: CourseService = Depends(get_course_service)) -> dict:
    """
    Get a single class of a course, including its video URL.
    """
    course_class = course_service.get_class_by_course_slug(slug, class_id)

    if not course_class:
        raise HTTPException(status_code=404, detail="Class not found")

    return course_class


@app.post("/courses/{course_id}/ratings")
def rate_course(
    course_id: int,
    rating_in: RatingCreate,
    response: Response,
    rating_service: RatingService = Depends(get_rating_service)
) -> dict:
    """
    Rate a course (1 to 5 stars).
    Creates the user's rating (201) or updates the existing one (200).
    """
    if not rating_service.course_exists(course_id):
        raise HTTPException(status_code=404, detail="Course not found")

    rating, created = rating_service.upsert_rating(course_id, rating_in.user_id, rating_in.rating)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return rating


@app.get("/courses/{course_id}/ratings/user/{user_id}")
def get_user_rating(
    course_id: int,
    user_id: int,
    rating_service: RatingService = Depends(get_rating_service)
) -> dict:
    """
    Get the rating a user gave to a course.
    """
    if not rating_service.course_exists(course_id):
        raise HTTPException(status_code=404, detail="Course not found")

    rating = rating_service.get_user_rating(course_id, user_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    return rating


@app.delete("/courses/{course_id}/ratings/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_rating(
    course_id: int,
    user_id: int,
    rating_service: RatingService = Depends(get_rating_service)
) -> Response:
    """
    Soft delete the rating a user gave to a course.
    """
    if not rating_service.course_exists(course_id):
        raise HTTPException(status_code=404, detail="Course not found")

    if not rating_service.delete_user_rating(course_id, user_id):
        raise HTTPException(status_code=404, detail="Rating not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
