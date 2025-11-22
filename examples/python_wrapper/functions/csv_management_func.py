import csv

def create_csv(header: list, message: list[list], output_file: str) -> None:
    """Function to create a CSV"""
    data = []

    # Add the header
    data.append(header)

    # Add the data
    for message_ele in message:
        data.append(message_ele)

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)


def read_csv(filepath: str) -> list[dict]:
    """Reads a CSV file and returns a list of dictionaries."""
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


# Example of how to create CSV:
# Should be on both the cubesat and the base station
# header = ["Timestamp","Bus_Voltage_V","Bus_Current_A","Battery_Temp_C","OBDH_Temp_C","Panel_Temp_C","Mode","ADCS_Mode","ReactionWheel_Speed_rpm","Sun_Vector_X","Sun_Vector_Y","Sun_Vector_Z"]

# message = [["2025-11-02T12:00:00.000Z",27.1,0.45,12.4,18.7,25.3,"Nominal","Detumbling",1500,0.55,-0.32,0.77],
#            ["2025-11-02T12:00:10.000Z",27.0,0.46,12.3,18.8,25.4,"Nominal","Detumbling",1490,0.56,-0.31,0.77],
#            ["2025-11-02T12:00:20.000Z",27.2,0.45,12.2,18.7,25.3,"Nominal","SunPointing",1550,0.57,-0.30,0.78]]

# create_csv(header, message, "house_keeping_csv_test_1.csv")


# Example of to read CSV
# data = read_csv("house_keeping_csv_test_1.csv")
# for row in data:
#     print(row)


def csv_to_bitstream(path: str) -> tuple[str, int]:
    """Convert a CSV into a bitstream (string of 0/1)."""
    # CSV read
    rows = read_csv(path)

    encoded_rows = []
    for row in rows:
        encoded_fields = []
        for key, value in row.items():
            # Normalize types to string
            if value.lower() in ("true", "false"):
                val_str = '1' if value.lower() == 'true' else '0'
            else:
                val_str = value
            encoded_fields.append(val_str)
        encoded_rows.append('|'.join(encoded_fields))
    full_str = ';'.join(encoded_rows)
    
    # Convert to bits
    bitstream = ''.join(f"{byte:08b}" for byte in full_str.encode('utf-8'))
    return bitstream, len(full_str)


def bitstream_to_csv(bitstream: str) -> list[dict]:
    """Decode a UTF-8 bitstream back to CSV-style list of dicts."""
    # Convert bits back to bytes
    byte_array = bytes(int(bitstream[i:i+8], 2) for i in range(0, len(bitstream), 8))
    text = byte_array.decode('utf-8')

    # Split rows and fields
    rows = text.split(';')
    decoded = []
    for row in rows:
        fields = row.split('|')
        decoded.append(fields)
    return decoded

####################################################

# Encode to bitstream
# bitstream, _ = csv_to_bitstream("house_keeping_csv_test_1.csv")
# print("Bitstream (first 80 bits):", bitstream[:80])
# print(f"Total Bistream lenght = {len(bitstream)} bits")

# # Decode back
# decoded = bitstream_to_csv(bitstream)
# print("\nDecoding structure ...")

# create_csv(header, decoded, "./reconstructed/reconstructed_house_keeping_csv_test_1.csv")

####################################################