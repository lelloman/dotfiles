#!/bin/bash

# Script to cycle through workspaces on the current monitor only
# Usage: workspace-cycle.sh [next|prev]

DIRECTION="$1"

if [ "$DIRECTION" != "next" ] && [ "$DIRECTION" != "prev" ]; then
    echo "Usage: $0 [next|prev]"
    exit 1
fi

# Get current workspace info
WORKSPACES_JSON=$(i3-msg -t get_workspaces)
CURRENT_JSON=$(echo "$WORKSPACES_JSON" | jq -r '.[] | select(.focused == true)')
CURRENT_NUM=$(echo "$CURRENT_JSON" | jq -r '.num // empty')
CURRENT_OUTPUT=$(echo "$CURRENT_JSON" | jq -r '.output')

if [ -z "$CURRENT_NUM" ] || [ -z "$CURRENT_OUTPUT" ]; then
    echo "Error: Could not get current workspace info"
    exit 1
fi

# Get all workspaces on current output sorted by number
WORKSPACES_JSON=$(i3-msg -t get_workspaces)
WORKSPACE_NUMS=$(echo "$WORKSPACES_JSON" | jq -r --arg output "$CURRENT_OUTPUT" '[.[] | select(.output == $output) | .num] | sort_by(.) | .[]' | grep -E '^[0-9]+$')

if [ -z "$WORKSPACE_NUMS" ]; then
    echo "Error: No workspaces found on output $CURRENT_OUTPUT"
    exit 1
fi

# Convert to array
mapfile -t WS_ARRAY <<< "$WORKSPACE_NUMS"
NUM_WS=${#WS_ARRAY[@]}

# Find current workspace index
CURRENT_IDX=-1
for i in "${!WS_ARRAY[@]}"; do
    if [ "${WS_ARRAY[$i]}" = "$CURRENT_NUM" ]; then
        CURRENT_IDX=$i
        break
    fi
done

if [ $CURRENT_IDX -eq -1 ]; then
    echo "Error: Current workspace not found in list"
    exit 1
fi

# Calculate next/prev index with wraparound
if [ "$DIRECTION" = "next" ]; then
    NEXT_IDX=$(( (CURRENT_IDX + 1) % NUM_WS ))
else
    NEXT_IDX=$(( (CURRENT_IDX - 1 + NUM_WS) % NUM_WS ))
fi

NEXT_WS="${WS_ARRAY[$NEXT_IDX]}"

# Switch to the workspace
i3-msg "workspace number $NEXT_WS"
