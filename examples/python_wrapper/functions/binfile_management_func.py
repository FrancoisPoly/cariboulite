def bitstring_to_binfile(bitstring: str, filepath: str) -> None:
    """Write a bitstring (e.g. '11001010') to a binary .bin file."""
    # Pad to full bytes (8 bits per byte)
    padding = (8 - len(bitstring) % 8) % 8
    bitstring_padded = bitstring + '0' * padding

    # Convert to bytes
    byte_array = int(bitstring_padded, 2).to_bytes(len(bitstring_padded) // 8, byteorder='big')

    # Write binary file
    with open(filepath, 'wb') as f:
        f.write(byte_array)

def binfile_to_bitstring(filepath: str) -> str:
    """Read a binary .bin file and return its bitstring representation."""
    with open(filepath, 'rb') as f:
        data = f.read()
    return ''.join(f'{byte:08b}' for byte in data)