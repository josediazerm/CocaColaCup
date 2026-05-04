#!/usr/bin/env python3
"""Repack individual .rb files back into RPG Maker XP's Scripts.rxdata."""

import struct
import zlib
import os
import re

def write_marshal_int(val):
    """Write a Marshal-format integer."""
    if val == 0:
        return b'\x00'
    elif 1 <= val <= 122:
        return bytes([val + 5])
    elif -123 <= val <= -1:
        return bytes([val + 251])
    elif val > 122:
        result = b''
        if val <= 0xFF:
            result = b'\x01' + struct.pack('<B', val)
        elif val <= 0xFFFF:
            result = b'\x02' + struct.pack('<H', val)
        elif val <= 0xFFFFFF:
            result = b'\x03' + struct.pack('<I', val)[:3]
        else:
            result = b'\x04' + struct.pack('<I', val)
        return result
    else:
        # negative
        val = val & 0xFFFFFFFF
        if val >= 0xFFFFFF00:
            return b'\xff' + struct.pack('<B', val & 0xFF)
        elif val >= 0xFFFF0000:
            return b'\xfe' + struct.pack('<H', val & 0xFFFF)
        elif val >= 0xFF000000:
            return b'\xfd' + struct.pack('<I', val)[:3]
        else:
            return b'\xfc' + struct.pack('<I', val)

def write_marshal_string(s):
    """Write a raw Marshal string (just length + bytes, no tag)."""
    data = s if isinstance(s, bytes) else s.encode('utf-8')
    return write_marshal_int(len(data)) + data

def write_ivar_string(s):
    """Write a Marshal string with instance variables (encoding)."""
    data = s if isinstance(s, bytes) else s.encode('utf-8')
    result = b'I'
    result += b'"'
    result += write_marshal_string(data)
    # One instance variable: :E => true (UTF-8 encoding)
    result += write_marshal_int(1)
    result += b':'
    result += write_marshal_int(1)
    result += b'E'
    result += b'T'  # true
    return result

def build_scripts_rxdata(scripts):
    """Build a Scripts.rxdata file from a list of (id, name, code) tuples."""
    result = b'\x04\x08'  # Marshal header
    result += b'['
    result += write_marshal_int(len(scripts))

    encoding_symbol_written = False

    for script_id, name, code in scripts:
        result += b'['
        result += write_marshal_int(3)  # 3 elements per entry

        # Element 0: script ID (integer)
        result += b'i'
        result += write_marshal_int(script_id)

        # Element 1: script name (string with encoding)
        name_bytes = name.encode('utf-8')
        if not encoding_symbol_written:
            result += b'I"'
            result += write_marshal_string(name_bytes)
            result += write_marshal_int(1)  # 1 instance variable
            result += b':'
            result += write_marshal_int(1)
            result += b'E'
            result += b'T'  # true
            encoding_symbol_written = True
        else:
            result += b'I"'
            result += write_marshal_string(name_bytes)
            result += write_marshal_int(1)
            result += b';'  # symbol reference
            result += write_marshal_int(0)  # reference to first symbol :E
            result += b'T'

        # Element 2: compressed code (string, no encoding ivar needed)
        compressed = zlib.compress(code.encode('utf-8'))
        result += b'"'
        result += write_marshal_string(compressed)

    return result

def main():
    scripts_dir = "Scripts"
    output_path = os.path.join("Data", "Scripts.rxdata")
    backup_path = os.path.join("Data", "Scripts.rxdata.bak")

    if not os.path.isdir(scripts_dir):
        print(f"Error: {scripts_dir}/ directory not found")
        return

    # Read the original to extract script IDs
    # Parse script files
    script_files = sorted([f for f in os.listdir(scripts_dir) if f.endswith('.rb')])

    scripts = []
    for filename in script_files:
        filepath = os.path.join(scripts_dir, filename)
        # Extract index from filename
        match = re.match(r'^(\d+)_(.+)\.rb$', filename)
        if not match:
            continue

        idx = int(match.group(1))
        name = match.group(2)

        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        # Use a simple hash as script ID
        script_id = idx * 1000 + 100

        scripts.append((script_id, name, code))

    # Backup original
    if os.path.exists(output_path):
        import shutil
        shutil.copy2(output_path, backup_path)
        print(f"Backed up original to {backup_path}")

    # We need to preserve original script IDs. Let's re-read the original
    # to get the IDs.
    from extract_scripts import parse_scripts_simple
    original_scripts = parse_scripts_simple(output_path.replace('.bak', '') if not os.path.exists(backup_path) else backup_path)

    # Map original index -> script_id
    orig_ids = {i: sid for i, sid, name, code in original_scripts}

    # Rebuild with original IDs where possible
    final_scripts = []
    for i, (_, name, code) in enumerate(scripts):
        sid = orig_ids.get(i, i * 1000 + 100)
        final_scripts.append((sid, name, code))

    data = build_scripts_rxdata(final_scripts)

    with open(output_path, 'wb') as f:
        f.write(data)

    print(f"Wrote {len(final_scripts)} scripts to {output_path} ({len(data)} bytes)")

if __name__ == "__main__":
    main()
