import os  # import asyncio

from hypothesis import given
import ipd
import mlb

# ar = asyncio.run
ar = lambda x: x

def main():
    # ipd.tests.maintest(mlb.tests.conftest.mlb_test_stuff, globals())
    os.system(f'pytest -x --hypothesis-show-statistics --durations=10 {__file__}')

# for Model in mlb.specs:
#
#     @given(st.builds(Model))
#     def test_property(instance):
#         pass

def add_users_and_groups(tool):
    a = tool.newuser(name='alice')
    b = tool.newuser(name='bob')
    c = tool.newuser(name='craig')
    g = tool.newgroup(name='good')
    h = tool.newgroup(name='bad')

def test_server_basic_backend(backend):
    add_users_and_groups(backend)
    a, b, c = ar(backend.users('alice bob craig'.split()))
    g, h = ar(backend.groups(['good', 'bad']))
    assert ar(backend.nusers()) == 3
    assert ar(backend.ngroups()) == 2
    g.users.extend([a, b])
    h.users.append(c)
    assert len(g.users) == 2
    assert len(h.users) == 1
    assert a in g.users
    assert b in g.users
    assert c not in g.users
    assert c in h.users
    g.users.remove(a)
    assert a not in g.users
    assert b in g.users
    g.users.append(c)
    assert c in g.users

def test_server_basic_client(client):
    add_users_and_groups(client)
    a, b, c = client.users('alice bob craig'.split())
    g, h = client.groups(['good', 'bad'])
    g.users.extend([a, b])
    h.users.append(c)
    assert a in g.users
    assert b in g.users
    assert c not in g.users
    assert c in h.users
    g.users.remove(a)
    assert a not in g.users
    assert b in g.users
    g.users.append(c)
    assert c in g.users

def test_add_1000_backend(backend):
    for i in range(100):
        backend.newuser(name=f'user{i}')

def test_add_10_client(client):
    for i in range(10):
        client.newuser(name=f'user{i}')

def add_hypothesis_tests():
    for Spec in mlb.specs:
        strat = mlb.tests.mlbstrats(Spec)

        def make_test_funcs(_Spec=Spec, _strat=strat):
            @given(data=_strat)
            def test_add_to_db(data, mlb_per_module):
                spec = _Spec(**data)
                thing = mlb_per_module.client.getorupload_by_name(spec)

            return {k: v for k, v in locals().items() if k.startswith('test_')}

        for k, v in make_test_funcs().items():
            globals()[f'{k}_{Spec.__name__}'] = v

if __name__ == '__main__':
    main()
