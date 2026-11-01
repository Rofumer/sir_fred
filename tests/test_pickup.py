"""Patch C (pick-up tolerance) in room 2: one item at X=97, Y=136.

Fred stands on the floor (Y=128) at every X from 60 to 136 and presses the
pick-up key Z; the item is taken when it appears in the inventory
($99A9..$99AC).
  * original: picked up exactly when |X - 97| < 16
  * QoL: |X - 97| < PICK_X (20 by default), i.e. a strictly wider window
  * QOL_PICKUP=0 build == original
"""
import sys

from common import ORIGINAL, QOL, FRED_Y, build_qol, place, start_game

ITEM_X = 97


def to_room2(path):
    e, _ = start_game(path)
    e.press('O')
    e.run_frames(68)
    e.release()
    e.run_frames(60)
    return e, e.save_state()


def pickup_window(path, xs=range(60, 138, 1)):
    e, base = to_room2(path)
    got = []
    for x in xs:
        e.load_state(base)
        place(e, x, y=128, facing=1)
        e.run_frames(20)
        if e.peek(FRED_Y) != 128:
            continue
        e.press('Z')
        e.run_frames(10)
        e.release()
        e.run_frames(10)
        if any(e.peek(0x99A9 + i) for i in range(4)):
            got.append(x)
    return got


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    o = pickup_window(ORIGINAL)
    q = pickup_window(QOL)
    s = pickup_window(build_qol(QOL_PICKUP=0))
    print('  original: X %d..%d (%d positions)' % (min(o), max(o), len(o)))
    print('  QoL     : X %d..%d (%d positions)' % (min(q), max(q), len(q)))
    check(o == [x for x in range(60, 138) if abs(x - ITEM_X) < 16], 'original |dx| < 16')
    check(q == [x for x in range(60, 138) if abs(x - ITEM_X) < 20], 'QoL |dx| < 20')
    check(s == o, 'QOL_PICKUP=0 identical to original')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
