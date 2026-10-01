from app.services.course_service import CourseService
from app.tests.conftest import add_ratings, make_course


def _by_id(courses):
    return {course["id"]: course for course in courses}


def test_average_and_total(db_session):
    course = make_course(db_session, "stats")
    add_ratings(db_session, course, [4, 5, 5])

    result = CourseService(db_session).get_course_by_slug("stats")
    assert result["average_rating"] == 4.7
    assert result["total_ratings"] == 3


def test_course_without_ratings_returns_null_and_zero(db_session):
    course = make_course(db_session, "no-ratings")
    service = CourseService(db_session)

    listed = _by_id(service.get_all_courses())[course.id]
    assert listed["average_rating"] is None
    assert listed["total_ratings"] == 0

    detail = service.get_course_by_slug("no-ratings")
    assert detail["average_rating"] is None
    assert detail["total_ratings"] == 0


def test_soft_deleted_ratings_are_ignored(db_session):
    course = make_course(db_session, "soft-deleted-ratings")
    add_ratings(db_session, course, [1, 1, 1], deleted=True)
    add_ratings(db_session, course, [5])

    listed = _by_id(CourseService(db_session).get_all_courses())[course.id]
    assert listed["average_rating"] == 5.0
    assert listed["total_ratings"] == 1


def test_rounding_tie_uses_round_half_to_even(db_session):
    # D4: round(float(avg), 1) keeps Python's behavior, 4.25 -> 4.2 (not 4.3)
    course = make_course(db_session, "rounding")
    add_ratings(db_session, course, [4, 4, 4, 5])

    result = CourseService(db_session).get_course_by_slug("rounding")
    assert result["average_rating"] == 4.2
    assert result["total_ratings"] == 4


def test_soft_deleted_course_not_listed(db_session):
    course = make_course(db_session, "deleted-course", deleted=True)
    add_ratings(db_session, course, [5, 4])

    service = CourseService(db_session)
    assert course.id not in _by_id(service.get_all_courses())
    assert service.get_course_by_slug("deleted-course") is None
