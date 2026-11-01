"""Read/write ZX Spectrum .z80 snapshots (v1/v2/v3, 48K only).

The writer preserves the original header (registers and all service fields)
byte for byte and only re-encodes the memory pages, so a patched snapshot
resumes in exactly the same CPU state as the original.
"""
import struct

PAGE_48K = {8: 0x4000, 4: 0x8000, 5: 0xC000}


def _decompress(data, length=None):
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if length is None and data[i:i + 4] == b'\x00\xED\xED\x00':
            break
        if i + 3 < n and data[i] == 0xED and data[i + 1] == 0xED:
            out += bytes([data[i + 3]]) * data[i + 2]
            i += 4
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _compress(block):
    out = bytearray()
    i = 0
    n = len(block)
    while i < n:
        b = block[i]
        j = i
        while j < n and block[j] == b and j - i < 255:
            j += 1
        run = j - i
        # A single ED immediately after an ED must not start a sequence
        if (run >= 5) or (b == 0xED and run >= 2):
            out += bytes([0xED, 0xED, run, b])
            i = j
        else:
            out.append(b)
            i += 1
            # ED followed by anything: emit next byte literally
            if b == 0xED and i < n:
                out.append(block[i])
                i += 1
    return bytes(out)


class Z80Snapshot:
    def __init__(self, path):
        data = open(path, 'rb').read()
        self.raw = data
        self.header = bytearray(data[:30])
        pc = struct.unpack('<H', data[6:8])[0]
        if pc != 0:
            self.version = 1
            self.ext = b''
            compressed = bool(data[12] & 0x20)
            body = data[30:]
            mem = _decompress(body) if compressed else body[:49152]
            self.ram = bytearray(mem)
        else:
            extlen = struct.unpack('<H', data[30:32])[0]
            self.ext = bytearray(data[32:32 + extlen])
            self.version = 2 if extlen == 23 else 3
            hw = self.ext[2]
            if (self.version == 2 and hw not in (0, 1)) or (self.version == 3 and hw not in (0, 1, 3)):
                raise ValueError('not a 48K snapshot (hw=%d)' % hw)
            self.ram = bytearray(49152)
            p = 32 + extlen
            seen = set()
            while p < len(data):
                blen, page = struct.unpack('<HB', data[p:p + 3])
                p += 3
                if blen == 0xFFFF:
                    blk = data[p:p + 16384]
                    p += 16384
                else:
                    blk = _decompress(data[p:p + blen], length=blen)
                    p += blen
                if len(blk) != 16384:
                    raise ValueError('page %d decompressed to %d bytes' % (page, len(blk)))
                if page in PAGE_48K:
                    a = PAGE_48K[page] - 0x4000
                    self.ram[a:a + 16384] = blk
                    seen.add(page)
            if seen != set(PAGE_48K):
                raise ValueError('missing pages: %s' % (set(PAGE_48K) - seen))
        if len(self.ram) != 49152:
            raise ValueError('RAM size %d' % len(self.ram))

    # register accessors -------------------------------------------------
    @property
    def pc(self):
        if self.version == 1:
            return struct.unpack('<H', self.header[6:8])[0]
        return struct.unpack('<H', self.ext[0:2])[0]

    @property
    def sp(self):
        return struct.unpack('<H', self.header[8:10])[0]

    def registers(self):
        h = self.header
        w = lambda o: struct.unpack('<H', h[o:o + 2])[0]
        return {
            'A': h[0], 'F': h[1], 'BC': w(2), 'HL': w(4), 'PC': self.pc, 'SP': w(8),
            'I': h[10], 'R': (h[11] & 0x7F) | ((h[12] & 1) << 7), 'border': (h[12] >> 1) & 7,
            'DE': w(13), "BC'": w(15), "DE'": w(17), "HL'": w(19), "A'": h[21], "F'": h[22],
            'IY': w(23), 'IX': w(25), 'IFF1': h[27], 'IFF2': h[28], 'IM': h[29] & 3,
        }

    def peek(self, addr):
        return self.ram[addr - 0x4000]

    def save(self, path, ram=None):
        ram = self.ram if ram is None else ram
        assert len(ram) == 49152
        if self.version == 1:
            h = bytearray(self.header)
            h[12] |= 0x20
            out = bytes(h) + _compress(bytes(ram)) + b'\x00\xED\xED\x00'
        else:
            out = bytearray(self.header) + struct.pack('<H', len(self.ext)) + bytes(self.ext)
            for page in (4, 5, 8):
                a = PAGE_48K[page] - 0x4000
                blk = _compress(bytes(ram[a:a + 16384]))
                if len(blk) >= 16384:
                    out += struct.pack('<HB', 0xFFFF, page) + bytes(ram[a:a + 16384])
                else:
                    out += struct.pack('<HB', len(blk), page) + blk
        open(path, 'wb').write(out)
        return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='show registers / unpack RAM of a 48K .z80')
    ap.add_argument('z80')
    ap.add_argument('--ram', help='write the 49152-byte RAM image (4000-FFFF) here')
    a = ap.parse_args()
    s = Z80Snapshot(a.z80)
    print('version', s.version)
    for k, v in s.registers().items():
        print('%-6s %s' % (k, hex(v)))
    if a.ram:
        open(a.ram, 'wb').write(bytes(s.ram))
        print('RAM written to', a.ram)
