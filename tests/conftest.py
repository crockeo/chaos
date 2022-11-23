import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        curdir = Path.cwd()
        try:
            os.chdir(tmp_path)
            yield tmp_path
        finally:
            os.chdir(curdir)
