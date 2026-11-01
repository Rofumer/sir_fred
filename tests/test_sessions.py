"""Whole-game checks with recorded play sessions (tests/sessions/*.txt).

1. Free space really is free: the ORIGINAL game with every free block that
   is free in the original (F1, F2, F4, F5, I3, I4) overwritten with RST 0
   ($C7) must play every session exactly like the untouched original
   (Fred's position every frame and the final RAM outside those blocks).
   F3 / I1 / I2 only become free through their own patches and are covered
   by test_window.py and test_rope.py.
2. The QoL build survives the sessions: no reset (PC never in 0000..0037),
   frames keep counting, Fred keeps moving.
3. Goal-driven route (tests/make_sessions.py logic) on the QoL build:
   pit -> vine -> ledge -> hill -> room 3 (water) - room changes, climbing
   and swimming still work.
"""
import os
import sys

from common import ORIGINAL, QOL, HERE, FRED_X, FRED_Y, Emu

sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from emu import run_script  # noqa: E402

FREE_IN_ORIGINAL = [(0x8692, 0x8707), (0x6509, 0x6537), (0xA21E, 0xA22B),
                    (0xE842, 0xE851), (0x8EA3, 0x8EAA), (0x9293, 0x929A)]
SESSIONS = ['explore1.txt', 'explore2.txt']


def trajectory(e, script):
    tr = []
    resets = []

    def step(em):
        tr.append((em.peek(FRED_X), em.peek(FRED_Y)))
        if em.reg[24] < 0x38:
            resets.append(em.frame)
    run_script(e, os.path.join(HERE, 'sessions', script), step)
    return tr, resets


def masked_ram(e):
    ram = bytearray(e.ram())
    for lo, hi in FREE_IN_ORIGINAL:
        ram[lo - 0x4000:hi - 0x4000] = bytes(hi - lo)
    return bytes(ram)


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    for s in SESSIONS:
        a = Emu(ORIGINAL)
        b = Emu(ORIGINAL)
        for lo, hi in FREE_IN_ORIGINAL:
            for addr in range(lo, hi):
                b.poke(addr, 0xC7)
        ta, _ = trajectory(a, s)
        tb, rb = trajectory(b, s)
        check(ta == tb and masked_ram(a) == masked_ram(b) and not rb,
              '%s: original with poisoned free space plays identically (%d frames)' % (s, len(ta)))

        q = Emu(QOL)
        tq, rq = trajectory(q, s)
        moved = len(set(tq)) > 20
        check(not rq and moved,
              '%s: QoL build runs without reset, Fred moves (%d distinct positions)' % (s, len(set(tq))))

    import make_sessions
    e = make_sessions.explore2(QOL, save=False)
    # explore2 ends in the water room: Fred swims near the surface (Y < 70)
    # and the room-3 water attribute (cyan paper) fills the middle of the screen
    attr = e.peek(0x5800 + 12 * 32 + 10)
    check((attr >> 3) & 7 == 5, 'QoL: goal-driven route reaches the water room (room changes, vine, swimming)')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
