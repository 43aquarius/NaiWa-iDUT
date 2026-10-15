#!/usr/bin/env python3
"""
NaiLong theme color replacement:
- Replace DUT blue / green colors with NaiLong yellow family (from naiwa images + website)
- Uses HSL hue-shift preserving lightness (keeps depth hierarchy)
- Applies to resources.arsc + all binary XMLs in res/
- Safe pattern: Res_value struct (08 00 00 1d <data>) so only color-typed values are touched
"""
import struct, os, colorsys, sys

WS = '/home/z/my-project/workspace'
WORK = f'{WS}/apk_work'

# canonical mappings (brand colors)
CANON = {
    0xff0073bd: 0xfffece0e,  # idg_theme_color / idg_btn_bg_nor (DUT blue -> naiwa yellow)
    0xff005c97: 0xffe0a800,  # dark blue -> dark amber
    0xff0dac67: 0xfffece0e,  # main green -> naiwa yellow
    0xff0a8a52: 0xffe0a800,  # dark green -> dark amber
}

NAI_HUE = 47.0 / 360.0   # naiwa yellow hue

def hue_shift(argb):
    """Shift a blue/green ARGB to the naiwa-yellow hue, preserving L; returns None if not blue/green"""
    a = (argb >> 24) & 0xff
    r = (argb >> 16) & 0xff
    g = (argb >> 8) & 0xff
    b = argb & 0xff
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hd = h * 360
    # saturated blues (180-290) or greens (60-180) only; grays/slates (low s) stay neutral
    is_blue = 180 <= hd <= 290 and s > 0.25
    is_green = 60 <= hd < 180 and s > 0.25
    if not (is_blue or is_green):
        return None
    if l < 0.08:  # near black - leave
        return None
    # new saturation: vivid but not neon
    ns = min(max(s, 0.78), 0.98) if l > 0.15 else max(min(s, 0.85), 0.5)
    nr, ng, nb = colorsys.hls_to_rgb(NAI_HUE, l, ns)
    val = (a << 24) | (int(nr * 255) << 16) | (int(ng * 255) << 8) | int(nb * 255)
    return val

# build the full replacement map from all known colors in the app
def build_map(extra_colors):
    m = dict(CANON)
    for c in extra_colors:
        if c in m:
            continue
        nc = hue_shift(c)
        if nc is not None and nc != c:
            m[c] = nc
    return m

# gather all ARGB8 color values present (type 0x1d and 0x1c patterns) from arsc + XMLs
def gather_colors():
    found = set()
    files = [f'{WORK}/resources.arsc']
    for root, dirs, fnames in os.walk(f'{WORK}/res'):
        for fn in fnames:
            if fn.endswith('.xml'):
                files.append(os.path.join(root, fn))
    for path in files:
        data = open(path, 'rb').read()
        for dtype in (b'\x08\x00\x00\x1d', b'\x08\x00\x00\x1c'):
            i = 0
            while True:
                i = data.find(dtype, i)
                if i < 0 or i + 8 > len(data):
                    break
                val = struct.unpack_from('<I', data, i + 4)[0]
                found.add(val)
                i += 8
    return found

def apply_replacements():
    colors = gather_colors()
    rmap = build_map(colors)
    print(f"color replacement map: {len(rmap)} entries")
    for k, v in sorted(rmap.items()):
        print(f"  0x{k:08x} -> 0x{v:08x}")

    files = [f'{WORK}/resources.arsc']
    for root, dirs, fnames in os.walk(f'{WORK}/res'):
        for fn in fnames:
            if fn.endswith('.xml'):
                files.append(os.path.join(root, fn))

    total_repl = 0
    files_touched = 0
    for path in files:
        data = bytearray(open(path, 'rb').read())
        count = 0
        for dtype in (b'\x08\x00\x00\x1d', b'\x08\x00\x00\x1c'):
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
            total_repl += count
            files_touched += 1
            rel = path.replace(WORK + '/', '')
            print(f"  {rel}: {count} colors")
    print(f"\nTOTAL: {total_repl} color values replaced in {files_touched} files")

if __name__ == '__main__':
    apply_replacements()
