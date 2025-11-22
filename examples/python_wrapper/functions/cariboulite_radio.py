import ctypes
from pathlib import Path

# Make sure you build the C tool with this command:
# gcc -shared -fPIC -o libcariboulite_radio.so main.c -lcariboulite -lm

# Load the shared library
_lib = ctypes.CDLL(str(Path(__file__).with_name("libcariboulite_radio.so")))

# Define function signature
_lib.transmit.argtypes = [
    ctypes.c_double,  # sample_rate
    ctypes.c_double,  # tx_freq
    ctypes.c_double,  # tx_bw
    ctypes.c_int,     # tx_power
    ctypes.c_char_p,  # filepath
    ctypes.c_char_p   # Channel
]
_lib.transmit.restype = ctypes.c_int

def transmit(sample_rate, tx_freq, tx_bw, tx_power, filepath, channel="s1g"):
    """
    Transmit a bitstream using OOK modulation on CaribouLite.

    Args:
        sample_rate (float): Sample rate in Hz
        tx_freq (float): TX frequency in Hz
        tx_bw (float): Bandwidth in Hz
        tx_power (int): Power in dBm
        filepath (str): Path to bitstream text file
	channel (str): channel choice ("s1g" or "hif")
    """

    if channel != "s1g" and channel != "hif":
        raise NameError(f'"{channel}" is not correct\nThe channel choices are either "s1b" or "hif"')

    if sample_rate > 4e6:
        raise ValueError("The maximum samplerate allowed by the cariboulite is 4MHz (4 000 000 Hz)")

    if tx_freq >= 1e9 and channel == "s1g":
        raise ValueError("For TX frequencies > 1GHz (1 000 000 000 Hz), consider using the other channel: 'hif'")

    if tx_freq < 1e9 and channel == "hif":
        raise ValueError("For TX frequencies < 1GHz (1 000 000 000 Hz), consider using the other channel: 's1g'")

    if tx_bw > 2.5e6:
        raise ValueError("The maximum bandwidth allowed by the cariboulite is 2.5MHz (2 500 000 Hz)")

    if tx_power > 14:
        raise ValueError("The maximum TX power allowed by the cariboulite is 14 dB")

    result = _lib.transmit(
        ctypes.c_double(sample_rate),
        ctypes.c_double(tx_freq),
        ctypes.c_double(tx_bw),
        ctypes.c_int(tx_power),
        filepath.encode('utf-8'),
	channel.encode('utf-8')
    )
    if result != 0:
        raise RuntimeError(f"Transmission failed with code {result}")
