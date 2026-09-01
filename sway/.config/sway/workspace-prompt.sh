#!/usr/bin/env bash

set -euo pipefail

action="${1:-focus}"
case "$action" in
    focus) prompt="Go to workspace: " ;;
    move) prompt="Move to workspace: " ;;
    *) echo "Usage: $0 [focus|move]" >&2; exit 1 ;;
esac

choices="$({ swaymsg -t get_workspaces -r 2>/dev/null | jq -r '.[].name'; seq 1 10; printf '%s\n' 31 32 33 34 35; } | awk 'NF && !seen[$0]++')"
workspace="$(printf '%s\n' "$choices" | fuzzel --dmenu --prompt "$prompt")" || exit 0
[ -n "$workspace" ] || exit 0

if [ "$action" = "move" ]; then
    swaymsg "move container to workspace \"$workspace\"" >/dev/null
else
    swaymsg "workspace \"$workspace\"" >/dev/null
fi
