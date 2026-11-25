#!/bin/sh
set -e

REPO_URL="https://github.com/justkrismanohar/fine-tuning-build.git"
TARGET_DIR="/civicdesk"

# Clone on first start, or pull latest changes on container restart
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "Cloning repository into $TARGET_DIR..."
    git clone "$REPO_URL" "$TARGET_DIR"
else
    echo "Updating repository in $TARGET_DIR..."
    git -C "$TARGET_DIR" pull --ff-only
fi

# Hand off execution to your main command (e.g., JupyterLab / model servers)
exec "$@"