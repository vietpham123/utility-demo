#!/usr/bin/env python3
"""
Generate clean training examples from extracted DQL queries.
Focuses on reusable patterns without customer-specific data.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def clean_query(dql: str) -> str:
    """Remove customer-specific values and simplify query."""
    # Remove scan limit hints
    dql = re.sub(r',?\s*scanLimitGBytes:\s*-?\d+', '', dql)
    # Remove specific IDs
    dql = re.sub(r'"[a-f0-9-]{36}"', '"<id>"', dql)  # UUIDs
    dql = re.sub(r'"[0-9]{12}"', '"<account-id>"', dql)  # AWS account IDs
    return dql.strip()


def extract_intent_from_query(dql: str) -> str:
    """Extract the intent based on query patterns."""
    dql_lower = dql.lower()
    
    if 'fetch logs' in dql_lower:
        if 'error' in dql_lower or 'severity' in dql_lower:
            return 'log_errors'
        elif 'count' in dql_lower:
            return 'log_count'
        else:
            return 'log_search'
    elif 'fetch spans' in dql_lower:
        if 'duration' in dql_lower or 'percentile' in dql_lower:
            return 'service_latency'
        elif 'error' in dql_lower or 'failed' in dql_lower:
            return 'failed_requests'
        else:
            return 'span_analysis'
    elif 'fetch events' in dql_lower or 'fetch bizevents' in dql_lower:
        return 'events'
    elif 'fetch dt.entity.kubernetes_cluster' in dql_lower:
        return 'kubernetes_cluster'
    elif 'fetch dt.entity.kubernetes' in dql_lower:
        return 'kubernetes_entity'
    elif 'fetch dt.entity.host' in dql_lower:
        return 'host_entity'
    elif 'fetch dt.entity.service' in dql_lower:
        return 'service_entity'
    elif 'fetch dt.entity.process_group' in dql_lower:
        return 'process_entity'
    elif 'fetch dt.entity.aws' in dql_lower:
        return 'aws_entity'
    elif 'fetch dt.entity.azure' in dql_lower:
        return 'azure_entity'
    elif 'timeseries' in dql_lower:
        if 'cpu' in dql_lower:
            return 'host_cpu'
        elif 'memory' in dql_lower:
            return 'host_memory'
        elif 'disk' in dql_lower:
            return 'host_disk'
        elif 'network' in dql_lower or 'nic' in dql_lower:
            return 'host_network'
        elif 'lambda' in dql_lower:
            return 'aws_lambda'
        elif 'bedrock' in dql_lower:
            return 'aws_bedrock'
        elif 'azure' in dql_lower:
            return 'azure_metrics'
        elif 'request' in dql_lower or 'response' in dql_lower:
            return 'service_metrics'
        else:
            return 'metrics'
    elif 'data record' in dql_lower:
        return 'data_record'
    else:
        return 'query'


def generate_nl(title: str, dql: str, category: str) -> str:
    """Generate a natural language description."""
    # Clean up title
    title = title.strip()
    if not title or title.lower() in ['', 'tile', 'untitled']:
        return None
    if title.startswith('Variable:'):
        return None  # Skip variable queries
    
    # Remove brackets and common prefixes
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\s*\([^)]*\)\s*$', '', title)
    
    if len(title) < 3:
        return None
    
    # Make it natural
    title_lower = title.lower()
    
    # Add context based on query type
    if 'timeseries' in dql.lower():
        return f"Show {title_lower} over time"
    elif 'count()' in dql.lower() or 'summarize' in dql.lower():
        return f"Count of {title_lower}"
    else:
        return f"Show {title_lower}"


def extract_expected_contains(dql: str) -> list:
    """Extract expected patterns that should be in generated queries."""
    contains = []
    dql_lower = dql.lower()
    
    # Data sources
    if 'fetch logs' in dql_lower:
        contains.append('fetch logs')
    if 'fetch spans' in dql_lower:
        contains.append('fetch spans')
    if 'fetch events' in dql_lower:
        contains.append('fetch events')
    if 'fetch dt.entity' in dql_lower:
        match = re.search(r'fetch (dt\.entity\.\w+)', dql_lower)
        if match:
            contains.append(f'fetch {match.group(1)}')
    if 'timeseries' in dql_lower:
        contains.append('timeseries')
    
    # Aggregations
    if 'count()' in dql_lower:
        contains.append('count()')
    if 'sum(' in dql_lower:
        contains.append('sum(')
    if 'avg(' in dql_lower:
        contains.append('avg(')
    if 'percentile(' in dql_lower:
        match = re.search(r'percentile\([^,]+,\s*(\d+)\)', dql_lower)
        if match:
            contains.append(f'percentile')
    
    # Filters
    if 'severity' in dql_lower:
        contains.append('severity')
    if 'filter' in dql_lower:
        contains.append('filter')
    
    # Grouping
    if 'by:' in dql_lower or 'by {' in dql_lower:
        contains.append('by')
    
    return contains


def main():
    input_file = Path('full-dashboards/golden_dataset.json')
    output_file = Path('clean_examples.py')
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    examples_by_category = defaultdict(list)
    seen = set()  # Deduplicate
    
    for category, queries in data.items():
        for q in queries:
            dql = q['dql'].strip()
            title = q.get('title', '')
            
            # Skip invalid queries
            if not dql or len(dql) < 30:
                continue
            if dql.count('$') > 4:  # Too customer-specific
                continue
            if dql.count('\n') > 15:  # Too complex
                continue
                
            # Skip variable queries
            if title.startswith('Variable:'):
                continue
            
            # Generate NL
            nl = generate_nl(title, dql, category)
            if not nl:
                continue
            
            # Deduplicate by NL
            if nl.lower() in seen:
                continue
            seen.add(nl.lower())
            
            # Clean the query
            clean_dql = clean_query(dql)
            
            # Get intent and expected patterns
            intent = extract_intent_from_query(clean_dql)
            expected = extract_expected_contains(clean_dql)
            
            examples_by_category[category].append({
                'nl': nl,
                'intent': intent,
                'expected_contains': expected,
                'dql': clean_dql
            })
    
    # Write output
    with open(output_file, 'w') as f:
        f.write('"""\nClean DQL Examples - Extracted from production dashboards.\n')
        f.write(f'Total examples: {sum(len(v) for v in examples_by_category.values())}\n"""\n\n')
        f.write('DASHBOARD_EXAMPLES = [\n')
        
        for category in sorted(examples_by_category.keys()):
            examples = examples_by_category[category]
            # Limit per category
            examples = examples[:30]
            
            f.write(f'\n    # === {category.upper()} ===\n')
            for ex in examples:
                f.write('    {\n')
                f.write(f'        "nl": "{ex["nl"]}",\n')
                f.write(f'        "intent": "{ex["intent"]}",\n')
                f.write(f'        "expected_contains": {ex["expected_contains"]},\n')
                # Format DQL with proper escaping
                dql_escaped = ex['dql'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                f.write(f'        "dql": """{ex["dql"]}""",\n')
                f.write('    },\n')
        
        f.write(']\n')
    
    print(f"Generated {sum(len(v) for v in examples_by_category.values())} examples")
    for cat in sorted(examples_by_category.keys()):
        print(f"  {cat}: {len(examples_by_category[cat])}")


if __name__ == '__main__':
    main()
