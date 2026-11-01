"""Locate unreachable byte ranges directly after unconditional control
transfers (JP/JR/RET/JP (HL)) in executed code.

A range [n, m) is reported when:
  * n follows an executed unconditional JP/JR/RET,
  * no byte in [n, m) was executed / read / written in the recorded sessions,
  * no 16-bit word anywhere in RAM points into [n, m),
  * no relative jump (JR/DJNZ) anywhere targets [n, m),
  * m is the next address that is executed or referenced.
These are candidates only; each must still be read by a human.

usage: python tools/deadcode.py build/mem_*.pkl
"""
import os
import pickle
import sys

from skoolkit.traceutils import disassemble

HERE = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(HERE, '..', 'original', 'Sir_Fred_RAM_48K_verified.bin'), 'rb').read()
mem = [0] * 0x4000 + list(d)

touched = bytearray(65536)
execd = bytearray(65536)
for f in sys.argv[1:]:
    m = pickle.load(open(f, 'rb'))
    for a in range(0x4000, 0x10000):
        if m['r'][a] or m['w'][a] or m['x'][a]:
            touched[a] = 1
        if m['x'][a]:
            execd[a] = 1

refd = bytearray(65536)
for i in range(len(d) - 1):
    refd[d[i] | d[i + 1] << 8] = 1
    if d[i] in (0x18, 0x20, 0x28, 0x30, 0x38, 0x10):
        refd[(0x4000 + i + 2 + (d[i + 1] - 256 if d[i + 1] > 127 else d[i + 1])) & 0xFFFF] = 1

UNCOND = ('JP $', 'JR $', 'RET', 'JP (HL)', 'JP (IX)', 'JP (IY)', 'RETI', 'RETN')
found = []
for a in range(0x5B00, 0x10000):
    if not execd[a]:
        continue
    text, ln = disassemble(mem, a, '$', '02X', '04X')[:2]
    if text.startswith(UNCOND) and text not in ('RET NZ', 'RET Z') and not text.startswith('RET ') :
        n = a + ln
        if n >= 0x10000 or execd[n] or touched[n] or refd[n]:
            continue
        m = n
        while m < 0x10000 and not (execd[m] or touched[m] or refd[m]):
            m += 1
        if m - n >= 6:
            found.append((n, m))
for n, m in sorted(set(found)):
    print('%04X-%04X %4d bytes  after: %s' % (n, m - 1, m - n,
          disassemble(mem, n, '$', '02X', '04X')[0]))
print('total', sum(m - n for n, m in set(found)))
