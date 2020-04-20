from app import app
import pytest

@pytest.fixture
def app():
    app = app
    return app