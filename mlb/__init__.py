import os

from mlb.specifications import *
from mlb import *
from mlb.backend import *
from mlb.frontend import *

projdir = os.path.realpath(os.path.dirname(__file__))
profiler = lambda f: f
