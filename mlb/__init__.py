import os
from mlb.specifications import specs
from mlb import backend, frontend
from mlb.backend import MLBBackend
from mlb.frontend import MLBClient, MLBTool

projdir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
