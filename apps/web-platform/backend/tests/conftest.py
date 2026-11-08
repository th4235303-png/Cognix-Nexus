import pytest
from app.main import _rate_windows

@pytest.fixture(autouse=True)
def reset_rate_limit():
    _rate_windows.clear()
    yield
    _rate_windows.clear()
