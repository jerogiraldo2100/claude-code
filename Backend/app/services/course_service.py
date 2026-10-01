from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.course import Course
from app.models.course_rating import CourseRating
from app.models.lesson import Lesson
from app.models.teacher import Teacher


class CourseService:
    """
    Service class for handling course-related operations.
    Implements the contract specifications for course endpoints.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Get all courses with basic information (no teachers or lessons).
        
        Returns:
            List of course dictionaries with: id, name, description, thumbnail, slug,
            average_rating, total_ratings
        """
        courses = self.db.query(Course).filter(Course.deleted_at.is_(None)).all()
        rating_stats = self._get_rating_stats([course.id for course in courses])

        return [
            {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "thumbnail": course.thumbnail,
                "slug": course.slug,
                **rating_stats.get(course.id, self._empty_rating_stats())
            }
            for course in courses
        ]

    def get_course_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get course details by slug including teachers and lessons.
        
        Args:
            slug: The course slug
            
        Returns:
            Course dictionary with teachers and lessons, or None if not found
        """
        course = (
            self.db.query(Course)
            .options(
                joinedload(Course.teachers),
                joinedload(Course.lessons)
            )
            .filter(Course.slug == slug)
            .filter(Course.deleted_at.is_(None))
            .first()
        )
        
        if not course:
            return None

        rating_stats = self._get_rating_stats([course.id])

        return {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "thumbnail": course.thumbnail,
            "slug": course.slug,
            "teacher_id": [teacher.id for teacher in course.teachers],
            **rating_stats.get(course.id, self._empty_rating_stats()),
            "classes": [
                {
                    "id": lesson.id,
                    "name": lesson.name,
                    "description": lesson.description,
                    "slug": lesson.slug
                }
                for lesson in course.lessons
                if lesson.deleted_at is None
            ]
        }

    def get_class_by_course_slug(self, slug: str, class_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single class (lesson) of a course, or None if the course or the class doesn't exist.
        """
        lesson = (
            self.db.query(Lesson)
            .join(Course, Lesson.course_id == Course.id)
            .filter(
                Course.slug == slug,
                Course.deleted_at.is_(None),
                Lesson.id == class_id,
                Lesson.deleted_at.is_(None),
            )
            .first()
        )

        if not lesson:
            return None

        return {
            "id": lesson.id,
            "name": lesson.name,
            "description": lesson.description,
            "slug": lesson.slug,
            "video_url": lesson.video_url,
            "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
            "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
            "deleted_at": None,
        }

    def _get_rating_stats(self, course_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Get average rating and ratings count for several courses in a single query.
        Soft-deleted ratings are ignored.

        Returns:
            Dict of course_id -> {"average_rating": float, "total_ratings": int}
            (courses without ratings are not included)
        """
        if not course_ids:
            return {}

        rows = (
            self.db.query(
                CourseRating.course_id,
                func.avg(CourseRating.rating),
                func.count(CourseRating.id)
            )
            .filter(CourseRating.course_id.in_(course_ids))
            .filter(CourseRating.deleted_at.is_(None))
            .group_by(CourseRating.course_id)
            .all()
        )

        return {
            course_id: {
                "average_rating": round(float(average), 1),
                "total_ratings": total
            }
            for course_id, average, total in rows
        }

    @staticmethod
    def _empty_rating_stats() -> Dict[str, Any]:
        return {"average_rating": None, "total_ratings": 0}
