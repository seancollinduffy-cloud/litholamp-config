import paramiko
import time

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"

print("Connecting to remote server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

def run_cmd(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    time.sleep(1) # give it a sec
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print("OUT:", out)
    if err: print("ERR:", err)

# 1. Kill old Gunicorn on port 80
run_cmd("fuser -k 80/tcp")
# 2. Kill anything on 8001 and 3000 just in case
run_cmd("fuser -k 8001/tcp")
run_cmd("fuser -k 3000/tcp")
# 3. Delete existing PM2 processes
run_cmd("pm2 delete all")

# 4. Start the new Python API backend on 8001 in the background
run_cmd("cd /root/formnow/litholamp-api && source venv/bin/activate && nohup uvicorn main:app --host 0.0.0.0 --port 8001 > /root/formnow/litholamp-api/api_log.txt 2>&1 &")

# Wait a second for it to start
time.sleep(2)

# 5. Start the new Next.js frontend on port 80 via PM2
run_cmd("cd /root/formnow/litholamp-web && pm2 start npm --name 'litholamp-web' -- start -- -p 80")
run_cmd("pm2 save")

print("Done! Check the live site.")
ssh.close()
