#!/usr/bin/env bash

set -euo pipefail

direction="${1:-}"
if [ "$direction" != "next" ] && [ "$direction" != "prev" ]; then
    echo "Usage: $0 [next|prev]" >&2
    exit 1
fi

workspaces_json="$(swaymsg -t get_workspaces -r)"
current_name="$(jq -r '.[] | select(.focused) | .name // empty' <<< "$workspaces_json")"
current_output="$(jq -r '.[] | select(.focused) | .output // empty' <<< "$workspaces_json")"

if [ -z "$current_name" ] || [ -z "$current_output" ]; then
    echo "Error: could not determine the focused workspace" >&2
    exit 1
fi

mapfile -t workspace_names < <(
    jq -r --arg output "$current_output" \
        '.[] | select(.output == $output) | .name' \
        <<< "$workspaces_json"
)

if [ "${#workspace_names[@]}" -eq 0 ]; then
    echo "Error: no workspaces on output $current_output" >&2
    exit 1
fi

current_idx=-1
for i in "${!workspace_names[@]}"; do
    if [ "${workspace_names[$i]}" = "$current_name" ]; then
        current_idx="$i"
        break
    fi
done

if [ "$current_idx" -lt 0 ]; then
    echo "Error: focused workspace is not in the output workspace list" >&2
    exit 1
fi

if [ "$direction" = "next" ]; then
    next_idx=$(( (current_idx + 1) % ${#workspace_names[@]} ))
else
    next_idx=$(( (current_idx - 1 + ${#workspace_names[@]}) % ${#workspace_names[@]} ))
fi

quoted_next_name="$(jq -Rrn --arg name "${workspace_names[$next_idx]}" '$name | @json')"
swaymsg "workspace $quoted_next_name" >/dev/null
