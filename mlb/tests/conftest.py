import collections
import contextlib
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from hypothesis import strategies as st

import ipd
import mlb

MLBTestStuff = collections.namedtuple('MLBTestStuff', 'backend server client testclient')

class MLBStrats(ipd.dev.testing.PydanticStrats):
    def __init__(self):
        super().__init__(
            overrides={
                '*.name': st.text().filter(str.isidentifier),
                '*.ref': st.integers().map(hex).map(lambda s: s[2:]),
                'ConfigFilesSpec.repo': st.sampled_from(['mlb', 'ide']).map(Path),
            },
            type_mapping={
                mlb.ParseKind: st.sampled_from(mlb.ParseKind),
                mlb.VarKind: st.sampled_from(mlb.VarKind),
            },
            exclude_attrs={'datecreated'},
        )

    def postprocess_moodel_strategy(self, Model, strat):
        if Model.modelkind() in 'method protocol'.split():
            return strat.filter(lambda d: d['config'] or d['param'])
        return strat

mlbstrats = MLBStrats()

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
            yield MLBTestStuff(backend, server, client, testclient)
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
