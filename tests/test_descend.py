"""Patch B (climb down onto a vine) in room 1: vine top cell $44 at map
(10,19), vine below it. Fred stands on the right-hand ledge (Y=64), presses
DOWN, and we follow the whole descent animation.
  * original window (facing left) must be X 152..158
  * QoL window must contain it and be wider
  * after every successful descent Fred must end on the vine (ROPE_ON=1)
    at the same place as in the original
  * DESC_TOL=0 build == original
"""
import sys

from common import ORIGINAL, QOL, ROPE_ON, FRED_X, FRED_Y, build_qol, place, start_game


def descend(path, xs=range(144, 176, 2), facing=0):
    e, base = start_game(path)
    res = {}
    for x in xs:
        e.load_state(base)
        place(e, x, facing=facing)
        e.run_frames(3)
        e.press('A')
        e.run_frames(4)
        e.release()
        started = False
        for _ in range(200):
            e.run_frames(1)
            if e.peek(0x923C):
                started = True
            if started and e.peek(0x923C) == 0:
                e.run_frames(5)
                break
        if started:
            res[x] = (e.peek(ROPE_ON), e.peek(FRED_X), e.peek(FRED_Y))
    return res


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    o = descend(ORIGINAL)
    q = descend(QOL)
    s = descend(build_qol(DESC_TOL=0))
    print('  original:', o)
    print('  QoL     :', q)
    check(sorted(o) == [152, 154, 156, 158], 'original window X 152..158')
    check(set(o) <= set(q) and len(q) > len(o), 'QoL window wider')
    check(all(v[0] == 1 for v in q.values()), 'every QoL descent ends on the vine')
    check(set(q.values()) == set(o.values()), 'end position identical to original')
    check(s == o, 'DESC_TOL=0 identical to original')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
