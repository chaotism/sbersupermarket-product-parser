import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import find_dotenv, load_dotenv
from starlette.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / Path('application')
TEST_ENV = '.env.test'
if not APP_DIR.exists():
    raise Exception(f'Wrong app dir configuration: {APP_DIR}')
sys.path.append(str(APP_DIR))
load_dotenv(
    find_dotenv(filename=str(BASE_DIR / Path(TEST_ENV)), raise_error_if_not_found=True)
)

from config import auth_config  # noqa: E402
from web.app import app  # noqa: E402


AUTH_TOKEN = 'hello'
auth_config.tokens_list.append(AUTH_TOKEN)


@pytest.fixture(scope='function')
def test_client():
    cwd = Path(__file__).parent.parent.parent
    subprocess.check_call(['make', 'db-migrate'], cwd=cwd)
    with TestClient(app=app) as client:
        yield client
    subprocess.check_call(['make', 'db-reset'], cwd=cwd)


@pytest.fixture(scope='session')
def test_token():
    return {auth_config.auth_token_key_name: auth_config.tokens_list[0]}


@pytest.fixture(scope='function')
def test_client_with_auth_token(test_token, test_client):
    test_client.headers.update(test_token)
    yield test_client
    for key in test_token:
        test_client.headers.pop(key)


# This line would raise an error if we use it after 'settings' has been imported.
os.environ['API_DEBUG'] = 'TRUE'
