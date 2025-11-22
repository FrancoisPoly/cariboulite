def file_to_bitstring(path: str) -> str:
    """Read any file and return its content as a bit string ('0'/'1')."""
    with open(path, "rb") as f:
        data = f.read()
    bitstring = ''.join(f"{byte:08b}" for byte in data)
    return bitstring


def bitstring_to_file(bitstring: str, output_path: str) -> None:
    """Recreate a file from a bit string ('0'/'1')."""
    # Split into chunks of 8 bits (1 byte)
    bytes_list = [int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8)]
    data = bytes(bytes_list)
    with open(output_path, "wb") as f:
        f.write(data)

# Convert a file to bitstring
# bits = file_to_bitstring("text_report_1.txt")
# print("First 64 bits:", bits[:64])
# print(f"Total length of bitstring: {len(bits)} bits")

# # Recreate it
# bitstring_to_file(bits, "./reconstructed/reconstructed_text_report_1.txt")