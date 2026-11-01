"""Headless ZX Spectrum 48K harness built on SkoolKit's C Z80 simulator.

Runs a .z80 snapshot frame by frame (50 Hz interrupts), lets a script hold
keys, inspect/poke memory and save screenshots as PNG.
"""
import os
import struct
import sys
import zlib

from skoolkit import CSimulator
from skoolkit.simulator import Simulator
from skoolkit.simutils import from_snapshot, PC, T
from skoolkit.snapshot import Snapshot

FRAME = 69888

# key name -> (half-row index 0..7 as used by SkoolKit, bit)
# half-row i corresponds to port address line A(8+i)
_ROWS = [
    ['SHIFT', 'Z', 'X', 'C', 'V'],
    ['A', 'S', 'D', 'F', 'G'],
    ['Q', 'W', 'E', 'R', 'T'],
    ['1', '2', '3', '4', '5'],
    ['0', '9', '8', '7', '6'],
    ['P', 'O', 'I', 'U', 'Y'],
    ['ENTER', 'L', 'K', 'J', 'H'],
    ['SPACE', 'SYM', 'M', 'N', 'B'],
]
KEYS = {k: (r, b) for r, row in enumerate(_ROWS) for b, k in enumerate(row)}


class _Tracer:
    """Minimal port tracer: keyboard on even ports, kempston on 0x1F."""

    def __init__(self, emu):
        self.emu = emu
        self.border = []      # required by CSimulator.trace

    def read_port(self, registers, port):
        if port & 0xFF == 0x1F:
            return self.emu.kempston
        if port % 2 == 0:
            h = (port >> 8) ^ 0xFF
            v = 0
            for i in range(8):
                if h & (1 << i):
                    v |= self.emu.keyboard[i]
            return (v | 0x40) ^ 0xFF
        return 0xFF

    def write_port(self, registers, port, value, *args):
        if port % 2 == 0:
            self.emu.border = value & 7


class Emu:
    def __init__(self, z80path, python=False):
        snap = Snapshot.get(z80path)
        cls = Simulator if python or CSimulator is None else CSimulator
        self.sim = from_snapshot(cls, snap, config={'fast_djnz': False, 'fast_ldir': False})
        self.mem = self.sim.memory
        self.reg = self.sim.registers
        self.keyboard = [0] * 8
        self.kempston = 0
        self.border = 0
        self.sim.set_tracer(_Tracer(self))
        self.frame = 0
        self.hooks = []          # callables(emu) run once per frame

    # --- input --------------------------------------------------------
    def press(self, *keys):
        for k in keys:
            r, b = KEYS[k]
            self.keyboard[r] |= 1 << b

    def release(self, *keys):
        if not keys:
            self.keyboard = [0] * 8
            return
        for k in keys:
            r, b = KEYS[k]
            self.keyboard[r] &= ~(1 << b)

    # --- execution ----------------------------------------------------
    def run_frames(self, n=1, stop=-1):
        """Run n frames. Returns PC if it hit `stop`, else None."""
        for _ in range(n):
            t_end = (self.reg[T] // FRAME + 1) * FRAME
            # stop<0 -> no stop address (use an impossible one)
            res = self.sim.trace(self.reg[PC], stop if stop >= 0 else 0x10000, 0, t_end,
                                 1, None, None, self.keyboard, None, None)
            stop_cond = res[0]
            if stop_cond == 3:
                return self.reg[PC]
            self.frame += 1
            for h in self.hooks:
                h(self)
        return None

    def run_until(self, addr, max_frames=500):
        for _ in range(max_frames):
            r = self.run_frames(1, stop=addr)
            if r is not None:
                return True
        return False

    def step(self):
        """Execute exactly one instruction (no interrupt handling)."""
        self.sim.trace(self.reg[PC], 0x10000, 1, 0, 0, None, None, self.keyboard, None, None)

    # --- state --------------------------------------------------------
    def save_state(self):
        return (bytes(self.mem[0x4000:0x10000]), list(self.reg), list(self.keyboard), self.frame)

    def load_state(self, st):
        ram, reg, kb, fr = st
        self.mem[0x4000:0x10000] = ram
        for i, v in enumerate(reg):
            self.reg[i] = v
        self.keyboard = list(kb)
        self.frame = fr

    # --- memory -------------------------------------------------------
    def peek(self, a):
        return self.mem[a]

    def peekw(self, a):
        return self.mem[a] | self.mem[a + 1] << 8

    def poke(self, a, v):
        self.mem[a] = v & 0xFF

    def ram(self):
        return bytes(self.mem[0x4000:0x10000])

    # --- screen -------------------------------------------------------
    def screenshot(self, path, scale=2):
        scr = self.mem[0x4000:0x5B00]
        pal = [(0, 0, 0), (0, 0, 0xD7), (0xD7, 0, 0), (0xD7, 0, 0xD7), (0, 0xD7, 0), (0, 0xD7, 0xD7), (0xD7, 0xD7, 0), (0xD7, 0xD7, 0xD7)]
        palb = [(0, 0, 0), (0, 0, 0xFF), (0xFF, 0, 0), (0xFF, 0, 0xFF), (0, 0xFF, 0), (0, 0xFF, 0xFF), (0xFF, 0xFF, 0), (0xFF, 0xFF, 0xFF)]
        rows = []
        for y in range(192):
            line = bytearray()
            base = ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
            for cx in range(32):
                bits = scr[base + cx]
                attr = scr[6144 + (y // 8) * 32 + cx]
                p = palb if attr & 64 else pal
                ink, paper = p[attr & 7], p[(attr >> 3) & 7]
                for b in range(8):
                    c = ink if bits & (0x80 >> b) else paper
                    line += bytes(c) * scale
            for _ in range(scale):
                rows.append(bytes(line))
        _write_png(path, 256 * scale, 192 * scale, rows)


def _write_png(path, w, h, rows):
    raw = b''.join(b'\x00' + r for r in rows)

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, 'wb').write(png)


def disasm_live(emu, addr):
    from skoolkit.traceutils import disassemble
    return disassemble(emu.mem, addr, '$', '02X', '04X')[:2]


def trace_steps(emu, n, show=True):
    """Single-step n instructions printing live disassembly."""
    out = []
    for _ in range(n):
        pc = emu.reg[PC]
        text, _ = disasm_live(emu, pc)
        line = '%04X %-20s A=%02X BC=%04X DE=%04X HL=%04X IX=%04X SP=%04X' % (
            pc, text, emu.reg[0], emu.reg[2] << 8 | emu.reg[3], emu.reg[4] << 8 | emu.reg[5],
            emu.reg[6] << 8 | emu.reg[7], emu.reg[8] << 8 | emu.reg[9], emu.reg[12])
        out.append(line)
        if show:
            print(line)
        emu.step()
    return out


def run_script(emu, path, on_step=None):
    """Play a session script (lines: '<frames> [KEY ...]')."""
    for line in open(path):
        line = line.split('#')[0].split()
        if not line:
            continue
        emu.release()
        emu.press(*line[1:])
        for _ in range(int(line[0])):
            emu.run_frames(1)
            if on_step:
                on_step(emu)
    emu.release()
