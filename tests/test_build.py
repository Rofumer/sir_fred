"""Build / snapshot integrity.

  * the original snapshot unpacks to exactly the verified 48K RAM dump
  * the QoL snapshot is a valid 48K .z80 v2 file with the ORIGINAL header
    (registers, PC=$0038, IM 1, SP, border) and 49152 bytes of RAM
  * every feature switch builds on its own; with all switches off the
    output file is byte-identical to the original
  * every changed byte lies in a declared patch site or free block
    (so no neighbouring code or data is damaged)
"""
import os
import sys

from common import ORIGINAL, QOL, ROOT, build_qol

sys.path.insert(0, os.path.join(ROOT, 'tools'))
from z80snap import Z80Snapshot  # noqa: E402

OFF = dict(QOL_ROPE=0, QOL_DESCEND=0, QOL_PICKUP=0, QOL_USE=0, QOL_COYOTE=0, QOL_INERTIA=0, QOL_SWING=0)

# (start, end_exclusive, what)
ALLOWED = [
    (0x879D, 0x87A4, 'A hook: CALL qol_rope_scan / JR NZ / JR'),
    (0x87A4, 0x87AD, 'I1 free (old rope test)'), (0x87B2, 0x87BC, 'I2 free (old rope test)'),
    (0x8692, 0x8707, 'F1 free'), (0x6509, 0x6537, 'F2 free'), (0x67B9, 0x67D6, 'window tail + F3'),
    (0xA21E, 0xA22B, 'F4 free'), (0xE842, 0xE851, 'F5 free'),
    (0x8EA3, 0x8EAA, 'I3 free'), (0x9293, 0x929A, 'I4 free'),
    (0x964F, 0x9669, 'B: descend test'), (0x969D, 0x96A0, 'B: CALL qol_desc_fix'),
    (0x9A48, 0x9A49, 'C'), (0x9A51, 0x9A52, 'C'), (0x9A5C, 0x9A5D, 'C'), (0x9A65, 0x9A66, 'C'),
    (0x5F11, 0x5F13, 'D'), (0x5FD6, 0x5FD8, 'D'), (0x6422, 0x6424, 'D'), (0x64A7, 0x64A9, 'D'),
    (0x828D, 0x8292, 'E: walk-off'), (0xEAD4, 0xEADB, 'E: air / ground ticks'),
    (0x8EAE, 0x8EAF, 'F'), (0x8F6E, 0x8F6F, 'F'),
    (0x888E, 0x8891, 'G: no damping'), (0x8A1A, 0x8A20, 'G: initial phase'),
    (0x8B14, 0x8B16, 'G: pump cap'), (0x89E1, 0x89E3, 'G: speed threshold'),
]


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    o = Z80Snapshot(ORIGINAL)
    dump = open(os.path.join(ROOT, 'original', 'Sir_Fred_RAM_48K_verified.bin'), 'rb').read()
    check(bytes(o.ram) == dump, 'original .z80 unpacks to the verified RAM dump')

    q = Z80Snapshot(QOL)
    regs = q.registers()
    check(q.version == 2 and len(q.ram) == 49152, 'QoL snapshot: z80 v2, 48K RAM')
    check(q.header == o.header and q.ext == o.ext, 'QoL snapshot: header identical to original')
    check(regs['PC'] == 0x38 and regs['IM'] == 1 and regs['SP'] == 0xFFED, 'registers PC=0038 IM1 SP=FFED')

    off = build_qol(**OFF)
    check(open(off, 'rb').read() == open(ORIGINAL, 'rb').read(), 'all features off == original file')

    for feat in OFF:
        defs = dict(OFF)
        defs[feat] = 1
        p = build_qol(**defs)
        s = Z80Snapshot(p)
        n = sum(1 for a, b in zip(s.ram, o.ram) if a != b)
        check(n > 0 or feat == 'QOL_INERTIA', '%s alone builds (%d bytes changed)' % (feat, n))

    full = build_qol(QOL_INERTIA=1, TURN_SPEED=12)
    s = Z80Snapshot(full)
    bad = []
    for i, (a, b) in enumerate(zip(s.ram, o.ram)):
        if a != b:
            addr = 0x4000 + i
            if not any(lo <= addr < hi for lo, hi, _ in ALLOWED):
                bad.append(addr)
    check(not bad, 'all changes inside declared sites (%s)' % ', '.join('%04X' % a for a in bad[:8]))
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
