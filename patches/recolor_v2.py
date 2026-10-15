#!/usr/bin/env python3
"""NaiWa theme recolor v2 — WIDE net.
Covers: resources.arsc + ALL binary XMLs under res/.
- blues/cyans (hue 175-275, s>0.12) -> naiwa yellow (hue 47) preserving L
- greens (hue 75-175, s>0.25) -> naiwa yellow
- slate blue-greys included via the s>0.12 net
- also patches the arsc string 'main_page_bg.jpg' -> 'main_page_bg.png' (same length)
"""
import struct, os, colorsys, sys

WORK = '/home/z/my-project/build/work'
ARSC = f'{WORK}/resources.arsc'

NAI_HUE = 47.0 / 360.0

# canonical mappings (brand colors) — exact naiwa yellow family
CANON = {
    0xff0073bd: 0xfffece0e,  # idg_theme_color (DUT blue) -> naiwa yellow
    0xff005c97: 0xffd9a600,  # dark blue -> dark amber (vivid)
    0xff0dac67: 0xfffece0e,  # main green -> naiwa yellow
    0xff0a8a52: 0xffd9a600,  # dark green -> dark amber
    0xff1e88e5: 0xfff9cb26,  # material blue 600 -> bright yellow
}

def shift_color(argb):
    """Return shifted ARGB or None."""
    a = (argb >> 24) & 0xff
    if a == 0:
        return None
    if argb in CANON:
        return CANON[argb]
    r = (argb >> 16) & 0xff
    g = (argb >> 8) & 0xff
    b = argb & 0xff
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hd = h * 360
    if l < 0.05 or l > 0.995 or s < 0.12:
        return None
    is_blue = 175 <= hd <= 275
    is_green = 75 <= hd < 175 and s > 0.25
    if not (is_blue or is_green):
        return None
    # target saturation: vivid for saturated sources, muted for weak/slate
    if s > 0.45:
        ns = min(max(0.55 + 0.4 * s, 0.75), 0.98)
    else:
        ns = min(max(s * 0.8, 0.15), 0.50)
    nr, ng, nb = colorsys.hls_to_rgb(NAI_HUE, l, ns)
    val = (a << 24) | (int(nr * 255) << 16) | (int(ng * 255) << 8) | int(nb * 255)
    return val if val != argb else None

# ---- gather all colors ----
def gather():
    found = {}
    files = [ARSC]
    for root, dirs, fnames in os.walk(f'{WORK}/res'):
        for fn in fnames:
            if fn.endswith('.xml'):
                files.append(os.path.join(root, fn))
    for path in files:
        data = open(path, 'rb').read()
        for dtype in (b'\x08\x00\x00\x1d', b'\x08\x00\x00\x1c', b'\x08\x00\x00\x1e'):
            i = 0
            while True:
                i = data.find(dtype, i)
                if i < 0 or i + 8 > len(data):
                    break
                val = struct.unpack_from('<I', data, i + 4)[0]
                found.setdefault(val, 0)
                found[val] += 1
                i += 8
    return found

colors = gather()
rmap = {}
for c, cnt in colors.items():
    nc = shift_color(c)
    if nc is not None:
        rmap[c] = nc
print(f"color replacement map: {len(rmap)} entries")
for k, v in sorted(rmap.items()):
    print(f"  0x{k:08x} -> 0x{v:08x}  (seen {colors[k]}x)")

# ---- apply ----
def apply(path):
    data = bytearray(open(path, 'rb').read())
    count = 0
    for dtype in (b'\x08\x00\x00\x1d', b'\x08\x00\x00\x1c', b'\x08\x00\x00\x1e'):
        i = 0
        while True:
            i = bytes(data).find(dtype, i)
            if i < 0 or i + 8 > len(data):
                break
            val = struct.unpack_from('<I', data, i + 4)[0]
            if val in rmap:
                struct.pack_into('<I', data, i + 4, rmap[val])
                count += 1
            i += 8
    if count:
        open(path, 'wb').write(bytes(data))
    return count

total = 0
touched = 0
for root, dirs, fnames in os.walk(f'{WORK}/res'):
    for fn in fnames:
        if fn.endswith('.xml'):
            p = os.path.join(root, fn)
            c = apply(p)
            if c:
                total += c
                touched += 1
c = apply(ARSC)
total += c
if c:
    touched += 1
print(f"\nTOTAL: {total} color values replaced in {touched} files (+arsc)")

# ---- arsc string patch: main_page_bg.jpg -> main_page_bg.png ----
data = bytearray(open(ARSC, 'rb').read())
replaced = False
for enc in ('utf-16-le', 'utf-8'):
    old = 'res/drawable-xxhdpi-v4/main_page_bg.jpg'.encode(enc)
    new = 'res/drawable-xxhdpi-v4/main_page_bg.png'.encode(enc)
    if len(old) == len(new):
        i = data.find(old)
        while i >= 0:
            data[i:i+len(old)] = new
            replaced = True
            print(f"arsc string patched ({enc}): main_page_bg.jpg -> .png @0x{i:x}")
            i = data.find(old, i + len(new))
if replaced:
    open(ARSC, 'wb').write(bytes(data))
else:
    print("WARNING: main_page_bg.jpg string not found in arsc!")
