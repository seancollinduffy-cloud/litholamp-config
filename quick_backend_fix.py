import paramiko
import os
import time

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

sftp = ssh.open_sftp()
sftp.put("litholamp-api/main.py", "/root/formnow/litholamp-api/main.py")
sftp.close()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Poll until command finishes
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    status = stdout.channel.recv_exit_status()
    print("STATUS:", status)

run_cmd("fuser -k 8001/tcp")
run_cmd("cd /root/formnow/litholamp-api && nohup /root/formnow/venv/bin/python main.py > api_log.txt 2>&1 &")

ssh.close()
print("Backend fix deployed successfully!")
