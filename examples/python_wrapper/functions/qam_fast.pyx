# qam_fast.pyx
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
import numpy as np
cimport numpy as np
from libc.math cimport sqrt

# Helper: compute bits per symbol (assume M is power of two)
cdef inline int _bits_per_symbol(int M):
    cdef int b = 0
    cdef int tmp = M
    while tmp > 1:
        tmp >>= 1
        b += 1
    return b

# --------------------
# Modulator (C-level)
# --------------------
def qam_mod_baseband(np.ndarray[np.uint8_t, ndim=1] bits not None,
                     int qam_order=16,
                     int samples_per_symbol=8):
    """
    Modulate bits (np.uint8 array of 0/1) to complex128 baseband samples.
    Returns np.ndarray[np.complex128] of length n_symbols * samples_per_symbol.
    """
    cdef int M = qam_order
    cdef int bps = _bits_per_symbol(M)
    cdef Py_ssize_t n_bits = bits.shape[0]

    # pad bits to full symbols if needed
    cdef int pad = (bps - (n_bits % bps)) % bps
    if pad:
        bits = np.concatenate((bits, np.zeros(pad, dtype=np.uint8)))

    cdef Py_ssize_t n_symbols = bits.shape[0] // bps

    # create symbol indices (integers 0..M-1)
    cdef np.ndarray[np.int32_t, ndim=1] symbols = np.empty(n_symbols, dtype=np.int32)
    cdef Py_ssize_t i, j
    cdef int acc
    for i in range(n_symbols):
        acc = 0
        # pack bps bits into acc (MSB first)
        for j in range(bps):
            acc = (acc << 1) | <int>bits[i*bps + j]
        symbols[i] = acc

    # map integer symbol k -> QAM point (I + jQ)
    # Using square 2D grid mapping: low 2 bits -> I level, high bits -> Q level for powers-of-4 M
    cdef np.ndarray[np.complex128_t, ndim=1] qam_sym = np.empty(n_symbols, dtype=np.complex128)
    cdef double I, Q
    for i in range(n_symbols):
        # for conventional mapping used elsewhere: I = 2*((k % 4) - 1.5), Q = 2*((k // 4)-1.5)
        # this works for 16-QAM; for larger M this pattern still maps on 4x... grid by decomposition
        k = symbols[i]
        I = 2.0 * ((k % 4) - 1.5)
        Q = 2.0 * ((k // 4) - 1.5)
        qam_sym[i] = I + 1j * Q

    # Normalize average power to 1
    cdef double avgp = 0.0
    for i in range(n_symbols):
        avgp += (qam_sym[i].real*qam_sym[i].real + qam_sym[i].imag*qam_sym[i].imag)
    avgp /= n_symbols
    cdef double norm = sqrt(avgp)
    if norm != 0.0:
        for i in range(n_symbols):
            qam_sym[i] /= norm

    # Upsample / pulse shape: here we output rectangular (repetition) samples_per_symbol each.
    # Pre-allocate output
    cdef Py_ssize_t out_len = n_symbols * samples_per_symbol
    cdef np.ndarray[np.complex128_t, ndim=1] baseband = np.empty(out_len, dtype=np.complex128)
    cdef Py_ssize_t idx_out
    for i in range(n_symbols):
        idx_out = i * samples_per_symbol
        # fill samples_per_symbol copies
        for j in range(samples_per_symbol):
            baseband[idx_out + j] = qam_sym[i]

    return baseband

# --------------------
# Demodulator (C-level)
# --------------------
def qam_demod_baseband(np.ndarray[np.complex128_t, ndim=1] baseband not None,
                       int qam_order=16,
                       int samples_per_symbol=8):
    """
    Demodulate complex baseband samples to bit array (np.uint8).
    Assumes perfect timing (symbol boundaries aligned to sample 0).
    Returns np.ndarray[np.uint8_t] of length n_symbols * bits_per_symbol.
    """
    cdef int M = qam_order
    cdef int bps = _bits_per_symbol(M)
    cdef Py_ssize_t nsamples = baseband.shape[0]
    cdef Py_ssize_t n_symbols = nsamples // samples_per_symbol

    # take one sample per symbol (simple sampling)
    cdef np.ndarray[np.complex128_t, ndim=1] symbols_rx = np.empty(n_symbols, dtype=np.complex128)
    cdef Py_ssize_t i, j
    for i in range(n_symbols):
        symbols_rx[i] = baseband[i * samples_per_symbol]

    # normalize power
    cdef double avgp = 0.0
    for i in range(n_symbols):
        avgp += (symbols_rx[i].real*symbols_rx[i].real + symbols_rx[i].imag*symbols_rx[i].imag)
    avgp /= n_symbols
    cdef double norm = sqrt(avgp) if avgp > 0.0 else 1.0
    if norm != 0.0:
        for i in range(n_symbols):
            symbols_rx[i] /= norm

    # build reference constellation (same mapping as mod)
    cdef np.ndarray[np.complex128_t, ndim=1] constellation = np.empty(M, dtype=np.complex128)
    cdef int k
    for k in range(M):
        I = 2.0 * ((k % 4) - 1.5)
        Q = 2.0 * ((k // 4) - 1.5)
        constellation[k] = (I + 1j * Q)
    # normalize constellation
    cdef double cavg = 0.0
    for k in range(M):
        cavg += (constellation[k].real*constellation[k].real + constellation[k].imag*constellation[k].imag)
    cavg /= M
    cdef double cnorm = sqrt(cavg)
    for k in range(M):
        constellation[k] /= cnorm

    # nearest-neighbor decision (squared distance to avoid sqrt)
    cdef np.ndarray[np.int32_t, ndim=1] decoded_symbols = np.empty(n_symbols, dtype=np.int32)
    cdef double best_dist, dist, dx, dy
    cdef int best_k
    for i in range(n_symbols):
        best_dist = 1e300
        best_k = 0
        for k in range(M):
            dx = symbols_rx[i].real - constellation[k].real
            dy = symbols_rx[i].imag - constellation[k].imag
            dist = dx*dx + dy*dy
            if dist < best_dist:
                best_dist = dist
                best_k = k
        decoded_symbols[i] = best_k

    # convert decoded symbols to bits array (MSB-first per symbol)
    cdef np.ndarray[np.uint8_t, ndim=1] bits_out = np.empty(n_symbols * bps, dtype=np.uint8)
    cdef int val
    for i in range(n_symbols):
        val = decoded_symbols[i]
        # produce bits from MSB to LSB
        for j in range(bps-1, -1, -1):
            bits_out[i*bps + j] = <np.uint8_t>(val & 1)
            val >>= 1

    return bits_out
