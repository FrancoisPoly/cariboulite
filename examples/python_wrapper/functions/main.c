#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>
#include <stdint.h>
#include <unistd.h>
#include <stdbool.h>
#include <string.h>
#include <cariboulite.h>


// Make sure you build the C tool with this command:
// gcc -shared -fPIC -o libcariboulite_radio.so main.c -lcariboulite -lm


// Main parameters
#define DEFAULT_BIT_US 1000 // Normal duration of each on/off command
#define SINGLE_FACTOR  2.1  // Multiplication factor when single "0" or "1" are broadcasted
#define MULTIPLE_FACTOR 2.5 // Multiplication factor when consecutive "0" or "1" are broadcasted

// Function that starts the transmission of a CW (radio = on)
void start_tx(cariboulite_radio_state_st* radio)
{
    cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_rx, false); // Deactivate RX channel
    cariboulite_radio_set_cw_outputs(radio, false, true); // Set CW
    cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, true); // Activate TX channel
}

// Function that "stops" the transmission (radio = off)
// If the Cariboulite source code were complete, this function would enable the transmission of IQ samples
void stop_tx(cariboulite_radio_state_st* radio)
{
    cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_rx, false); // Deactivate RX channel
    cariboulite_radio_set_cw_outputs(radio, false, false); // Send IQ samples -> doesn't work, so it doesn't send anything -> radio off
    cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, true); // Activate TX channel
}

// Main transmit function
// Exposed function for Python
int transmit(double sample_rate, double tx_freq, double tx_bw, int tx_power, const char* filepath, const char* channel)
{
    /*
    The main inputs are:
    - Samplerate
    - Transmission Frequency
    - Transmission Bandwidth
    - Transmission Power
    - Path to the .txt containing the bitstring to broadcast
    - Choice of channel: "s1g" -> low freq channel
                         "hif" -> high freq channel
    */

    // [1 - Detect and initialize the Cariboulite board]
    cariboulite_version_en hw_ver;
    char hw_name[128], hw_uuid[128];

    if (!cariboulite_detect_connected_board(&hw_ver, hw_name, hw_uuid)) {
        printf("No board detected.\n");
        return -1;
    }

    if (cariboulite_init(false, cariboulite_log_level_none) != 0) {
        printf("Failed to initialize CaribouLite.\n");
        return -1;
    }

    // Setting chosen TX channel
    cariboulite_radio_state_st* radio = cariboulite_get_radio(cariboulite_channel_s1g);

    if (strcmp(channel, "s1g") == 0) {
	cariboulite_radio_state_st* radio = cariboulite_get_radio(cariboulite_channel_s1g);
        if (!radio) {
            printf("Failed to get S1G radio.\n");
            cariboulite_close();
            return -1;
        }
    } else if (strcmp(channel, "hif") == 0) {
	cariboulite_radio_state_st* radio = cariboulite_get_radio(cariboulite_channel_hif);
        if (!radio) {
            printf("Failed to get HIF radio.\n");
            cariboulite_close();
            return -1;
        }
    }


    // [2 - Setting the TX parameters]
    double freq = tx_freq;
    cariboulite_radio_set_frequency(radio, true, &freq);
    cariboulite_radio_set_tx_power(radio, tx_power);
    cariboulite_radio_set_tx_bandwidth(radio, tx_bw);
    cariboulite_radio_set_tx_samp_cutoff_flt(radio, sample_rate);

    // [3 - Loading bitstring from .txt file]
    FILE *fp = fopen(filepath, "r");
    if (!fp) {
        perror("Cannot open bitstream file");
        cariboulite_close();
        return -1;
    }

    // Memory allocation
    fseek(fp, 0, SEEK_END);
    long fsize = ftell(fp);
    rewind(fp);

    uint8_t *bitstream = malloc(fsize);
    if (!bitstream) {
        printf("Memory allocation failed\n");
        fclose(fp);
        cariboulite_close();
        return -1;
    }

    long bitcount = 0;
    for (int c = fgetc(fp); c != EOF; c = fgetc(fp)) {
        if (c == '0') bitstream[bitcount++] = 0;
        else if (c == '1') bitstream[bitcount++] = 1;
    }
    fclose(fp);

    // [4 - Run Length Encoding (RLE) on the binary data to send]
    long *runs = malloc(bitcount * sizeof(long));
    long run_count = 0, count = 1;
    for (long i = 1; i < bitcount; i++) {
        if (bitstream[i] == bitstream[i - 1]) count++;
        else { runs[run_count++] = count; count = 1; }
    }
    runs[run_count++] = count;

    // [5 - Broadcasting the RLE-OOK-encoded binary data
    uint8_t current = bitstream[0]; // The broadcasted message should start with a binary value = 1 -> "on"
    for (long i = 0; i < run_count; i++) {
        int run_len = runs[i];
        if (current == 1) start_tx(radio); // if binary val == 1 -> "on"
        else stop_tx(radio); // if binary val == 0 -> "off"

        // For timing and sychronization purposes, increasing the TX delays by constant values
        double factor = (run_len > 1) ? MULTIPLE_FACTOR : SINGLE_FACTOR;
        usleep(run_len * DEFAULT_BIT_US * factor);
        current ^= 1;
    }

    // [6 - Closing the Cariboulite board]
    // Freeing memory
    free(bitstream);
    free(runs);

    // Equivalent to the real "stop_tx" function in the official C++ API
    cariboulite_radio_set_cw_outputs(radio, false, false);
    cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, false);
    cariboulite_close();
    return 0;
}
