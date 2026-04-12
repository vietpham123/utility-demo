#!/bin/bash
# Export all dashboards with full content using dtctl

OUTPUT_DIR="/Users/viet.pham/Documents/Dynatrace Data/Exelon/full-dashboards"
DASHBOARD_IDS="/tmp/dashboard-ids.txt"
DTCTL="/opt/homebrew/bin/dtctl"

mkdir -p "$OUTPUT_DIR"

total=$(wc -l < "$DASHBOARD_IDS")
count=0

while read id; do
  count=$((count + 1))
  if [ ! -f "$OUTPUT_DIR/$id.json" ]; then
    echo "[$count/$total] Exporting: $id"
    "$DTCTL" get dashboard "$id" -o json > "$OUTPUT_DIR/$id.json" 2>/dev/null
  else
    echo "[$count/$total] Already exists: $id"
  fi
done < "$DASHBOARD_IDS"

echo "Export complete. Total: $count dashboards"
