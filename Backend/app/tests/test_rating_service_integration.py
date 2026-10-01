import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import CourseRating
from app.services.rating_service import RatingService
from app.tests.conftest import make_course


def _rows(db, course_id, user_id):
    return (
        db.query(CourseRating)
        .filter(CourseRating.course_id == course_id, CourseRating.user_id == user_id)
        .order_by(CourseRating.id)
        .all()
    )


def test_upsert_creates_then_updates_single_active_row(db_session):
    course = make_course(db_session, "upsert")
    service = RatingService(db_session)

    first, created = service.upsert_rating(course.id, 1, 3)
    assert created is True
    assert first["rating"] == 3

    second, created = service.upsert_rating(course.id, 1, 5)
    assert created is False
    assert second["id"] == first["id"]
    assert second["rating"] == 5

    rows = _rows(db_session, course.id, 1)
    assert len(rows) == 1
    assert rows[0].deleted_at is None


def test_revote_after_delete_creates_new_row(db_session):
    course = make_course(db_session, "revote")
    service = RatingService(db_session)

    first, _ = service.upsert_rating(course.id, 1, 2)
    assert service.delete_user_rating(course.id, 1) is True

    second, created = service.upsert_rating(course.id, 1, 4)
    assert created is True
    assert second["id"] != first["id"]

    rows = _rows(db_session, course.id, 1)
    assert len(rows) == 2
    assert rows[0].deleted_at is not None
    assert rows[1].deleted_at is None
    assert rows[1].rating == 4


def test_delete_without_active_rating_and_get_after_delete(db_session):
    course = make_course(db_session, "delete")
    service = RatingService(db_session)

    assert service.delete_user_rating(course.id, 1) is False

    service.upsert_rating(course.id, 1, 5)
    assert service.get_user_rating(course.id, 1)["rating"] == 5
    assert service.delete_user_rating(course.id, 1) is True
    assert service.get_user_rating(course.id, 1) is None
    assert service.delete_user_rating(course.id, 1) is False


def test_upsert_integrity_error_branch_updates_existing_row(db_session, monkeypatch):
    course = make_course(db_session, "race")
    db_session.commit()
    service = RatingService(db_session)

    # Simulate a concurrent request: the row is inserted after the lookup returned None
    db_session.execute(
        text(
            "INSERT INTO course_ratings (course_id, user_id, rating, created_at, updated_at) "
            "VALUES (:course_id, 1, 2, now(), now())"
        ),
        {"course_id": course.id},
    )
    db_session.commit()

    original = RatingService._get_active_rating
    calls = {"count": 0}

    def first_call_misses(self, course_id, user_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return original(self, course_id, user_id)

    monkeypatch.setattr(RatingService, "_get_active_rating", first_call_misses)

    rating, created = service.upsert_rating(course.id, 1, 5)
    assert created is False
    assert rating["rating"] == 5
    assert calls["count"] == 2

    # Session is still usable and there is a single active row with the new value
    active = [r for r in _rows(db_session, course.id, 1) if r.deleted_at is None]
    assert len(active) == 1
    assert active[0].rating == 5


def test_upsert_non_duplicate_integrity_error_is_reraised(db_session):
    service = RatingService(db_session)

    # FK violation: no active rating exists after the rollback, so the original error must surface
    with pytest.raises(IntegrityError, match="foreign key"):
        service.upsert_rating(999_999, 1, 5)

    # Session is still usable after the rollback
    assert service.get_user_rating(999_999, 1) is None


def test_course_exists(db_session):
    active = make_course(db_session, "active")
    deleted = make_course(db_session, "deleted", deleted=True)
    service = RatingService(db_session)

    assert service.course_exists(active.id) is True
    assert service.course_exists(deleted.id) is False
    assert service.course_exists(999999) is False
