import ipd
import mlb

def run(**kw):
    ipd.crud.run(mlb.backend.Backend, mlb.frontend.Client, **kw)
