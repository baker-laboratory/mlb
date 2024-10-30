import os
from mlb.specifications import specs, ParseKind, VarKind
from mlb import backend, frontend, tests
from mlb.backend import MLBBackend
from mlb.frontend import MLBClient, MLBTool

projdir = os.path.realpath(os.path.dirname(__file__))
