import ipd
import mlb

class MLBClient(ipd.crud.ClientBase, backend=mlb.MLBBackend):
    pass
