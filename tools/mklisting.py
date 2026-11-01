"""Generate disassembly/sirfred_core.asm: annotated, re-assemblable listing
of the routines documented in docs/REVERSE_ENGINEERING.md.

Every range is emitted as ORG + instructions with labels substituted for
known addresses. tests/test_listing.py assembles the file over the original
image with sjasmplus and requires a byte-identical result.

usage: python tools/mklisting.py
"""
import os
import re

from skoolkit.traceutils import disassemble

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
d = open(os.path.join(ROOT, 'original', 'Sir_Fred_RAM_48K_verified.bin'), 'rb').read()
mem = [0] * 0x4000 + list(d)

# variables / data (EQU)
VARS = {
    0x8496: ('FRED_X', 'Fred X (px, left edge), step 2'),
    0x8497: ('FRED_Y', 'Fred Y (px, top), 64 = floor of room 1'),
    0x8498: ('FRED_OLDX', 'position the sprite is drawn at (erase)'),
    0x8499: ('FRED_OLDY', ''),
    0x849B: ('FRED_SPEED', 'horizontal momentum'),
    0x849C: ('FRED_AIR', 'airborne: 1 jump, $20 walk-off/fall'),
    0x84A7: ('FRED_DIR', '0 left, 1 right'),
    0x8419: ('WIN_YFINE', 'Y & 7 of the last window'),
    0x841A: ('WIN_XFINE', 'X & 7 of the last window'),
    0x841B: ('WINDOW_BUF', '5 rows x 4 cells around Fred'),
    0x8417: ('TUMBLE', 'set after a long fall: no rope grab'),
    0x8418: ('STUN', 'stun counter after hitting a wall fast'),
    0x8430: ('CROUCH', 'shorter jump / lower box'),
    0x8431: ('JUMP_VEL', 'vertical speed, fixed point'),
    0x8432: ('JUMP_RISING', '1 while going up'),
    0x8434: ('JUMP_ACC', 'fraction accumulator for JUMP_VEL'),
    0x8719: ('ROPE_ON', 'hanging on rope / vine'),
    0x871E: ('ROPE_INDEX', 'map cell >> 3'),
    0x871F: ('ROPE_SEG', 'segment Fred holds'),
    0x8723: ('ROPE_TABLE', '7-byte rope entries'),
    0x923A: ('FALL_TICKS', 'ticks falling; $14 = hurt'),
    0x923C: ('DESCEND_ANIM', 'climb-down-onto-vine animation'),
    0x98F7: ('PICK_DEBOUNCE', 'pick-up key repeat counter'),
    0x98FB: ('SWIMMING', 'Fred is in water'),
    0x9981: ('ROOM_ITEMS', 'pointer: items of this room (X,Y,type)*n,$FF'),
    0x99A9: ('INVENTORY', '4 slots'),
    0x99AD: ('INV_SLOT', 'selected slot 0..3'),
    0xB3B0: ('ROOM_MAP', '32x20 collision map'),
    0x5C78: ('FRAMES', 'ROM frame counter'),
}

