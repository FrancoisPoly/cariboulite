from .types_to_bin_func import *
from .csv_management_func import *
from .txt_management_func import *
from .jason_management_func import *

class payload_type:
    """
    Class used to create the payload to send via the Cariboulite SDR
    """
    def __init__(self,
                 version: int,                 # CFDP version (always 1 for current spec)
                 direction: int,               # 0 for spacecraft to ground, 1 for inverse
                 transmission_mode: int,       # Acknowledged (1) or Unacknowledged (0)
                 CRC_flag: bool,               # False if CRC is not included
                 transfer_ID: int,             # ID of the transfer
                 spacecraft_ID: int,           # ID of the spacecraft
                 groundstation_ID: int,        # ID of the ground station
                 telemetry_log: str = None,    # Bit string of telemetry log info.
                 image_path: str = None,       # File path to an image
                 csv_path: str = None,         # File path to a housekeeping csv
                 text_report_path: str = None, # File path to a text report
                 json_path: str = None):       # File path to a housekeeping json
                 
        # Initialisation of the parameters
        self.version = version
        self.direction = direction
        self.transmission_mode = transmission_mode
        self.CRC_flag = CRC_flag
        self.transfer_ID = transfer_ID
        self.spacecraft_ID = spacecraft_ID
        self.groundstation_ID = groundstation_ID
        self.telemetry_log = telemetry_log
        self.image_path = image_path
        self.csv_path = csv_path
        self.text_report_path = text_report_path
        self.json_path = json_path

    def bistream(self, cp: bool = True) -> str:
        """Ecoding of the bitstream"""
        bitstream_str = ""

        if cp:
            # Add the cycling prefix's head
            # RLE -> (1 1 1 1 1 2 1 3 1 4 1 5 2 10 2 20 2 50 2 100 2)
            bitstream_str += "10101001000100001000001100000000001100000000000000000000110000000000000000000000000000000000000000000000000011000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011"

        bitstream_str += encode_chunk(0, int_to_binary(self.version))
        bitstream_str += encode_chunk(0, int_to_binary(self.direction))
        bitstream_str += encode_chunk(0, int_to_binary(self.transmission_mode))
        bitstream_str += encode_chunk(4, bool_to_bitstring(self.CRC_flag))
        bitstream_str += encode_chunk(0, int_to_binary(self.transfer_ID))
        bitstream_str += encode_chunk(0, int_to_binary(self.spacecraft_ID))
        bitstream_str += encode_chunk(0, int_to_binary(self.groundstation_ID))

        # Telemetry log bitstring
        if self.telemetry_log != None:
            bitstream_str += encode_chunk(5, self.telemetry_log)

        # Image bitstring
        if self.image_path != None:
            bits, _, _, _ = image_to_bitstring(self.image_path, mode='L')
            bitstream_str += encode_chunk(3, bits) # image bits

        # CSV's data bitstring
        if self.csv_path != None:
            bitstream_str += encode_chunk(6, csv_to_bitstream(self.csv_path)[0])

        # Text report's bitstring
        if self.text_report_path != None:
            bitstream_str += encode_chunk(7, file_to_bitstring(self.text_report_path))

        if self.json_path != None:
            bitstream_str += encode_chunk(8, json_file_to_bitstring(self.json_path))


        if cp:
            # Add the cycling prefix's tail
            # RLE -> (30)
            bitstream_str += "111111111111111111111111111111"

        return bitstream_str

