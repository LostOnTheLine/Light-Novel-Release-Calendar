#!/bin/sh
REPO_DIR="${REPO_DIR:-/git}"  # Default to /git
FIRST_PUSH_DELAY="${FIRST_PUSH_DELAY:-60}"  # Default 60 seconds

# Initialize repo if not present
if [ ! -d "$REPO_DIR/.git" ]; then
    mkdir -p "$REPO_DIR"
    cd "$REPO_DIR"
    git init -b main  # Set initial branch to main
    git config --global --add safe.directory "$REPO_DIR"  # Bypass ownership check
    git remote add origin https://$GITHUB_USER:$GITHUB_TOKEN@github.com/$GITHUB_USER/$GITHUB_REPO.git
    git config user.name "$GITHUB_USER"
    git config user.email "$GITHUB_EMAIL"
    git pull origin main || { git commit --allow-empty -m "Initial commit" && git push origin main; }
fi

# Initial delay before first push
echo "Waiting $FIRST_PUSH_DELAY seconds before first push..."
sleep "$FIRST_PUSH_DELAY"

# Sync loop
while true; do
    cd "$REPO_DIR"
    git config --global --add safe.directory "$REPO_DIR"  # Ensure set for each loop
    git fetch origin
    git checkout main  # Ensure on main branch
    git pull origin main
    
    # Check for changes
    git add .
    if git status --porcelain | grep -q .; then
        updates=$(jq -r '.general_statistics.updates_processed[0]' data/light_novel_releases.json)
        books=$(jq -r '.general_statistics.books_updated | join(", ")' data/light_novel_releases.json)
        msg="Processed $updates book updates: $books"
        git commit -m "$msg"
        git push origin main
    else
        echo "No changes to commit"
    fi
    
    sleep $((${SYNC_INTERVAL_HOURS:-1} * 3600))
done