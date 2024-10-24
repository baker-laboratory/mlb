import ipd
import mlb

class MLBBackend(ipd.crud.BackendBase, models=mlb.specs):
    def __init__(self, dbengine, datadir):
        super().__init__(dbengine)
        self.datadir = datadir
