#!/usr/bin/env python3
"""Generate theme assets v2:
1. welcome_bg_pic.9.png — compiled via aapt2 (proper npTc, border stripped)
2. main_page_bg.9.png — naiwa centered, edge stretch bands, compiled via aapt2
3. Copy animation frames + icons + guide pages from repo theme/
"""
import os, subprocess, shutil, zipfile, sys
from PIL import Image, ImageDraw, ImageFilter

REPO = '/home/z/my-project/naiwa-idut'
WORK = '/home/z/my-project/build/work'
GEN = '/home/z/my-project/build/gen'
AAPT2 = '/home/z/my-project/tools/bt/android-14/aapt2'
TMP = '/home/z/my-project/build/aapt_gen'

os.makedirs(GEN, exist_ok=True)
os.makedirs(f'{TMP}/res/drawable', exist_ok=True)

BG = (255, 251, 239)        # ffbeff cream
INK = (254, 206, 14)        # fece0e naiwa yellow

# ============ 1. welcome_bg source 9-patch (1082x1922 incl border) ============
W, H = 1082, 1922
img = Image.new('RGB', (W, H), BG)
# vertical gradient: cream -> slightly warm bottom
top = Image.new('L', (W, H), 0)
td = ImageDraw.Draw(top)
for y in range(H):
    td.line([(0, y), (W, y)], fill=int(30 * (y / H)))
warm = Image.new('RGB', (W, H), (255, 244, 207))
img = Image.composite(warm, img, top)
# soft radial glow center
glow = Image.new('L', (W, H), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([200, 480, 882, 1440], fill=80)
glow = glow.filter(ImageFilter.GaussianBlur(200))
white = Image.new('RGB', (W, H), (255, 255, 255))
img = Image.composite(white, img, glow)
# border: white first
px = img.load()
for x in range(W):
    px[x, 0] = (255, 255, 255)
    px[x, H-1] = (255, 255, 255)
for y in range(H):
    px[0, y] = (255, 255, 255)
    px[W-1, y] = (255, 255, 255)
# full-stretch markers: top row x=1..1080, left col y=1..1920
for x in range(1, W-1):
    px[x, 0] = (0, 0, 0)
for y in range(1, H-1):
    px[0, y] = (0, 0, 0)
img.save(f'{TMP}/res/drawable/welcome_bg_pic.9.png')
print("welcome_bg source 9-patch saved")

# ============ 2. main_page_bg source 9-patch ============
naiwa = Image.open(f'{REPO}/naiwa.png').convert('RGBA')
nw, nh = naiwa.size  # 905x1439
# scale naiwa to height 1480
scale = 1480 / nh
nw2, nh2 = int(nw * scale), int(nh * scale)
naiwa_s = naiwa.resize((nw2, nh2), Image.LANCZOS)
img2 = Image.new('RGB', (W, H), BG)
# soft warm vertical gradient
grad = Image.new('L', (W, H), 0)
gd2 = ImageDraw.Draw(grad)
for y in range(H):
    gd2.line([(0, y), (W, y)], fill=int(50 * (y / H)))
img2 = Image.composite(Image.new('RGB', (W, H), (255, 240, 200)), img2, grad)
# paste naiwa centered (x offset on 1080 content width)
cx = (W - nw2) // 2
cy = (H - nh2) // 2
img2.paste(naiwa_s, (cx, cy), naiwa_s)
# border
px2 = img2.load()
for x in range(W):
    px2[x, 0] = (255, 255, 255)
    px2[x, H-1] = (255, 255, 255)
for y in range(H):
    px2[0, y] = (255, 255, 255)
    px2[W-1, y] = (255, 255, 255)
# edge stretch bands: top row x in [1,cx-1] and [cx+nw2+1, W-2]; left col y in [1,cy-1] and [cy+nh2+1, H-2]
for x in list(range(1, cx)) + list(range(cx + nw2 + 1, W - 1)):
    px2[x, 0] = (0, 0, 0)
for y in list(range(1, cy)) + list(range(cy + nh2 + 1, H - 1)):
    px2[0, y] = (0, 0, 0)
img2.save(f'{TMP}/res/drawable/main_page_bg.9.png')
print(f"main_page_bg source 9-patch saved (naiwa {nw2}x{nh2} at ({cx},{cy}))")

# ============ 3. compile both with aapt2 ============
r = subprocess.run([AAPT2, 'compile', '--dir', f'{TMP}/res', '-o', f'{TMP}/compiled.zip'],
                   capture_output=True, text=True, timeout=120)
print("aapt2 compile:", r.returncode, r.stderr[:300])
for name in ('welcome_bg_pic', 'main_page_bg'):
    zf = zipfile.ZipFile(f'{TMP}/compiled.zip')
    flat = zf.read(f'drawable_{name}.9.png.flat')
    i = flat.find(b'\x89PNG')
    png = flat[i:]
    iend = png.find(b'IEND')
    png = png[:iend+8]
    out = f'{GEN}/{name}.9.png'
    open(out, 'wb').write(png)
    im = Image.open(out)
    print(f"compiled {out}: {im.size} {im.mode} {len(png)} bytes")

# ============ 4. copy frames / icons / guides from repo ============
FRAMES_DST = f'{WORK}/res/mipmap-hdpi-v4'
for i in range(12):
    src = f'{REPO}/theme/frames/frame_{i:02d}.png'
    shutil.copyfile(src, f'{FRAMES_DST}/refresh_loading{i+1:02d}.png')
print("12 frames copied")

for d, f in [
    ('mipmap-mdpi-v4', 'ic_launcher.png'), ('mipmap-hdpi-v4', 'ic_launcher.png'),
    ('mipmap-xhdpi-v4', 'ic_launcher.png'), ('mipmap-xxhdpi-v4', 'ic_launcher.png'),
    ('mipmap-xxxhdpi-v4', 'ic_launcher.png'),
]:
    src = f'{REPO}/theme/icons/ic_launcher_{d.replace("mipmap-","").replace("-v4","")}.png'
    if not os.path.exists(src):
        src = f'{REPO}/theme/icons/ic_launcher_xxhdpi.png'
    shutil.copyfile(src, f'{WORK}/res/{d}/{f}')
shutil.copyfile(f'{REPO}/theme/icons/ic_app_launcher.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_app_launcher_round.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher_round.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_launcher_foreground.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_foreground.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_launcher_background.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_background.png')
print("icons copied")

os.makedirs(f'{WORK}/assets/UserGuide', exist_ok=True)
for i in range(4):
    shutil.copyfile(f'{REPO}/theme/feature_guide_{i}.png', f'{WORK}/assets/UserGuide/feature_guide_{i}.png')
print("guide pages copied")

# ============ 5. install compiled 9-patches into work tree ============
shutil.copyfile(f'{GEN}/welcome_bg_pic.9.png', f'{WORK}/res/drawable-xxhdpi-v4/welcome_bg_pic.9.png')
# main_page_bg: arsc string will be patched .jpg -> .png (same length)
open(f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.png', 'wb').write(open(f'{GEN}/main_page_bg.9.png','rb').read())
os.remove(f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.jpg')
print("9-patches installed")
