#!/usr/bin/env python3
"""Generate icons, main background, welcome text, and user guide images for NaiLong theme"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os
from collections import deque

WS = '/home/z/my-project/workspace'
OUT = f'{WS}/gen'
os.makedirs(OUT, exist_ok=True)

INK = (254, 206, 14)        # fece0e
BG = (255, 251, 239)        # fffbef
FG = (58, 44, 0)            # 3a2c00
MUTED = (143, 122, 69)      # 8f7a45

F_SERIF_BLACK = '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Black.ttf'
F_WENKAI = '/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Medium.ttf'
F_SANS_VAR = '/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf'

def font_black(size):
    return ImageFont.truetype(F_SERIF_BLACK, size)
def font_wk(size):
    return ImageFont.truetype(F_WENKAI, size)
def font_sans(size, weight=700):
    f = ImageFont.truetype(F_SANS_VAR, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

naiwa_sq = Image.open(f'{WS}/NaiWa-iDUT/naiwa (2).jpeg').convert('RGB')   # 1080x1080
naiwa_bg = Image.open(f'{WS}/NaiWa-iDUT/naiwa.png').convert('RGB')        # 905x1439
core = Image.open(f'{WS}/assets/core.webp').convert('RGBA')               # 720x720 alpha naiwa

# ============ extract naiwa character (remove white bg via border flood fill) ============
def extract_subject(img_rgb, thresh=232):
    """Flood fill from borders: connected near-white -> transparent"""
    w, h = img_rgb.size
    px = img_rgb.load()
    visited = bytearray(w * h)
    from collections import deque
    q = deque()
    # seed all border pixels
    for x in range(w):
        q.append((x, 0)); q.append((x, h-1))
    for y in range(h):
        q.append((0, y)); q.append((w-1, y))
    def is_white(p):
        return p[0] >= thresh and p[1] >= thresh and p[2] >= thresh
    while q:
        x, y = q.popleft()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        i = y * w + x
        if visited[i]:
            continue
        p = px[x, y]
        if not is_white(p):
            continue
        visited[i] = 1
        q.append((x+1, y)); q.append((x-1, y))
        q.append((x, y+1)); q.append((x, y-1))
    # alpha mask: 255 = keep, 0 = remove
    mask = Image.new('L', (w, h), 255)
    mpx = mask.load()
    for i in range(w * h):
        if visited[i]:
            mpx[i % w, i // w] = 0
    # feather edges slightly
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    out = img_rgb.convert('RGBA')
    out.putalpha(mask)
    return out

print("extracting naiwa subject from jpeg...")
naiwa_cut = extract_subject(naiwa_sq)
# crop to content bbox
bbox = naiwa_cut.getbbox()
naiwa_cut_c = naiwa_cut.crop(bbox)
print(f"extracted: {naiwa_cut_c.size}")
naiwa_cut_c.save(f'{OUT}/naiwa_cut.png')

def paste_center(base, img, cx, cy, target_h=None):
    if target_h:
        r = target_h / img.height
        img = img.resize((int(img.width * r), int(target_h)), Image.LANCZOS)
    base.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))
    return base

# ============ legacy launcher icons (full square with white bg) ============
def make_legacy_icon(size):
    icon = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    # cream radial tint
    glow = Image.new('L', (size, size), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-size*0.2, -size*0.2, size*1.2, size*1.2], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.25))
    cream = Image.new('RGBA', (size, size), BG + (255,))
    icon = Image.composite(cream, icon, glow)
    # naiwa fills ~82% height
    nh = int(size * 0.82)
    nai = naiwa_cut_c.resize((int(naiwa_cut_c.width * nh / naiwa_cut_c.height), nh), Image.LANCZOS)
    icon.alpha_composite(nai, ((size - nai.width) // 2, (size - nai.height) // 2))
    return icon

def make_round_icon(size):
    icon = make_legacy_icon(size)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    mask = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([0, 0, size-1, size-1], fill=255)
    out.paste(icon, (0, 0), mask)
    return out

# ic_launcher: all densities
for dens, size in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
    make_legacy_icon(size).save(f'{OUT}/ic_launcher_{dens}.png', optimize=True)
    print(f"ic_launcher_{dens}.png done")
# ic_app_launcher (xxhdpi 144) + round
make_legacy_icon(144).save(f'{OUT}/ic_app_launcher.png', optimize=True)
make_round_icon(144).save(f'{OUT}/ic_app_launcher_round.png', optimize=True)
print("app launcher icons done")

# adaptive icon: background solid yellow, foreground extracted naiwa (324x324)
fg_icon = Image.new('RGBA', (324, 324), (0, 0, 0, 0))
paste_center(fg_icon, naiwa_cut_c, 162, 162, target_h=int(324 * 0.62))
fg_icon.save(f'{OUT}/ic_launcher_foreground.png', optimize=True)
bg_icon = Image.new('RGBA', (324, 324), INK + (255,))
# subtle radial: lighter center
glow = Image.new('L', (324, 324), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([40, 40, 284, 284], fill=110)
glow = glow.filter(ImageFilter.GaussianBlur(70))
light = Image.new('RGBA', (324, 324), (255, 226, 80, 255))
bg_icon = Image.composite(light, bg_icon, glow)
bg_icon.save(f'{OUT}/ic_launcher_background.png', optimize=True)
print("adaptive icon layers done")

# ============ main_page_bg.jpg (1080x1920 from naiwa.png) ============
w, h = naiwa_bg.size  # 905x1439
# scale to fill 1080x1920: scale = max(1080/905, 1920/1439)
scale = max(1080 / w, 1920 / h)
nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
big = naiwa_bg.resize((nw, nh), Image.LANCZOS)
left, top = (nw - 1080) // 2, (nh - 1920) // 2
mainbg = big.crop((left, top, left + 1080, top + 1920))
mainbg.save(f'{OUT}/main_page_bg.jpg', quality=88, optimize=True)
print("main_page_bg.jpg:", os.path.getsize(f'{OUT}/main_page_bg.jpg'))

# ============ icon_login_welcome_txt.png (396x66) ============
txt = Image.new('RGBA', (396, 66), (0, 0, 0, 0))
d = ImageDraw.Draw(txt)
f = font_black(48)
bbox = d.textbbox((0, 0), '中国奶龙大学', font=f)
tw = bbox[2] - bbox[0]
d.text(((396 - tw) / 2, 4), '中国奶龙大学', font=f, fill=FG + (255,))
txt = txt.filter(ImageFilter.GaussianBlur(0.3))
txt.save(f'{OUT}/icon_login_welcome_txt.png', optimize=True)
print("icon_login_welcome_txt.png done")

# ============ UserGuide feature_guide_0..3.png (1080x1920) ============
guide_texts = [
    ('欢迎使用奶蛙 i大工', '奶龙为你护送一切校园服务'),
    ('奶蛙校园通', '课表、成绩、一卡通全都装进奶龙的肚子里'),
    ('扫码与门禁', '让奶龙帮你扫码开门、借书、刷卡'),
    ('开始奶龙之旅', '点击下方按钮进入中国奶龙大学'),
]
for i, (title, sub) in enumerate(guide_texts):
    g = Image.new('RGBA', (1080, 1920), BG + (255,))
    d = ImageDraw.Draw(g)
    # soft yellow glow circle behind naiwa
    glow = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([240, 240, 840, 840], fill=INK + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    g.alpha_composite(glow)
    # naiwa character
    paste_center(g, naiwa_cut_c, 540, 540, target_h=560)
    # title
    f1 = font_black(88)
    bbox = d.textbbox((0, 0), title, font=f1)
    tw = bbox[2] - bbox[0]
    d.text(((1080 - tw) / 2, 1080), title, font=f1, fill=FG + (255,))
    # subtitle
    f2 = font_wk(46)
    bbox = d.textbbox((0, 0), sub, font=f2)
    tw = bbox[2] - bbox[0]
    d.text(((1080 - tw) / 2, 1230), sub, font=f2, fill=MUTED + (255,))
    # progress dots (4 pages)
    for k in range(4):
        cx = 540 + (k - 1.5) * 60
        if k == i:
            d.ellipse([cx - 14, 1490 - 14, cx + 14, 1490 + 14], fill=INK + (255,))
        else:
            d.ellipse([cx - 10, 1490 - 10, cx + 10, 1490 + 10], fill=MUTED + (120,))
    # bottom yellow bar
    d.rectangle([0, 1860, 1080, 1920], fill=INK + (255,))
    g.convert('RGB').save(f'{OUT}/feature_guide_{i}.png', optimize=True)
    print(f"feature_guide_{i}.png done")
print("ALL ASSETS DONE")
