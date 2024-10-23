import mlb
import subprocess
import threading

def run_gitea_subprocess():
    # Environment=USER=gitea HOME=/mlb/repos GITEA_WORK_DIR=/mlb/server/gitea/workdir
    subprocess.Popen(f'/usr/bin/gitea web -c {mlb.projdir}/config/gitea.ini'.split())

def run_gitea():
    t = threading.Thread(target=run_gitea_subprocess)
    t.setDaemon(True)
    t.start()
