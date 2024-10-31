import itertools as it
import random
import sys

import networkx as nx
import pytest

import ipd
import mlb

def main():
    ipd.tests.maintest(mlb.tests.conftest.mlb_test_stuff, globals())

@ipd.dev.timed
def test_make_testdag(client, backend):
    wdgen = WordDags()
    user = client.newuser()
    exe = client.newexe(name='pyexe', path=sys.executable, apptainer=False, version=str(sys.version))
    for i in range(1):
        wd = wdgen.rand_dag(client, 8)
        import matplotlib.pyplot as plt
        # fig = nx.draw(wd)
        # plt.show()
        # assert 0
        wdgen.dag_to_tasks(client, wd, tag=i)

@ipd.dev.timed
class WordDags:
    def __init__(self):
        self.words = ipd.dev.run('grep -v \\\' /usr/share/dict/words').split('\n')
        self.words = [w for w in self.words if not w.istitle()]

    def rand_dag(self, client, nnodes=7, edges='sorted', efrac=10.5):
        while True:
            words = sorted([random.choice(self.words) for _ in range(nnodes)])
            g = nx.DiGraph()
            g.add_nodes_from(words)
            for word1, word2 in [(v, w) for v, w in it.product(words, words) if v < w]:
                if random.random() > efrac: continue
                # print(word1, word2)
                g.add_edge(word1, word2)
            # print(g)
            # for n in g.nodes():
            # print(list(g.predecessors(n)))
            # print(list(g.successors(n)))o
            # check graph is connected
            assert nx.is_directed_acyclic_graph(g)
            if nx.is_weakly_connected(g):
                return g

    def dag_to_tasks(self, client, g, tag=''):
        outvars = [client.getornewvar(name=s, kind='str') for s in g.nodes()]
        result = client.newresult(name=f'final_result{tag}')
        proto = client.newprotocol(name=f'concat{tag}', result=result)
        result.outvars = outvars
        for n in g.nodes():
            # print(n)
            inp = list(g.predecessors(n))
            invars = [client.getornewvar(name=s, kind='str') for s in inp]
            param = client.newparam(name=f'prm_{n}')
            param.required = [v.name for v in invars]
            param.invars = invars
            out = list(g.successors(n))
            outvars = [client.getornewvar(name=s, kind='str') for s in out]
            result = client.newresult(name=f'rslt_{n}')
            result.guaranteed.extend([v.name for v in outvars])
            result.outvars = outvars
            exe = client.exe(name='pyexe')
            method = client.newmethod(name=f'cat_{n}', exe=exe.id, param=param.id, result=result.id)
            # method.print_compact(recurse=2, shorten=1)
            proto.methods.append(method)
        # proto.print_compact(recurse=2, shorten=1)
        return proto
        rich.print(proto)
        for m in proto.methods:
            print('   ', m.name)
            print('        in: ', [v.name for v in m.param.invars])
            print('        out:', [v.name for v in m.result.outvars])
        rich.print([v.name for v in proto.result.outvars])

if __name__ == '__main__':
    main()
