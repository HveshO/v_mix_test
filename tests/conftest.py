import time

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.main import app
from app.db import engine
from app.models import Base


def _wait_for_db():
    for _ in range(50):
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
                return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("DB is not ready")


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as c:
        c.execute(text("DELETE FROM test_result"))
        c.execute(text("DELETE FROM test_run"))
        c.execute(text("DELETE FROM test_case"))
    yield


@pytest.fixture()
def client():
    return TestClient(app)
