import ipd
import mlb
import inspect
import asyncio
import traceback
import pydantic
from hypothesis import given, strategies as st
from rich import print

ar = asyncio.run

def main():
    from mlb.tests.conftest import mlb_test_stuff
    with mlb_test_stuff() as (backend, server, client, testclient):
        for fn in [f for n, f in globals().items() if n.startswith('test_')]:
            backend._clear_all_data_for_testing_only()
            print('=' * 20, fn, '=' * 20)
            try:
                args = {p: locals()[p] for p in inspect.signature(fn).parameters}
                fn(**args)
            except pydantic.ValidationError as e:
                print(e)
                print(e.errors())
                print(traceback.format_exc())
                break
    print('PASS')
    ipd.dev.global_timer.report()

for Model in mlb.specs:

    @given(st.builds(Model))
    def test_property(instance):
        pass

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

if __name__ == '__main__':
    main()
