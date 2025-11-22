from functions.cariboulite_radio import transmit

"""
Example of how to use the transmit function
"""

transmit(
    sample_rate = 4e6,
    tx_freq = 900e6,
    tx_bw = 1e6,
    tx_power = 0,
    filepath = "/home/sm1/bitstream.txt"
)
