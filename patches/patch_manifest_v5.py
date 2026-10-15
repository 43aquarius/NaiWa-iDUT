#!/usr/bin/env python3
"""Inject <activity android:name="com.naiwa.theme.AboutNaiWaActivity"
android:theme="..." android:exported="false"/> into AndroidManifest.xml.

Binary AXML surgery on work/build/AndroidManifest.xml:
  1. Append the class-name string to the UTF-16 string pool (rebuild the
     pool chunk: header + 382 offsets + old data + new string).
  2. Insert a START/END element pair right after the existing
     AboutActivity element (theme copied from it: 0x7f100126).
  3. Fix the top-level chunk size.
Self-verifies by re-parsing: the new activity element must appear with
exported=false and the right class name, and the walk must consume the
file exactly.
"""
import struct, sys
sys.path.insert(0, '/home/z/my-project/NaiWa-iDUT/patches')
from arsc_parser import StringPool

PATH = '/home/z/my-project/NaiWa-iDUT/work/build/AndroidManifest.xml'
NEW_NAME = 'com.naiwa.theme.AboutNaiWaActivity'
THEME_REF = 0x7f100126

d = open(PATH, 'rb').read()
ft, fhs, fsz = struct.unpack_from('<HHI', d, 0)
assert ft == 0x0003

# ---- 1. read pool ----
pt, phs, psz, sc, stc, flags, ss, sts = struct.unpack_from('<HHIIIIII', d, 8)
assert pt == 0x0001 and stc == 0 and flags & 0x100 == 0, 'unexpected pool'
sp = StringPool(d, 8)
# idempotency guard: already patched?
for i in range(sc):
    if sp.get_string(i) == NEW_NAME:
        print(f'already patched (pool idx {i}), nothing to do')
        sys.exit(0)
# required indices
idx = {}
for i in range(sc):
    s = sp.get_string(i)
    if s in ('activity', 'theme', 'name', 'exported',
             'com.ruijie.whistle.module.setting.view.AboutActivity',
             'http://schemas.android.com/apk/res/android'):
        idx[s] = i
A = idx['activity']; TH = idx['theme']; NA = idx['name']
EX = idx['exported']; ABOUT = idx['com.ruijie.whistle.module.setting.view.AboutActivity']
NS = idx['http://schemas.android.com/apk/res/android']

# ---- 2. locate AboutActivity START/END pair ----
pos = 8 + sp.size
about_start = about_end = None
while pos + 8 <= len(d):
    ct, chs, csz = struct.unpack_from('<HHI', d, pos)
    if ct == 0x0102:
        line, comment, ns, name = struct.unpack_from('<IIII', d, pos + 8)
        attrStart, attrSize, attrCount = struct.unpack_from('<HHH', d, pos + 24)
        if sp.get_string(name) == 'activity':
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', d, aoff)
                vs, vr, vdt, vdd = struct.unpack_from('<HBBI', d, aoff + 12)
                if sp.get_string(aname) == 'name' and vdt == 0x03 and vdd == ABOUT:
                    about_start = pos
    if about_start is not None and ct == 0x0103 and about_end is None and pos >= about_start:
        # matching end for a self-contained element: first END at depth
        e_ns, e_name = struct.unpack_from('<II', d, pos + 16)
        if sp.get_string(e_name) == 'activity':
            about_end = pos + csz
    pos += csz
assert about_start is not None and about_end is not None, 'AboutActivity element not found'
print(f'AboutActivity element @ {about_start}..{about_end}')

# ---- 3. build new string (UTF-16) ----
b = NEW_NAME.encode('utf-16-le')
nch = len(NEW_NAME)
new_str = struct.pack('<H', nch) + b + b'\x00\x00'
while len(new_str) % 4:
    new_str += b'\x00'
old_data_len = psz - ss
new_offset = old_data_len
new_count = sc + 1
new_ss = 28 + 4 * new_count
new_data_len = old_data_len + len(new_str)
new_pool_size = new_ss + new_data_len

old_offsets = [struct.unpack_from('<I', d, 8 + 28 + 4 * i)[0] for i in range(sc)]
old_data = d[8 + ss: 8 + psz]

