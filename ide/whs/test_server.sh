mkdir -p /tmp/mlb && cd /tmp/mlb
if [ ! -d "testenv" ]; then python -m venv testenv; fi
source testenv/bin/activate
pip install -q -e /home/sheffler/mlb
pip install -q -e /home/sheffler/src/ppp

mlbserver
