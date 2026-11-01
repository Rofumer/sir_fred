"""Patch A (rope grab) behaviour in room 1 (rope at map column 13).

For every start X (step 2) and both facings Fred jumps straight up; we
record whether he grabs the rope and where he is snapped to.
  * original window must be X 88..94 (right) / 104..110 (left)
  * QoL window must contain the original one and be wider
  * QoL built with ROPE_FWD=0, ROPE_BACK=0, ROPE_ROWS=1 == original
  * snap position after the grab is the same as in the original
  * a wall between Fred and the rope blocks the grab (built with FWD=8)
"""
import sys

from common import (ORIGINAL, QOL, ROOM_MAP, ROPE_ON, FRED_X, FRED_Y,
                    build_qol, place, start_game)


def grab_window(path, xs=range(64, 136, 2), walls=()):
    e, base = start_game(path)
    res = {}
    for facing in (1, 0):
        hits = {}
        for x in xs:
            e.load_state(base)
            place(e, x, facing=facing)
            for r, c in walls:
                e.poke(ROOM_MAP + r * 32 + c, 1)
            e.run_frames(3)
            e.press('Q')
            for _ in range(40):
                e.run_frames(1)
                if e.peek(ROPE_ON):
                    hits[x] = (e.peek(FRED_X), e.peek(FRED_Y))
                    break
            e.release()
        res[facing] = hits
    return res


def natural_grabs(path, holds=range(1, 41)):
    """No pokes: hold RIGHT for k frames, let inertia stop Fred, jump."""
    e, base = start_game(path)
    hits = []
    for k in holds:
        e.load_state(base)
        e.press('P')
        e.run_frames(k)
        e.release()
        for _ in range(200):
            x = e.peek(FRED_X)
            e.run_frames(4)
            if e.peek(FRED_X) == x or e.peek(ROPE_ON):
                break
        if e.peek(ROPE_ON):
            continue                    # caught it while walking - not a jump test
        e.press('Q')
        for _ in range(40):
            e.run_frames(1)
            if e.peek(ROPE_ON):
                hits.append(k)
                break
        e.release()
    return hits


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    orig = grab_window(ORIGINAL)
    qol = grab_window(QOL)
    same = grab_window(build_qol(ROPE_FWD=0, ROPE_BACK=0, ROPE_ROWS=1))
    for f, name in ((1, 'right'), (0, 'left')):
        o, q = sorted(orig[f]), sorted(qol[f])
        print('  facing %-5s original %s' % (name, o))
        print('  facing %-5s QoL      %s' % (name, q))
        check(set(o) <= set(q) and len(q) > len(o), 'QoL window wider than original (%s)' % name)
        check(orig[f] == same[f], 'FWD=BACK=0 ROWS=1 identical to original (%s)' % name)
        check(len(set(q_ for q_ in qol[f].values())) == 1 and
              set(qol[f].values()) == set(orig[f].values()), 'snap position unchanged (%s)' % name)
    check(sorted(orig[1]) == [88, 90, 92, 94] and sorted(orig[0]) == [104, 106, 108, 110],
          'original window as documented')

    no = natural_grabs(ORIGINAL)
    nq = natural_grabs(QOL)
    print('  natural approach (hold RIGHT k frames, stop, jump): original %d/40, QoL %d/40'
          % (len(no), len(nq)))
    check(len(nq) > len(no), 'more natural approaches end on the rope')

    wide = build_qol(ROPE_FWD=8)
    wall_r = [(r, 12) for r in range(5, 10)]
    wall_l = [(r, 14) for r in range(5, 10)]
    a = grab_window(wide, xs=[80])[1]
    b = grab_window(wide, xs=[80], walls=wall_r)[1]
    c = grab_window(wide, xs=[118])[0]
    d = grab_window(wide, xs=[118], walls=wall_l)[0]
    check(80 in a and 80 not in b, 'wall at column 12 blocks a right-facing grab')
    check(118 in c and 118 not in d, 'wall at column 14 blocks a left-facing grab')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
