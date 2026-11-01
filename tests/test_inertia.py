"""Patch F (turn-around skid threshold), off by default.

Fred runs right for 20 frames, then LEFT is held; we count frames until X
starts to decrease. A bigger TURN_SPEED must make him turn sooner; the
default TURN_SPEED=8 build must equal the original.
"""
import sys

from common import ORIGINAL, FRED_X, build_qol, start_game


def turn_frames(path):
    e, _ = start_game(path)
    e.press('P')
    e.run_frames(20)
    e.release()
    e.press('O')
    best = e.peek(FRED_X)
    for f in range(300):
        e.run_frames(1)
        x = e.peek(FRED_X)
        if x < best:
            return f
        best = max(best, x)
    return None


ONLY_F = dict(QOL_ROPE=0, QOL_DESCEND=0, QOL_PICKUP=0, QOL_USE=0, QOL_COYOTE=0, QOL_INERTIA=1)


def run():
    o = turn_frames(ORIGINAL)
    d = turn_frames(build_qol(TURN_SPEED=8, **ONLY_F))
    q = turn_frames(build_qol(TURN_SPEED=32, **ONLY_F))
    print('  frames until Fred turns: original %s, TURN_SPEED=8 %s, TURN_SPEED=32 %s' % (o, d, q))
    ok = d == o and q is not None and o is not None and q < o
    print(('PASS ' if ok else 'FAIL ') + 'TURN_SPEED=8 == original, 32 turns sooner')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