# (start, end_exclusive, label, title, {addr: comment})
ROUTINES = [
    (0xE966, 0xEB22, 'MAIN_LOOP', 'main game loop and input dispatch', {
        0xE966: 'delay', 0xE9F2: 'SPACE: pause/quit', 0xE9F9: 'Z: pick up / cycle inventory',
        0xEAC3: 'airborne? -> AIR_HANDLER', 0xEAD7: 'ground tick starts here',
        0xEADB: 'M (fire): use item', 0xEB00: 'A: down', 0xEB06: 'Q: up / jump',
        0xEB0C: 'O: left', 0xEB12: 'P: right', 0xEB18: 'no key: idle'}),
    (0x9FBE, 0x9FE8, 'KEY_STUBS', 'redefinable key tests (LD A,row / IN / AND mask), Z = pressed', {
        0x9FBE: 'Z  pick up', 0x9FC5: 'P  right', 0x9FCC: 'O  left', 0x9FD3: 'M  fire',
        0x9FDA: 'A  down', 0x9FE1: 'Q  up / jump'}),
    (0x8751, 0x8799, 'WINDOW', 'build 4x5 cell window (spaghetti part 1)', {
        0x8751: 'BC = (X, Y)', 0x8754: 'alternative entry with BC preset (executes ADD A,H)',
        0x877A: '5 rows', 0x8782: '4 cells per row'}),
    (0x67B2, 0x67FE, 'WINDOW2', 'cell window builder, part 2 (jumps back and forth with part 1)', {
        0x67B9: 'exit: HL = map ptr (row Y/8-1, col X/8-1), IX = WINDOW_BUF'}),
    (0x879A, 0x881C, 'ROPE_GRAB', 'airborne rope / vine grab test (one cell!) and snap onto rope', {
        0x87A8: 'self-modifies the displacement at 87B4',
        0x87B2: 'cell row Y/8, column (X+16)/8 or X/8', 0x87B6: '(cell & $C5) == 4: grabbable',
        0x87BC: 'grab: ROPE_ON = 1', 0x87E2: 'find segment for Fred Y',
        0x8803: 'snap Fred onto the rope'}),
    (0x828D, 0x82C9, 'WALK_OFF', 'walk off a ledge: start falling, nudge X 6-8px', {}),
    (0x82F7, 0x8334, 'JUMP_START', 'start a jump: JUMP_VEL=$80, speed/4', {}),
    (0x8377, 0x83C3, 'JUMP_PHYS', 'jump/fall vertical physics (2px steps)', {
        0x8383: 'rising: v -= v/4, apex below $20', 0x83A5: 'falling: v += v/4+4'}),
    (0x8E3A, 0x8E68, 'H_IDLE', 'no key pressed (on ground)', {}),
    (0x8E68, 0x8E83, 'H_RIGHT', 'P: walk right', {0x8EAA: 'speed >= 8: keep sliding'}),
    (0x8EAA, 0x8F28, 'H_RIGHT2', 'walk right (cont.)', {0x8EAD: 'turn-around skid threshold'}),
    (0x8F28, 0x8FE3, 'H_LEFT', 'O: walk left', {0x8F6D: 'turn-around skid threshold'}),
    (0x8FFB, 0x9071, 'H_DOWN', 'A: down (rope: climb down; ledge: climb onto vine)', {}),
    (0x9072, 0x90F5, 'H_UP', 'Q: up (rope: climb; ground: jump)', {0x90E5: 'jump from ground'}),
    (0x90F5, 0x9128, 'AIR_HANDLER', 'per-tick airborne movement', {}),
    (0x919F, 0x9238, 'AIR2', 'airborne: wall test, rope grab, landing', {
        0x91AC: 'rope grab test every airborne tick'}),
    (0x929A, 0x92A0, 'FLOOR_TEST', 'floor under Fred? result $20 = none', {}),
    (0x92E9, 0x9339, 'WALL_TEST', 'wall ahead (cells column 3 / 0 of window), carry = blocked', {}),
    (0x964F, 0x96B1, 'DESCEND', 'DOWN at ledge: climb onto vine (one cell = $44!) + first animation step', {
        0x9653: 'feet row, column X/8 (left) ...', 0x965C: '... or (X+16)/8 (right)',
        0x9689: 'animation step 1: turn round, snap X to the cell grid'}),
    (0x99AE, 0x99DB, 'PICK_KEY', 'Z: pick up an item or cycle the inventory slot', {}),
    (0x99DB, 0x9A73, 'PICK_UP', 'find an item overlapping Fred; swap with selected slot', {
        0x9A32: 'proximity: |dX| < 16, dY -15..+23'}),
    (0xB773, 0xB7B4, 'BOX_TEST', 'rectangle overlap (HL,DE vs HL\',DE\'); B78F = Fred box', {
        0xB78F: 'FRED_BOX: HL=(X,Y) D=24 E=16; airborne D=18'}),
    (0x64D4, 0x6509, 'RESET_STATE', 'clear Fred / room state', {}),
    (0x6509, 0x6533, 'DEAD_DISPATCH', 'DEAD CODE: stale copy of the input dispatcher (no references) - QoL free block F2', {}),
]


