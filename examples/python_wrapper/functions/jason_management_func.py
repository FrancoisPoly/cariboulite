def json_file_to_bitstring(json_path: str) -> str:
    """
    Function that reads a json file and transforms it into a bitstring
    """
    # Read the file as raw bytes
    with open(json_path, "rb") as f:
        data = f.read()

    # Convert each byte to 8-bit binary and concatenate
    bitstring = ''.join(f"{byte:08b}" for byte in data)
    return bitstring

def bitstring_to_json_file(bitstring: str, output_path: str) -> None:
    """
    Function that takes a bitsring and creates a json file
    """
    # Ensure bitstring length is a multiple of 8
    if len(bitstring) % 8 != 0:
        raise ValueError("Bitstring length must be divisible by 8")

    # Convert binary → bytes
    byte_list = [
        int(bitstring[i:i+8], 2)
        for i in range(0, len(bitstring), 8)
    ]

    data = bytes(byte_list)

    # Write the JSON file back
    with open(output_path, "wb") as f:
        f.write(data)

"""
Use example:
"""
# json_string = json_file_to_bitstring("./info_to_send/house_keeping_json_test_1.json")

# bitstring_to_json_file(json_string, "./reconstructed_house_keeping_json_test_1.json")
