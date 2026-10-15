#!/usr/bin/env python3
"""Surgical binary-XML attr patches v3:
1. activity_main.xml: root LinearLayout background @color/background_color_fb(0x7f060049)
   -> @drawable/main_page_bg(0x7f080265)  [naiwa main page background]
2. fragment_tab_service.xml: root LinearLayout background @color/back_ground_color_f0(0x7f060034)
   -> @null (0)  [transparent so the naiwa bg shows through]
3. fragment_tab_mine.xml: root RelativeLayout background @drawable/bg_shape_mine(0x7f0800a5)
   -> @drawable/main_page_bg(0x7f080265)  [V3: "我的"页面背景 = naiwa]
"""
import struct, sys
sys.path.insert(0, '/home/z/my-project/NaiWa-iDUT/patches')
from arsc_parser import StringPool

START_ELEM = 0x0102

def parse(data):
    t, hs, sz = struct.unpack_from('<HHI', data, 0)
    assert t == 0x0003, f"not AXML: {hex(t)}"
    sp = StringPool(data, hs)
    pos = hs + sp.size
    out = []
    while pos + 8 <= len(data):
        ct, chs, csz = struct.unpack_from('<HHI', data, pos)
        if csz == 0:
            break
        if ct == START_ELEM:
            line, comment, ns, name, attrStart, attrSize, attrCount, idIdx, classIdx, styleIdx = struct.unpack_from('<IIIIHHHHHH', data, pos + 8)
            ename = sp.get_string(name)
            attrs = []
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', data, aoff)
                vsize, vres0, vdtype, vdata = struct.unpack_from('<HBBI', data, aoff + 12)
                attrs.append((aoff, sp.get_string(aname), vdtype, vdata))
            out.append((pos, ename, attrs))
        pos += csz
    return out

def patch(path, patches):
    data = bytearray(open(path, 'rb').read())
    changed = []
    for eoff, ename, attrs in parse(bytes(data)):
        for aoff, an, dtype, vdata in attrs:
            for matcher, newval, label in patches:
                if matcher(ename, an, dtype, vdata):
                    struct.pack_into('<I', data, aoff + 16, newval)
                    changed.append(f"<{ename}> {an} 0x{vdata:08x} -> 0x{newval:08x} ({label})")
    if changed:
        open(path, 'wb').write(bytes(data))
    for c in changed:
        print("  " + c)
    return len(changed)

WORK = '/home/z/my-project/NaiWa-iDUT/work/build'

n = patch(f'{WORK}/res/layout/activity_main.xml', [
    (lambda e, a, t, v: a == 'background' and t == 0x01 and v == 0x7f060049,
     0x7f080265, "bg -> main_page_bg (naiwa)"),
])
print(f"activity_main.xml: {n} patches")

n = patch(f'{WORK}/res/layout/fragment_tab_service.xml', [
    (lambda e, a, t, v: a == 'background' and t == 0x01 and v == 0x7f060034,
     0x00000000, "bg -> @null transparent"),
])
print(f"fragment_tab_service.xml: {n} patches")

n = patch(f'{WORK}/res/layout/fragment_tab_mine.xml', [
    (lambda e, a, t, v: a == 'background' and t == 0x01 and v == 0x7f0800a5,
     0x7f080265, "V3: mine bg -> main_page_bg (naiwa)"),
])
print(f"fragment_tab_mine.xml: {n} patches")

# verify
for f in ('activity_main.xml', 'fragment_tab_service.xml', 'fragment_tab_mine.xml'):
    data = open(f'{WORK}/res/layout/{f}', 'rb').read()
    elems = parse(data)
    eoff, ename, attrs = elems[0]
    for aoff, an, dtype, vdata in attrs:
        if an == 'background':
            print(f"VERIFY {f} root<{ename}> background = 0x{vdata:08x} (type 0x{dtype:02x})")
