import paramiko
import sys

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

stdin, stdout, stderr = ssh.exec_command('tail -n 50 /root/.pm2/logs/litholamp-web-out.log')
out = stdout.read()
sys.stdout.buffer.write(out)

stdin, stdout, stderr = ssh.exec_command('tail -n 50 /root/.pm2/logs/litholamp-web-error.log')
err = stdout.read()
sys.stdout.buffer.write(b"\\n=== ERROR ===\\n")
sys.stdout.buffer.write(err)

ssh.close()
