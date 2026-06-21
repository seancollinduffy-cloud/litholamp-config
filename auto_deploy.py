import paramiko
import os
import stat

host = "198.71.49.155"
port = 22
username = "root"
password = "3waH8JAmSxUBZ"
remote_dir = "/root/formnow"

def deploy():
    print("Connecting to remote server via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)

    print("Opening SFTP channel...")
    sftp = ssh.open_sftp()
    
    local_dirs = ["litholamp-api", "litholamp-web"]
    
    for local_dir in local_dirs:
        print(f"Uploading {local_dir}...")
        for root, dirs, files in os.walk(local_dir):
            if 'node_modules' in root or '.next' in root or '__pycache__' in root or 'customer_renders' in root:
                continue
                
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, local_dir)
                remote_path = f"{remote_dir}/{local_dir}/{rel_path}".replace("\\", "/")
                
                # Ensure remote directory exists
                remote_folder = os.path.dirname(remote_path)
                try:
                    sftp.stat(remote_folder)
                except FileNotFoundError:
                    # Very simple mkdir -p equivalent over SFTP
                    folders = remote_folder.replace(remote_dir, "").strip("/").split("/")
                    cur = remote_dir
                    for f in folders:
                        if not f: continue
                        cur = f"{cur}/{f}"
                        try:
                            sftp.stat(cur)
                        except FileNotFoundError:
                            sftp.mkdir(cur)
                            
                sftp.put(local_path, remote_path)
                
    print("Upload complete. Restarting services...")
    
    # Restart the python API server using nohup so it stays alive!
    cmd = f"cd {remote_dir}/litholamp-api && fuser -k 8000/tcp ; fuser -k 8001/tcp ; nohup python3 main.py > api_log.txt 2>&1 &"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    print("Restarting complete!")
    sftp.close()
    ssh.close()
    print("Everything is live!")

if __name__ == "__main__":
    deploy()
