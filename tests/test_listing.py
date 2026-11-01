"""disassembly/sirfred_core.asm must re-assemble to the original bytes."""
import os
import subprocess
import sys

from common import ROOT

SJ = os.path.join(ROOT, 'tools', 'bin', 'sjasmplus.exe' if os.name == 'nt' else 'sjasmplus')


def run():
    wrap = os.path.join(ROOT, 'build', 'listing_check.asm')
    out = os.path.join(ROOT, 'build', 'listing_check.bin')
    with open(wrap, 'w') as f:
        f.write(' DEVICE ZXSPECTRUM48\n ORG $4000\n')
        f.write(' INCBIN "../original/Sir_Fred_RAM_48K_verified.bin"\n')
        f.write(' INCLUDE "../disassembly/sirfred_core.asm"\n')
        f.write(' SAVEBIN "listing_check.bin", $4000, $C000\n')
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([SJ, '--nologo', '--msg=war', 'listing_check.asm'], cwd=os.path.dirname(wrap),
                       capture_output=True, text=True)
    orig = open(os.path.join(ROOT, 'original', 'Sir_Fred_RAM_48K_verified.bin'), 'rb').read()
    ok = r.returncode == 0 and os.path.exists(out) and open(out, 'rb').read() == orig
    if not ok:
        print(r.stdout[-2000:], r.stderr[-2000:])
        if os.path.exists(out):
            new = open(out, 'rb').read()
            diff = [i + 0x4000 for i in range(len(orig)) if orig[i] != new[i]]
            print('differences at', ['%04X' % a for a in diff[:20]])
    print(('PASS ' if ok else 'FAIL ') + 'annotated listing re-assembles to the original bytes')
    return ok


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
