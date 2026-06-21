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

files_to_upload = [
    ("litholamp-web/src/app/page.tsx", "/root/formnow/litholamp-web/src/app/page.tsx"),
    ("litholamp-web/src/app/success/page.tsx", "/root/formnow/litholamp-web/src/app/success/page.tsx"),
    ("litholamp-web/next.config.ts", "/root/formnow/litholamp-web/next.config.ts")
]

for local, remote in files_to_upload:
    sftp.put(local, remote)

sftp.close()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Poll until command finishes
    while not stdout.channel.exit_status_ready():
        time.sleep(1)
        
    status = stdout.channel.recv_exit_status()
    print("STATUS:", status)

run_cmd("cd /root/formnow/litholamp-web && npm run build && pm2 restart litholamp-web")

ssh.close()
print("Fix deployed successfully!")
