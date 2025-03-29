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
        # Count added and updated lines in JSON file
        added=$(git diff --cached --numstat | grep "data/light_novel_releases.json" | awk '{print $1}' || echo 0)
        updated=$(git diff --cached --numstat | grep "data/light_novel_releases.json" | awk '{print $2}' || echo 0)
        
        # Handle case where file is new (no deletions)
        if [ "$added" -gt 0 ] && [ "$updated" -eq 0 ]; then
            msg="Added $added releases from scraper"
        elif [ "$added" -gt 0 ] || [ "$updated" -gt 0 ]; then
            msg="Updated $updated releases from scraper, added $added release(s) from scraper"
        else
            msg="Minor updates from scraper"
        fi
        
        git commit -m "$msg"
        git push origin main
    else
        echo "No changes to commit"
    fi
    
    sleep $((${SYNC_INTERVAL_HOURS:-1} * 3600))
done