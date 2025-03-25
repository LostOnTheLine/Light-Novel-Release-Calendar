#!/bin/sh

# Clone the repo if not already present
if [ ! -d "/repo" ]; then
    git clone https://github.com/$GITHUB_USER/$GITHUB_REPO.git /repo
fi

cd /repo

# Copy the JSON file from the shared volume
cp /data/light_novel_releases.json .

# Git operations
git config --global user.name "$GITHUB_USER"
git config --global user.email "$GITHUB_EMAIL"
git add light_novel_releases.json
git commit -m "Update light novel releases - $(date -u)"
git push https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$GITHUB_REPO.git main

echo "Pushed to GitHub"