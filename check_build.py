import paramiko
import sys

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

stdin, stdout, stderr = ssh.exec_command('cd /root/formnow/litholamp-web && npm run build')
out = stdout.read()
err = stderr.read()
sys.stdout.buffer.write(out)
sys.stdout.buffer.write(err)

ssh.close()
