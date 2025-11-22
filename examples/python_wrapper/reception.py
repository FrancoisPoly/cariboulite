from functions.class_info import payload_type
from functions.types_to_bin_func import *
from functions.ook_decoding_func import *
import inspect

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

"""
At this point, the message has already been sent and received via RF signals
"""

"""
Reception of the bitstream by an RF receiver
"""

print("-----------------")
print("    Reception")
print("-----------------\n")

print("Processing data ...\n")

# If the message is modulated with QAM, the following commands can be used to demodulate it
# received_bitstream = QAM_demod(rf_signal, fc)
# received_bitstream = QAM_demod_baseband(rf_baseband)
# received_bitstream = array_to_bitstring(qam_fast.qam_demod_baseband(rf_baseband, qam_order=16, samples_per_symbol=8))

reception_source = 2 # 1 for a bistream straigth out of a .txt file
                     # 2 for information in a .wav file (recorded by an SDR)

if reception_source == 1:
    with open("./info_to_send/bitstream.txt", "r", encoding="utf-8") as f:
        received_bitstream =  f.read()

else:
    # Decoding the RLE_bin_data from the RF transmision
    RLE_bin_data = ook_decoding("./reconstructed_data/recording.wav")

    # Loading the original RLE binaray data
    original = bitstring_file_to_runs("./info_to_send/bitstream.txt")

    # Computing the symbol error rate (%) of the RF transmission
    # avg = symmetric_ratio_average(original, RLE_bin_data[:-1])
    # print(f"SER: {(1-avg)*100} %")

    received_bitstream = runs_to_bitstring(RLE_bin_data)[213:-30] # without the CP head and tail #TODO remove the tail !!!

    print(received_bitstream)


"""
Decoding the received bitstream
"""
result_list = decode_bitstream(received_bitstream)

# Extract parameter names ---
params = inspect.signature(payload_type.__init__).parameters
param_names = [p for p in params if p != "self"]

# Print the results to make sure the transmission works
print("\n")
for i in range(len(result_list)):
    print(f"{param_names[i]}: {result_list[i]}")

