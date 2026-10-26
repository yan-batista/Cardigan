#!/usr/bin/env bash
# Adds Cardigan to the application menu (and to "Open with" for markdown files).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
icons="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

mkdir -p "$apps" "$icons"
cp "$repo/cardigan/icon.svg" "$icons/cardigan.svg"

cat > "$apps/cardigan.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Cardigan
Comment=Markdown to-do lists as a kanban board
Exec=python3 -m cardigan %f
Path=$repo
Icon=cardigan
StartupWMClass=cardigan
Terminal=false
Categories=Office;ProjectManagement;
MimeType=text/markdown;text/plain;
DESKTOP

update-desktop-database "$apps" 2>/dev/null || true
echo "Installed: $apps/cardigan.desktop"
