"""Find CALL/JP/LD references to an address in the RAM image.
usage: python tools/xref.py ADDR [ADDR...]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(HERE, '..', 'original', 'Sir_Fred_RAM_48K_verified.bin'), 'rb').read()
OPS = {0xCD: 'CALL', 0xC3: 'JP', 0xC4: 'CALL NZ', 0xCC: 'CALL Z', 0xD4: 'CALL NC', 0xDC: 'CALL C',
       0xC2: 'JP NZ', 0xCA: 'JP Z', 0xD2: 'JP NC', 0xDA: 'JP C', 0x21: 'LD HL', 0x11: 'LD DE', 0x01: 'LD BC',
       0x22: 'LD (),HL', 0x2A: 'LD HL,()', 0x32: 'LD (),A', 0x3A: 'LD A,()'}
for arg in sys.argv[1:]:
    t = int(arg, 16)
    hits = []
    for i in range(len(d) - 2):
        if d[i + 1] == t & 255 and d[i + 2] == t >> 8 and d[i] in OPS:
            hits.append('%04X %s' % (0x4000 + i, OPS[d[i]]))
        if i + 3 < len(d) and d[i] in (0xDD, 0xFD, 0xED) and d[i + 2] == t & 255 and d[i + 3] == t >> 8:
            hits.append('%04X %02X %02X' % (0x4000 + i, d[i], d[i + 1]))
    # relative jumps
    for i in range(len(d) - 1):
        if d[i] in (0x18, 0x20, 0x28, 0x30, 0x38, 0x10):
            tgt = 0x4000 + i + 2 + (d[i + 1] - 256 if d[i + 1] > 127 else d[i + 1])
            if tgt == t:
                hits.append('%04X JR/DJNZ' % (0x4000 + i))
    print('%04X: %s' % (t, ', '.join(hits)))
