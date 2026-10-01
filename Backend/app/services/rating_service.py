from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.course_rating import CourseRating


class RatingService:
    """
    Service class for handling course rating operations.
    Implements the contract specifications for rating endpoints.
    """

    def __init__(self, db: Session):
        self.db = db

    def course_exists(self, course_id: int) -> bool:
        """
        Check that the course exists and is not soft-deleted.
        """
        return (
            self.db.query(Course.id)
            .filter(Course.id == course_id)
            .filter(Course.deleted_at.is_(None))
            .first()
            is not None
        )

    def upsert_rating(self, course_id: int, user_id: int, rating: int) -> Tuple[Dict[str, Any], bool]:
        """
        Create the user's rating for a course, or update it if one is already active.

        Returns:
            Tuple of (rating dictionary, created flag)
        """
        existing = self._get_active_rating(course_id, user_id)
        if existing:
            existing.rating = rating
            self.db.commit()
            self.db.refresh(existing)
            return self._to_dict(existing), False

        new_rating = CourseRating(course_id=course_id, user_id=user_id, rating=rating)
        self.db.add(new_rating)
        try:
            self.db.commit()
        except IntegrityError:
            # A concurrent request created the rating first: update that one instead
            self.db.rollback()
            existing = self._get_active_rating(course_id, user_id)
            if existing is None:
                # Not a duplicate (e.g. FK or CHECK violation): surface the original error
                raise
            existing.rating = rating
            self.db.commit()
            self.db.refresh(existing)
            return self._to_dict(existing), False

        self.db.refresh(new_rating)
        return self._to_dict(new_rating), True

    def get_user_rating(self, course_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the user's active rating for a course, or None if there is none.
        """
        rating = self._get_active_rating(course_id, user_id)
        return self._to_dict(rating) if rating else None

    def delete_user_rating(self, course_id: int, user_id: int) -> bool:
        """
        Soft delete the user's active rating for a course.

        Returns:
            True if a rating was deleted, False if there was none
        """
        rating = self._get_active_rating(course_id, user_id)
        if not rating:
            return False

        rating.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def _get_active_rating(self, course_id: int, user_id: int) -> Optional[CourseRating]:
        return (
            self.db.query(CourseRating)
            .filter(CourseRating.course_id == course_id)
            .filter(CourseRating.user_id == user_id)
            .filter(CourseRating.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def _to_dict(rating: CourseRating) -> Dict[str, Any]:
        return {
            "id": rating.id,
            "course_id": rating.course_id,
            "user_id": rating.user_id,
            "rating": rating.rating,
            "created_at": rating.created_at,
            "updated_at": rating.updated_at,
        }
