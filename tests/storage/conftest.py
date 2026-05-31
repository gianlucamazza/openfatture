"""Fixtures for storage layer tests."""

import pytest

from openfatture.storage.database.base import engine, init_db


@pytest.fixture(scope="function", autouse=True)
def test_db():
    """
    Initialize database for session tests.

    This fixture:
    - Creates an in-memory SQLite database
    - Initializes the database schema
    - Cleans up after test completion
    - Runs automatically for all tests in this module (autouse=True)
    """
    # Initialize database with in-memory SQLite
    init_db("sqlite:///:memory:")

    yield  # Tests run here

    # Cleanup: dispose engine to close all connections
    global engine
    if engine is not None:
        engine.dispose()
