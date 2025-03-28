#!/bin/sh
REPO_DIR="/data/Light-Novel-Release-Calendar"

# Initialize repo if not present
if [ ! -d "$REPO_DIR/.git" ]; then
    mkdir -p "$REPO_DIR"
    cd "$REPO_DIR"
    git init
    git remote add origin "https://$GITHUB_USER:$GITHUB_TOKEN@github.com/$GITHUB_USER/$GITHUB_REPO.git"
    git config user.name "$GITHUB_USER"
    git config user.email "$GITHUB_EMAIL"
    git pull origin main || git commit --allow-empty -m "Initial commit" && git push origin main
fi

# Sync loop
while true; do
    cd "$REPO_DIR"
    git pull origin main
    git add .
    git commit -m "Update releases from scraper" || echo "No changes to commit"
    git push origin main
    sleep $((${SYNC_INTERVAL_HOURS:-1} * 3600))
done