#!/usr/bin/env bash

set -euo pipefail

direction="${1:-}"
if [ "$direction" != "next" ] && [ "$direction" != "prev" ]; then
    echo "Usage: $0 [next|prev]" >&2
    exit 1
fi

workspaces_json="$(swaymsg -t get_workspaces -r)"
current_num="$(jq -r '.[] | select(.focused) | .num // empty' <<< "$workspaces_json")"
current_output="$(jq -r '.[] | select(.focused) | .output // empty' <<< "$workspaces_json")"

if [ -z "$current_num" ] || [ -z "$current_output" ]; then
    echo "Error: could not determine the focused workspace" >&2
    exit 1
fi

mapfile -t workspace_nums < <(
    jq -r --arg output "$current_output" \
        '[.[] | select(.output == $output and .num >= 0) | .num] | sort | .[]' \
        <<< "$workspaces_json"
)

if [ "${#workspace_nums[@]}" -eq 0 ]; then
    echo "Error: no numeric workspaces on output $current_output" >&2
    exit 1
fi

current_idx=-1
for i in "${!workspace_nums[@]}"; do
    if [ "${workspace_nums[$i]}" = "$current_num" ]; then
        current_idx="$i"
        break
    fi
done

if [ "$current_idx" -lt 0 ]; then
    echo "Error: focused workspace is not in the output workspace list" >&2
    exit 1
fi

if [ "$direction" = "next" ]; then
    next_idx=$(( (current_idx + 1) % ${#workspace_nums[@]} ))
else
    next_idx=$(( (current_idx - 1 + ${#workspace_nums[@]}) % ${#workspace_nums[@]} ))
fi

swaymsg "workspace number ${workspace_nums[$next_idx]}" >/dev/null
