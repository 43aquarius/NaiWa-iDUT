#!/usr/bin/env python3
"""Binary AXML writer v5 — regenerates welcome_layout.xml.

v3/v4 layout set welcome_image src=@drawable/anim_loading_view, i.e. the
animation-list itself. If that AnimationDrawable inflates or casts badly
at runtime the ImageView can end up blank -> whole splash looks empty.
v5 instead points src at the STEADY PNG FRAME (refresh_loading12,
res 0x7f0d0011): a plain BitmapDrawable that always renders. The
AnimStarter smali patch then switches to the animation-list and starts
it; if anything fails we still show the full mascot statically.
Everything else matches the v3 writer (idIdx=1, self-verified).
"""
import struct, sys
sys.path.insert(0, '/home/z/my-project/NaiWa-iDUT/patches')
from arsc_parser import StringPool

OUT = '/home/z/my-project/NaiWa-iDUT/work/build/res/layout/welcome_layout.xml'

ANDROID_URI = 'http://schemas.android.com/apk/res/android'

STRINGS = [
    'id', 'background', 'visibility', 'layout_width', 'layout_height',
    'layout_marginTop', 'layout_marginBottom', 'scaleType',
    'layout_alignParentBottom', 'layout_centerHorizontal', 'src',
    'ImageView', 'RelativeLayout', 'android', ANDROID_URI,
]
RESMAP = [
    0x010100d0,  # id
    0x010100d4,  # background
    0x010100dc,  # visibility
    0x010100f4,  # layout_width
    0x010100f5,  # layout_height
    0x010100f8,  # layout_marginTop
    0x010100fa,  # layout_marginBottom
    0x0101011d,  # scaleType
    0x0101018e,  # layout_alignParentBottom
    0x01010190,  # layout_centerHorizontal
    0x01010119,  # src
]
SI = {s: i for i, s in enumerate(STRINGS)}
NS_IDX = SI[ANDROID_URI]

def REF(v):  return (0x01, v)
def INT(v):  return (0x10, v & 0xffffffff)
def BOOL(v): return (0x12, 0xffffffff if v else 0)
def DIM(v):  return (0x05, (v << 8) | 1)

ELEMS = [
    ('RelativeLayout', [
        ('id', REF(0x7f090444)),            # rl_act_welcome_content
        ('background', REF(0x00000000)),    # @null
        ('visibility', INT(0)),             # VISIBLE
        ('layout_width', INT(-1)),
        ('layout_height', INT(-1)),
    ]),
    ('ImageView', [
        ('id', REF(0x7f090615)),            # welcome_image
        ('layout_width', INT(-1)),
        ('layout_height', INT(-1)),
        ('scaleType', INT(7)),              # centerInside
        ('layout_centerHorizontal', BOOL(True)),
        ('src', REF(0x7f0d0011)),           # @mipmap/refresh_loading12 (steady frame)
    ]),
    ('ImageView', [
        ('id', REF(0x7f0902fc)),            # iv_welcome_icon
        ('layout_width', DIM(133)),
        ('layout_height', DIM(133)),
        ('layout_marginTop', DIM(80)),
        ('scaleType', INT(1)),              # fitXY
        ('layout_centerHorizontal', BOOL(True)),
        ('src', REF(0x7f0d0002)),           # @mipmap/ic_launcher
    ]),
    ('ImageView', [
        ('id', REF(0x7f0902fd)),            # iv_welcome_txt
        ('layout_width', DIM(200)),
        ('layout_height', DIM(133)),
        ('layout_marginBottom', DIM(80)),
        ('scaleType', INT(1)),
        ('layout_alignParentBottom', BOOL(True)),
        ('layout_centerHorizontal', BOOL(True)),
    ]),
]

def build_string_pool():
    data = bytearray()
    offsets = []
    for s in STRINGS:
        b = s.encode('utf-8')
        offsets.append(len(data))
        data.append(len(s))
        data.append(len(b))
        data.extend(b)
        data.append(0)
    while len(data) % 4:
        data.append(0)
    headerSize = 28
    stringsStart = headerSize + 4 * len(STRINGS)
    size = stringsStart + len(data)
    hdr = struct.pack('<HHIIIIII', 0x0001, headerSize, size, len(STRINGS), 0,
                      0x100, stringsStart, 0)
    chunk = bytearray(hdr)
    for off in offsets:
        chunk.extend(struct.pack('<I', off))
    chunk.extend(data)
    assert len(chunk) == size, f"{len(chunk)} != {size}"
    return bytes(chunk)

