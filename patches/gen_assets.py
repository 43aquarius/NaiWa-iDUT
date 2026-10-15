#!/usr/bin/env python3
"""
NaiLong (奶龙/奶蛙) theme asset generation for i大工 app.
Generates: 12 animation frames, 9-patch welcome bg, icons, background, text art.

Website reference (中国奶龙大学.com):
  --bg: #fffbef, --fg: #3a2c00, --muted: #8f7a45, --ink: #fece0e
  Badge: white disc + rotating text ring (ring.webp) + core naiwa (core.webp)
  + progress ring (track rgba(254,206,14,.22), bar #fece0e)
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import struct, math, os

WS = '/home/z/my-project/workspace'
OUT = f'{WS}/gen'
os.makedirs(OUT, exist_ok=True)
os.makedirs(f'{OUT}/frames', exist_ok=True)

# palette
INK = (254, 206, 14)        # fece0e 奶龙黄
BG = (255, 251, 239)        # ffbeff cream
FG = (58, 44, 0)            # 3a2c00 dark
MUTED = (143, 122, 69)      # 8f7a45

# fonts
F_BOLD = '/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf'
F_SERIF_BLACK = '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Black.ttf'
F_WENKAI = '/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Medium.ttf'

def font_bold(size, weight=700):
    f = ImageFont.truetype(F_BOLD, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

def font_black(size):
    return ImageFont.truetype(F_SERIF_BLACK, size)

def font_wk(size):
    return ImageFont.truetype(F_WENKAI, size)

# ---- source art ----
ring = Image.open(f'{WS}/assets/ring.webp').convert('RGBA')      # 720x720 text ring
core = Image.open(f'{WS}/assets/core.webp').convert('RGBA')      # 720x720 naiwa core

def draw_text_center(draw, cx, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)

# ============ 1. Animation frames (480x640, transparent) ============
FRAME_W, FRAME_H = 480, 640
BADGE_D = 300                 # badge diameter
BCX, BCY = 240, 215           # badge center
ARC_R = 168                   # progress arc radius (outside badge)
STROKE = 7

def polar_point(cx, cy, r, deg):
    rad = math.radians(deg - 90)   # 0deg = top, clockwise
    return (cx + r * math.cos(rad), cy + r * math.sin(rad))

def arc_bbox(cx, cy, r):
    return [cx - r, cy - r, cx + r, cy + r]

N_FRAMES = 12
for i in range(N_FRAMES):
    frame = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))

    # --- soft drop shadow under badge ---
    shadow = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sb = BADGE_D / 2 + 6
    sd.ellipse([BCX - sb, BCY - sb + 14, BCX + sb, BCY + sb + 14], fill=(58, 44, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    frame.alpha_composite(shadow)

    d = ImageDraw.Draw(frame)

    # --- progress track ring (translucent yellow) ---
    d.arc(arc_bbox(BCX, BCY, ARC_R), 0, 360, fill=INK + (56,), width=STROKE)

    # --- progress arc: fills up over the 12 frames (like the website 2.6s fill) ---
    sweep = (i + 1) / N_FRAMES * 360.0
    if sweep > 0:
        d.arc(arc_bbox(BCX, BCY, ARC_R), 0, sweep, fill=INK + (255,), width=STROKE)
    # arc start cap dot
    d.ellipse([BCX - 4, BCY - ARC_R - 4, BCX + 4, BCY - ARC_R + 4], fill=INK + (255,))

    # --- white disc badge ---
    rb = BADGE_D / 2
    d.ellipse([BCX - rb, BCY - rb, BCX + rb, BCY + rb], fill=(255, 255, 255, 255))

    # --- rotating text ring (30 deg per frame) ---
    angle = i * (360.0 / N_FRAMES)
    ring_s = ring.resize((BADGE_D, BADGE_D), Image.LANCZOS)
    ring_r = ring_s.rotate(angle, resample=Image.BICUBIC, expand=False)
    frame.alpha_composite(ring_r, (int(BCX - BADGE_D / 2), int(BCY - BADGE_D / 2)))

    # --- core naiwa with breathing scale (like website breathe 1.8s) ---
    breathe = 1.0 + 0.016 * math.sin(2 * math.pi * i / N_FRAMES)
    core_d = int(BADGE_D * 0.98 * breathe)
    core_s = core.resize((core_d, core_d), Image.LANCZOS)
    frame.alpha_composite(core_s, (int(BCX - core_d / 2), int(BCY - core_d / 2)))

    # --- title & subtitle ---
    d2 = ImageDraw.Draw(frame)
    draw_text_center(d2, 240, 400, '中国奶龙大学', font_black(52), FG + (255,))
    # animated dots: i%3+1 dots (like the website's bouncing dots)
    ndots = (i % 3) + 1
    dots = '.' * ndots
    sub = f'奶龙正在护送你前往{dots}'
    draw_text_center(d2, 240, 486, sub, font_wk(30), MUTED + (255,))

    frame.save(f'{OUT}/frames/frame_{i:02d}.png', optimize=True)
print(f"generated {N_FRAMES} frames")

# ============ 2. welcome_bg_pic.9.png (1080x1920 full-stretch) ============
src9 = f'{WS}/apk_orig/res/drawable-xxhdpi-v4/welcome_bg_pic.9.png'
orig = open(src9, 'rb').read()

# extract npTc chunk from original
def extract_chunk(data, ctype):
    pos = 8
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        ct = data[pos+4:pos+8]
        if ct == ctype.encode():
            return data[pos+8:pos+8+length], data[pos:pos+12+length]
        if ct == b'IEND':
            break
        pos += 12 + length
    return None, None

nptc, nptc_full = extract_chunk(orig, 'npTc')
nptc, nptc_full = extract_chunk(orig, 'npTc')
print(f"npTc chunk: {len(nptc)} bytes")

# build new 9-patch: cream bg + soft radial glow + full black borders
img9 = Image.new('RGB', (1080, 1920), BG)
# radial glow: brighter center, slightly warm edges
glow = Image.new('L', (1080, 1920), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([190, 460, 890, 1460], fill=90)
glow = glow.filter(ImageFilter.GaussianBlur(220))
warm = Image.new('RGB', (1080, 1920), (255, 255, 255))
img9 = Image.composite(warm, img9, glow)
# subtle bottom warm band (naiwa yellow tint, like a sunrise)
band = Image.new('L', (1080, 1920), 0)
bd = ImageDraw.Draw(band)
bd.rectangle([0, 1720, 1080, 1920], fill=70)
band = band.filter(ImageFilter.GaussianBlur(90))
yellowish = Image.new('RGB', (1080, 1920), (254, 226, 120))
img9 = Image.composite(yellowish, img9, band)
# paint borders (full stretch = all black, matching original npTc full-stretch)
px = img9.load()
for x in range(1080):
    px[x, 0] = (0, 0, 0)
for y in range(1920):
    px[0, y] = (0, 0, 0)
img9.save(f'{OUT}/welcome_bg_pic.9.png')

# re-insert npTc chunk into the new PNG
data = open(f'{OUT}/welcome_bg_pic.9.png', 'rb').read()
# insert npTc before IEND
iend_pos = data.rfind(b'IEND') - 4
new_data = data[:iend_pos] + nptc_full + data[iend_pos:]
open(f'{OUT}/welcome_bg_pic.9.png', 'wb').write(new_data)
print("welcome_bg_pic.9.png with npTc:", os.path.getsize(f'{OUT}/welcome_bg_pic.9.png'), "bytes")
