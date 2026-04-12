#!/bin/bash
# Export dashboards in parallel using dtctl

OUTPUT_DIR="/Users/viet.pham/Documents/Dynatrace Data/Exelon/full-dashboards"
DASHBOARD_IDS="/tmp/dashboard-ids.txt"
DTCTL="/opt/homebrew/bin/dtctl"
PARALLEL_JOBS=5  # Number of concurrent exports

mkdir -p "$OUTPUT_DIR"

export_dashboard() {
    local id="$1"
    local outfile="$OUTPUT_DIR/$id.json"
    
    if [ ! -f "$outfile" ] || [ ! -s "$outfile" ]; then
        "$DTCTL" get dashboard "$id" -o json > "$outfile" 2>/dev/null
    fi
}

export -f export_dashboard
export OUTPUT_DIR DTCTL

echo "Starting parallel export (${PARALLEL_JOBS} jobs)..."
cat "$DASHBOARD_IDS" | xargs -P "$PARALLEL_JOBS" -I{} bash -c 'export_dashboard "{}"'
echo "Export complete!"
