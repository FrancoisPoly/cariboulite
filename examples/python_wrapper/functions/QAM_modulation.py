from scipy.signal import firwin, lfilter
import numpy as np
import matplotlib.pyplot as plt
from numba import njit

from .types_to_bin_func import *


# TEST

@njit
def fast_bits_to_symbols(bits, bits_per_symbol):
    n = len(bits)
    symbols = np.empty(n // bits_per_symbol, np.int32)
    for i in range(0, n, bits_per_symbol):
        acc = 0
        for j in range(bits_per_symbol):
            acc = (acc << 1) | bits[i+j]
        symbols[i // bits_per_symbol] = acc
    return symbols

def bits_to_symbols(bits, M):
    """Map bits to QAM symbols"""
    bits_per_symbol = int(np.log2(M))
    symbols = []
    for i in range(0, len(bits), bits_per_symbol):
        b = bits[i:i+bits_per_symbol]
        k = int("".join(map(str, b)), 2)
        symbols.append(k)
    return np.array(symbols)

def QAM_mod(bitstream: str,
            fc: float,
            fs: float = 2e6,
            qam_order: int = 16,
            samples_per_symbol: int = 20
            ) -> np.ndarray:
    """Modulate a bitstream with a QAM of any order"""

    print("QAM modulation ...")
    # --- Parameters ---
    M = qam_order  # QAM order (16-QAM)
    bits_per_symbol = int(np.log2(M))
    # fc = carrier/center frequency (Hz)
    # fs = sampling rate (Hz)
    Ts = 1 / fs

    # --- Gather bits to transmit ---
    bits = bitstring_to_array(bitstream)

    symbols = bits_to_symbols(bits, M)

    # --- Create constellation (Gray-coded) ---
    # Map 0–15 to I/Q levels (-3,-1,+1,+3)
    I = 2 * ((symbols % 4) - 1.5)
    Q = 2 * ((symbols // 4) - 1.5)
    qam_symbols = I + 1j * Q

    # --- Normalize average power to 1 ---
    qam_symbols /= np.sqrt((np.mean(np.abs(qam_symbols)**2)))

    # --- Create baseband signal (each symbol lasts N samples) ---
    baseband = np.repeat(qam_symbols, samples_per_symbol)

    # --- Modulate to carrier ---
    t = np.arange(len(baseband)) * Ts
    I_wave = np.real(baseband) * np.cos(2*np.pi*fc*t)
    Q_wave = np.imag(baseband) * np.sin(2*np.pi*fc*t)
    rf_signal = I_wave - Q_wave

    # # --- Plot results ---
    # plt.figure()
    # plt.plot(t[:2000]*1e3, rf_signal[:2000])
    # plt.title(f"{M}-QAM Modulated RF Signal (first 2000 samples)")
    # plt.xlabel("Time (ms)")
    # plt.ylabel("Amplitude")
    # plt.grid(True)
    # plt.savefig("test_QAM")

    # # --- Constellation plot ---
    # plt.figure()
    # plt.scatter(np.real(qam_symbols), np.imag(qam_symbols))
    # plt.title("16-QAM Constellation")
    # plt.xlabel("In-phase")
    # plt.ylabel("Quadrature")
    # plt.grid(True)
    # plt.axis('equal')
    # plt.savefig("test_QAM")

    return rf_signal


def QAM_demod(rf_signal: np.ndarray, fc: float, fs: float = 2e6, qam_order: int = 16, samples_per_symbol: int = 20):
    """Demodulate a QAM RF signal back into a bitstream string."""

    print("QAM demodulation ...")
    M = qam_order
    bits_per_symbol = int(np.log2(M))
    Ts = 1 / fs
    t = np.arange(len(rf_signal)) * Ts

    # --- Downconvert to baseband ---
    I_down = rf_signal * np.cos(2 * np.pi * fc * t)
    Q_down = -rf_signal * np.sin(2 * np.pi * fc * t)
    baseband = I_down + 1j * Q_down

    # --- Lowpass filter (simple averaging) ---
    # crude method; replace with proper filter for real SDR use
    taps = firwin(101, cutoff=1/samples_per_symbol, fs=fs)
    baseband_filtered = lfilter(taps, 1.0, baseband)

    # --- Symbol synchronization (assume perfect timing) ---
    symbols_rx = baseband_filtered[::samples_per_symbol]

    # --- Normalize power ---
    symbols_rx /= np.sqrt(np.mean(np.abs(symbols_rx)**2))

    # --- Define ideal constellation points ---
    I = 2 * ((np.arange(M) % 4) - 1.5)
    Q = 2 * ((np.arange(M) // 4) - 1.5)
    constellation = (I + 1j * Q) / np.sqrt(np.mean(np.abs(I + 1j * Q)**2))

    # --- Nearest neighbor decoding ---
    symbols_decoded = []
    for s in symbols_rx:
        distances = np.abs(s - constellation)
        k_hat = np.argmin(distances)
        symbols_decoded.append(k_hat)
    symbols_decoded = np.array(symbols_decoded)

    # --- Convert symbols back to bits ---
    bitstream = "".join(format(k, f'0{bits_per_symbol}b') for k in symbols_decoded)

    return bitstream

#####################################################################################
# Simplified version?

def QAM_mod_baseband(bitstream: str, qam_order: int = 16, samples_per_symbol: int = 8):
    """Modulate a bitstream with a QAM of any order"""

    print("QAM modulation ...")
    M = qam_order
    bits = np.fromiter((int(b) for b in bitstream), dtype=np.uint8)
    bits_per_symbol = int(np.log2(M))
    
    # Pad to full symbols
    if len(bits) % bits_per_symbol != 0:
        bits = np.pad(bits, (0, bits_per_symbol - len(bits) % bits_per_symbol))
    
    symbols = []
    for i in range(0, len(bits), bits_per_symbol):
        b = bits[i:i+bits_per_symbol]
        symbols.append(int("".join(map(str, b)), 2))
    symbols = np.array(symbols)
    
    # QAM constellation
    I = 2 * ((symbols % 4) - 1.5)
    Q = 2 * ((symbols // 4) - 1.5)
    qam_symbols = (I + 1j * Q)
    qam_symbols /= np.sqrt(np.mean(np.abs(qam_symbols)**2))
    
    # Pulse shaping
    baseband = np.repeat(qam_symbols, samples_per_symbol)
    return baseband

def QAM_demod_baseband(baseband, qam_order: int = 16, samples_per_symbol: int = 8):
    """Demodulate a QAM RF signal back into a bitstream string."""

    print("QAM demodulation ...\n")
    M = qam_order
    bits_per_symbol = int(np.log2(M))

    # Symbol timing (perfect)
    symbols_rx = baseband[::samples_per_symbol]
    symbols_rx /= np.sqrt(np.mean(np.abs(symbols_rx)**2))

    # Reference constellation
    I = 2 * ((np.arange(M) % 4) - 1.5)
    Q = 2 * ((np.arange(M) // 4) - 1.5)
    constellation = (I + 1j * Q) / np.sqrt(np.mean(np.abs(I + 1j * Q)**2))

    # Decision
    decoded = []
    for s in symbols_rx:
        k = np.argmin(np.abs(s - constellation))
        decoded.append(k)

    # Convert back to bits
    bitstream = "".join(format(k, f'0{bits_per_symbol}b') for k in decoded)
    return bitstream