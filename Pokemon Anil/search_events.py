#!/usr/bin/env python3
"""Search map events and common events for trade-related script calls."""

import os
import struct
import sys

# We need to parse rxdata files which use Ruby Marshal format
# Let's use a simplified approach - search for text patterns in the binary data

def search_binary_for_patterns(filepath, patterns):
    """Search a binary file for text patterns."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except:
        return []

    results = []
    data_lower = data.lower()
    for pattern in patterns:
        pattern_bytes = pattern.lower().encode('utf-8')
        pos = 0
        while True:
            pos = data_lower.find(pattern_bytes, pos)
            if pos == -1:
                break
            # Get surrounding context
            start = max(0, pos - 100)
            end = min(len(data), pos + len(pattern_bytes) + 100)
            context = data[start:end]
            # Filter to printable chars
            context_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)
            results.append((pattern, pos, context_text))
            pos += 1
    return results

def main():
    patterns = [
        'prodigio', 'Wonder', 'wondertrade', 'wonder_trade',
        'pbStartTrade', 'pbChoosePokemonForTrade', 'pbStartTradePC',
        'pbChoosePokemonForTradePC', 'intercambio', 'Intercambio',
        'Don ', 'trade'
    ]

    # Search common events
    ce_path = os.path.join('Data', 'CommonEvents.rxdata')
    if os.path.exists(ce_path):
        results = search_binary_for_patterns(ce_path, patterns)
        if results:
            print(f"\n=== {ce_path} ===")
            for pattern, pos, context in results:
                print(f"  [{pattern}] at offset {pos}: ...{context}...")

    # Search all map files
    data_dir = 'Data'
    for fname in sorted(os.listdir(data_dir)):
        if fname.startswith('Map') and fname.endswith('.rxdata') and fname != 'MapInfos.rxdata':
            fpath = os.path.join(data_dir, fname)
            results = search_binary_for_patterns(fpath, patterns)
            if results:
                # Filter to only interesting results (not just 'trade' in random data)
                interesting = [r for r in results if r[0].lower() not in ('trade', 'don ') or
                             'trade' in r[2].lower() and ('start' in r[2].lower() or 'choose' in r[2].lower() or 'prodigio' in r[2].lower())]
                if not interesting:
                    interesting = [r for r in results if r[0].lower() != 'don ']
                if interesting:
                    print(f"\n=== {fname} ===")
                    for pattern, pos, context in interesting[:10]:
                        print(f"  [{pattern}] at offset {pos}: ...{context}...")

if __name__ == '__main__':
    main()
