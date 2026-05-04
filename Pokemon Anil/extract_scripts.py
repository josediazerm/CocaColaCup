#!/usr/bin/env python3
"""Extract scripts from RPG Maker XP's Scripts.rxdata to individual .rb files."""

import struct
import zlib
import os
import re

def read_rxdata(path):
    """Read and parse Scripts.rxdata (Ruby Marshal format for array of [id, name, compressed_code])."""
    with open(path, 'rb') as f:
        data = f.read()

    scripts = []
    pos = 0

    # Ruby Marshal header: \x04\x08
    if data[0:2] != b'\x04\x08':
        raise ValueError("Not a valid Marshal file")
    pos = 2

    # Should be an array
    if data[pos] != ord('['):
        raise ValueError("Expected array at top level")
    pos += 1

    # Read array length (Marshal integer)
    array_len, pos = read_marshal_int(data, pos)

    for i in range(array_len):
        script_id, name, code = read_script_entry(data, pos)
        pos_after = find_next_entry(data, pos)
        scripts.append((i, script_id, name, code))
        pos = pos_after

    return scripts

def read_marshal_int(data, pos):
    """Read a Marshal-format integer."""
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
        val = -1
        for i in range(n):
            val &= ~(0xFF << (8 * i))
            val |= data[pos] << (8 * i)
            pos += 1
        return val - (1 << (8 * n)) if val >= (1 << (8 * n - 1)) else val, pos
    elif 6 <= b <= 127:
        return b - 5, pos
    elif 128 <= b <= 250:
        return b - 251, pos
    else:
        return b - 5, pos

def read_marshal_string(data, pos):
    """Read a Marshal string."""
    length, pos = read_marshal_int(data, pos)
    s = data[pos:pos+length]
    pos += length
    return s, pos

def find_next_entry(data, pos):
    """Skip over one complete Marshal object (a script entry array)."""
    # Each entry is an array [id, name, compressed_data]
    if data[pos] != ord('['):
        raise ValueError(f"Expected '[' at pos {pos}, got {data[pos]}")
    pos += 1
    entry_len, pos = read_marshal_int(data, pos)

    for _ in range(entry_len):
        pos = skip_marshal_object(data, pos)

    return pos

def skip_marshal_object(data, pos):
    """Skip one Marshal object and return position after it."""
    tag = data[pos]
    pos += 1

    if tag == ord('i'):  # Integer
        _, pos = read_marshal_int(data, pos)
    elif tag == ord('"'):  # String
        s, pos = read_marshal_string(data, pos)
        # Check for encoding suffix
        if pos < len(data) and data[pos] == ord(':'):
            pos += 1
            # symbol
            sym_len, pos = read_marshal_int(data, pos)
            pos += sym_len
            # encoding value
            pos = skip_marshal_object(data, pos)
    elif tag == ord('I'):  # Instance variables (usually wraps a string)
        pos = skip_marshal_object(data, pos)
        # Read instance variable count
        count, pos = read_marshal_int(data, pos)
        for _ in range(count):
            # symbol
            if data[pos] == ord(':'):
                pos += 1
                sym_len, pos = read_marshal_int(data, pos)
                pos += sym_len
            elif data[pos] == ord(';'):
                pos += 1
                _, pos = read_marshal_int(data, pos)
            pos = skip_marshal_object(data, pos)
    elif tag == ord('0'):  # nil
        pass
    elif tag == ord('T'):  # true
        pass
    elif tag == ord('F'):  # false
        pass
    elif tag == ord('['):  # Array
        arr_len, pos = read_marshal_int(data, pos)
        for _ in range(arr_len):
            pos = skip_marshal_object(data, pos)
    elif tag == ord(':'):  # Symbol
        sym_len, pos = read_marshal_int(data, pos)
        pos += sym_len
    elif tag == ord(';'):  # Symbol reference
        _, pos = read_marshal_int(data, pos)
    else:
        raise ValueError(f"Unknown Marshal tag '{chr(tag)}' (0x{tag:02x}) at pos {pos-1}")

    return pos

