#!/usr/bin/env bash
# NaiWa v4 full build pipeline (reproducible)
# v3 pipeline + gen_assets_v4 (pure-gradient welcome bg + 34 naiwa icons)
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

echo "=== 2. Generate v3 assets (frames, 9-patches, icons, guides, avatars, empty states) ==="
python3 patches/gen_assets_v3.py | tail -8

echo "=== 2b. Generate v4 assets (pure-gradient welcome bg + BigNaiWa tab/service icons + 34 icons) ==="
python3 patches/gen_assets_v4.py | tail -6

echo "=== 3. Generate welcome_layout.xml (binary AXML writer, self-verified) ==="
python3 patches/gen_welcome_layout_v3.py | tail -2

echo "=== 4. Patch layouts (activity_main / fragment_tab_service / fragment_tab_mine) ==="
python3 patches/patch_layouts_v3.py | tail -4

echo "=== 5. Smali patches (always-show welcome + AnimStarter + 2600ms) ==="
python3 patches/patch_smali_v3.py | tail -3

echo "=== 6. Recolor values (arsc + binary XMLs) ==="
python3 patches/recolor_v3.py | tail -3

echo "=== 7. Recolor images (pixel-level) ==="
python3 patches/recolor_images_v3.py 2>/dev/null | tail -2

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
cd $W && rm -rf v3check && mkdir v3check && cd v3check
unzip -q -o "../build/i大工_奶蛙版_3.3.12.apk" classes2.dex res/layout/welcome_layout.xml res/layout/fragment_tab_mine.xml
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble classes2.dex -o v3_smali 2>/dev/null
echo "--- welcome must have nop (no if-eqz) before setContentView:"
grep -B4 "sget v1, Lcom/ruijie/whistle/R\$layout;->welcome_layout" v3_smali/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali | grep -cE "if-eqz v2" || echo "0 if-eqz (GOOD)"
ls v3_smali/com/naiwa/theme/AnimStarter.smali && echo "AnimStarter OK"
python3 /home/z/my-project/scripts/axml_parser.py res/layout/fragment_tab_mine.xml | head -1

echo "=== 10b. Verify v4 assets inside final APK ==="
unzip -q -o "../build/i大工_奶蛙版_3.3.12.apk" \
  "res/drawable-xxhdpi-v4/icon_tab_main_nor.png" \
  "res/drawable-xxhdpi-v4/icon_tab_main_pre.png" \
  "res/drawable-xxhdpi-v4/icon_tab_message_pre.png" \
  "res/drawable-xxhdpi-v4/icon_tab_service_pre.png" \
  "res/drawable-xxhdpi-v4/icon_tab_me_pre.png" \
  "res/drawable-xxhdpi-v4/icon_service_all.png" \
  "res/drawable-xxhdpi-v4/icon_service_study.png" \
  "res/drawable-xxhdpi-v4/icon_first_page_logo.png" \
  "res/drawable-xxhdpi-v4/welcome_bg_pic.9.png"
python3 - <<'PYEOF'
from PIL import Image
import numpy as np
ok = True
# tab/service icons: must exist, be 60/78 canvas, and NOT be the old white glyphs
for name, sz in [('icon_tab_main_nor', 60), ('icon_tab_main_pre', 60), ('icon_tab_message_pre', 60),
                 ('icon_tab_service_pre', 60), ('icon_tab_me_pre', 60),
                 ('icon_service_all', 78), ('icon_service_study', 78), ('icon_first_page_logo', 348)]:
    im = Image.open(f'res/drawable-xxhdpi-v4/{name}.png').convert('RGBA')
    a = np.array(im)
    op = a[a[:, :, 3] > 128]
    mean = op[:, :3].mean(axis=0) if len(op) else [0, 0, 0]
    # old white glyph mean RGB ~ (255,255,255); new sprites are colorful
    colorful = (abs(255 - mean[0]) + abs(255 - mean[1]) + abs(255 - mean[2])) > 40
    status = 'OK' if (im.size[0] == sz and colorful and len(op) > 50) else 'FAIL'
    if status == 'FAIL': ok = False
    print(f'  {name}: {im.size} meanRGB={tuple(int(x) for x in mean)} colorful={colorful} {status}')
# welcome bg 9-patch: strip border -> must be smooth (no hard edges = no mascot baked in)
im = Image.open('res/drawable-xxhdpi-v4/welcome_bg_pic.9.png').convert('RGB')
c = np.array(im.crop((1, 1, im.width - 1, im.height - 1)), dtype=int)
row_diff = np.abs(np.diff(c, axis=0)).mean()
col_diff = np.abs(np.diff(c, axis=1)).mean()
max_edge = max(np.abs(np.diff(c, axis=0)).max(), np.abs(np.diff(c, axis=1)).max())
hvar = c.std(axis=1).mean()
smooth = hvar < 3 and max_edge < 40  # gradient-only: tiny horizontal variance, no hard edges
print(f'  welcome_bg: hvar={hvar:.2f} rowdiff={row_diff:.2f} coldiff={col_diff:.2f} maxedge={max_edge} -> {"pure gradient OK" if smooth else "NOT PURE GRADIENT"}')
if not smooth: ok = False
print('V4 ASSET VERIFY', 'PASS' if ok else 'FAIL')
PYEOF
cd ../..

cp "$W/build/i大工_奶蛙版_3.3.12.apk" "i大工_奶蛙版_3.3.12.apk"
echo "=== BUILD DONE: i大工_奶蛙版_3.3.12.apk ==="
