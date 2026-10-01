from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.db.base import get_db
from app.main import app
from app.models import Lesson
from app.tests.conftest import add_ratings, make_course, make_teacher


@pytest.fixture
def client(db_session):
    # Every route must use the test session, never the development database
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_rating_flow(client, db_session):
    course = make_course(db_session, "api-flow")
    deleted = make_course(db_session, "api-deleted", deleted=True)
    url = f"/courses/{course.id}/ratings"

    assert client.post(url, json={"user_id": 1, "rating": 4}).status_code == 201
    response = client.post(url, json={"user_id": 1, "rating": 5})
    assert response.status_code == 200
    assert response.json()["rating"] == 5

    response = client.get(f"{url}/user/1")
    assert response.status_code == 200
    assert response.json()["rating"] == 5

    assert client.delete(f"{url}/user/1").status_code == 204
    assert client.get(f"{url}/user/1").status_code == 404

    response = client.post(f"/courses/{deleted.id}/ratings", json={"user_id": 1, "rating": 3})
    assert response.status_code == 404


def test_course_detail_reflects_ratings(client, db_session):
    course = make_course(db_session, "api-detail")
    url = f"/courses/{course.id}/ratings"
    client.post(url, json={"user_id": 1, "rating": 4})
    client.post(url, json={"user_id": 2, "rating": 5})

    body = client.get("/courses/api-detail").json()
    assert body["average_rating"] == 4.5
    assert body["total_ratings"] == 2


def _count_list_queries(client, db_connection):
    statements = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if not statement.upper().startswith(("SAVEPOINT", "RELEASE", "ROLLBACK")):
            statements.append(statement)

    event.listen(db_connection, "before_cursor_execute", before_cursor_execute)
    try:
        assert client.get("/courses").status_code == 200
    finally:
        event.remove(db_connection, "before_cursor_execute", before_cursor_execute)
    return statements


def _add_courses(db_session, start, end):
    for i in range(start, end):
        course = make_course(db_session, f"n1-{i}")
        course.teachers.append(make_teacher(db_session, f"n1-{i}@example.com"))
        add_ratings(db_session, course, [i % 5 + 1, 5])
    db_session.flush()


def test_courses_list_has_no_n_plus_one(client, db_session, db_connection):
    _add_courses(db_session, 0, 2)
    with_two = _count_list_queries(client, db_connection)

    _add_courses(db_session, 2, 6)
    with_six = _count_list_queries(client, db_connection)

    assert len(with_two) == len(with_six)
    assert sum("course_ratings" in s for s in with_six) == 1


def test_course_class_endpoint(client, db_session):
    course = make_course(db_session, "api-class")
    other = make_course(db_session, "api-class-other")
    lesson = Lesson(course_id=course.id, name="Clase 1", description="Intro", slug="clase-1", video_url="https://example.com/v.mp4")
    deleted = Lesson(course_id=course.id, name="Old", description="Old", slug="old", video_url="https://example.com/o.mp4", deleted_at=datetime.utcnow())
    db_session.add_all([lesson, deleted])
    db_session.commit()

    response = client.get(f"/courses/api-class/classes/{lesson.id}")
    assert response.status_code == 200
    assert response.json()["video_url"] == "https://example.com/v.mp4"

    # Class from another course, soft-deleted class and unknown course are all 404
    assert client.get(f"/courses/{other.slug}/classes/{lesson.id}").status_code == 404
    assert client.get(f"/courses/api-class/classes/{deleted.id}").status_code == 404
    assert client.get(f"/courses/missing/classes/{lesson.id}").status_code == 404
