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

def run_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
    status = stdout.channel.recv_exit_status()
    print("STATUS:", status)

sftp = ssh.open_sftp()
sftp.put("litholamp-web/src/components/ThreeDViewer.tsx", "/root/formnow/litholamp-web/src/components/ThreeDViewer.tsx")
sftp.close()

run_cmd("cd /root/formnow/litholamp-web && npm run build && pm2 restart litholamp-web")
ssh.close()
print("ThreeDViewer uploaded and built!")
