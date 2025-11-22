import struct
from PIL import Image
import numpy as np

from .csv_management_func import *
from .txt_management_func import *
from .binfile_management_func import *
from .jason_management_func import *


##### Ints #####
def int_to_binary(n: int) -> str:
    """Convert an integer to its binary string (without 0b prefix)."""
    # Method: using format()
    binary_data = format(n, 'b')  # same result, but more flexible for padding

    return binary_data


def binary_str_to_int(bstr: str) -> int:
    """Convert a binary string like '1101' into an integer."""
    return int(bstr, 2)



##### Floats #####
def float64_to_bin(f: float) -> str:
    """Convert a Python float into a binary string (IEEE 754, 64-bit)."""
    # Pack float into 8 bytes (double precision)
    packed = struct.pack('!d', f)  # ! = network (big-endian), d = double
    # Convert bytes to bits
    bits = ''.join(f'{byte:08b}' for byte in packed)
    return bits

def float32_to_bin(f: float) -> str:
    """Convert a Python float into a 32-bit binary string."""
    packed = struct.pack('!f', f)  # ! = big-endian, f = 32-bit float
    return ''.join(f'{byte:08b}' for byte in packed)

def bin_to_float32or64(bstr: str) -> float:
    """Convert a 32-bit or 64-bit binary string (IEEE 754) back into a Python float."""
    if len(bstr) != 64 and len(bstr) != 32:
        raise ValueError("Binary string must be exactly 32 or 64 bits for float 32/64 conversion.")
    
    if len(bstr) == 32: #TODO Voir pourquoi ça crée un peu d'imprécision
        as_bytes = int(bstr, 2).to_bytes(4, byteorder='big')
        return struct.unpack('!f', as_bytes)[0]
    else: # Float 64
         # Convert bitstring to bytes
        as_bytes = int(bstr, 2).to_bytes(8, byteorder='big')
        # Unpack bytes into float
        return struct.unpack('!d', as_bytes)[0]



##### Strings #####
def str_to_bin(s: str) -> str:
    """Convert a text string into a binary string (8 bits per char)."""
    return ''.join(format(ord(c), '08b') for c in s)

def bin_to_str(bstr: str) -> str:
    """Convert a binary string (multiple of 8 bits) back into text."""
    if len(bstr) % 8 != 0:
        raise ValueError("Binary string length must be a multiple of 8.")
    chars = [chr(int(bstr[i:i+8], 2)) for i in range(0, len(bstr), 8)]
    return ''.join(chars)



##### Images #####
def image_to_bitstring(path: str, mode: str = 'RGB') -> tuple[str, int, int, str]:
    """
    Convert an image file into a binary string.
    mode: 'RGB' for color (3×8 bits/pixel) or 'L' for grayscale (8 bits/pixel)
    """
    img = Image.open(path).convert(mode)
    pixels = list(img.getdata())
    width, height = img.size

    # Flatten depending on mode
    if mode == 'RGB':
        flat = [v for pixel in pixels for v in pixel]
    elif mode == 'L':  # grayscale = single int per pixel
        flat = pixels
    else:
        raise ValueError("Unsupported mode: use 'RGB' or 'L'")

    bitstring = ''.join(format(v, '08b') for v in flat)

    return bitstring, width, height, mode

def bitstring_to_image(bitstring: str, width: int, height: int, mode: str = 'RGB') -> Image.Image:
    """
    Reconstruct an image (RGB or grayscale) from a binary string.
    """
    if len(bitstring) % 8 != 0:
        raise ValueError("Bitstring length must be multiple of 8.")
    bytes_list = [int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8)]

    if mode == 'RGB':
        pixels = [tuple(bytes_list[i:i+3]) for i in range(0, len(bytes_list), 3)]
    elif mode == 'L':
        pixels = bytes_list
    else:
        raise ValueError("Unsupported mode: use 'RGB' or 'L'")

    img = Image.new(mode, (width, height))
    img.putdata(pixels)
    return img


##### Bool #####
def bool_to_bitstring(value: bool) -> str:
    """Convert a single boolean to a 1-bit string ('1' or '0')."""
    return '1' if value else '0'

def bitstring_to_bool(bitstring: str) -> bool:
    """Convert a 1-bit string ('1' or '0') to a single boolean."""
    return True if bitstring == "1" else False


##### Entire bitstream #####
def encode_chunk(type_id: int, payload_bits: str) -> str:
    """Prefix type and length to a binary payload."""
    type_bits = format(type_id, '08b')
    length_bits = format(len(payload_bits), '032b')
    return type_bits + length_bits + payload_bits

def decode_bitstream(bitstream: str) -> list:
    """Iteratively parse type, length, and payload sections."""
    i = 0
    results = []
    while i < len(bitstream):
        type_id = int(bitstream[i:i+8], 2)
        length = int(bitstream[i+8:i+40], 2)
        payload = bitstream[i+40:i+40+length]
        results.append((type_id, payload))
        i += 40 + length


    # Decoding of the bitstream
    result_list = []
    for type_id, payload in results:
        if type_id == 0: # Int
            value = binary_str_to_int(payload)
            result_list.append(value)
        elif type_id == 1: # Float
            value = bin_to_float32or64(payload)
            result_list.append(value)
        elif type_id == 2: # String
            value = bin_to_str(payload)
            result_list.append(value)
        elif type_id == 3: # Image
            # Let's assume the receiver knows the width, height and color mode of received image (always the same)
            w = 568
            h = 425
            mode = "L"
            img = bitstring_to_image(payload, w, h, mode=mode)
            
            print("Receiving image ...")
            img.save("./reconstructed_data/reconstructed_image.png")
        elif type_id == 4: # Boolean
            value = bitstring_to_bool(payload)
            result_list.append(value)
        elif type_id == 5: # Telemetry raw binary data
            print("Receiving bin data from telemetry ...")
            value = payload
            bitstring_to_binfile(value, "./reconstructed_data/reconstructed_telemetry_log.bin")
        elif type_id == 6: # CSV
            value = bitstream_to_csv(payload)

            # Creating a new CSV file
            print("Receiving a CSV file ...")
            # Let's assume the receiver knows the header of the CSV file (always the same)
            header = ["Timestamp",
                      "Bus_Voltage_V",
                      "Bus_Current_A",
                      "Battery_Temp_C",
                      "OBDH_Temp_C",
                      "Panel_Temp_C",
                      "Mode",
                      "ADCS_Mode",
                      "ReactionWheel_Speed_rpm",
                      "Sun_Vector_X",
                      "Sun_Vector_Y",
                      "Sun_Vector_Z"]

            create_csv(header, value, "./reconstructed_data/reconstructed_house_keeping_csv_test_1.csv")

        elif type_id == 7: # .txt
            print("Receiving a txt report ...")
            bitstring_to_file(payload, "./reconstructed_data/reconstructed_text_report_1.txt")

        elif type_id == 8: # .json
            print("Receiving a JSON file ...")
            bitstring_to_json_file(payload, "./reconstructed_data/reconstructed_house_keeping_json_test_1.json")

    return result_list

def bitstring_to_array(bitstring: str) -> np.ndarray:
    """Convert a string of bits like '110010' to a NumPy array of 0s and 1s."""
    return np.fromiter((int(b) for b in bitstring), dtype=np.uint8)

def array_to_bitstring(array: np.ndarray) -> str:
    """Convert a NumPy array of 0s and 1s to a bitstring like '110010'."""
    return ''.join(map(str, array.astype(np.uint8)))