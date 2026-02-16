#!/usr/bin/env bash
set -euo pipefail

# Installs git hooks for the StoryEngine monorepo.
# Run once after cloning:  ./scripts/install-hooks.sh

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SCRIPTS_DIR="$REPO_ROOT/scripts"

echo "Installing git hooks..."

ln -sf "$SCRIPTS_DIR/pre-commit" "$HOOKS_DIR/pre-commit"

echo "Done. Pre-commit hook installed."
