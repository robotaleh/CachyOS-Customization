#!/bin/bash

DIR="$HOME/.dynamic-login-wallpaper"
mkdir -p "$DIR"

FILE="$DIR/latest_wallpaper.png"
OUTPUT="$DIR/dynamic-login-wallpaper.png"


xdotool key super+d

# sleep 0.2

# Captura
spectacle -b -n -o "$FILE"

# sleep 0.2

xdotool key super+d

# Crop
TOP_MARGIN=50
BOTTOM_MARGIN=70

MONITOR_W=2560
MONITOR_H=1440

LEFT_MONITOR_W=1440
LEFT_MONITOR_H=2560

OFFSET_TRIM_H=$(((LEFT_MONITOR_H - MONITOR_H)/2))

FINAL_H=$((MONITOR_H - TOP_MARGIN - BOTTOM_MARGIN))
FINAL_W=$(((FINAL_H * LEFT_MONITOR_H)/LEFT_MONITOR_W))

FINAL_OFFSET_H=$((OFFSET_TRIM_H + TOP_MARGIN))
FINAL_OFFSET_W=$((LEFT_MONITOR_W + ((MONITOR_W-FINAL_W)/2)))

magick "$FILE" \
  -crop ${FINAL_W}x${FINAL_H}+${FINAL_OFFSET_W}+${FINAL_OFFSET_H} \
  +repage \
  "$OUTPUT"

rm "$FILE"

exit 0