def labels_map():
    m = {a: n for a, (n, _) in VARS.items()}
    for s, _, lab, _, _ in ROUTINES:
        m.setdefault(s, lab)
    m.update({0x8206: 'TICK_END', 0x7FFF: 'REDRAW_FRED', 0x80F1: 'DELAY', 0xCC6F: 'JUMP_SOUND',
              0x8188: 'BUMP_WALL', 0x87AD: 'ROPE_NONE', 0x9669: 'DESCEND_ANIM_STEP'})
    return m


def main():
    labs = labels_map()
    out = ['; Sir Fred (Mikro-Gen re-release) - annotated core routines.',
           '; Generated by tools/mklisting.py from original/Sir_Fred_RAM_48K_verified.bin.',
           '; Assembles (sjasmplus) to exactly the original bytes: tests/test_listing.py.',
           '']
    for a, (n, c) in sorted(VARS.items()):
        out.append('%-16s EQU $%04X%s' % (n, a, ('    ; ' + c) if c else ''))
    out.append('%-16s EQU $%04X' % ('TICK_END', 0x8206))
    for a, n in sorted(labs.items()):
        if a not in VARS and n in ('REDRAW_FRED', 'DELAY', 'JUMP_SOUND', 'BUMP_WALL'):
            out.append('%-16s EQU $%04X' % (n, a))
    out.append('')
    local_labels = {a: n for a, n in labs.items() if a not in VARS}
    defined = set()
    for s, e, lab, title, cm in ROUTINES:
        out.append('; ' + '=' * 74)
        out.append('; %s  %04X-%04X  %s' % (lab, s, e - 1, title))
        out.append('; ' + '=' * 74)
        out.append('        ORG $%04X' % s)
        a = s
        while a < e:
            text, ln = disassemble(mem, a, '$', '02X', '04X')[:2]
            if a + ln > e:
                text = 'DEFB ' + ','.join('$%02X' % mem[i] for i in range(a, e))
                ln = e - a
            raw = ' '.join('%02X' % mem[i] for i in range(a, a + ln))

            def sub(mo):
                v = int(mo.group(1), 16)
                n = labs.get(v)
                if n and (n not in local_labels.values() or n in defined or v in VARS
                          or any(r[0] == v for r in ROUTINES) or n in ('TICK_END', 'REDRAW_FRED', 'DELAY', 'JUMP_SOUND', 'BUMP_WALL')):
                    return n
                return mo.group(0)
            if not text.startswith('DEFB'):
                text = re.sub(r'\$([0-9A-F]{4})', sub, text)
            lbl = ''
            if a == s:
                lbl = lab + ':'
                defined.add(lab)
            elif a in local_labels and local_labels[a] not in defined and not any(r[0] == a for r in ROUTINES):
                lbl = local_labels[a] + ':'
                defined.add(local_labels[a])
            if lbl:
                out.append(lbl)
            c = cm.get(a, '')
            out.append('        %-24s ; %04X  %-12s %s' % (text, a, raw, c))
            a += ln
        out.append('')
    # routines referenced as labels but not emitted need EQUs
    emitted = {lab for _, _, lab, _, _ in ROUTINES}
    extra = [(a, n) for a, n in labs.items() if n not in emitted and a not in VARS
             and n not in ('TICK_END', 'REDRAW_FRED', 'DELAY', 'JUMP_SOUND', 'BUMP_WALL')]
    text = '\n'.join(out)
    eqs = ['%-16s EQU $%04X' % (n, a) for a, n in sorted(extra) if re.search(r'\b%s\b' % n, text)
           and (n + ':') not in text]
    text = text.replace('\n\n; ' + '=' * 74, '\n' + '\n'.join(eqs) + '\n\n; ' + '=' * 74, 1)
    os.makedirs(os.path.join(ROOT, 'disassembly'), exist_ok=True)
    open(os.path.join(ROOT, 'disassembly', 'sirfred_core.asm'), 'w').write(text + '\n')
    print('wrote disassembly/sirfred_core.asm (%d lines)' % text.count('\n'))


if __name__ == '__main__':
    main()
