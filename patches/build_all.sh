#!/usr/bin/env bash
# Full NaiWa v2 build pipeline
set -e
cd /home/z/my-project
B=/home/z/my-project/build

echo "=== 1. Reset work tree from original ==="
rm -rf $B/work
mkdir -p $B/work
cp -r $B/orig/res $B/work/res
cp -r $B/orig/assets $B/work/assets
cp $B/orig/resources.arsc $B/work/resources.arsc
cp $B/orig/AndroidManifest.xml $B/work/AndroidManifest.xml

echo "=== 2. Generate assets (9-patches via aapt2, frames, icons, guides) ==="
python3 scripts/gen_assets_v2.py | tail -6

echo "=== 3. Generate welcome_layout.xml (AXML writer) ==="
python3 scripts/gen_welcome_layout.py | tail -2

echo "=== 4. Patch activity_main + fragment_tab_service ==="
python3 scripts/patch_layouts.py | tail -4

echo "=== 5. Recolor values (arsc + XMLs, wide net) ==="
python3 scripts/recolor_v2.py | tail -4

echo "=== 6. Recolor images (pixel-level) ==="
python3 scripts/recolor_images.py 2>/dev/null | tail -2

echo "=== 7. Assemble APK ==="
python3 scripts/assemble_apk.py | tail -4

echo "=== 8. Zipalign + sign ==="
export LD_LIBRARY_PATH=/home/z/my-project/tools/bt/android-14/lib64
rm -f $B/aligned.apk "$B/i大工_奶蛙版_3.3.12_v2.apk"
$B/../tools/bt/android-14/zipalign -f -p 4 $B/unsigned.apk $B/aligned.apk
java -jar /home/z/my-project/tools/bt/android-14/lib/apksigner.jar sign \
    --ks $B/naiwa.keystore --ks-pass pass:nailong2026 --key-pass pass:nailong2026 \
    --ks-key-alias nailong \
    --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
    --out "$B/i大工_奶蛙版_3.3.12_v2.apk" $B/aligned.apk
java -jar /home/z/my-project/tools/bt/android-14/lib/apksigner.jar verify "$B/i大工_奶蛙版_3.3.12_v2.apk" && echo "SIGNATURE OK"
ls -la "$B/i大工_奶蛙版_3.3.12_v2.apk"
echo "=== BUILD DONE ==="
