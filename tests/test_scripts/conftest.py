import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import find_dotenv, load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / Path('application')))
load_dotenv(
    find_dotenv(
        filename=str(BASE_DIR / Path('.env.example')), raise_error_if_not_found=True
    )
)


@pytest.fixture(scope='function')
def test_clear_db():
    cwd = Path(__file__).parent.parent.parent
    subprocess.check_call(['alembic', 'upgrade', 'head'], cwd=cwd)
    yield
    subprocess.check_call(['alembic', 'downgrade', 'base'], cwd=cwd)


# This line would raise an error if we use it after 'settings' has been imported.
os.environ['DEBUG'] = 'TRUE'
