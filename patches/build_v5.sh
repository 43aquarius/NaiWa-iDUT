#!/usr/bin/env bash
# NaiWa v5 full build pipeline (reproducible)
# v4 pipeline + v5:
#   - gen_assets_v5: 12-frame pop-in animation rebuilt (strong curve, safe layout)
#   - gen_welcome_layout_v5: welcome_image src = steady frame PNG (static fallback)
#   - patch_anim_xml_v5: animation-list oneshot=true
#   - patch_smali_v5: v3 patches + AnimStarter v2 + nop server-image race
#     + "关于i大工奶蛙" row + AboutNaiWaActivity
#   - patch_manifest_v5: register AboutNaiWaActivity
# Env: JDK17+, Android build-tools r34 at /home/z/tools/android-14,
#      smali/baksmali 2.5.2 + guava + jcommander 1.78 + antlr-runtime at /home/z/tools/smali_lib,
#      python3 + PIL + numpy
set -e
cd /home/z/my-project/NaiWa-iDUT
REPO=/home/z/my-project/NaiWa-iDUT
W=work
BT=/home/z/tools/android-14
SMALI_CP='/home/z/tools/smali_lib/*'

echo "=== 0. (once) unpack + disassemble original ==="
if [ ! -d $W/orig ]; then
  mkdir -p $W && cd $W
  unzip -q -o "../i大工_3.3.12.75026.apk" -d orig
  cd ..
fi

echo "=== 1. Reset build tree from original ==="
rm -rf $W/build && mkdir -p $W/build
cp -r $W/orig/res $W/build/res
cp -r $W/orig/assets $W/build/assets
cp $W/orig/resources.arsc $W/build/resources.arsc
cp $W/orig/AndroidManifest.xml $W/build/AndroidManifest.xml
rm -rf $W/smali_work
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble $W/orig/classes.dex -o $W/smali_work/smali_classes
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble $W/orig/classes2.dex -o $W/smali_work/smali_classes2

echo "=== 2. Generate v3 assets (9-patches, guides, avatars, empty states) ==="
python3 patches/gen_assets_v3.py | tail -8

echo "=== 2b. Generate v4 assets (pure-gradient welcome bg + tab/service icons) ==="
python3 patches/gen_assets_v4.py | tail -6

echo "=== 2c. Generate v5 assets (12-frame pop-in animation) ==="
python3 patches/gen_assets_v5.py | tail -3

echo "=== 3. Generate welcome_layout.xml v5 (steady-frame src fallback) ==="
python3 patches/gen_welcome_layout_v5.py | tail -2

echo "=== 4. Patch layouts (activity_main / fragment_tab_service / fragment_tab_mine) ==="
python3 patches/patch_layouts_v3.py | tail -4

echo "=== 5. Smali patches v5 (welcome anim + AnimStarter v2 + no server-image race + 关于i大工奶蛙) ==="
python3 patches/patch_smali_v5.py | tail -5

echo "=== 6. Recolor values (arsc + binary XMLs) ==="
python3 patches/recolor_v3.py | tail -3

echo "=== 7. Recolor images (pixel-level) ==="
python3 patches/recolor_images_v3.py 2>/dev/null | tail -2

echo "=== 7b. Patch anim_loading_view.xml oneshot=true (after recolor) ==="
python3 patches/patch_anim_xml_v5.py | tail -2

echo "=== 7c. Inject AboutNaiWaActivity into AndroidManifest ==="
python3 patches/patch_manifest_v5.py | tail -2

echo "=== 8. Reassemble dex + APK ==="
cd $W
java -cp "$SMALI_CP" org.jf.smali.Main assemble smali_work/smali_classes -o build/new_classes.dex
java -cp "$SMALI_CP" org.jf.smali.Main assemble smali_work/smali_classes2 -o build/new_classes2.dex
cd ..
python3 patches/assemble_v3.py | tail -3

echo "=== 9. Zipalign + sign ==="
export LD_LIBRARY_PATH=$BT/lib64
cd $W/build
$BT/zipalign -f -p 4 unsigned.apk aligned.apk
java -jar $BT/lib/apksigner.jar sign \
  --ks $REPO/naiwa.keystore --ks-pass pass:nailong2026 --key-pass pass:nailong2026 \
  --ks-key-alias nailong \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --out "i大工_奶蛙版_3.3.12.apk" aligned.apk 2>/dev/null
java -jar $BT/lib/apksigner.jar verify "i大工_奶蛙版_3.3.12.apk" && echo "SIGNATURE OK"
cd ../..

