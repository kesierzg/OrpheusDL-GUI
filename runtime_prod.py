import struct
from collections.abc import Sequence

from unicorn.unicorn import Uc
from unicorn.x86_const import (
    UC_X86_REG_GS_BASE,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSP,
)

from unplayplay.consts import MEM
from unplayplay.emu.addressing import align

def setup_stack(mu: Uc):
    mu.mem_map(MEM.STACK_ADDR, align(MEM.STACK_SIZE))
    mu.reg_write(UC_X86_REG_RSP, MEM.STACK_ADDR + MEM.STACK_SIZE)

def setup_teb(mu: Uc):
    mu.mem_map(MEM.TEB_ADDR, MEM.PAGE_SIZE)
    stack_base = MEM.STACK_ADDR + MEM.STACK_SIZE
    stack_limit = MEM.STACK_ADDR
    teb_data = struct.pack("<QQQ", 0, stack_base, stack_limit)
    mu.mem_write(MEM.TEB_ADDR, teb_data)
    mu.mem_write(MEM.TEB_ADDR + 0x30, struct.pack("<Q", MEM.TEB_ADDR))
    mu.reg_write(UC_X86_REG_GS_BASE, MEM.TEB_ADDR)

def emulate_call(mu: Uc, func: int, args: Sequence[int]):
    original_rsp = mu.reg_read(UC_X86_REG_RSP)
    rsp = mu.reg_read(UC_X86_REG_RSP)
    rsp -= 0x20
    rsp -= 8
    mu.mem_write(rsp, struct.pack("<Q", MEM.EXIT_ADDR))
    mu.reg_write(UC_X86_REG_RSP, rsp)
    regs = [UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9]
    for index, arg in enumerate(args[:4]):
        mu.reg_write(regs[index], arg)
    mu.emu_start(func, MEM.EXIT_ADDR)
    mu.reg_write(UC_X86_REG_RSP, original_rsp)
