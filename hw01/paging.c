#include <stdlib.h>
#include <stdio.h>

#include "paging.h"

struct _mmu {
    uint8_t **frame_pointers;
    size_t size;
};

// Part 1
mmu* new_mmu(uint8_t **frame_pointers, size_t size)
{
    mmu *unit;
    unit = malloc(sizeof(mmu));
    if (unit == NULL) {
        fprintf(stderr, "Alloc failed.\n");
        return NULL;
    }

    unit->size = size;
    unit->frame_pointers = frame_pointers;
    return unit;
}

void free_mmu(mmu *mmu)
{
    free(mmu);
}

int translate_address(mmu *mmu, uint16_t address, uint8_t **translated)
{
    uint8_t offset = address;
    uint8_t paging_index = address>>8;
    if (!mmu) {
        fprintf(stderr, "Uninitialised mmu.\n");
        return 1;
    }
    if (paging_index >= mmu->size) {
        fprintf(stderr, "Invalid page.\n");
        return 1;
    }

    *translated = (uint8_t*) (mmu->frame_pointers[paging_index]) + offset;
    return 0;
}

int read_byte(mmu *mmu, uint16_t address, uint8_t *byte)
{
    uint8_t *translated;
    if (translate_address(mmu, address, &translated) != 0) {
        return 1;
    }

    *byte = *translated;
    return 0;
}

int write_byte(mmu *mmu, uint16_t address, uint8_t byte)
{
    uint8_t *translated;
    if (translate_address(mmu, address, &translated) != 0) {
        return 1;
    }

    *translated = byte;
    return 0;
}

// Part 2
void init_string(char *string)
{
    string[0] = '|';
    string[17] = '|';
    string[18] = '\n';
    string[19] = '\0';
}

void add_to_string(char *string, uint8_t *address, uint8_t index)
{
    uint8_t first_displayable = 32;
    uint8_t last_displayable = 126;

    if (*address < first_displayable || *address > last_displayable) {
        string[index] = '.';
        return;
    }
    string[index] = *address;
}

void print_formatting(char *string, size_t *index, size_t *number_of_rows)
{
    if (*index % 8 == 0) {
        printf(" ");
    }

    if (*index % 16 == 0) {
        printf("%s", string);
        *number_of_rows += 1;
        printf("%08lx  ", 16 * *number_of_rows);
        *index = 0;
    }
}

void hexdump_page(mmu *mmu, uint16_t start, uint16_t end)
{
    uint8_t *start_translated;
    uint8_t *end_translated;
    if (translate_address(mmu, start, &start_translated) != 0 || translate_address(mmu, end, &end_translated) != 0) {
        return;
    }

    char string[20];
    size_t index = 0;
    size_t number_of_rows = 0;
    uint8_t *address;
    init_string(string);

    printf("%08x  ", 0);
    for (address = start_translated; address <= end_translated; address++) {
        index++;
        printf("%02x ", *address);
        add_to_string(string, address, index);
        print_formatting(string, &index, &number_of_rows);
    }

    while (index != 0) {
        index++;
        string[index] = '.';
        printf("   ");
        print_formatting(string, &index, &number_of_rows);
    }
    printf("\n");
}

void hexdump(mmu *mmu, uint16_t start, uint16_t end)
{
    uint16_t page_start;
    uint16_t page_end;
    size_t pages_amount = (end>>8) - (start>>8) + 1;

    for (size_t page = 0; page < pages_amount; page++) {
        if (page == 0) {
            page_start = (uint8_t) start;
        } else {
            page_start = page<<8;
        }

        if (page == pages_amount - 1) {
            page_end = (page<<8) + (uint8_t) end;
        } else {
            page_end = (page<<8) + FRAME_SIZE - 1;
        }

        printf("Page %ld:\n", page);
        hexdump_page(mmu, page_start, page_end);
    }
}
