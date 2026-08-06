from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_ai_extraction_service
from app.main import app

_engine = create_engine(settings.DATABASE_URL)


@pytest.fixture
def db_session():
    """A session bound to a SAVEPOINT that's rolled back after the test.

    Lets InvoiceRepository call db.commit() normally while keeping every test
    isolated - see SQLAlchemy's "Joining a Session into an External Transaction" recipe.
    """
    connection = _engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def mock_ai_service():
    return MagicMock()


@pytest.fixture
def client(db_session, upload_dir, mock_ai_service):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_ai_extraction_service] = lambda: mock_ai_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
