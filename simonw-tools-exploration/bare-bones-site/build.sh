#!/bin/bash
# build.sh – orchestrate the bare-bones tools site build
set -e

# Make sure we have full git history so commit dates are accurate
if [ -f .git/shallow ]; then
    git fetch --unshallow
fi

echo "=== Gathering tool metadata ==="
python gather_links.py

echo "=== Building index.html ==="
python build_index.py

echo "=== Done! ==="
