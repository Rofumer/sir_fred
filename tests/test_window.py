"""The compacted window-builder tail (patches/window_compact.asm) must give
exactly the same result as the original for every Fred position.

Calls $8751 directly in the emulator for all X (0..255) and Y (0..191) on
the original and on the QoL image and compares A, F, BC, DE, HL, IX, SP and
the window bytes $8419..$842E.
"""
import sys

from common import ORIGINAL, QOL, start_game, FRED_X, FRED_Y

SENTINEL = 0x0001          # return address; never executed (trace stops there)
REGS = {'A': 0, 'F': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'H': 6, 'L': 7,
        'IXh': 8, 'IXl': 9, 'SP': 12}


def call_window(e, x, y):
    e.poke(FRED_X, x)
    e.poke(FRED_Y, y)
    reg = e.reg
    sp = 0xFF80
    sp -= 2
    e.poke(sp, SENTINEL & 0xFF)
    e.poke(sp + 1, SENTINEL >> 8)
    reg[12] = sp
    reg[24] = 0x8751
    e.sim.trace(0x8751, SENTINEL, 100000, 0, 0, None, None, e.keyboard, None, None)
    assert reg[24] == SENTINEL, 'did not return'
    out = {k: reg[i] for k, i in REGS.items()}
    out['win'] = bytes(e.mem[0x8419:0x842F])
    return out


def run():
    eo, so = start_game(ORIGINAL)
    eq, sq = start_game(QOL)
    bad = 0
    n = 0
    for y in range(0, 192):
        for x in range(0, 256):
            eo.load_state(so)
            eq.load_state(sq)
            a = call_window(eo, x, y)
            b = call_window(eq, x, y)
            n += 1
            if a != b:
                bad += 1
                if bad < 5:
                    print('MISMATCH x=%d y=%d\n  orig %s\n  qol  %s' % (x, y, a, b))
    print('window builder: %d positions compared, %d mismatches' % (n, bad))
    return bad == 0


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
