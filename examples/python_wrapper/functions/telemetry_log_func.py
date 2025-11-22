import random

def generate_random_tele_log_bitstring(len_of_log: int = 2500) -> str:
    """Function that generates a random telemetry log bit string"""
    tele_log = ""

    for _ in range(len_of_log):
        tele_log += str(random.randint(0, 1))

    return tele_log

# Example of use
# print(len(generate_random_tele_log_bitstring(3000)))