new_pool = bytearray()
new_pool.extend(struct.pack('<HHIIIIII', 0x0001, 28, new_pool_size, new_count, 0,
                            0, new_ss, 0))
for off in old_offsets:
    new_pool.extend(struct.pack('<I', off))
new_pool.extend(struct.pack('<I', new_offset))
new_pool.extend(old_data)
new_pool.extend(new_str)
assert len(new_pool) == new_pool_size, f'{len(new_pool)} != {new_pool_size}'
NEW_IDX = new_count - 1

# ---- 4. build new activity element chunks ----
def attr_entry(name_idx, dtype, ddata):
    return (struct.pack('<III', NS, name_idx, 0xffffffff) +
            struct.pack('<HBBI', 8, 0, dtype, ddata & 0xffffffff))

attrs = (attr_entry(TH, 0x01, THEME_REF) +      # theme
         attr_entry(NA, 0x03, NEW_IDX) +        # name (string)
         attr_entry(EX, 0x12, 0))               # exported=false
start_size = 8 + 16 + 12 + len(attrs)
start = (struct.pack('<HHI', 0x0102, 16, start_size) +
         struct.pack('<IIII', 267, 0xffffffff, 0xffffffff, A) +
         struct.pack('<HHHHHH', 20, 20, 3, 0, 0, 0) +
         attrs)
end = (struct.pack('<HHI', 0x0103, 16, 24) +
       struct.pack('<IIII', 267, 0xffffffff, 0xffffffff, A))
elem = start + end

# ---- 5. reassemble file ----
head = d[:8 + psz]                       # file hdr + old pool -> replaced
rest = d[8 + psz:]                       # everything after pool
# rest contains chunks; find about_end relative to rest (pool size unchanged so far)
rel_end = about_end - (8 + psz)          # AboutActivity END abs - pool end
new_rest = rest[:rel_end] + elem + rest[rel_end:]
out = bytearray()
out.extend(struct.pack('<HHI', ft, fhs, 8 + len(new_pool) + len(new_rest)))
out.extend(new_pool)
out.extend(new_rest)
open(PATH, 'wb').write(bytes(out))
print(f'manifest rewritten: {len(d)} -> {len(out)} bytes (+{len(out)-len(d)})')

# ---- 6. verify by re-parsing ----
d2 = open(PATH, 'rb').read()
t2, h2, s2 = struct.unpack_from('<HHI', d2, 0)
assert t2 == 0x0003 and s2 == len(d2), 'file header broken'
sp2 = StringPool(d2, 8)
assert sp2.stringCount == new_count
assert sp2.get_string(NEW_IDX) == NEW_NAME
pos = 8 + sp2.size
depth = 0
found = False
ok = True
while pos + 8 <= len(d2):
    ct, chs, csz = struct.unpack_from('<HHI', d2, pos)
    if csz == 0 or pos + csz > len(d2):
        ok = False; break
    if ct == 0x0102:
        line, comment, ns, name = struct.unpack_from('<IIII', d2, pos + 8)
        attrStart, attrSize, attrCount = struct.unpack_from('<HHH', d2, pos + 24)
        ename = sp2.get_string(name)
        if ename == 'activity' and attrCount == 3:
            got = {}
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', d2, aoff)
                vs, vr, vdt, vdd = struct.unpack_from('<HBBI', d2, aoff + 12)
                got[sp2.get_string(aname)] = (vdt, vdd)
            if got.get('name', (0, 0))[0] == 0x03 and sp2.get_string(got['name'][1]) == NEW_NAME:
                assert got.get('exported', (0, 1))[1] == 0, 'exported must be false'
                assert got.get('theme', (0, 0))[1] == THEME_REF
                found = True
        depth += 1
    elif ct == 0x0103:
        depth -= 1
    pos += csz
assert pos == len(d2) and depth == 0, f'walk broken pos={pos}/{len(d2)} depth={depth}'
assert found, 'new activity element not found after patch'
print('VERIFY OK: AboutNaiWaActivity registered (exported=false), manifest walks clean')