def attr_entry(name, dtype, ddata):
    ns = struct.pack('<I', NS_IDX)
    nm = struct.pack('<I', SI[name])
    raw = struct.pack('<I', 0xffffffff)
    val = struct.pack('<HBBI', 8, 0, dtype, ddata & 0xffffffff)
    return ns + nm + raw + val

def start_elem(name, attrs, line=1):
    body = struct.pack('<IIII', line, 0xffffffff, NS_IDX, SI[name])
    ext = struct.pack('<HHHHHH', 20, 20, len(attrs), 1, 0, 0)
    attrdata = b''.join(attr_entry(n, t, d) for n, (t, d) in attrs)
    size = 8 + 8 + 8 + 12 + len(attrdata)
    hdr = struct.pack('<HHI', 0x0102, 16, size)
    return hdr + body + ext + attrdata

def end_elem(name, line=1):
    hdr = struct.pack('<HHI', 0x0103, 16, 24)
    body = struct.pack('<IIII', line, 0xffffffff, NS_IDX, SI[name])
    return hdr + body

def namespace_start():
    hdr = struct.pack('<HHI', 0x0100, 16, 24)
    body = struct.pack('<IIII', 1, 0xffffffff, SI['android'], SI[ANDROID_URI])
    return hdr + body

def namespace_end():
    hdr = struct.pack('<HHI', 0x0101, 16, 24)
    body = struct.pack('<IIII', 1, 0xffffffff, SI['android'], SI[ANDROID_URI])
    return hdr + body

def resource_map():
    n = len(RESMAP)
    hdr = struct.pack('<HHI', 0x0180, 8, 8 + 4 * n)
    return hdr + b''.join(struct.pack('<I', r) for r in RESMAP)

pool = build_string_pool()
rmap = resource_map()
ns_s = namespace_start()
body = bytearray()
line = 1
body.extend(start_elem(ELEMS[0][0], ELEMS[0][1], line))
for name, attrs in ELEMS[1:]:
    line += 1
    body.extend(start_elem(name, attrs, line))
    body.extend(end_elem(name, line))
line += 1
body.extend(end_elem(ELEMS[0][0], line))
ns_e = namespace_end()

total = 8 + len(pool) + len(rmap) + len(ns_s) + len(body) + len(ns_e)
final = struct.pack('<HHI', 0x0003, 8, total) + pool + rmap + ns_s + body + ns_e
open(OUT, 'wb').write(final)
print(f"wrote {OUT}: {len(final)} bytes (v4 was 1108)")

# ============ verify by re-parsing ============
data = open(OUT, 'rb').read()
t, hs, sz = struct.unpack_from('<HHI', data, 0)
assert t == 0x0003 and sz == len(data), "header mismatch"
sp = StringPool(data, hs)
pos = hs + sp.size
depth = 0
ok = True
saw_frame = False
while pos + 8 <= len(data):
    ct, chs, csz = struct.unpack_from('<HHI', data, pos)
    if csz == 0:
        print("!! zero-size chunk at", pos); ok = False; break
    if ct == 0x0102:
        line, comment, ns, name, attrStart, attrSize, attrCount, idIdx, classIdx, styleIdx = struct.unpack_from('<IIIIHHHHHH', data, pos + 8)
        ename = sp.get_string(name)
        depth += 1
        for i in range(attrCount):
            aoff = pos + 16 + attrStart + i * attrSize
            ans, aname, araw = struct.unpack_from('<III', data, aoff)
            vsize, vres0, vdtype, vdata = struct.unpack_from('<HBBI', data, aoff + 12)
            an = sp.get_string(aname)
            if an == 'src' and vdtype == 0x01 and vdata == 0x7f0d0011:
                saw_frame = True
    elif ct == 0x0103:
        depth -= 1
    pos += csz
assert pos == len(data), f"trailing bytes: {pos} vs {len(data)}"
assert saw_frame, "welcome_image src must be 0x7f0d0011 (steady frame)"
print("VERIFY OK: src=0x7f0d0011 steady-frame fallback in place")
