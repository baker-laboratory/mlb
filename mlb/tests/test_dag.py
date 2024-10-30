import itertools as it
import random
import sys

import pytest
import networkx as nx

import ipd
import mlb

def main():
    ipd.tests.maintest(mlb.tests.conftest.mlb_test_stuff, globals())

@pytest.mark.xfail
def test_make_testdag(client):
    wdgen = WordDags()
    user = client.newuser()
    exe = client.newexe(name='pyexe', path=sys.executable, apptainer=False, version=str(sys.version))
    for i in range(3):
        wd = wdgen.rand_dag(client)
        wdgen.dag_to_tasks(client, wd)

class WordDags:
    def __init__(self):
        self.words = ipd.dev.run('grep -v \\\' /usr/share/dict/words').split('\n')
        self.words = [w for w in self.words if not w.istitle()]

    def rand_dag(self, client, nnodes=7, edges='sorted', efrac=0.5):
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
            # print(list(g.successors(n)))
            # check graph is connected
            assert nx.is_directed_acyclic_graph(g)
            if nx.is_weakly_connected(g):
                return g

    def dag_to_tasks(self, client, g):
        for n in g.nodes():
            # print(n)
            inp = list(g.predecessors(n))
            invars = [client.newvar(name=s, kind='str') for s in inp]
            params = client.newparams(name=f'inp_{n}')
            params.required = [v.name for v in invars]
            params.invars = invars
            out = list(g.successors(n))
            outvars = [client.newvar(name=s, kind='str') for s in out]
            result = client.newresult(name=f'inp_{n}')
            result.guaranteed.extend([v.name for v in outvars])
            result.outvars = outvars

            exe = client.exe(name='pyexe')
            method = client.newmethod(name=f'cat_{n}', exe=exe.id, params=params.id, result=result.id)
            # print()

if __name__ == '__main__':
    main()
