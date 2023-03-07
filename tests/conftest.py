from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def bagels_path():
    return Path(__file__).absolute().parent / "data"
