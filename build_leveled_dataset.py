#!/usr/bin/env python3
"""
Build a leveled golden dataset with simple, intermediate, and complex DQL examples.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def calculate_complexity(dql: str) -> tuple[str, int]:
    """
    Calculate complexity level of a DQL query.
    Returns: (level, score)
    
    Simple (1-4): Basic fetch/timeseries with 1-2 filters
    Intermediate (5-10): Multiple operations, grouping, some field manipulation
    Complex (11+): Joins, subqueries, parsing, advanced transformations
    """
    dql_lower = dql.lower()
    score = 0
    
    # Count structural elements
    lines = len([l for l in dql.split('\n') if l.strip()])
    pipe_count = dql.count('|')
    
    # Basic complexity from pipeline depth
    if pipe_count <= 2:
        score += 1
    elif pipe_count <= 5:
        score += 3
    elif pipe_count <= 10:
        score += 5
    else:
        score += 7
    
    # Joins add significant complexity
    if 'join' in dql_lower:
        score += 5
        if dql_lower.count('join') > 1:
            score += 3
    
    # Subqueries/append
    if 'append' in dql_lower:
        score += 4
    
    # Lookup operations
    if 'lookup' in dql_lower:
        score += 4
    
    # Parsing adds complexity
    if 'parse ' in dql_lower:
        score += 3
    if 'json:' in dql_lower:
        score += 2
    
    # Field manipulation
    if 'fieldsflatten' in dql_lower:
        score += 2
    
    # Aggregations (each adds a bit)
    agg_count = sum(1 for agg in ['count(', 'sum(', 'avg(', 'max(', 'min(', 'percentile('] 
                    if agg in dql_lower)
    score += min(agg_count, 3)  # Cap contribution
    
    # Conditional logic
    if_count = dql_lower.count('if(')
    if if_count > 0:
        score += min(if_count * 2, 4)
    
    # Array functions
    array_funcs = ['arrayavg', 'arraysum', 'arraymax', 'arraymin', 'arraypercentile', 
                   'arraymovingavg', 'arraydelta', 'icollectarray', 'collectarray']
    for func in array_funcs:
        if func in dql_lower:
            score += 2
    
    # Determine level based on score
    if score <= 4:
        return 'simple', score
    elif score <= 10:
        return 'intermediate', score
    else:
        return 'complex', score


def is_valid_example(dql: str, title: str) -> bool:
    """Check if query is suitable for training."""
    # Skip variable definitions
    if title.startswith('Variable:'):
        return False
    
    # Skip very short queries (just IDs or empty)
    if len(dql.strip()) < 30:
        return False
    
    # Skip overly long queries (hard to learn from)
    if len(dql.strip()) > 2000:
        return False
    
    # Skip queries with too many lines
    lines = len([l for l in dql.split('\n') if l.strip()])
    if lines > 40:
        return False
    
    # Skip queries that are just static values
    if not any(kw in dql.lower() for kw in ['fetch', 'timeseries', 'data record', 'data\n']):
        return False
    
    return True


def generate_nl_description(title: str, dql: str, level: str) -> str:
    """Generate natural language description."""
    title = title.strip()
    
    # Clean up title
    title = re.sub(r'^\[.*?\]\s*', '', title)  # Remove [prefix]
    title = re.sub(r'\s*\([^)]*\)\s*$', '', title)  # Remove (suffix)
    title = re.sub(r'^\d+\.\s*', '', title)  # Remove numbering
    
    if not title or title.lower() in ['', 'tile', 'untitled']:
        return None
    
    if len(title) < 3:
        return None
    
    # Skip titles with problematic characters
    if '"' in title or "'" in title:
        # Remove quotes instead of skipping
        title = title.replace('"', '').replace("'", '')
    
    # Make it natural language (lowercase)
    return title.lower()


def extract_intent(dql: str, category: str) -> str:
    """Extract intent from query."""
    dql_lower = dql.lower()
    
    if 'fetch logs' in dql_lower:
        if 'error' in dql_lower or any(s in dql_lower for s in ['severity == "error"', 'loglevel == "error"']):
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
    elif 'fetch dt.entity' in dql_lower:
        match = re.search(r'fetch (dt\.entity\.\w+)', dql_lower)
        if match:
            entity = match.group(1).split('.')[-1]
            return f'{entity}_entity'
        return 'entity'
    elif 'fetch dt.davis.problems' in dql_lower:
        return 'problems'
    elif 'fetch security' in dql_lower:
        return 'security'
    elif 'fetch user.events' in dql_lower:
        return 'rum'
    elif 'timeseries' in dql_lower:
        if 'cpu' in dql_lower:
            return 'cpu_metrics'
        elif 'memory' in dql_lower:
            return 'memory_metrics'
        elif 'disk' in dql_lower:
            return 'disk_metrics'
        elif 'network' in dql_lower or 'nic' in dql_lower:
            return 'network_metrics'
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
    elif 'data record' in dql_lower or dql_lower.startswith('data'):
        return 'data_record'
    
    return f'{category}_query'


def extract_expected_contains(dql: str) -> list:
    """Extract key patterns that should appear in generated queries."""
    contains = []
    dql_lower = dql.lower()
    
    # Data sources
    if 'fetch logs' in dql_lower:
        contains.append('fetch logs')
    if 'fetch spans' in dql_lower:
        contains.append('fetch spans')
    if 'fetch events' in dql_lower:
        contains.append('fetch events')
    if 'fetch bizevents' in dql_lower:
        contains.append('fetch bizevents')
    if 'fetch dt.entity' in dql_lower:
        match = re.search(r'fetch (dt\.entity\.\w+)', dql_lower)
        if match:
            contains.append(f'fetch {match.group(1)}')
    if 'timeseries' in dql_lower:
        contains.append('timeseries')
    
    # Key aggregations
    if 'count()' in dql_lower:
        contains.append('count()')
    if 'sum(' in dql_lower:
        contains.append('sum(')
    if 'avg(' in dql_lower:
        contains.append('avg(')
    
    # Key operations
    if 'filter' in dql_lower:
        contains.append('filter')
    if 'summarize' in dql_lower:
        contains.append('summarize')
    if 'join' in dql_lower:
        contains.append('join')
    if 'by:' in dql_lower or 'by {' in dql_lower:
        contains.append('by')
    
    return contains[:5]  # Limit to 5 key patterns


def clean_dql(dql: str) -> str:
    """Clean up DQL for training."""
    # Remove excessive scan limits
    dql = re.sub(r',?\s*scanLimitGBytes:\s*-?\d+', '', dql)
    return dql.strip()


def main():
    input_file = Path('/Users/viet.pham/Documents/Dynatrace Data/Exelon/full-dashboards/golden_dataset.json')
    output_file = Path('/Users/viet.pham/Documents/Dynatrace Data/Exelon/leveled_golden_dataset.json')
    output_py = Path('/Users/viet.pham/Documents/Dynatrace Data/Exelon/leveled_examples.py')
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Organize by category and level
    leveled_data = defaultdict(lambda: {'simple': [], 'intermediate': [], 'complex': []})
    
    for category, queries in data.items():
        for q in queries:
            dql = q['dql'].strip()
            title = q.get('title', '')
            
            # Skip invalid examples
            if not is_valid_example(dql, title):
                continue
            
            # Calculate complexity
            level, score = calculate_complexity(dql)
            
            # Generate NL description
            nl = generate_nl_description(title, dql, level)
            if not nl:
                continue
            
            # Build example
            example = {
                'nl': nl,
                'intent': extract_intent(dql, category),
                'expected_contains': extract_expected_contains(dql),
                'dql': clean_dql(dql),
                'complexity_score': score,
                'dashboard': q.get('dashboard', ''),
                'original_title': title
            }
            
            leveled_data[category][level].append(example)
    
    # Select best examples for each level (limit to prevent redundancy)
    final_dataset = {}
    
    for category in sorted(leveled_data.keys()):
        final_dataset[category] = {}
        
        for level in ['simple', 'intermediate', 'complex']:
            examples = leveled_data[category][level]
            
            # Deduplicate by NL
            seen_nl = set()
            unique_examples = []
            for ex in examples:
                nl_key = ex['nl'].lower()[:30]  # First 30 chars as key
                if nl_key not in seen_nl:
                    seen_nl.add(nl_key)
                    unique_examples.append(ex)
            
            # Score examples for quality
            def quality_score(ex):
                score = 0
                # Prefer shorter NL descriptions (more concise)
                if len(ex['nl']) < 40:
                    score += 3
                elif len(ex['nl']) < 60:
                    score += 1
                
                # Prefer queries with appropriate length for level
                dql_len = len(ex['dql'])
                if level == 'simple' and dql_len < 200:
                    score += 3
                elif level == 'intermediate' and 150 < dql_len < 500:
                    score += 3
                elif level == 'complex' and 400 < dql_len < 1500:
                    score += 3
                
                # Penalize very long queries
                if dql_len > 1500:
                    score -= 2
                
                # Prefer descriptive titles
                if ex['nl'].count(' ') >= 2:  # At least 3 words
                    score += 2
                
                return score
            
            # Sort by quality then by complexity score
            unique_examples.sort(key=lambda x: (-quality_score(x), x['complexity_score']))
            
            # Select top examples
            limit = 5 if category in ['logs', 'spans', 'kubernetes', 'metrics', 'aws', 'azure'] else 3
            final_dataset[category][level] = unique_examples[:limit]
    
    # Save JSON
    with open(output_file, 'w') as f:
        json.dump(final_dataset, f, indent=2)
    
    # Generate Python file
    with open(output_py, 'w') as f:
        f.write('"""\nLeveled Golden DQL Examples\n')
        f.write('Extracted from production Dynatrace dashboards.\n')
        f.write('Organized by complexity: simple, intermediate, complex.\n"""\n\n')
        f.write('LEVELED_EXAMPLES = {\n')
        
        for category in sorted(final_dataset.keys()):
            f.write(f'\n    # {"="*70}\n')
            f.write(f'    # {category.upper()}\n')
            f.write(f'    # {"="*70}\n')
            f.write(f'    "{category}": {{\n')
            
            for level in ['simple', 'intermediate', 'complex']:
                examples = final_dataset[category][level]
                f.write(f'        "{level}": [\n')
                
                for ex in examples:
                    # Escape quotes in NL
                    nl_escaped = ex['nl'].replace('"', '\\"')
                    f.write('            {\n')
                    f.write(f'                "nl": "{nl_escaped}",\n')
                    f.write(f'                "intent": "{ex["intent"]}",\n')
                    f.write(f'                "expected_contains": {ex["expected_contains"]},\n')
                    f.write(f'                "dql": """{ex["dql"]}""",\n')
                    f.write('            },\n')
                
                f.write('        ],\n')
            
            f.write('    },\n')
        
        f.write('}\n\n')
        
        # Add flat examples list for compatibility
        f.write('# Flat list for backward compatibility\n')
        f.write('EXAMPLES = []\n')
        f.write('for category, levels in LEVELED_EXAMPLES.items():\n')
        f.write('    for level, examples in levels.items():\n')
        f.write('        for ex in examples:\n')
        f.write('            ex_copy = ex.copy()\n')
        f.write('            ex_copy["category"] = category\n')
        f.write('            ex_copy["level"] = level\n')
        f.write('            EXAMPLES.append(ex_copy)\n')
    
    # Print summary
    print("=" * 60)
    print("LEVELED GOLDEN DATASET SUMMARY")
    print("=" * 60)
    
    total = {'simple': 0, 'intermediate': 0, 'complex': 0}
    
    for category in sorted(final_dataset.keys()):
        print(f"\n{category.upper()}:")
        for level in ['simple', 'intermediate', 'complex']:
            count = len(final_dataset[category][level])
            total[level] += count
            print(f"  {level}: {count} examples")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {sum(total.values())} examples")
    print(f"  Simple: {total['simple']}")
    print(f"  Intermediate: {total['intermediate']}")
    print(f"  Complex: {total['complex']}")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - {output_file}")
    print(f"  - {output_py}")


if __name__ == '__main__':
    main()
