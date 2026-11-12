from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.database.connection import get_db
from app.main import app


@pytest.fixture(scope="session")
def migrated_database(tmp_path_factory: pytest.TempPathFactory):
    database_path = tmp_path_factory.mktemp("database") / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    alembic_config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(migrated_database) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=migrated_database, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with migrated_database.begin() as connection:
            connection.exec_driver_sql("DELETE FROM interview_reports")
            connection.exec_driver_sql("DELETE FROM answer_evaluations")
            connection.exec_driver_sql("DELETE FROM candidate_answers")
            connection.exec_driver_sql("DELETE FROM interview_questions")
            connection.exec_driver_sql("DELETE FROM interview_sessions")
            connection.exec_driver_sql("DELETE FROM job_matches")
            connection.exec_driver_sql("DELETE FROM resume_analyses")
            connection.exec_driver_sql("DELETE FROM job_descriptions")
            connection.exec_driver_sql("DELETE FROM resumes")


@pytest.fixture
def client(db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
