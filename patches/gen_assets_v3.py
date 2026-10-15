#!/usr/bin/env python3
"""NaiWa v3 asset generation.
v2 assets + v3 additions:
  1. welcome_bg_pic.9.png — cream gradient + NAIWA MASCOT + 「中国奶龙大学」 title
     (strong static fallback: even if the animation code fails, cold-start window shows naiwa)
  2. main_page_bg.9.png — naiwa centered 9-patch (aapt2 compiled)
  3. bg_mine_panel.9.png — "我的"页面内容面板: naiwa image + white veil + rounded top corners
     (replaces the white panel so the whole Mine page IS the naiwa image)
  4. animation frames -> mipmap refresh_loading01-12
  5. launcher icons
  6. guide pages
  7. v3 NEW: naiwa default avatars (custom_head_bg_*) + app_def + empty-state images
"""
import os, subprocess, shutil, zipfile, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = '/home/z/my-project/NaiWa-iDUT'
WORK = f'{REPO}/work/build'
GEN = f'{REPO}/work/gen'
ASSETS = f'{REPO}/work/naiwa_assets'
AAPT2 = '/home/z/tools/android-14/aapt2'
TMP = f'{REPO}/work/aapt_gen'

os.makedirs(GEN, exist_ok=True)
os.makedirs(f'{TMP}/res/drawable', exist_ok=True)

BG = (255, 251, 239)        # FFFBEF cream
INK = (254, 206, 14)        # FECE0E naiwa yellow

# ---------- helpers ----------
def add_9patch_markers_full(img):
    """Full-stretch 9-patch: black markers along entire top row + left col (inside 1px border)."""
    W, H = img.size
    px = img.load()
    for x in range(W):
        px[x, 0] = (255, 255, 255)
        px[x, H-1] = (255, 255, 255)
    for y in range(H):
        px[0, y] = (255, 255, 255)
        px[W-1, y] = (255, 255, 255)
    for x in range(1, W-1):
        px[x, 0] = (0, 0, 0)
    for y in range(1, H-1):
        px[0, y] = (0, 0, 0)
    return img

def compile_9patches(names):
    r = subprocess.run([AAPT2, 'compile', '--dir', f'{TMP}/res', '-o', f'{TMP}/compiled.zip'],
                       capture_output=True, text=True, timeout=180)
    print("aapt2 compile rc:", r.returncode, r.stderr[:200])
    zf = zipfile.ZipFile(f'{TMP}/compiled.zip')
    for name in names:
        flat = zf.read(f'drawable_{name}.9.png.flat')
        i = flat.find(b'\x89PNG')
        png = flat[i:]
        iend = png.find(b'IEND')
        png = png[:iend+8]
        out = f'{GEN}/{name}.9.png'
        open(out, 'wb').write(png)
        im = Image.open(out)
        print(f"  compiled {name}.9.png: {im.size} {im.mode} {len(png)}B")

def find_font(size):
    # Chinese-capable fonts first
    for p in ('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
              '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
              '/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Regular.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size), p
            except Exception:
                pass
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size), p
            except Exception:
                pass
    return ImageFont.load_default(), 'default'

# ============ 1. welcome_bg: cream + mascot + title ============
W, H = 1082, 1922  # includes 1px 9-patch border
img = Image.new('RGB', (W, H), BG)
# vertical gradient cream -> warm
top = Image.new('L', (W, H), 0)
td = ImageDraw.Draw(top)
for y in range(H):
    td.line([(0, y), (W, y)], fill=int(36 * (y / H)))
