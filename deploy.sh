#!/bin/bash

# Configuration
REMOTE="root@198.71.49.155"
REMOTE_DIR="/root/formnow"
BACKUP_DIR="litholamp_remote_backup"

echo "========================================================"
echo " 1. DOWNLOADING BACKUP FROM IONOS SERVER"
echo "========================================================"
echo "You will be prompted for your remote server password..."
mkdir -p "$BACKUP_DIR"
rsync -avz "$REMOTE":"$REMOTE_DIR/" "./$BACKUP_DIR/"

echo ""
echo "========================================================"
echo " 2. UPLOADING LATEST CODE TO IONOS SERVER"
echo "========================================================"
echo "You will be prompted for your remote server password again..."

# We exclude heavy cache and node_modules folders to make the upload fast
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' --exclude 'customer_renders' ./litholamp-api/ "$REMOTE":"$REMOTE_DIR/litholamp-api/"
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' --exclude 'customer_renders' ./litholamp-web/ "$REMOTE":"$REMOTE_DIR/litholamp-web/"

echo ""
echo "========================================================"
echo " DEPLOYMENT COMPLETE! "
echo "========================================================"
echo "Your old remote code is safely backed up in the '$BACKUP_DIR' folder."
echo "Your new code is now uploaded to the server."
echo ""
echo "Next Steps: "
echo "Go back to your open SSH terminal on the server, CD into the folders, and restart your python and node/next.js processes to apply the changes!"
