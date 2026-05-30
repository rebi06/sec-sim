import pytest
from app.infrastructure.db import init_db


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
