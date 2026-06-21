import paramiko
import time
import sys

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

def run_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Poll until command finishes
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print("STATUS:", status)
    if out: print("OUT:", out[:500])
    if err: print("ERR:", err[:500])
    return status

print("Finding venv...")
run_cmd("find /root -name 'venv' -type d")

print("Checking FastAPI location...")
run_cmd("find /root -name 'uvicorn' -type f")
