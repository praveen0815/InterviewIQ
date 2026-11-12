from sqlalchemy import inspect, text

from app.database.connection import check_database_connection


def test_database_connection_helper_returns_a_boolean() -> None:
    assert isinstance(check_database_connection(), bool)


def test_alembic_migration_creates_resumes_table(migrated_database) -> None:
    inspector = inspect(migrated_database)
    assert "resumes" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("resumes")}
    assert {"id", "user_id", "original_filename", "file_type", "file_path", "extracted_text"} <= columns
    with migrated_database.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM resumes")).scalar_one() == 0