warm = Image.new('RGB', (W, H), (255, 243, 205))
img = Image.composite(warm, img, top)
# soft radial glow center
glow = Image.new('L', (W, H), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([240, 560, 842, 1360], fill=90)
glow = glow.filter(ImageFilter.GaussianBlur(180))
white = Image.new('RGB', (W, H), (255, 255, 255))
img = Image.composite(white, img, glow)

# paste naiwa cutout centered (content area 1080x1920)
naiwa = Image.open(f'{REPO}/theme/naiwa_cut.png').convert('RGBA')
nh = 760
nw = int(naiwa.width * nh / naiwa.height)
naiwa_s = naiwa.resize((nw, nh), Image.LANCZOS)
cx, cy = (W - nw) // 2, 640
img.paste(naiwa_s, (cx, cy), naiwa_s)
# soft shadow under mascot
sh = Image.new('L', (W, H), 0)
sd = ImageDraw.Draw(sh)
sd.ellipse([cx+30, cy+nh-60, cx+nw-30, cy+nh-10], fill=70)
sh = sh.filter(ImageFilter.GaussianBlur(24))
dark = Image.new('RGB', (W, H), (212, 190, 140))
img = Image.composite(dark, img, sh)

# title 中国奶龙大学 + subtitle
f_title, fp = find_font(96)
f_sub, _ = find_font(44)
dr = ImageDraw.Draw(img)
title = '中国奶龙大学'
sub = '奶龙正在护送你前往……'
tb = dr.textbbox((0, 0), title, font=f_title)
tw = tb[2] - tb[0]
dr.text(((W - tw) / 2, 1520), title, fill=(58, 44, 0), font=f_title)
sb = dr.textbbox((0, 0), sub, font=f_sub)
sw = sb[2] - sb[0]
dr.text(((W - sw) / 2, 1660), sub, fill=(150, 120, 40), font=f_sub)
print("welcome_bg composed with mascot + title (font:", fp, ")")

img = add_9patch_markers_full(img)
img.save(f'{TMP}/res/drawable/welcome_bg_pic.9.png')

# ============ 2. main_page_bg: naiwa centered 9-patch ============
naiwa_full = Image.open(f'{REPO}/naiwa.png').convert('RGBA')
scale = 1480 / naiwa_full.height
nw2, nh2 = int(naiwa_full.width * scale), int(scale * naiwa_full.height)
naiwa_s2 = naiwa_full.resize((nw2, nh2), Image.LANCZOS)
img2 = Image.new('RGB', (W, H), BG)
grad = Image.new('L', (W, H), 0)
gd2 = ImageDraw.Draw(grad)
for y in range(H):
    gd2.line([(0, y), (W, y)], fill=int(50 * (y / H)))
img2 = Image.composite(Image.new('RGB', (W, H), (255, 240, 200)), img2, grad)
cx = (W - nw2) // 2
cy = (H - nh2) // 2
img2.paste(naiwa_s2, (cx, cy), naiwa_s2)
px2 = img2.load()
for x in range(W):
    px2[x, 0] = (255, 255, 255)
    px2[x, H-1] = (255, 255, 255)
for y in range(H):
    px2[0, y] = (255, 255, 255)
    px2[W-1, y] = (255, 255, 255)
# edge stretch bands: top row outside naiwa; left col outside naiwa
for x in list(range(1, cx)) + list(range(cx + nw2 + 1, W - 1)):
    px2[x, 0] = (0, 0, 0)
for y in list(range(1, cy)) + list(range(cy + nh2 + 1, H - 1)):
    px2[0, y] = (0, 0, 0)
img2.save(f'{TMP}/res/drawable/main_page_bg.9.png')
print(f"main_page_bg source saved (naiwa {nw2}x{nh2} at ({cx},{cy}))")

# ============ 3. mine panel: naiwa + veil + rounded corners ============
# Panel is drawn stretched over the content area below the 107dp header strip.
# Design: naiwa image with a white veil (readable content), rounded TOP corners.
img3 = Image.new('RGB', (W, H), BG)
grad3 = Image.new('L', (W, H), 0)
gd3 = ImageDraw.Draw(grad3)
for y in range(H):
    gd3.line([(0, y), (W, y)], fill=int(50 * (y / H)))
img3 = Image.composite(Image.new('RGB', (W, H), (255, 240, 200)), img3, grad3)
img3.paste(naiwa_s2, (cx, cy), naiwa_s2)
# white veil: stronger at top (profile area 59%), lighter at bottom (35%)
veil = Image.new('L', (W, H), 0)
vd = ImageDraw.Draw(veil)
for y in range(H):
    vd.line([(0, y), (W, y)], fill=int(150 - 60 * (y / H)))  # 150 -> 90
veil_img = Image.new('RGB', (W, H), (255, 255, 255))
img3 = Image.composite(veil_img, img3, veil)
# rounded top corners (match orig bg_mine_panel style), content-area coords +1 border offset
RAD = 66
mask = Image.new('L', (W, H), 255)
md = ImageDraw.Draw(mask)
md.rectangle([0, 0, W, RAD + 2], fill=0)
md.rounded_rectangle([0, 0, W, RAD * 2 + 40], radius=RAD, fill=255)
img3.putalpha(mask)
img3 = img3.convert('RGBA')
# 9-patch markers (border is 1px frame around 1080x1920 content):
#   top row: black marker at x where the COLUMN may stretch (outside naiwa columns);
#   left col: black marker at y where the ROW may stretch (outside naiwa rows);
#   all other border pixels: fully transparent.
px3 = img3.load()
for x in range(W):
    px3[x, 0] = (0, 0, 0, 255) if (x < cx or x > cx + nw2) else (0, 0, 0, 0)
    px3[x, H-1] = (0, 0, 0, 0)
for y in range(H):
    px3[0, y] = (0, 0, 0, 255) if (y < cy or y > cy + nh2) else (0, 0, 0, 0)
    px3[W-1, y] = (0, 0, 0, 0)
# aapt2 requires the four corner pixels to be opaque white or transparent
px3[0, 0] = (0, 0, 0, 0)
px3[W-1, 0] = (0, 0, 0, 0)
px3[0, H-1] = (0, 0, 0, 0)
px3[W-1, H-1] = (0, 0, 0, 0)
img3.save(f'{TMP}/res/drawable/bg_mine_panel.9.png')
print("mine panel source saved (veil + rounded corners)")

# compile all three
compile_9patches(['welcome_bg_pic', 'main_page_bg', 'bg_mine_panel'])

# ============ 4. frames -> mipmap ============
FRAMES_DST = f'{WORK}/res/mipmap-hdpi-v4'
for i in range(12):
    shutil.copyfile(f'{REPO}/theme/frames/frame_{i:02d}.png',
                    f'{FRAMES_DST}/refresh_loading{i+1:02d}.png')
print("12 frames copied")

# ============ 5. icons ============
for d in ('mipmap-mdpi-v4', 'mipmap-hdpi-v4', 'mipmap-xhdpi-v4', 'mipmap-xxhdpi-v4', 'mipmap-xxxhdpi-v4'):
    shutil.copyfile(f'{REPO}/theme/icons/ic_launcher_xxhdpi.png', f'{WORK}/res/{d}/ic_launcher.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_app_launcher.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_app_launcher_round.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher_round.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_launcher_foreground.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_foreground.png')
shutil.copyfile(f'{REPO}/theme/icons/ic_launcher_background.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_background.png')
print("icons copied")

# ============ 6. guide pages ============
os.makedirs(f'{WORK}/assets/UserGuide', exist_ok=True)
for i in range(4):
    shutil.copyfile(f'{REPO}/theme/feature_guide_{i}.png', f'{WORK}/assets/UserGuide/feature_guide_{i}.png')
print("guide pages copied")

# ============ 7. install 9-patches into build tree ============
shutil.copyfile(f'{GEN}/welcome_bg_pic.9.png', f'{WORK}/res/drawable-xxhdpi-v4/welcome_bg_pic.9.png')
open(f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.png', 'wb').write(open(f'{GEN}/main_page_bg.9.png', 'rb').read())
if os.path.exists(f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.jpg'):
    os.remove(f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.jpg')
shutil.copyfile(f'{GEN}/bg_mine_panel.9.png', f'{WORK}/res/drawable-xxhdpi-v4/bg_mine_panel.9.png')
print("9-patches installed into build tree")

# ============ 8. v3: naiwa avatars + empty states ============
XX = f'{WORK}/res/drawable-xxhdpi-v4'

def naiwa_face(size):
    """Naiwa head from the launcher icon art (naiwa (2).jpeg is a face-on shot)."""
    src = Image.open(f'{REPO}/naiwa (2).jpeg').convert('RGBA')
    s = min(src.size)
    left = (src.width - s) // 2
    top = (src.height - s) // 2
    src = src.crop((left, top, left + s, top + s)).resize((size, size), Image.LANCZOS)
    return src

# 8a. default avatars (custom_head_bg_* are the avatar placeholders; keep same canvas size)
for name in ('custom_head_bg_default', 'custom_head_bg_boy', 'custom_head_bg_girl',
             'custom_head_bg_org', 'custom_head_bg_parent'):
    p = f'{XX}/{name}.png'
    if os.path.exists(p):
        old = Image.open(p)
        sz = old.size
        face = naiwa_face(max(sz)).resize(sz, Image.LANCZOS)
        # circular mask like a head portrait
        mask = Image.new('L', sz, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, sz[0]-1, sz[1]-1], fill=255)
        out = Image.new('RGBA', sz, (255, 251, 239, 255))
        out.paste(face, (0, 0), mask)
        out.save(p)
        print(f"  avatar {name} -> naiwa {sz}")

# 8b. app_def (default H5 app icon placeholder 180x180)
p = f'{XX}/app_def.png'
if os.path.exists(p):
    sz = Image.open(p).size
    naiwa_face(max(sz)).resize(sz, Image.LANCZOS).save(p)
    print(f"  app_def -> naiwa {sz}")

# 8c. empty state images: mascot + 奶蛙 bubble
mascot = Image.open(f'{ASSETS}/naiwa_start_mascot.webp').convert('RGBA')
def empty_state(w, h, text=None):
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    m = mascot.copy()
    m.thumbnail((int(w * 0.42), int(h * 0.9)), Image.LANCZOS)
    mx = (w - m.width) // 2
    my = (h - m.height) // 2
    canvas.paste(m, (mx, my), m)
    if text:
        f, _ = find_font(int(h * 0.14))
        dr = ImageDraw.Draw(canvas)
        bb = dr.textbbox((0, 0), text, font=f)
        tw = bb[2] - bb[0]
        dr.text(((w - tw) / 2, h - int(h * 0.18)), text, fill=(190, 160, 90, 255), font=f)
    return canvas

EMPTY_MAP = {
    'icon_chatlist_empty.png': None,
    'icon_app_or_file_empty.png': None,
    'icon_custom_org_empty.png': None,
    'icon_connect_book_or_search_result_empty.png': None,
    'icon_my_collected_notice_empty.png': None,
    'icon_my_received_notice_empty.png': None,
    'icon_my_sended_notice_empty.png': None,
    'icon_notice_delay_read_state_empty.png': None,
    'icon_notice_readed_empty.png': None,
    'icon_notice_unreaded_empty.png': None,
}
# NOTE: icon_service_empty / icon_my_service_empty / icon_card_manage_*_empty_view are
# FUNCTION icons (clover/bookmark/card+), NOT empty-state placeholders — do not replace.
for name, spec in EMPTY_MAP.items():
    p = f'{XX}/{name}'
    if not os.path.exists(p):
        continue
    old = Image.open(p)
    sz = old.size
    es = empty_state(*sz)
    es.save(p)
    print(f"  empty {name} -> naiwa mascot {sz}")

# 8d. web-downloaded mascot gallery sheet for the about page? (skip - keep scope tight)
print("\nGEN ASSETS V3 DONE")
