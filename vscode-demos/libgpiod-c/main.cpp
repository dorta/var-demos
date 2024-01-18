#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#ifndef    CONSUMER
#define    CONSUMER    "Variscite"
#endif

#define VERIFY_MACH_ID_STR(str, match) (strstr(str, " " match " "))

typedef enum
{
    DART_MX8M,
    SOM_MX8M_MINI,
    /* TODO: Add others */
    SOM_UNKNOWN
} som_t;

typedef struct platform_data_t
{
    const char *gpio_chip_name;
    unsigned int gpio_line_num;
} platform_data_t;

/**
 * Parse /sys/devices/soc0/machine to determine the current Variscite SoM
 */
som_t detect_som() {
    FILE *fptr;
    som_t som = SOM_UNKNOWN;
    char machine[200];
    int len;
    if ((fptr = fopen("/sys/devices/soc0/machine","r")) == NULL){
           printf("Error: Failed to open /sys/devices/soc0/machine\n");
    } else {
       len = fread(machine, sizeof(char), 200, fptr);
       if(len > 0) {
            if(VERIFY_MACH_ID_STR(machine, "DART-MX8M")) {
                som = DART_MX8M;
            } else if (VERIFY_MACH_ID_STR(machine, "VAR-SOM-MX8M-MINI")) {
                som = SOM_MX8M_MINI;
            } else {
                printf("Error: Unsupported SoM!\n");
            }
       } else {
            printf("Error: Failed to read /sys/devices/soc0/machine\n");
       }
   }

   return som;
}


int main(int argc, char **argv)
{
    // Make volatile so we can debug
    volatile unsigned int i, ret, val;
    struct gpiod_chip *chip;
    struct gpiod_line *line;
    const char * chipname = 0;
    unsigned int line_num;
    platform_data_t platform;

    memset(&platform, 0, sizeof(platform_data_t));

    // Detect SOM and configure gpiochip and line_num
    switch(detect_som()) {
        case DART_MX8M:
            platform.gpio_chip_name = "gpiochip6"; // dt8mcustomboard i2c gpio expander
            platform.gpio_line_num = 7; // i2c gpio expander gpio #7
        break;
        case SOM_MX8M_MINI:
            /* VAR-SOM-MX8M-MINI Symphony Custom Board I2C GPIO #0 */
            platform.gpio_chip_name = "gpiochip5";
            platform.gpio_line_num = 0;
        break;
        /* Todo: Add other SoMs */
        default:
        break;
    }

    if (!platform.gpio_chip_name) {
        goto end;
    }

    chip = gpiod_chip_open_by_name(platform.gpio_chip_name);
    if (!chip) {
        perror("Open chip failed\n");
        goto end;
    }

    line = gpiod_chip_get_line(chip, platform.gpio_line_num);
    if (!line) {
        perror("Get line failed\n");
        goto close_chip;
    }

    ret = gpiod_line_request_output(line, CONSUMER, 0);
    if (ret < 0) {
        perror("Request line as output failed\n");
        goto release_line;
    }

    /* Blink 5 times */
    val = 0;
    for (i = 0; i < 5; i++) {
        ret = gpiod_line_set_value(line, val);
        if (ret < 0) {
            perror("Set line output failed\n");
            goto release_line;
        }
        printf("Output %u on line #%u\n", val, line_num);
        sleep(1);
        val = !val;
    }

release_line:
    gpiod_line_release(line);
close_chip:
    gpiod_chip_close(chip);
end:
    return 0;
}
