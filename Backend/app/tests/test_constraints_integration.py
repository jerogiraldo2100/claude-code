from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import CourseRating
from app.tests.conftest import make_course


@pytest.mark.parametrize("value", [0, 6])
def test_rating_out_of_range_violates_check(db_session, value):
    course = make_course(db_session, "check")
    db_session.add(CourseRating(course_id=course.id, user_id=1, rating=value))
    with pytest.raises(IntegrityError, match="ck_course_ratings_rating_range"):
        db_session.flush()


def test_two_active_ratings_violate_partial_unique_index(db_session):
    course = make_course(db_session, "unique")
    db_session.add(CourseRating(course_id=course.id, user_id=1, rating=3))
    db_session.flush()
    db_session.add(CourseRating(course_id=course.id, user_id=1, rating=4))
    with pytest.raises(IntegrityError, match="uq_course_ratings_course_user_active"):
        db_session.flush()


def test_soft_deleted_rating_does_not_block_active_one(db_session):
    course = make_course(db_session, "unique-deleted")
    db_session.add(CourseRating(course_id=course.id, user_id=1, rating=3, deleted_at=datetime.utcnow()))
    db_session.add(CourseRating(course_id=course.id, user_id=1, rating=4))
    db_session.flush()


def test_unknown_course_violates_foreign_key(db_session):
    db_session.add(CourseRating(course_id=999999, user_id=1, rating=3))
    with pytest.raises(IntegrityError, match="foreign key"):
        db_session.flush()
