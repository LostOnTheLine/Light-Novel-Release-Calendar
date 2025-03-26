#!/bin/sh

SYNC_INTERVAL_HOURS=${SYNC_INTERVAL_HOURS:-1}  # Default to 1 hour

# Clone the repo if not already present
if [ ! -d "/repo" ]; then
    git clone https://github.com/$GITHUB_USER/$GITHUB_REPO.git /repo
fi

cd /repo

while true; do
    # Copy the JSON file
    cp /data/light_novel_releases.json .
    
    # Git operations
    git config --global user.name "$GITHUB_USER"
    git config --global user.email "$GITHUB_EMAIL"
    git add light_novel_releases.json
    git commit -m "Update light novel releases - $(date -u)" || echo "No changes to commit"
    git push https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$GITHUB_REPO.git main
    
    echo "Pushed to GitHub at $(date -u)"
    sleep $(($SYNC_INTERVAL_HOURS * 3600))  # Convert hours to seconds
done