echo "=== 10. Verify critical patches in final APK ==="
cd $W && rm -rf v5check && mkdir v5check && cd v5check
unzip -q -o "../build/i大工_奶蛙版_3.3.12.apk" \
  classes2.dex AndroidManifest.xml \
  res/layout/welcome_layout.xml res/layout/fragment_tab_mine.xml \
  res/drawable/anim_loading_view.xml \
  res/mipmap-hdpi-v4/refresh_loading01.png \
  res/mipmap-hdpi-v4/refresh_loading12.png
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble classes2.dex -o v5_smali 2>/dev/null

echo "--- a) welcome: no if-eqz before setContentView (must print 0):"
grep -B4 "sget v1, Lcom/ruijie/whistle/R\$layout;->welcome_layout" v5_smali/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali | grep -cE "if-eqz v2" || echo "0 if-eqz (GOOD)"

echo "--- b) AnimStarter v2 + AboutNaiWaActivity + n\$nw classes:"
ls v5_smali/com/naiwa/theme/AnimStarter.smali v5_smali/com/naiwa/theme/AboutNaiWaActivity.smali "v5_smali/b/a/a/a/k/e/n\$nw.smali"

echo "--- c) displayImage nop-ed (must print 0):"
grep -c "universalimageloader/core/ImageLoader;->displayImage" v5_smali/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali || echo "0 displayImage (GOOD)"

echo "--- d) mine fragment has 关于i大工奶蛙:"
grep -c "u5173\\\\u4e8ei\\\\u5927\\\\u5de5\\\\u5976\\\\u86d9" "v5_smali/b/a/a/a/k/e/n.smali"

echo "--- e) layout src + anim oneshot + manifest registration:"
python3 /home/z/my-project/scripts/axml_parser.py res/layout/welcome_layout.xml | grep -o "src=@ref/0x7f0d0011" | head -1
python3 /home/z/my-project/scripts/axml_parser.py res/drawable/anim_loading_view.xml | head -1
python3 - <<'PYEOF'
import struct, sys
sys.path.insert(0, '/home/z/my-project/NaiWa-iDUT/patches')
from arsc_parser import StringPool
d = open('AndroidManifest.xml', 'rb').read()
sp = StringPool(d, 8)
new_idx = None
for i in range(sp.stringCount):
    if sp.get_string(i) == 'com.naiwa.theme.AboutNaiWaActivity':
        new_idx = i
assert new_idx is not None, 'new class string missing from manifest pool'
pos = 8 + sp.size
found = False
while pos + 8 <= len(d):
    ct, chs, csz = struct.unpack_from('<HHI', d, pos)
    if ct == 0x0102:
        ns, name = struct.unpack_from('<II', d, pos + 16)
        attrStart, attrSize, attrCount = struct.unpack_from('<HHH', d, pos + 24)
        if sp.get_string(name) == 'activity' and attrCount == 3:
            got = {}
            for i in range(attrCount):
                aoff = pos + 16 + attrStart + i * attrSize
                ans, aname, araw = struct.unpack_from('<III', d, aoff)
                vs, vr, vdt, vdd = struct.unpack_from('<HBBI', d, aoff + 12)
                got[sp.get_string(aname)] = (vdt, vdd)
            if got.get('name', (0, 0)) == (0x03, new_idx) and got.get('exported', (1, 1))[1] == 0:
                found = True
    pos += csz
assert found, 'AboutNaiWaActivity activity element not found in APK manifest'
print('  MANIFEST: AboutNaiWaActivity registered OK')
PYEOF

echo "--- f) frames: pop-in scale (frame1 must be much smaller):"
python3 - <<'PYEOF'
from PIL import Image
import numpy as np
a1 = np.array(Image.open('res/mipmap-hdpi-v4/refresh_loading01.png').convert('RGBA'))
a12 = np.array(Image.open('res/mipmap-hdpi-v4/refresh_loading12.png').convert('RGBA'))
o1 = (a1[:, :, 3] > 40).sum(); o12 = (a12[:, :, 3] > 40).sum()
print(f'  frame1 opaque={o1}  frame12 opaque={o12}  ratio={o1/o12:.2f}')
assert o1 < o12 * 0.6, 'frame1 too big: pop-in broken'
print('  FRAME CHECK OK')
PYEOF

cd ../..
cp "$W/build/i大工_奶蛙版_3.3.12.apk" "i大工_奶蛙版_3.3.12.apk"
echo "=== BUILD DONE: i大工_奶蛙版_3.3.12.apk ==="
