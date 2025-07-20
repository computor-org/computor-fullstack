#!/usr/bin/env bash
# Script to install git hooks for the project

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Installing git hooks..."

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ Error: Not in a git repository!"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Install pre-commit hook
if [ -f "$SCRIPT_DIR/pre-commit" ]; then
    echo "📋 Installing pre-commit hook..."
    cp "$SCRIPT_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "✅ Pre-commit hook installed"
else
    echo "⚠️  Warning: pre-commit hook not found in $SCRIPT_DIR"
fi

# Future: Add more hooks here as needed
# Example:
# if [ -f "$SCRIPT_DIR/pre-push" ]; then
#     cp "$SCRIPT_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push"
#     chmod +x "$GIT_HOOKS_DIR/pre-push"
# fi

echo
echo "✅ Git hooks installation complete!"
echo
echo "The following protections are now active:"
echo "  🔒 Pre-commit: Prevents committing secrets (GitLab tokens, API keys, etc.)"
echo
echo "To bypass hooks in emergency (NOT RECOMMENDED):"
echo "  git commit --no-verify"
echo
echo "To uninstall hooks:"
echo "  rm $GIT_HOOKS_DIR/pre-commit"