"""
Integration test fixtures. Tests run against a dedicated PostgreSQL database
(platziflix_test by default), migrated with the real Alembic migrations.
Every test runs inside an outer transaction that is rolled back at the end.
"""
import os
from datetime import datetime

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Course, CourseRating, Teacher

ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")

TEST_DATABASE_URL = make_url(
    os.environ.get("TEST_DATABASE_URL")
    or make_url(settings.database_url).set(database="platziflix_test").render_as_string(hide_password=False)
)


@pytest.fixture(scope="session")
def test_engine():
    # Safety guard: never run integration tests against a non-test database
    if not (TEST_DATABASE_URL.database or "").endswith("_test"):
        pytest.exit(f"Refusing to run: database '{TEST_DATABASE_URL.database}' does not end with '_test'", returncode=1)

    # CREATE DATABASE cannot run inside a transaction
    admin_engine = create_engine(TEST_DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE_URL.database}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE_URL.database}"'))
    admin_engine.dispose()

    # alembic.ini points to the development database: override the URL
    url = TEST_DATABASE_URL.render_as_string(hide_password=False)
    alembic_cfg = Config(ALEMBIC_INI)
    alembic_cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_session(db_connection):
    # commit()/rollback() done by the services only affect a savepoint
    session = Session(bind=db_connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()


def make_course(db: Session, slug: str, deleted: bool = False) -> Course:
    course = Course(
        name=f"Course {slug}",
        description="Test course",
        thumbnail="https://example.com/thumb.png",
        slug=slug,
        deleted_at=datetime.utcnow() if deleted else None,
    )
    db.add(course)
    db.flush()
    return course


def make_teacher(db: Session, email: str) -> Teacher:
    teacher = Teacher(name=f"Teacher {email}", email=email)
    db.add(teacher)
    db.flush()
    return teacher


def add_ratings(db: Session, course: Course, values, deleted: bool = False) -> None:
    for user_id, value in enumerate(values, start=1):
        db.add(CourseRating(
            course_id=course.id,
            user_id=user_id,
            rating=value,
            deleted_at=datetime.utcnow() if deleted else None,
        ))
    db.flush()
