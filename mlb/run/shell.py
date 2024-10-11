import subprocess

def bash(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode(), result.stderr.decode(), result.returncode
