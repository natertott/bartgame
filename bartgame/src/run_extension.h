#ifndef RUN_EXTENSION_H
#define RUN_EXTENSION_H
#include "gba.h"
#define RUN_EXTENSION_SRAM_BASE 0x4000u
#define RUN_EXTENSION_SLOT_BYTES 4096u
#define RUN_PROFILE_SRAM_BASE 0x7D00u
#define RUN_PROFILE_SLOT_BYTES 128u
void run_extension_init(void);
void run_extension_write(u32 base_sum);
bool8 run_extension_load(u32 base_sum,u32 seed);
bool8 run_extension_finished(u32 base_sum);
void run_extension_erase(void);
void run_profile_write(void);
#endif
