#pragma once

#include <stdint.h>
#include <stddef.h>

#define FRAME_SIZE 256

typedef struct _mmu mmu;

mmu *new_mmu(uint8_t **frame_pointers, size_t size);

void free_mmu(mmu *mmu);

int read_byte(mmu *mmu, uint16_t address, uint8_t *byte);

int write_byte(mmu *mmu, uint16_t address, uint8_t byte);

void hexdump(mmu *mmu, uint16_t start, uint16_t end);
