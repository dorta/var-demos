#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <linux/input.h>
#include <fcntl.h>

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
    bool has_btn;
    const char *btn_input_dev;
    int btn_fd;
    pthread_mutex_t btn_mutex;
    unsigned int blink_val;
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

unsigned int get_blink_count(platform_data_t *platform)
{
    unsigned int ret;
    if (platform->has_btn) {
        pthread_mutex_lock(&platform->btn_mutex);
        ret = platform->blink_val;
        pthread_mutex_unlock(&platform->btn_mutex);
    } else {
        ret = platform->blink_val;
    }

    return ret;
}

void set_blink_count(platform_data_t *platform, unsigned int val)
{
    if (platform->has_btn) {
        pthread_mutex_lock(&platform->btn_mutex);
        platform->blink_val = val;
        pthread_mutex_unlock(&platform->btn_mutex);
    } else {
        platform->blink_val = val;
    }
}

void inc_blink_count(platform_data_t *platform)
{
    unsigned int count;

    count = get_blink_count(platform);
    count++;
    set_blink_count(platform, count);
}

void dec_blink_count(platform_data_t *platform)
{
    unsigned int count;

    count = get_blink_count(platform);
    if (count) {
        count--;
    }
    set_blink_count(platform, count);
}

void *btn_read_thread(void *data) {
    platform_data_t *platform = (platform_data_t *)data;
    struct input_event event;
    size_t bytes;
    while(1) {
        bytes = read(platform->btn_fd, &event, sizeof(struct input_event));
        if (bytes) {
            if (event.type == EV_KEY) {
                /* On press */
                if (event.value == 0) {
                    /* Works with any button */
                    inc_blink_count(platform);
                }
            }
        }
    }
}

int main(int argc, char **argv)
{
    // Make volatile so we can debug
    volatile unsigned int i, ret, val;
    struct gpiod_chip *chip;
    struct gpiod_line *line;
    platform_data_t platform;
    pthread_t btn_thread;

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
            platform.btn_input_dev = "/dev/input/event1";
            platform.has_btn = true;
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

    /* Open button input device and spawn thread if applicable */
    if (platform.has_btn) {
        platform.btn_fd = open(platform.btn_input_dev, O_RDONLY);
        if (platform.btn_fd < 0) {
            printf("Error: Unable to open %s\n", platform.btn_input_dev);
            goto release_line;
        }
        if (pthread_mutex_init(&platform.btn_mutex, NULL)) {
            printf("Error: Unable to init mutex\n");
            goto release_line;
        }

        if (pthread_create(&btn_thread, NULL, btn_read_thread, &platform)) {
            printf("Error: Unable to create thread\n");
            goto release_line;
        }
    }


    /* Toggle LED GPIO x10 times */
    set_blink_count(&platform, 10);
    val = 0;
    while(get_blink_count(&platform))
    {
        ret = gpiod_line_set_value(line, val);
        if (ret < 0) {
            perror("Set line output failed\n");
            goto release_line;
        }
        printf("blink count: %d output_val: %d\n", get_blink_count(&platform), val);

        usleep(500000);
        val = !val;

        dec_blink_count(&platform);
    }
    printf("Count expired, exiting...\n");

    if (platform.has_btn) {
        pthread_cancel(btn_thread);
        pthread_join(btn_thread, NULL);
    }

release_line:
    gpiod_line_release(line);
close_chip:
    gpiod_chip_close(chip);
end:
    return 0;
}
