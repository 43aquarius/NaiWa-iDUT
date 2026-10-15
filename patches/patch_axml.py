#!/usr/bin/env python3
"""Binary AXML patcher v2 - correct attribute offset calculation"""
import struct, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from arsc_parser import StringPool

START_ELEM = 0x0102

def parse_elements(data):
    """Yield (chunk_offset, elem_name, [(attr_abs_offset, attr_name, dtype, data_value)])"""
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
            line, comment, ns, name, attrStart, attrSize, attrCount, \
                idIdx, classIdx, styleIdx = struct.unpack_from('<IIIIHHHHHH', data, pos + 8)
            elem_name = sp.get_string(name)
            attrs = []
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', data, aoff)
                vsize, vres0, vdtype, vdata = struct.unpack_from('<HBBI', data, aoff + 12)
                an = sp.get_string(aname)
                if ns != 0xFFFFFFFF and an and not an.startswith('android:'):
                    pass  # android namespace attrs have plain names in pool
                attrs.append((aoff, an, vdtype, vdata))
            out.append((pos, elem_name, attrs))
        pos += csz
    return out

def run(target, patches, dry_run=False):
    data = bytearray(open(target, 'rb').read())
    elements = parse_elements(bytes(data))
    print(f"--- {target} ---")
    changed = []
    for eoff, ename, attrs in elements:
        for aoff, an, dtype, vdata in attrs:
            desc = f"<{ename}> {an} (dtype=0x{dtype:02x}, data=0x{vdata:08x})"
            for matcher, newval, label in patches:
                if matcher(ename, an, dtype, vdata):
                    if not dry_run:
                        struct.pack_into('<I', data, aoff + 16, newval)
                    changed.append(f"{desc} -> {label}")
    for c in changed:
        print("  " + c)
    if changed and not dry_run:
        open(target, 'wb').write(bytes(data))
    return changed

if __name__ == '__main__':
    target = '/home/z/my-project/workspace/apk_work/res/layout/welcome_layout.xml'
    patches = [
        (lambda e, a, t, v: a == 'background' and t == 0x01 and v == 0x0106000d,
         0x00000000, "@null (transparent)"),
        (lambda e, a, t, v: a == 'scaleType' and t == 0x10 and v == 6,
         7, "7 (centerInside)"),
    ]
    ch = run(target, patches)
    print(f"\npatched {len(ch)} attributes")

    # verify
    data2 = open(target, 'rb').read()
    for eoff, ename, attrs in parse_elements(data2):
        for aoff, an, dtype, vdata in attrs:
            if an in ('background', 'scaleType', 'visibility'):
                print(f"VERIFY <{ename}> {an} = 0x{vdata:08x}")
