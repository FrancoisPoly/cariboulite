from functions.class_info import payload_type
from functions.telemetry_log_func import generate_random_tele_log_bitstring
from functions.types_to_bin_func import *
from functions.cariboulite_radio import transmit

# No need to import because it is not in use:
#import qam_fast

"""
Following the CCSDS FILE DELIVERY PROTOCOL (CFDP),
Let's try to create a bitstream containing:

- version
- direction
- transmission_mode
- CRC_flag
- transfer_ID
- spacecraft_ID
- groundstation_ID
- file_data

file_data is a sub-bitstream containing:

- A telemetry log (.bin)
- An image (.jpg)
- CSV of housekeeping data (.csv)
- A text report (.txt)
"""

# Create the initial payload object
payload = payload_type(1,
                       0,
                       1,
                       False,
                       49,
                       8,
                       3)

# Add the telemetry log to the payload (random 2500 bit-long message)
payload.telemetry_log = generate_random_tele_log_bitstring()

# Add path to image
# payload.image_path = "./info_to_send/image.png"

# Add path to CSV
payload.csv_path = "./info_to_send/house_keeping_csv_test_1.csv"

# Add path to text report
payload.text_report_path = "./info_to_send/text_report_1.txt"

# Add path to JSON
# payload.json_path = "./info_to_send/house_keeping_json_test_1.json"


"""
Let's create the bitstream that the RF module will send
"""
bitstream = payload.bistream()

print(f"The payload has a length of {len(bitstream)} bits")

# Save the bitstream in a .txt file
with open("./info_to_send/bitstream.txt", "w") as f:
    f.write(bitstream)

"""
The .txt is then shared to the C api to send the bin data with the cariboulite 
"""
print("\n----------------")
print("  Transmission")
print("----------------\n")

transmit(
    sample_rate = 4e6,
    tx_freq = 868e6,
    tx_bw = 1e6,
    tx_power = 0,
    filepath = "./info_to_send/bitstream.txt"
)

print("Done!\n")

############################################################################################################
### Note: Since the TX of the cariboulite is incomplete, this is not used (but it's functionnal)
# """
# Let's modulate the bitstream via QAM
# """
# rf_baseband = qam_fast.qam_mod_baseband(bitstring_to_array(bitstream), qam_order=16, samples_per_symbol=8)
# rf_baseband.tofile("rf_baseband2.bin")

