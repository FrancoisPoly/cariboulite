#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>
#include <stdint.h>
#include <unistd.h>
#include <stdbool.h>
#include <cariboulite.h>

// Can be built with: gcc -o "name of the executable" main.c -lcariboulite -lm

// Define the radio's main parameters
#define SAMPLE_RATE 4000000.0   // 4 MHz
#define TX_FREQ    900000000.0  // 900 MHz
#define TX_BW       1000000.0   // 1 MHz
#define TX_POWER       5        // 0 dBm

// Start TX (C version) - func. that starts the transmission with the use of CW
void start_tx(cariboulite_radio_state_st* radio)
{
    if (cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_rx, false) != 0){
        printf("Cannot deactivate RX prior to transmission\n");
    }

    if (cariboulite_radio_set_cw_outputs(radio, false, true) != 0){  // set second to "true" for built-in CW
        printf("Cannot set to CW\n");
    }

    if (cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, true) != 0){
        printf("Cannot activate TX prior to transmission\n");
    }
}

// Stop TX (C version) - func. that stops the transmission with the fact the real transmission doesn't work
void stop_tx(cariboulite_radio_state_st* radio) // WARNING: when the transmission will be fixed, this func. won't work
{
    if (cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_rx, false) != 0){
        printf("Cannot deactivate RX prior to transmission\n");
    }

    if (cariboulite_radio_set_cw_outputs(radio, false, false) != 0){
        printf("Cannot set to IQ transfer\n");
    }

    if (cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, true) != 0){
        printf("Cannot activate TX prior to transmission\n");
    }
}



int main()
{
    // 1. Detect board
    cariboulite_version_en hw_ver;
    char hw_name[128];
    char hw_uuid[128];
    if (!cariboulite_detect_connected_board(&hw_ver, hw_name, hw_uuid)) {
        printf("No board detected, exiting.\n");
        return -1;
    }
    printf("Detected board: HWVer=%d, Name=%s, UUID=%s\n", hw_ver, hw_name, hw_uuid); // print the board's infos

    // 2. Initialize library
    if (cariboulite_init(false, cariboulite_log_level_none) != 0) {
        printf("Failed to initialize CaribouLite\n");
        return -1;
    }

    // 3. Get serial number
    uint32_t sn = cariboulite_get_sn();
    printf("Serial number: %08X\n", sn);

    // 4. Get S1G radio
    cariboulite_radio_state_st* radio = cariboulite_get_radio(cariboulite_channel_s1g);
    if (!radio) {
        printf("Failed to get S1G radio\n");
        cariboulite_close();
        return -1;
    }

    // 5. Configure TX
    double freq = TX_FREQ;
    if (cariboulite_radio_set_frequency(radio, true, &freq) != 0)
        printf("Cannot set TX frequency\n");

    if (cariboulite_radio_set_tx_power(radio, TX_POWER) != 0){
        printf("Cannot set POWER\n");
    }

    if (cariboulite_radio_set_tx_bandwidth(radio, TX_BW) != 0){
        printf("Cannot set BW\n");
    }

    if (cariboulite_radio_set_tx_samp_cutoff_flt(radio, SAMPLE_RATE) != 0){
        printf("Cannot set SR\n");
    }
    

    /*// 6. OOK test (on/off)
    bool bit = false;
    for (int i = 0; i < 100; i++)
    {
        if (bit)
        {
     	    start_tx(radio);
        }
        else
        {
            stop_tx(radio);
        }

        bit = !bit;  // toggle between on/off
        usleep(1000);  // 1 ms delay
    }*/



    // 6. OOK — load bitstream from file and transmit it
char filename[] = "/home/sm1/bitstream.txt";

// Load bitstream from file
FILE *fp = fopen(filename, "r");
if (!fp) {
    perror("Cannot open bitstream file");
    cariboulite_close();
    return -1;
}

// Count bits
fseek(fp, 0, SEEK_END);
long fsize = ftell(fp);
rewind(fp);

// Allocate buffer
uint8_t *bitstream = malloc(fsize);
if (!bitstream) {
    printf("Memory allocation failed\n");
    fclose(fp);
    cariboulite_close();
    return -1;
}

// Read characters and convert to bits
long bitcount = 0;
for (int c = fgetc(fp); c != EOF; c = fgetc(fp)) {
    if (c == '0') bitstream[bitcount++] = 0;
    else if (c == '1') bitstream[bitcount++] = 1;
    // ignore anything else: spaces, newlines, etc.
}
fclose(fp);

printf("Loaded %ld bits from file.\n", bitcount);


// run-length encoding (RLE)
long *runs = malloc(bitcount * sizeof(long));
long run_count = 0;

long count = 1;
for (long i = 1; i < bitcount; i++) {
    if (bitstream[i] == bitstream[i-1]) {
        count++;
    } else {
        runs[run_count++] = count;
        count = 1;
    }
}
runs[run_count++] = count;    // last run



// Transmission parameters
int bit_us = 1000;   // how long each bit stays ON/OFF (1 ms OOK)
                     // adjust as needed
		     // Gives time to the hardware to process

// Timing factors - Optained empirically
double single_factor =  2.1;
double multiple_factor = 2.5;

uint8_t current = bitstream[0]; // should always start with "on"
for (long i = 0; i < run_count; i++) {
    int run_len = runs[i];
    if (current == 1){
	start_tx(radio); // Transmit for bits of value = 1
	if (run_len > 1){
	    usleep(run_len * bit_us * multiple_factor);
	    }
	else{
	    usleep(run_len * bit_us * single_factor);
	    }
	}
    else{
	stop_tx(radio); // Don't transmit for bits of value = 0
	if (run_len > 1){
            usleep(run_len * bit_us * multiple_factor);
            }
        else{
            usleep(run_len * bit_us * single_factor);
            }
	}

    current ^= 1;   // flip 0→1 or 1→0
}


free(bitstream);




// 7. Stop TX
cariboulite_radio_set_cw_outputs(radio, false, false);
cariboulite_radio_activate_channel(radio, cariboulite_channel_dir_tx, false);

cariboulite_close();

    return 0;
}
