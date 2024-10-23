mkdir -p /tmp/mlb
cd /tmp/mlb
# python -m venv testenv
source testenv/bin/activate
# pip install -q -e /home/sheffler/mlb
# pip install -e /home/sheffler/src/ppp

mlbserver &
mlb benchmark ppi new test_ppi_benchmask
pkill mlbserver
