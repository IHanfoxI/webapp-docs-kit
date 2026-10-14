#!/usr/bin/env bash
# webapp-docs-kit installer for Linux and macOS.
#   ./install.sh                 -> for your user: links the skills into every agent found
#   ./install.sh --project DIR   -> copies the skills into DIR/.claude/skills and DIR/.agents/skills
#   ./install.sh --uninstall     -> removes the links created by this script
#
# Skill folders per agent (user scope):
#   ~/.claude/skills            Claude Code
#   ~/.agents/skills            Codex, Gemini CLI, GitHub Copilot, OpenCode and other Agent Skills clients
#   ~/.cursor/skills            Cursor (only if ~/.cursor exists)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS="visual-check user-manual video-tutorial"
SCRIPTS="$ROOT/skills/visual-check/scripts"

targets() {
    echo "$HOME/.claude/skills"
    echo "$HOME/.agents/skills"
    [ -d "$HOME/.cursor" ] && echo "$HOME/.cursor/skills"
    return 0
}

if [ "${1:-}" = "--uninstall" ]; then
    for dir in $(targets); do
        for s in $SKILLS; do
            if [ -L "$dir/$s" ]; then rm "$dir/$s"; echo "Removed $dir/$s"; fi
        done
    done
    exit 0
fi

command -v node >/dev/null && command -v npm >/dev/null || { echo "Node.js 18+ is required: https://nodejs.org"; exit 1; }

missing=""
command -v ffmpeg >/dev/null || missing="$missing ffmpeg(video-tutorial)"
command -v pdftoppm >/dev/null || missing="$missing poppler(user-manual)"
command -v python3 >/dev/null || missing="$missing python3(user-manual)"
if ! command -v soffice >/dev/null && [ ! -x /Applications/LibreOffice.app/Contents/MacOS/soffice ]; then
    missing="$missing libreoffice(user-manual)"
fi
[ -n "$missing" ] && echo "Optional tools not found:$missing. See docs/prerequisites.md."

(cd "$SCRIPTS" && npm install --silent)
node "$SCRIPTS/node_modules/playwright-core/cli.js" install chromium

link_into() {  # $1 = skills folder
    mkdir -p "$1"
    for s in $SKILLS; do
        if [ -e "$1/$s" ] && [ ! -L "$1/$s" ]; then
            echo "Skipped $1/$s: it exists and is not a link"; continue
        fi
        ln -sfn "$ROOT/skills/$s" "$1/$s"
        echo "Linked $1/$s"
    done
}

if [ "${1:-}" = "--project" ]; then
    # A copy (not a link) so it travels with the project's repository.
    project="${2:?Pass the project folder}"
    for dest in "$project/.claude/skills" "$project/.agents/skills"; do
        mkdir -p "$dest"
        for s in $SKILLS; do
            rsync -a --delete --exclude node_modules "$ROOT/skills/$s/" "$dest/$s/"
            echo "Copied $dest/$s"
        done
    done
    echo "Run npm install in $project/.claude/skills/visual-check/scripts (and .agents/...) before first use."
else
    for dir in $(targets); do link_into "$dir"; done
fi
echo "Done. Restart your agent and try /visual-check, /user-manual or /video-tutorial in a project."
