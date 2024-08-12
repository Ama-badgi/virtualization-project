#define _POSIX_C_SOURCE  200112L

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "paging.h"

# define ERROR(...) \
do { \
    fprintf(stderr, "ERROR %s:%d : ", __func__, __LINE__); \
    fprintf(stderr, __VA_ARGS__); \
    fprintf(stderr, "\n"); \
} while (0)


# define ERROR_ERRNO(...) \
do { \
    char ebuf[1024]; \
    strerror_r(errno, ebuf, sizeof(ebuf)); \
    fprintf(stderr, "ERROR %s:%d : ", __func__, __LINE__); \
    fprintf(stderr, __VA_ARGS__); \
    fprintf(stderr, " : %s\n", ebuf); \
    fprintf(stderr, "\n"); \
} while (0)


static void
free_frames(uint8_t **frames, unsigned long nframes)
{
    if (!frames)
        return;

    for (unsigned long i = 0; i < nframes; i++) {
        free(frames[i]);
    }

    free(frames);
}


static int
create_frames(uint8_t ***frames, unsigned long nframes)
{
    if (!(*frames = malloc(sizeof(*frames) * nframes))) {
        return -1;
    }

    for (unsigned long i = 0; i < nframes; i++) {
        void *ptr;

        if (posix_memalign(&ptr, FRAME_SIZE, 0x100) < 0) {
            free_frames(*frames, i);
            return -1;
        }

        (*frames)[i] = ptr;
    }

    return 0;
}


static void
zero_frames(uint8_t **frames, unsigned long nframes)
{
    for (unsigned long i = 0; i < nframes; i++) {
        memset(frames[i], 0, FRAME_SIZE);
    }
}


static int
str2int(const char *str, unsigned long *num)
{
    char *endptr = NULL;
    unsigned long val;

    errno = 0;
    val = strtol(str, &endptr, 0);

    if (errno != 0 || endptr == str || (endptr && *endptr != '\0')) {
        ERROR("Cannot parse number: %s", str);
        return -1;
    }

    *num = val;
    return 0;
}

/**
 * Check if every address can be read and written.
 */
static int
test1(uint8_t **frames, unsigned long nframes)
{
    mmu *mmu = new_mmu(frames, nframes);
    int ret = -1;

    if (!mmu) {
        ERROR("Unable to create MMU");
        goto cleanup;
    }

    for (size_t addr = 0x0000; addr < nframes * FRAME_SIZE; addr++) {
        uint8_t b;

        if (read_byte(mmu, addr, &b) < 0) {
            ERROR("Failed to read byte at address 0x%x", (uint16_t)addr);
            goto cleanup;
        }

        if (write_byte(mmu, addr, b) < 0) {
            ERROR("Failed to write byte at address 0x%x", (uint16_t)addr);
            goto cleanup;
        }
    }

    ret = 0;
 cleanup:
    free_mmu(mmu);
    return ret;
}


/**
 * Writes "hello" "world" at 'random' locations and read it back.
 */
static int
test2(uint8_t **frames, unsigned long nframes)
{
    mmu *mmu = new_mmu(frames, nframes);
    const char *strings[] = { "hello", "world" };
    int i;
    int ret = -1;

    if (!mmu) {
        ERROR("Unable to create MMU");
        goto cleanup;
    }

    for (i = 0; i < 2; i++) {
        size_t len = strlen(strings[i]);
        uint16_t addr = i ? nframes * FRAME_SIZE - len : 0;
        int j;

        for (j = 0; j < len; j++) {
            if (write_byte(mmu, addr++, strings[i][j]) < 0) {
                ERROR("Failed to write byte at address 0x%x", addr);
                goto cleanup;
            }
        }
    }

    for (i = 0; i < 2; i++) {
        size_t len = strlen(strings[i]);
        uint16_t addr = i ? nframes * FRAME_SIZE - len : 0;
        int j;

        for (j = 0; j < len; j++) {
            uint8_t b;

            if (read_byte(mmu, addr++, &b) < 0) {
                ERROR("Failed to read byte at address 0x%x", addr);
                goto cleanup;
            }

            if (b != strings[i][j]) {
                ERROR("Unexpected value 0x%x; expected %c", b, strings[i][j]);
                goto cleanup;
            }
        }
    }

    printf("Test 2 hexdump\n");
    hexdump(mmu, 0x0, nframes * FRAME_SIZE - 1);

    ret = 0;
 cleanup:
    free_mmu(mmu);
    return ret;
}

static int
test3()
{
    uint8_t frame1[256];
    uint8_t frame2[256];
    uint8_t frame3[256];
    uint8_t *frames[3] = {frame1, frame2, frame3};

    memset(frame1, 32, 256);
    memset(frame2, 32, 256);
    memset(frame3, 32, 256);
    mmu *mmu = new_mmu(frames, 3);

    printf("\nTest 3 hexdump\n");
    hexdump(mmu, 0, 767);
    free_mmu(mmu);

    return 0;
}

static int
test4()
{
    char string[256] = "Nam quis nulla. Integer malesuada. In in enim a arcu imperdiet malesuada. \
Sed vel lectus. Donec odio urna, tempus molestie, porttitor ut, iaculis quis, sem. Phasellus rhoncus. \
Aenean id metus id velit ullamcorper pulvinar. Vestibulum fermentum tortor id m\0";
    uint8_t frame1[256];
    uint8_t *frames[1] = {frame1};

    memset(frame1, 0, 256);
    mmu *mmu = new_mmu(frames, 1);

    for (size_t idx = 0; idx < 256; idx++) {
        write_byte(mmu, idx, string[idx]);
    }
    printf("\nTest 4 hexdump\n");
    hexdump(mmu, 0, 255);
    free_mmu(mmu);

    return 0;
}

static int
test5()
{
    uint8_t frame1[256];
    uint8_t *frames[1] = {frame1};
    uint8_t byte;

    memset(frame1, 0, 256);
    mmu *mmu = new_mmu(frames, 1);

    printf("\nTest 5: Invalid pages\n");

    if (read_byte(mmu, 257, &byte) == 0) {
        ERROR("Read from invalid page.");
        return 1;
    }
    if (write_byte(mmu, 257, byte) == 0) {
        ERROR("Write to invalid page.");
        return 1;
    }

    free_mmu(mmu);

    return 0;
}

static int
run_tests(uint8_t **frames, unsigned long nframes)
{
    int ret = 0;

    zero_frames(frames, nframes);

    if (test1(frames, nframes) < 0)
        ret = -1;

    zero_frames(frames, nframes);

    if (test2(frames, nframes) < 0)
        ret = -1;

    test3();
    test4();

    if (test5() != 0)
        ret = -1;

    return ret;
}


int main(int argc, char *argv[])
{
    uint8_t **frames = NULL;
    unsigned long nframes = 4;
    int ret = EXIT_FAILURE;

    if (argc > 1) {
        unsigned long val;

        if (str2int(argv[1], &val) < 0)
            goto cleanup;

        if (val == 0) {
            ERROR("There's not much fun without memory");
            goto cleanup;
        }

        if (val > 256) {
            ERROR("Too much frames, maximum is 256");
            goto cleanup;
        }

        nframes = val;
    }

    // we allocate frames here for simplicity
    if (create_frames(&frames, nframes)) {
        ERROR("Cannot allocate memory");
        goto cleanup;
    }

    if (run_tests(frames, nframes) < 0) {
        ERROR("Some tests failed");
        goto cleanup;
    }

    ret = EXIT_SUCCESS;
 cleanup:
    free_frames(frames, nframes);
    return ret;
}

