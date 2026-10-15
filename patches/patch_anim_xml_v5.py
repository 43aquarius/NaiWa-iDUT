#!/usr/bin/env python3
"""Patch anim_loading_view.xml (binary AXML): oneshot=false -> true.

With the v5 script (pop-in then settle) the animation must play ONCE and
stop on the steady frame; looping would replay the pop-in every 1.2s.
Binary edit: find the <animation-list> START chunk, locate the attribute
whose name string is "oneshot" and flip its boolean data 0 -> 0xFFFFFFFF.
"""
import struct, sys
sys.path.insert(0, '/home/z/my-project/NaiWa-iDUT/patches')
from arsc_parser import StringPool

PATH = '/home/z/my-project/NaiWa-iDUT/work/build/res/drawable/anim_loading_view.xml'
data = bytearray(open(PATH, 'rb').read())

t, hs, sz = struct.unpack_from('<HHI', data, 0)
assert t == 0x0003
sp = StringPool(bytes(data), hs)

# find oneshot string index
oneshot_idx = None
for i in range(sp.stringCount if hasattr(sp, 'stringCount') else 0):
    s = sp.get_string(i)
    if s == 'oneshot':
        oneshot_idx = i
        break
assert oneshot_idx is not None, 'no oneshot attr string in pool'

# walk chunks, patch the animation-list START chunk attr
pos = hs + sp.size
patched = False
while pos + 8 <= len(data):
    ct, chs, csz = struct.unpack_from('<HHI', data, pos)
    if ct == 0x0102:
        (line, comment, ns, name, attrStart, attrSize, attrCount,
         idIdx, classIdx, styleIdx) = struct.unpack_from('<IIIIHHHHHH', data, pos + 8)
        ename = sp.get_string(name)
        if ename == 'animation-list':
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', data, aoff)
                if aname == oneshot_idx:
                    vsize, vres0, vdtype, vdata = struct.unpack_from('<HBBI', data, aoff + 12)
                    assert vdtype == 0x12, f'oneshot not boolean: {vdtype:02x}'
                    print(f'oneshot was 0x{vdata:08x} -> setting true')
                    struct.pack_into('<I', data, aoff + 16, 0xffffffff)
                    patched = True
    pos += csz
assert patched, 'oneshot attribute not patched'

open(PATH, 'wb').write(bytes(data))
print('PATCH ANIM XML V5 OK: oneshot=true (play once, hold steady frame)')