def parse_scripts_simple(path):
    """Simpler approach: use regex to find zlib-compressed blocks."""
    with open(path, 'rb') as f:
        data = f.read()

    # Parse using Marshal format properly
    scripts = []
    pos = 2  # Skip marshal header \x04\x08

    if data[pos] != ord('['):
        raise ValueError("Expected top-level array")
    pos += 1
    array_len, pos = read_marshal_int(data, pos)

    for i in range(array_len):
        # Each entry is an array of 3 elements
        if data[pos] != ord('['):
            raise ValueError(f"Expected array at pos {pos}")
        pos += 1
        entry_len, pos = read_marshal_int(data, pos)

        # Element 0: script ID (integer)
        if data[pos] == ord('i'):
            pos += 1
            script_id, pos = read_marshal_int(data, pos)
        else:
            script_id = i
            pos = skip_marshal_object_raw(data, pos)

        # Element 1: script name (string, usually with Instance variables wrapper)
        name, pos = read_string_element(data, pos)

        # Element 2: compressed script data (string)
        compressed, pos = read_string_element_raw(data, pos)

        # Decompress
        try:
            if compressed:
                code = zlib.decompress(compressed).decode('utf-8', errors='replace')
            else:
                code = ""
        except:
            code = ""

        scripts.append((i, script_id, name, code))

    return scripts

def skip_marshal_object_raw(data, pos):
    """Skip any marshal object."""
    return skip_marshal_object(data, pos)

def read_string_element(data, pos):
    """Read a string element that may be wrapped in I (instance variables)."""
    if data[pos] == ord('I'):
        pos += 1
        if data[pos] == ord('"'):
            pos += 1
            raw, pos = read_marshal_string(data, pos)
            name = raw.decode('utf-8', errors='replace')
        else:
            name = ""
            pos = skip_marshal_object(data, pos)
        # Read instance variables
        count, pos = read_marshal_int(data, pos)
        for _ in range(count):
            if data[pos] == ord(':'):
                pos += 1
                sym_len, pos = read_marshal_int(data, pos)
                pos += sym_len
            elif data[pos] == ord(';'):
                pos += 1
                _, pos = read_marshal_int(data, pos)
            pos = skip_marshal_object(data, pos)
        return name, pos
    elif data[pos] == ord('"'):
        pos += 1
        raw, pos = read_marshal_string(data, pos)
        return raw.decode('utf-8', errors='replace'), pos
    else:
        pos = skip_marshal_object(data, pos)
        return "", pos

def read_string_element_raw(data, pos):
    """Read raw bytes of a string element."""
    if data[pos] == ord('I'):
        pos += 1
        if data[pos] == ord('"'):
            pos += 1
            raw, pos = read_marshal_string(data, pos)
        else:
            raw = b""
            pos = skip_marshal_object(data, pos)
        count, pos = read_marshal_int(data, pos)
        for _ in range(count):
            if data[pos] == ord(':'):
                pos += 1
                sym_len, pos = read_marshal_int(data, pos)
                pos += sym_len
            elif data[pos] == ord(';'):
                pos += 1
                _, pos = read_marshal_int(data, pos)
            pos = skip_marshal_object(data, pos)
        return raw, pos
    elif data[pos] == ord('"'):
        pos += 1
        raw, pos = read_marshal_string(data, pos)
        return raw, pos
    else:
        pos = skip_marshal_object(data, pos)
        return b"", pos

def sanitize_filename(name):
    """Make a string safe for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name if name else "unnamed"

def main():
    scripts_path = os.path.join("Data", "Scripts.rxdata")
    output_dir = "Scripts"

    if not os.path.exists(scripts_path):
        print(f"Error: {scripts_path} not found")
        return

    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting scripts from {scripts_path}...")
    scripts = parse_scripts_simple(scripts_path)

    print(f"Found {len(scripts)} scripts")

    for idx, script_id, name, code in scripts:
        safe_name = sanitize_filename(name)
        if not safe_name or safe_name == "unnamed":
            safe_name = f"script_{idx}"

        filename = f"{idx:03d}_{safe_name}.rb"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"  [{idx:03d}] {name} -> {filename} ({len(code)} bytes)")

    print(f"\nDone! Extracted {len(scripts)} scripts to {output_dir}/")

if __name__ == "__main__":
    main()
