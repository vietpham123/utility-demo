#!/bin/bash
# Export dashboards in parallel using GNU parallel-style processing so we can use 5 concurrent jobs

OUTPUT_DIR="/Users/viet.pham/Documents/Dynatrace Data/Exelon/full-dashboards"  
DTCTL="/opt/homebrew/bin/dtctl"

# Export single dashboard
id="$1"
if [ -z "$id" ]; then
    echo "Usage: $0 <dashboard-id>"
    exit 1
fi

outfile="$OUTPUT_DIR/$id.json"
$DTCTL get dashboard "$id" -o json > "$outfile" 2>/dev/null

# Check if successful
if [ -s "$outfile" ]; then
    echo "OK: $id"
else
    echo "FAIL: $id"
    rm -f "$outfile"
fi
