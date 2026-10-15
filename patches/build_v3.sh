#!/usr/bin/env bash
# NaiWa v3 full build pipeline (reproducible)
# Env: JDK17+, Android build-tools r34 at /home/z/tools/android-14,
#      smali/baksmali 2.5.2 + guava + jcommander 1.78 + antlr-runtime at /home/z/tools/smali_lib,
#      python3 + PIL + numpy
set -e
cd /home/z/my-project/NaiWa-iDUT
W=work
BT=/home/z/tools/android-14
SMALI_CP='/home/z/tools/smali_lib/*'

echo "=== 0. (once) unpack + disassemble original ==="
if [ ! -d $W/orig ]; then
  mkdir -p $W && cd $W
  unzip -q -o "../i大工_3.3.12.75026.apk" -d orig
  java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble orig/classes.dex -o smali_work/smali_classes
  java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble orig/classes2.dex -o smali_work/smali_classes2
  cd ..
fi

echo "=== 1. Reset build tree from original ==="
rm -rf $W/build && mkdir -p $W/build
cp -r $W/orig/res $W/build/res
cp -r $W/orig/assets $W/build/assets
cp $W/orig/resources.arsc $W/build/resources.arsc
cp $W/orig/AndroidManifest.xml $W/build/AndroidManifest.xml
# reset smali_work from orig (re-disassemble to pristine)
rm -rf $W/smali_work
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble $W/orig/classes.dex -o $W/smali_work/smali_classes
java -cp "$SMALI_CP" org.jf.baksmali.Main disassemble $W/orig/classes2.dex -o $W/smali_work/smali_classes2

echo "=== 2. Generate assets (9-patch via aapt2, frames, icons, guides, avatars, empty states) ==="
python3 patches/gen_assets_v3.py | tail -8

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
  --ks ../naiwa.keystore --ks-pass pass:nailong2026 --key-pass pass:nailong2026 \
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
cd ../..

cp "$W/build/i大工_奶蛙版_3.3.12.apk" "i大工_奶蛙版_3.3.12.apk"
echo "=== BUILD DONE: i大工_奶蛙版_3.3.12.apk ==="
