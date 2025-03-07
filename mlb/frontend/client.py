import ipd
import mlb

class MLBClient(ipd.crud.ClientBase, Backend=mlb.backend.MLBBackend):
    pass
