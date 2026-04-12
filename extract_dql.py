#!/usr/bin/env python3
"""
Extract DQL queries from Dynatrace dashboards exported with dtctl.
Builds a golden dataset for NL-to-DQL training and examples.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Categories based on common Dashboard domains
CATEGORIES = {
    'kubernetes': ['k8s', 'kubernetes', 'container', 'pod', 'node', 'namespace', 'cluster', 'workload', 'deployment'],
    'logs': ['log', 'logs', 'fetch logs', 'severity', 'loglevel'],
    'hosts': ['host', 'dt.host', 'cpu_usage', 'memory_usage', 'disk', 'dt.entity.host'],
    'aws': ['aws', 'amazon', 'ec2', 'lambda', 's3', 'rds', 'eks', 'ecs', 'dynamodb', 'cloudwatch'],
    'azure': ['azure', 'microsoft', 'vm', 'aks', 'blob', 'azure.', 'cosmosdb'],
    'spans': ['spans', 'trace', 'distributed', 'service', 'request', 'endpoint'],
    'metrics': ['timeseries', 'metric', 'dt.', 'avg(', 'sum(', 'percentile'],
    'events': ['events', 'bizevents', 'event.', 'problem'],
    'security': ['vulnerability', 'security', 'attack', 'appsec'],
    'network': ['network', 'nic', 'tcp', 'connection', 'traffic'],
    'database': ['database', 'db.', 'sql', 'query', 'postgres', 'mysql'],
    'grail': ['grail', 'bucket', 'segment', 'ingest'],
    'automation': ['workflow', 'automation', 'schedule'],
}


def categorize_query(query: str, title: str, dashboard_name: str) -> str:
    """Categorize a DQL query based on keywords."""
    text = f"{query} {title} {dashboard_name}".lower()
    
    for category, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            return category
    
    return 'other'


def clean_query(query: str) -> str:
    """Clean and normalize a DQL query."""
    # Remove comments
    lines = []
    for line in query.split('\n'):
        # Remove // comments but keep the query
        if '//' in line:
            parts = line.split('//')
            if parts[0].strip():
                lines.append(parts[0])
        elif '/*' not in line and '*/' not in line:
            lines.append(line)
    
    # Join and clean whitespace
    cleaned = ' '.join(lines)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def extract_queries_from_dashboard(dashboard_path: Path) -> List[Tuple[str, str, str, str]]:
    """Extract DQL queries from a dashboard JSON file.
    
    Returns: List of (query, title, dashboard_name, category)
    """
    queries = []
    
    try:
        with open(dashboard_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        return queries
    
    dashboard_name = data.get('name', 'Unknown')
    
    # Extract from tiles
    if 'content' in data and 'tiles' in data['content']:
        tiles = data['content']['tiles']
        for tile_id, tile in tiles.items():
            if isinstance(tile, dict) and 'query' in tile:
                query = tile['query']
                title = tile.get('title', f'Tile {tile_id}')
                
                # Skip empty or too short queries
                if not query or len(query.strip()) < 10:
                    continue
                
                category = categorize_query(query, title, dashboard_name)
                queries.append((query, title, dashboard_name, category))
    
    # Extract from variables (also contain DQL)
    if 'content' in data and 'variables' in data['content']:
        for var in data['content']['variables']:
            if isinstance(var, dict) and 'input' in var:
                query = var['input']
                title = f"Variable: {var.get('key', 'unknown')}"
                
                if query and len(query.strip()) >= 10:
                    category = categorize_query(query, title, dashboard_name)
                    queries.append((query, title, dashboard_name, category))
    
    return queries


def generate_nl_description(query: str, title: str, category: str) -> str:
    """Generate a natural language description for a DQL query."""
    query_lower = query.lower()
    
    # Clean up title
    title_clean = title.strip()
    if title_clean.startswith("Variable:"):
        return None  # Skip variable queries
    if not title_clean or title_clean in ['', 'Tile', 'Untitled']:
        return None  # Skip untitled tiles
    
    # Remove brackets and common prefixes
    title_clean = re.sub(r'^\[.*?\]\s*', '', title_clean)  # Remove [prefix]
    title_clean = re.sub(r'\s*\(.*?\)\s*$', '', title_clean)  # Remove (suffix)
    
    if len(title_clean) < 5:
        return None  # Skip short/empty titles
    
    # Generate natural description based on query patterns
    descriptions = []
    
    # Detect data source
    if 'fetch logs' in query_lower:
        descriptions.append("log")
    elif 'fetch spans' in query_lower:
        descriptions.append("span/trace")
    elif 'fetch events' in query_lower or 'fetch bizevents' in query_lower:
        descriptions.append("event")
    elif 'fetch dt.entity' in query_lower:
        entity_match = re.search(r'fetch dt\.entity\.(\w+)', query_lower)
        if entity_match:
            entity = entity_match.group(1).replace('_', ' ')
            descriptions.append(entity)
    elif 'timeseries' in query_lower:
        descriptions.append("metric")
    
    # Detect aggregation
    if 'count()' in query_lower or 'count(' in query_lower:
        descriptions.append("count")
    elif 'avg(' in query_lower:
        descriptions.append("average")
    elif 'sum(' in query_lower:
        descriptions.append("total")
    elif 'percentile' in query_lower:
        descriptions.append("percentile")
    
    # Detect filters
    if 'severity' in query_lower and 'error' in query_lower:
        descriptions.append("error")
    
    # Build final description
    return title_clean.lower()


def build_golden_dataset(dashboards_dir: Path) -> Dict[str, List[dict]]:
    """Build golden dataset from all dashboards."""
    all_queries = []
    
    for dashboard_path in dashboards_dir.glob('*.json'):
        queries = extract_queries_from_dashboard(dashboard_path)
        all_queries.extend(queries)
    
    print(f"Extracted {len(all_queries)} queries from {len(list(dashboards_dir.glob('*.json')))} dashboards")
    
    # Group by category
    by_category = defaultdict(list)
    seen_queries = set()  # Dedup
    
    for query, title, dashboard_name, category in all_queries:
        cleaned = clean_query(query)
        
        # Skip duplicates and very short queries
        if cleaned in seen_queries or len(cleaned) < 20:
            continue
        seen_queries.add(cleaned)
        
        nl_description = generate_nl_description(query, title, category)
        
        by_category[category].append({
            'nl': nl_description,
            'dql': query.strip(),
            'title': title,
            'dashboard': dashboard_name,
            'category': category,
        })
    
    # Print summary
    print("\nQueries by category:")
    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(items)}")
    
    return dict(by_category)


def export_examples_py(dataset: Dict[str, List[dict]], output_path: Path, max_per_category: int = 20):
    """Export dataset as Python examples.py format."""
    
    examples = []
    
    for category, items in dataset.items():
        # Sort by query complexity (longer = more complex) and take top N
        sorted_items = sorted(items, key=lambda x: len(x['dql']), reverse=True)[:max_per_category]
        
        for item in sorted_items:
            # Determine expected_contains based on query patterns
            expected = []
            query = item['dql'].lower()
            
            if 'fetch logs' in query:
                expected.append('fetch logs')
            elif 'fetch spans' in query:
                expected.append('fetch spans')
            elif 'fetch events' in query or 'fetch bizevents' in query:
                expected.append('fetch')
            elif 'timeseries' in query:
                expected.append('timeseries')
            elif 'fetch dt.entity' in query:
                expected.append('fetch dt.entity')
            
            # Add aggregation functions
            for func in ['sum(', 'avg(', 'count(', 'percentile(', 'max(', 'min(']:
                if func in query:
                    expected.append(func.rstrip('('))
                    break
            
            # Add filter patterns
            if 'filter' in query:
                expected.append('filter')
            
            examples.append({
                'nl': item['nl'],
                'intent': f"{category}_{item['title'][:20].lower().replace(' ', '_')}",
                'expected_contains': expected,
                'dql': item['dql'],
            })
    
    # Write examples.py format
    with open(output_path, 'w') as f:
        f.write('"""\n')
        f.write('Golden DQL Examples - Extracted from Dynatrace dashboards.\n')
        f.write(f'Total examples: {len(examples)}\n')
        f.write('"""\n\n')
        f.write('DASHBOARD_EXAMPLES = [\n')
        
        current_category = None
        for ex in sorted(examples, key=lambda x: x['intent'].split('_')[0]):
            cat = ex['intent'].split('_')[0]
            if cat != current_category:
                f.write(f'\n    # === {cat.upper()} ===\n')
                current_category = cat
            
            # Escape quotes in strings
            nl = ex['nl'].replace('"', '\\"')
            dql = ex['dql'].replace('\\', '\\\\').replace('"', '\\"')
            expected = ex['expected_contains']
            
            f.write('    {\n')
            f.write(f'        "nl": "{nl}",\n')
            f.write(f'        "intent": "{ex["intent"]}",\n')
            f.write(f'        "expected_contains": {expected},\n')
            f.write(f'        "dql": """{ex["dql"]}""",\n')
            f.write('    },\n')
        
        f.write(']\n')
    
    print(f"\nExported {len(examples)} examples to {output_path}")


def main():
    dashboards_dir = Path("/Users/viet.pham/Documents/Dynatrace Data/Exelon/full-dashboards")
    output_dir = Path("/Users/viet.pham/Library/CloudStorage/OneDrive-Dynatrace/Documents/Dynatrace Data/nl_to_dql")
    
    if not dashboards_dir.exists():
        print(f"Dashboards directory not found: {dashboards_dir}")
        return
    
    # Build dataset
    dataset = build_golden_dataset(dashboards_dir)
    
    # Export to JSON for reference
    json_output = dashboards_dir / 'golden_dataset.json'
    with open(json_output, 'w') as f:
        json.dump(dataset, f, indent=2)
    print(f"Saved JSON dataset to {json_output}")
    
    # Export to examples.py format
    examples_output = output_dir / 'dashboard_examples.py'
    export_examples_py(dataset, examples_output, max_per_category=25)
    
    print("\nDone! Review the generated examples and merge with existing examples.py")


if __name__ == '__main__':
    main()
