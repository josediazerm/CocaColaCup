#!/usr/bin/env python3
"""Extract detailed event commands from map and common events for tradeExpert."""

import os

def extract_all_strings_sequential(data):
    """Extract all readable strings from binary data in order."""
    strings = []
    current = []
    for b in data:
        if 32 <= b < 127 or b in (10, 13):
            current.append(chr(b))
        else:
            if current and len(current) > 1:
                s = ''.join(current).strip()
                if s:
                    strings.append(s)
            current = []
    if current and len(current) > 1:
        s = ''.join(current).strip()
        if s:
            strings.append(s)
    return strings

def find_event_around_keyword(data, keyword, context_before=5000, context_after=10000):
    """Find all occurrences of keyword and extract surrounding strings."""
    keyword_bytes = keyword.encode('utf-8')
    results = []
    pos = 0
    while True:
        pos = data.find(keyword_bytes, pos)
        if pos == -1:
            break
        start = max(0, pos - context_before)
        end = min(len(data), pos + context_after)
        chunk = data[start:end]
        strings = extract_all_strings_sequential(chunk)
        results.append((pos, strings))
        pos += 1
    return results

def main():
    # Map059 - has tradeExpert and "prodigio" name
    print("=" * 80)
    print("MAP 059 - Don Prodigio event")
    print("=" * 80)

    with open(os.path.join('Data', 'Map059.rxdata'), 'rb') as f:
        data = f.read()

    results = find_event_around_keyword(data, 'tradeExpert', 3000, 5000)
    for pos, strings in results:
        print(f"\n--- At offset {pos} ---")
        for s in strings:
            print(f"  {s}")

    # Also look for "prodigio" in Map059 for more context
    print("\n\n" + "=" * 80)
    print("MAP 059 - 'prodigio' context")
    print("=" * 80)
    results = find_event_around_keyword(data, 'prodigio', 1000, 8000)
    for pos, strings in results:
        print(f"\n--- At offset {pos} ---")
        for i, s in enumerate(strings):
            print(f"  [{i}] {s}")

    # Map214
    print("\n\n" + "=" * 80)
    print("MAP 214 - Don Prodigio with Moneda Prodigiosa")
    print("=" * 80)

    with open(os.path.join('Data', 'Map214.rxdata'), 'rb') as f:
        data = f.read()

    results = find_event_around_keyword(data, 'tradeExpert', 3000, 5000)
    for pos, strings in results:
        print(f"\n--- At offset {pos} ---")
        for i, s in enumerate(strings):
            print(f"  [{i}] {s}")

    # CommonEvents
    print("\n\n" + "=" * 80)
    print("COMMON EVENTS - Don Prodigio")
    print("=" * 80)

    with open(os.path.join('Data', 'CommonEvents.rxdata'), 'rb') as f:
        data = f.read()

    results = find_event_around_keyword(data, 'Don Prodigio', 500, 2000)
    for pos, strings in results:
        print(f"\n--- At offset {pos} ---")
        for i, s in enumerate(strings):
            print(f"  [{i}] {s}")

if __name__ == '__main__':
    main()
