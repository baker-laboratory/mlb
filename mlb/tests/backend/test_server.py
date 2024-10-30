import asyncio
import ipd
import mlb

ar = asyncio.run

def main():
    ipd.tests.main(mlb.tests.conftest.mlb_test_stuff, globals())

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

if __name__ == '__main__':
    main()
