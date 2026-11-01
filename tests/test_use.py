"""Patch D (item USE tolerance) - routine-level test.

No item puzzle position is reached by the recorded sessions, so this test
works on the routines themselves (it does NOT prove a particular puzzle):
  * the four patched call sites now call qol_use_box, all other callers of
    B78F (enemies, hazards) still call B78F
  * qol_use_box returns B78F's box grown by USE_TOL on every side, BC kept
  * with B773 an object USE_TOL-1 px beyond Fred's original box is a hit
    for the QoL box and a miss for the original box; USE_TOL+1 px is a miss
"""
import re
import sys

from common import QOL, ROOT, FRED_X, FRED_Y, start_game

SENTINEL = 0x0001
USE_SITES = [0x5F10, 0x5FD5, 0x6421, 0x64A6]
OTHER_SITES = [0xB7E2, 0xBCBF, 0xCB6F, 0xCB92, 0xCD6F, 0xED54, 0xF0AF]


def sym(name):
    for line in open(ROOT + '/build/qol.sym'):
        m = re.match(r'(\S+): EQU 0x([0-9A-F]+)', line)
        if m and m.group(1) == name:
            return int(m.group(2), 16)
    raise KeyError(name)


def call(e, addr, regs=None):
    r = e.reg
    for i, v in (regs or {}).items():
        r[i] = v
    sp = 0xFF80 - 2
    e.poke(sp, SENTINEL & 0xFF)
    e.poke(sp + 1, SENTINEL >> 8)
    r[12] = sp
    r[24] = addr
    e.sim.trace(addr, SENTINEL, 100000, 0, 0, None, None, e.keyboard, None, None)
    assert r[24] == SENTINEL
    return {'BC': r[2] << 8 | r[3], 'DE': r[4] << 8 | r[5], 'HL': r[6] << 8 | r[7], 'F': r[1]}


def overlap(e, fred, obj):
    """B773 with Fred box (HL,DE) and object box (HL',DE'); carry = hit."""
    r = e.reg
    r[6], r[7] = fred['HL'] >> 8, fred['HL'] & 0xFF
    r[4], r[5] = fred['DE'] >> 8, fred['DE'] & 0xFF
    # primed registers (skoolkit.simutils.REGISTERS): ^D=20 ^E=21 ^H=22 ^L=23
    (oy, ox), (oh, ow) = obj
    r[22], r[23] = oy, ox
    r[20], r[21] = oh, ow
    out = call(e, 0xB773)
    return bool(out['F'] & 1)


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    tol = None
    for line in open(ROOT + '/build/patch_report.txt'):
        m = re.search(r'USE_TOL=(\d+)', line)
        if m:
            tol = int(m.group(1))
    qbox = sym('qol_use_box')
    e, base = start_game(QOL)
    check(all(e.peekw(s + 1) == qbox for s in USE_SITES), 'item-use sites call qol_use_box')
    check(all(e.peek(s) == 0xCD and e.peekw(s + 1) == 0xB78F for s in OTHER_SITES),
          'enemy / hazard sites still call B78F')

    for x, y in ((100, 64), (40, 128)):
        e.load_state(base)
        e.poke(FRED_X, x)
        e.poke(FRED_Y, y)
        o = call(e, 0xB78F, {2: 0x12, 3: 0x34})
        q = call(e, qbox, {2: 0x12, 3: 0x34})
        exp_hl = ((y - tol) << 8) | (x - tol)
        exp_de = o['DE'] + (2 * tol << 8) + 2 * tol
        check(q['HL'] == exp_hl and q['DE'] == exp_de and q['BC'] == 0x1234,
              'box at (%d,%d): orig HL=%04X DE=%04X -> QoL HL=%04X DE=%04X, BC kept'
              % (x, y, o['HL'], o['DE'], q['HL'], q['DE']))
        # object 16x16 to the right of Fred, gap g pixels
        for g, want_q in ((tol - 1, True), (tol + 1, False)):
            obj = ((y, x + 16 + g), (16, 16))
            ho = overlap(e, o, obj)
            hq = overlap(e, q, obj)
            check(not ho and hq == want_q, '  object %dpx right of Fred: original %s, QoL %s'
                  % (g, 'hit' if ho else 'miss', 'hit' if hq else 'miss'))
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
