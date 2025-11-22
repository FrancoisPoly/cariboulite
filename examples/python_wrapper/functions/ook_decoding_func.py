import numpy as np
from scipy.io import wavfile
import inspect

# from .class_info import payload_type
# from .types_to_bin_func import *

def rle(arr: np.ndarray) -> list[int]:
    """
    Function that transforms an on/off sequence to a run length encoding scheme\n
    e.g.: (on on on on off off ...) -> (4 2 ...)
    """
    if len(arr) == 0:
        return []
    lengths = []
    count = 1
    for i in range(1, len(arr)):
        if arr[i] == arr[i-1]:
            count += 1
        else:
            lengths.append(count)
            count = 1
    lengths.append(count)
    return lengths

def interpolator(interp_points: list[int|float], order: int) -> np.poly1d:
    x = np.array([coord[1] for coord in interp_points])
    y = np.array([coord[0] for coord in interp_points])

    # Fit the unique polynomial through n points
    coeffs = np.polyfit(x, y, deg=order) 
    poly = np.poly1d(coeffs)

    return poly

def invert_poly(poly: np.poly1d, y_target: int|float) -> np.float64:
    """
    Given a numpy.poly1d 'poly' and a target y value,
    return all real x such that poly(x) = y_target.
    """
    # Build the polynomial poly(x) - y_target
    coeffs = poly.c.copy()
    coeffs[-1] -= y_target

    # Solve for roots
    roots = np.roots(coeffs)

    # Keep only real roots (imag part close to zero)
    # Keep only positive roots
    real_roots = [r.real for r in roots
              if abs(r.imag) < 1e-9 and r.real > 0 and r.real < 200]

    return real_roots[0]

def decode_runs(runs: list[int], start_time_on: int|float, delta_on: int|float, interp_points: list[int|float]):
    """
    Function that will decode the run length encoding scheme (RLE) for on/off values\n
    into a RLE for binary data
    """
    # Build the interpolator and interpolate the function for "off" values
    poly = interpolator(interp_points, 2)

    out = []
    for i, r in enumerate(runs):
            if i % 2 == 0:
                # peak
                bin_len = round((r - start_time_on) / delta_on)
            else:
                # pause
                try:
                    bin_len = round(invert_poly(poly, r))
                except: 
                    bin_len = 1 # The interpolator doesn't work sometime when the val is too small
                                # Anyways, we know it's going to be a 1
                
            if bin_len <= 0:
                out.append(1)
            else:
                out.append(bin_len)

    return out

def runs_to_bitstring(runs: list[int]) -> str:
    """
    Function that transforms an RLE scheme for binary data into a bitstring
    """
    bit = '1'    # always start ON
    out = []

    for r in runs:
        out.append(bit * r)
        bit = '0' if bit == '1' else '1'   # flip
    return ''.join(out)


def symmetric_ratio_average(arr1: np.ndarray, arr2: np.ndarray) -> float:
    """
    Function that compares the array containing the RLE-binary data decoded from RF transmission\n
    to the original payload in order to compute the 'RF symbol error' (%)
    """
    arr1 = np.asarray(arr1, dtype=float)
    arr2 = np.asarray(arr2, dtype=float)

    # avoid divide-by-zero
    mask = (arr1 != 0) & (arr2 != 0)
    ratios = np.empty_like(arr1, dtype=float)
    ratios[mask] = np.minimum(arr1[mask], arr2[mask]) / np.maximum(arr1[mask], arr2[mask])
    ratios[~mask] = 0  # handle zeros safely

    return ratios.mean()

def bitstring_file_to_runs(path: str) -> list[int]:
    """
    Function that reads a .txt file containing a bitstring to transform it into an RLE scheme
    """
    with open(path, 'r') as f:
        content = f.read()

    # keep only valid bit characters
    bitstring = ''.join(ch for ch in content if ch in '01')

    if not bitstring:
        raise ValueError("No valid bit data found in file.")

    runs = []
    count = 1

    for i in range(1, len(bitstring)):
        if bitstring[i] == bitstring[i-1]:
            count += 1
        else:
            runs.append(count)
            count = 1

    runs.append(count)
    return runs

def ook_decoding(recording_file_path: str) -> list[int]:
    """
    Main function that decodes an RF transmision\n
    encoded with an on/off keying (OOK) scheme
    """

    # === Load WAV ===
    _, data = wavfile.read(recording_file_path)

    I = data[:,0].astype(float)
    Q = data[:,1].astype(float)

    mag = np.sqrt(I**2 + Q**2)
    threshold = mag.mean()
    binary = (mag > threshold).astype(int)

    # find first rising edge
    rising_edges = np.where((binary[1:] == 1) & (binary[:-1] == 0))[0]
    if rising_edges.size == 0:
        raise RuntimeError("No peak found in signal.")

    start = rising_edges[0]+1
    binary = binary[start:]

    # Transform the on/off value to run length of encoding
    # e.g.: (on on on on off off ...) -> (4 2 ...) 
    runs = rle(binary)

    # Find the on/off transmision points' length of the CP head
    # The on transmission points' length evolve linearly, so we can do averages
    data_1_on = ((runs[0] + runs[2] + runs[4] + runs[6] + runs[8] + runs[10])/6, 1)
    data_2_on = ((runs[12] + runs[14] + runs[16] + runs[18] + runs[20])/5, 2)

    data_1_off = ((runs[1] + runs[3])/2, 1)
    data_2_off = (runs[5], 2)
    data_3_off = (runs[7], 3)
    data_4_off = (runs[9], 4)
    data_5_off = (runs[11], 5)
    data_10_off = (runs[13], 10)
    data_20_off = (runs[15], 20)
    data_50_off = (runs[17], 50)
    data_100_off = (runs[19], 100)

    # The off transmission points' length don't evolve linearly, 
    # so we need a more robust interpolation scheme
    interpolation_points = [data_1_off,
                            data_2_off,
                            data_3_off,
                            data_4_off,
                            data_5_off,
                            data_10_off,
                            data_20_off,
                            data_50_off,
                            data_100_off]

    # Basic linear interpolation to find the start time and delta_t for on points
    result_on = np.linalg.solve(np.array([[1,data_1_on[1]],[1,data_2_on[1]]]), np.array([[data_1_on[0]],[data_2_on[0]]]))
    start_time_on = result_on[0][0]
    delta_on = result_on[1][0]

    # Transforming the on/off RLE scheme into RLE binaray data
    decoded = decode_runs(runs, start_time_on, delta_on, interpolation_points)

    return decoded
