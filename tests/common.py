"""Shared helpers for the behavioural tests (headless emulator)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

from emu import Emu  # noqa: E402

ORIGINAL = os.path.join(ROOT, 'original', 'SirFred.z80')
QOL = os.path.join(ROOT, 'build', 'Sir_Fred_QoL.z80')

FRED_X, FRED_Y, FRED_OLDX, FRED_OLDY = 0x8496, 0x8497, 0x8498, 0x8499
FRED_SPEED, FRED_AIR, FRED_DIR = 0x849B, 0x849C, 0x84A7
ROPE_ON = 0x8719
ROOM_MAP = 0xB3B0


def start_game(path):
    """Boot the snapshot, select '0 START GAME' and wait until Fred stands
    in the first room. Returns (emu, saved_state)."""
    e = Emu(path)
    e.run_frames(10)
    e.press('0')
    e.run_frames(5)
    e.release()
    e.run_frames(150)
    return e, e.save_state()


def place(e, x, y=None, facing=None):
    e.poke(FRED_X, x)
    e.poke(FRED_OLDX, x)
    if y is not None:
        e.poke(FRED_Y, y)
        e.poke(FRED_OLDY, y)
    if facing is not None:
        e.poke(FRED_DIR, facing)


def map_cells(e, value):
    return sorted((r, c) for r in range(20) for c in range(32) if e.peek(ROOM_MAP + r * 32 + c) == value)


def build_qol(**defs):
    """Build a variant snapshot into build/test_<hash>.z80 and return its path."""
    import build
    tag = '_'.join('%s%d' % kv for kv in sorted(defs.items())) or 'default'
    os.makedirs(os.path.join(ROOT, 'build', 'variants'), exist_ok=True)
    out = os.path.join(ROOT, 'build', 'variants', 'test_%s.z80' % tag)
    build.build(os.path.join(ROOT, 'qol.cfg'), out, defs, quiet=True)
    return out


def walk_to(e, target, max_taps=200):
    """Tap left/right until Fred's X is within 1px of target (no pokes)."""
    for _ in range(max_taps):
        x = e.peek(FRED_X)
        if abs(x - target) <= 1:
            return True
        k = 'P' if target > x else 'O'
        e.press(k)
        e.run_frames(1)
        e.release()
        e.run_frames(14)
    return False
