#!/bin/bash
# Alert when disk space on / drops below threshold

THRESHOLD_GB=5
MOUNT_POINT="/"

# Get available space in GB
avail_kb=$(df --output=avail "$MOUNT_POINT" | tail -1)
avail_gb=$((avail_kb / 1024 / 1024))

if [ "$avail_gb" -lt "$THRESHOLD_GB" ]; then
    i3-nagbar -t warning -m "Low disk space: ${avail_gb}GB remaining on $MOUNT_POINT" &
fi
