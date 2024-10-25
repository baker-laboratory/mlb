import mlb
import pytest
import tempfile
from fastapi.testclient import TestClient
import contextlib

@contextlib.contextmanager
def mlb_test_stuff():
    with tempfile.TemporaryDirectory() as tmpdir:
        server, backend, client = mlb.backend.run(
            port=54321,
            dburl=f'sqlite:////{tmpdir}/test.db',
            workers=1,
            loglevel='warning',
        )
        testclient = TestClient(backend.app)
        try:
            yield backend, server, client, testclient
        finally:
            server.stop()

@pytest.fixture(scope='module')
def mlb_per_module():
    with mlb_test_stuff() as stuff:
        yield stuff

@pytest.fixture(scope='function')
def mlb_per_func(mlb_per_module):
    mlb_per_module[0]._clear_all_data_for_testing_only()
    return mlb_per_module

@pytest.fixture(scope='function')
def backend(mlb_per_func):
    return mlb_per_func[0]

@pytest.fixture(scope='function')
def server(mlb_per_func):
    return mlb_per_func[1]

@pytest.fixture(scope='function')
def client(mlb_per_func):
    return mlb_per_func[2]

@pytest.fixture(scope='function')
def testclient(mlb_per_func):
    return mlb_per_func[3]
