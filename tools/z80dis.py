"""Quick Z80 disassembler for the Sir Fred RAM image.

usage: python tools/dis.py START END [image.bin]
Marks lines executed during the recorded gameplay trace with '*'.
"""
import os
import pickle
import sys

from skoolkit.traceutils import disassemble

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mem(path=None):
    path = path or os.path.join(HERE, '..', 'original', 'Sir_Fred_RAM_48K_verified.bin')
    d = open(path, 'rb').read()
    return [0] * 0x4000 + list(d)


def dis(mem, start, end, ex=None):
    out = []
    a = start
    while a < end:
        text, length = disassemble(mem, a, '$', '02X', '04X')[:2]
        length = max(1, length)
        raw = ' '.join('%02X' % mem[(a + i) & 0xFFFF] for i in range(length))
        mark = '*' if ex and a in ex else ' '
        out.append('%04X %s %-12s %s' % (a, mark, raw, text))
        a += length
    return out


if __name__ == '__main__':
    s = int(sys.argv[1], 16)
    e = int(sys.argv[2], 16)
    mem = load_mem(sys.argv[3] if len(sys.argv) > 3 else None)
    exf = os.path.join(HERE, '..', 'build', 'exmap.pkl')
    ex = pickle.load(open(exf, 'rb')) if os.path.exists(exf) else None
    print('\n'.join(dis(mem, s, e, ex)))
