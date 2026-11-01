"""Record which RAM bytes are read / written / executed during a scripted
play session (pure-Python SkoolKit simulator with instrumented memory).

Used to locate free space for new code: a candidate area must be untouched
in every recorded session AND have no static references (tools/xref.py).

usage: python tools/memusage.py SNAPSHOT SCRIPT OUT.pkl
  SCRIPT: text file, one command per line:  <frames> [KEY KEY ...]
"""
import pickle
import sys

from skoolkit.simulator import Simulator
from skoolkit.simutils import from_snapshot, PC, T
from skoolkit.snapshot import Snapshot

import emu as emumod

FRAME = 69888


class TrackedMemory(list):
    def __init__(self, data):
        super().__init__(data)
        self.r = bytearray(65536)
        self.w = bytearray(65536)

    def __getitem__(self, i):
        if isinstance(i, int):
            self.r[i & 0xFFFF] = 1
        return list.__getitem__(self, i)

    def __setitem__(self, i, v):
        if isinstance(i, int):
            self.w[i & 0xFFFF] = 1
        list.__setitem__(self, i, v)


def run(snapfile, script, outfile):
    snap = Snapshot.get(snapfile)
    sim0 = from_snapshot(Simulator, snap)
    mem = TrackedMemory(sim0.memory)
    sim = Simulator(mem, {k: v for k, v in []} or None)
    # copy registers
    for i, v in enumerate(sim0.registers):
        sim.registers[i] = v
    host = type('H', (), {})()
    host.keyboard = [0] * 8
    host.kempston = 0
    host.border = 0
    sim.set_tracer(emumod._Tracer(host))
    x = bytearray(65536)
    reg = sim.registers
    opcodes = sim.opcodes
    for line in open(script):
        line = line.split('#')[0].split()
        if not line:
            continue
        frames = int(line[0])
        host.keyboard = [0] * 8
        for k in line[1:]:
            r, b = emumod.KEYS[k]
            host.keyboard[r] |= 1 << b
        for _ in range(frames):
            t_end = (reg[T] // FRAME + 1) * FRAME
            while reg[T] < t_end:
                pc = reg[PC]
                x[pc] = 1
                opcodes[mem[pc]]()
                if reg[T] >= t_end - FRAME + 0 and reg[T] % FRAME < 32 and reg[26]:
                    pass
            if reg[26]:
                sim.accept_interrupt(reg, mem, reg[PC])
    pickle.dump({'r': bytes(mem.r), 'w': bytes(mem.w), 'x': bytes(x),
                 'ram': bytes(list.__getitem__(mem, slice(0x4000, 0x10000)))}, open(outfile, 'wb'))


if __name__ == '__main__':
    run(*sys.argv[1:4])
