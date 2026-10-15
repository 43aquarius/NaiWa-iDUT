#!/usr/bin/env python3
"""Assemble the final APK:
- iterate original.apk entries in order
- replace patched files (res/, assets/, resources.arsc, dex) with work/ versions
- skip removed files (main_page_bg.jpg) and signature files
- append genuinely new files (main_page_bg.png)
- preserve original compression per entry; resources.arsc STORED
"""
import zipfile, os, sys

ORIG = '/home/z/my-project/NaiWa-iDUT/i大工_3.3.12.75026.apk'
WORK = '/home/z/my-project/NaiWa-iDUT/work/build'
DEX = {'classes.dex': '/home/z/my-project/NaiWa-iDUT/work/build/new_classes.dex',
       'classes2.dex': '/home/z/my-project/NaiWa-iDUT/work/build/new_classes2.dex'}
OUT = '/home/z/my-project/NaiWa-iDUT/work/build/unsigned.apk'

SKIP_NAMES = {'META-INF/MANIFEST.MF', 'META-INF/CERT.SF', 'META-INF/CERT.RSA'}

zin = zipfile.ZipFile(ORIG)
added = set()
zout = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED)

n_replaced = 0
n_copied = 0
n_skipped = 0

for info in zin.infolist():
    name = info.filename
    if name in SKIP_NAMES or name.endswith(('.RSA', '.SF', '.DSA')) and name.startswith('META-INF/'):
        n_skipped += 1
        continue
    # new dex
    if name in DEX:
        data = open(DEX[name], 'rb').read()
        # dex was DEFLATED in original
        zout.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data,
                      compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        n_replaced += 1
        added.add(name)
        continue
    # patched tree files
    local = os.path.join(WORK, name)
    if os.path.isfile(local):
        data = open(local, 'rb').read()
        ctype = info.compress_type
        zout.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data,
                      compress_type=ctype, compresslevel=6)
        if data != zin.read(name):
            n_replaced += 1
        else:
            n_copied += 1
        added.add(name)
        continue
    # removed file (main_page_bg.jpg)
    if (name.startswith('res/') or name.startswith('assets/')) and not os.path.isfile(local):
        n_skipped += 1
        print(f"  dropped (removed by theme): {name}")
        continue
    # everything else: copy as-is
    data = zin.read(name)
    zout.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data,
                  compress_type=info.compress_type, compresslevel=6)
    added.add(name)
    n_copied += 1

# genuinely new files
for root, dirs, fnames in os.walk(f'{WORK}/res'):
    for fn in fnames:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, WORK).replace(os.sep, '/')
        if rel not in added:
            zout.writestr(zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0)),
                          open(p, 'rb').read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            added.add(rel)
            print(f"  added (new): {rel}")

zout.close()
print(f"\nreplaced: {n_replaced}, copied: {n_copied}, skipped: {n_skipped}")
print(f"unsigned apk: {OUT} ({os.path.getsize(OUT)} bytes)")
