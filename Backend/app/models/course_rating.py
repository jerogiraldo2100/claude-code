from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.orm import relationship
from .base import BaseModel


class CourseRating(BaseModel):
    """
    Rating (1 to 5 stars) given by a user to a course.
    A user can have at most one active (not soft-deleted) rating per course.
    """
    __tablename__ = 'course_ratings'

    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # No users table yet (no auth)
    rating = Column(SmallInteger, nullable=False)

    # Many-to-one relationship with Course
    course = relationship("Course", back_populates="ratings")

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_course_ratings_rating_range'),
        # Partial unique index: one active rating per user and course, soft-deleted rows don't count
        Index(
            'uq_course_ratings_course_user_active',
            'course_id',
            'user_id',
            unique=True,
            postgresql_where=text('deleted_at IS NULL'),
        ),
    )

    def __repr__(self):
        return f"<CourseRating(id={self.id}, course_id={self.course_id}, user_id={self.user_id}, rating={self.rating})>"
