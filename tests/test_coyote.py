"""Patch E (coyote time) in room 2: Fred walks left off the high ledge.

The walk-off is detected by FRED_AIR becoming $20 (set only by the
walk-off routine 828D). f frames later the jump key is pressed; we check
whether a jump starts (JUMP_RISING=1) before Fred lands.
  * original: never (jump key ignored in the air)
  * QoL: works for small f, stops working after COYOTE_TICKS game ticks
  * coyote jump keeps the momentum of a ledge jump (speed not divided twice)
  * QOL_COYOTE=0 build == original
"""
import sys

from common import ORIGINAL, QOL, FRED_AIR, FRED_SPEED, build_qol, start_game

JUMP_RISING = 0x8432


def to_ledge_edge(path):
    e, _ = start_game(path)
    e.press('O')
    e.run_frames(68)                     # into room 2 (X=224, Y=64)
    for _ in range(600):
        e.run_frames(1)
        if e.peek(FRED_AIR) == 0x20:
            break
    else:
        raise RuntimeError('no walk-off')
    e.release()
    return e, e.save_state()


def jump_after(path, delays):
    e, base = to_ledge_edge(path)
    out = {}
    for f in delays:
        e.load_state(base)
        e.run_frames(f)
        e.press('Q')
        jumped = None
        for _ in range(60):
            e.run_frames(1)
            if e.peek(JUMP_RISING):
                jumped = e.peek(FRED_SPEED)
                break
            if e.peek(FRED_AIR) == 0:
                break
        e.release()
        out[f] = jumped
    return out


def run():
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(('PASS ' if cond else 'FAIL ') + msg)
        ok = ok and cond

    delays = list(range(0, 20))
    o = jump_after(ORIGINAL, delays)
    q = jump_after(QOL, delays)
    s = jump_after(build_qol(QOL_COYOTE=0), delays)
    q4 = jump_after(build_qol(COYOTE_TICKS=12), delays)
    fmt = lambda d: ' '.join('%d:%s' % (k, '-' if v is None else v) for k, v in d.items())
    print('  original      ', fmt(o))
    print('  QoL (6 ticks) ', fmt(q))
    print('  QoL (12 ticks)', fmt(q4))
    ok_q = [f for f, v in q.items() if v is not None]
    ok_q4 = [f for f, v in q4.items() if v is not None]
    check(all(v is None for v in o.values()), 'original: no jump after walking off')
    check(len(ok_q) > 0 and ok_q == list(range(len(ok_q))), 'QoL: jump possible right after walk-off')
    check(len(ok_q) < len(delays), 'QoL: window closes again')
    check(len(ok_q4) > len(ok_q), 'COYOTE_TICKS=12 gives a longer window')
    check(s == o, 'QOL_COYOTE=0 identical to original')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
