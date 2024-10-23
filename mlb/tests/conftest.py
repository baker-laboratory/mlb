import mlb
import pytest
import tempfile
from fastapi.testclient import TestClient
import contextlib

@contextlib.contextmanager
def mlb_test_stuff():
    with tempfile.TemporaryDirectory() as tmpdir:
        server, backend, client = mlb.backend.server.run(
            port=54321,
            dburl=f'sqlite:////{tmpdir}/test.db',
            woerkers=1,
            loglevel='warning',
        )
        mlb.backend.server.defaults.ensure_init_db(backend)
        testclient = TestClient(backend.app)
        try:
            yield backend, server, client, testclient
        finally:
            server.stop()

@pytest.fixture(scope='module')
def mlb():
    with mlb_test_stuff() as stuff:
        yield stuff

@pytest.fixture(scope='function')
def mlb_per_func(mlb):
    mlb[0]._clear_all_data_for_testing_only()
    mlb.backend.defaults.add_defaults()
    return mlb

@pytest.fixture(scope='function')
def mlbbackend(mlb_per_func):
    return mlb_per_func[0]

@pytest.fixture(scope='function')
def mlbserver(mlb_per_func):
    return mlb_per_func[1]

@pytest.fixture(scope='function')
def mlbclient(mlb_per_func):
    return mlb_per_func[2]

@pytest.fixture(scope='function')
def mlbtestclient(mlb_per_func):
    return mlb_per_func[3]
