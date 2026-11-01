"""Build Sir_Fred_QoL.z80 from the original snapshot.

  1. unpack original/SirFred.z80 and check it against the verified RAM dump
  2. assemble patches/main.asm with sjasmplus, feature switches from qol.cfg
  3. write build/Sir_Fred_QoL.z80 with the ORIGINAL header (registers, IM,
     border, paging fields) and the patched RAM
  4. print every changed byte range (build/patch_report.txt)

usage: python tools/build.py [--cfg qol.cfg] [--out build/Sir_Fred_QoL.z80] [-D NAME=VAL ...]
"""
import argparse
import configparser
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from z80snap import Z80Snapshot  # noqa: E402

ORIG_Z80 = os.path.join(ROOT, 'original', 'SirFred.z80')
ORIG_BIN = os.path.join(ROOT, 'original', 'Sir_Fred_RAM_48K_verified.bin')
ORIG_SHA1 = '2030d767b6f9539d925de8b0596091930d356d9c'
SJASM = os.path.join(HERE, 'bin', 'sjasmplus.exe' if os.name == 'nt' else 'sjasmplus')


def read_cfg(path):
    cp = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    cp.optionxform = str
    cp.read(path, encoding='utf-8')
    defs = {}
    for sec in cp.sections():
        for k, v in cp.items(sec):
            defs[k] = int(v, 0)
    return defs


def diff_ranges(a, b, base=0x4000):
    out = []
    i = 0
    n = len(a)
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and (a[j] != b[j] or (j + 1 < n and a[j + 1] != b[j + 1] and j - i < 64)):
                j += 1
            out.append((base + i, a[i:j], b[i:j]))
            i = j
        else:
            i += 1
    return out


def build(cfg, out, extra_defs=None, quiet=False):
    raw = open(ORIG_Z80, 'rb').read()
    if hashlib.sha1(raw).hexdigest() != ORIG_SHA1:
        raise SystemExit('original snapshot checksum mismatch')
    snap = Z80Snapshot(ORIG_Z80)
    if bytes(snap.ram) != open(ORIG_BIN, 'rb').read():
        raise SystemExit('snapshot RAM differs from verified dump')

    defs = read_cfg(cfg)
    defs.update(extra_defs or {})
    builddir = os.path.join(ROOT, 'build')
    os.makedirs(builddir, exist_ok=True)
    # main build -> build/qol.{lst,sym}, build/patch_report.txt;
    # variants (tests) -> build/<name>.{lst,sym,txt} so they never clobber it
    stem = os.path.splitext(os.path.basename(out))[0]
    main = stem == 'Sir_Fred_QoL'
    artdir = builddir if main else os.path.dirname(os.path.abspath(out))
    art = (lambda ext: os.path.join(artdir, ('qol' if main else stem) + ext))
    report = os.path.join(builddir, 'patch_report.txt') if main else art('.txt')
    binpath = os.path.join(builddir, 'patched_ram.bin')
    if os.path.exists(binpath):
        os.remove(binpath)
    cmd = [SJASM, '--nologo', '--msg=war', '--lst=' + art('.lst'), '--sym=' + art('.sym')]
    cmd += ['-D%s=%d' % kv for kv in sorted(defs.items())]
    cmd.append('main.asm')
    r = subprocess.run(cmd, cwd=os.path.join(ROOT, 'patches'), capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(binpath):
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit('assembly failed')
    ram = open(binpath, 'rb').read()
    assert len(ram) == 49152

    snap.save(out, ram)
    chk = Z80Snapshot(out)
    assert bytes(chk.ram) == ram, 'snapshot round trip failed'
    assert chk.header == snap.header and chk.ext == snap.ext, 'header changed'

    rep = ['config: ' + ', '.join('%s=%d' % kv for kv in sorted(defs.items())),
           'output: %s (%d bytes)' % (os.path.relpath(out, ROOT), os.path.getsize(out))]
    total = 0
    for addr, old, new in diff_ranges(snap.ram, ram):
        total += len(new)
        rep.append('%04X-%04X %3d bytes  old %s' % (addr, addr + len(new) - 1, len(new), old.hex(' ')))
        rep.append('%s new %s' % (' ' * 20, new.hex(' ')))
    rep.append('changed bytes: %d' % total)
    open(report, 'w').write('\n'.join(rep) + '\n')
    if not quiet:
        print('\n'.join(rep))
    return ram


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cfg', default=os.path.join(ROOT, 'qol.cfg'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'build', 'Sir_Fred_QoL.z80'))
    ap.add_argument('-D', action='append', default=[], help='override, e.g. -D ROPE_FWD=6')
    a = ap.parse_args()
    extra = {}
    for d in a.D:
        k, v = d.split('=')
        extra[k] = int(v, 0)
    build(a.cfg, a.out, extra)


if __name__ == '__main__':
    main()
