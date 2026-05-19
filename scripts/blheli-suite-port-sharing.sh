#!/bin/bash

BOTTLE_DIR="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/BLHeli-Suite"
DOSDEVICES="$BOTTLE_DIR/dosdevices"

DEVICES=()

for dev in /dev/ttyUSB* /dev/ttyACM*; do
    [ -e "$dev" ] || continue

    info=$(udevadm info -a -n "$dev")

    if echo "$info" | grep -qE 'idVendor.*(0403|1a86|2341)' && \
       echo "$info" | grep -qE 'idProduct.*(6001|7523|0043)'; then
        DEVICES+=("$dev")
    fi
done

if [ ${#DEVICES[@]} -eq 0 ]; then
    echo "No Arduinos found"
    notify-send -a "BLHeli Suite" "Arduino not detected" "No Arduino Nano detected."
    exit 1 
else
echo "Detected Device(s): ${DEVICES[*]}"
fi

if pgrep -f "BLHeliSuite" > /dev/null; then
    echo "BLHeli is already running"
else
    setsid flatpak run --command=bottles-cli com.usebottles.bottles run -p BLHeliSuite -b BLHeliSuite -- %u > /dev/null 2>&1 &
    echo "Waiting for BLHeli to start..."
    for i in {1..15}; do
        if pgrep -f "BLHeliSuite" > /dev/null; then
            echo "BLHeli is running"
            break
        fi
        sleep 1
    done
    sleep 2
fi

i=1
MAP_MSG=""
for dev in "${DEVICES[@]}"; do
    com="$DOSDEVICES/com$i"

    rm -f "$com"
    ln -sf "$dev" "$com"

    echo "Assigned $dev → com$i"
    MAP_MSG+="$dev → COM$i\n"
    ((i++))
done

notify-send -a "BLHeli Suite" "Arduino(s) detected" "$(echo -e "$MAP_MSG")"