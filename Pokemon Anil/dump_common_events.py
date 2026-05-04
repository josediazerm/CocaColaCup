#!/usr/bin/env python3
"""Dump common events from CommonEvents.rxdata to find Don Prodigio logic."""

import os
import struct
import zlib

def read_marshal_int(data, pos):
    b = data[pos]
    pos += 1
    if b == 0:
        return 0, pos
    elif 1 <= b <= 4:
        n = b
        val = 0
        for i in range(n):
            val |= data[pos] << (8 * i)
            pos += 1
        return val, pos
    elif 252 <= b <= 255:
        n = 256 - b
        val = 0
        for i in range(n):
            val |= data[pos] << (8 * i)
            pos += 1
        if val >= (1 << (8 * n - 1)):
            val -= (1 << (8 * n))
        return val, pos
    elif 6 <= b <= 127:
        return b - 5, pos
    elif 128 <= b <= 250:
        return b - 251, pos
    else:
        return b - 5, pos

def extract_strings_around(data, keyword, context=500):
    """Extract all readable text around occurrences of a keyword."""
    keyword_bytes = keyword.encode('utf-8')
    results = []
    pos = 0
    while True:
        pos = data.find(keyword_bytes, pos)
        if pos == -1:
            break
        start = max(0, pos - context)
        end = min(len(data), pos + len(keyword_bytes) + context)
        chunk = data[start:end]
        # Extract readable strings
        strings = []
        current = []
        for b in chunk:
            if 32 <= b < 127 or b in (10, 13):
                current.append(chr(b))
            else:
                if current and len(current) > 2:
                    strings.append(''.join(current))
                current = []
        if current and len(current) > 2:
            strings.append(''.join(current))
        results.append((pos, strings))
        pos += 1
    return results

def main():
    filepath = os.path.join('Data', 'CommonEvents.rxdata')
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")
    print()

    # Search for Don Prodigio context
    print("=== Searching for 'Don Prodigio' context ===")
    results = extract_strings_around(data, 'Don Prodigio', context=2000)
    for pos, strings in results:
        print(f"\nAt offset {pos}:")
        for s in strings:
            s = s.strip()
            if len(s) > 3:
                print(f"  {s}")

    print("\n\n=== Searching for 'tradeExpert' context ===")
    results = extract_strings_around(data, 'tradeExpert', context=3000)
    for pos, strings in results:
        print(f"\nAt offset {pos}:")
        for s in strings:
            s = s.strip()
            if len(s) > 3:
                print(f"  {s}")

if __name__ == '__main__':
    main()
