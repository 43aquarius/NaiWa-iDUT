#!/usr/bin/env python3
"""NaiWa v4 asset generation — fixes user feedback round 3:
  1. welcome_bg_pic.9.png -> PURE gradient (no mascot/title baked) so no aspect
     distortion on tall screens; all content lives in the animation frames.
  2. Bottom tab icons (12) from 合成大奶蛙 sprites: main/message/service/me/notice/notes x nor/pre
  3. Service page filter icons (6): all/study/office/life/social/game
  4. Other high-visibility icons: home logo, about logo, contacts, favorites,
     sex badges, identity flags, gift coin, score, chat glyphs
Only overwrites existing PNG files in work/build/res/drawable-xxhdpi-v4
(same names -> no resources.arsc changes needed).
"""
import os, subprocess, zipfile, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

REPO = '/home/z/my-project/NaiWa-iDUT'
WORK = f'{REPO}/work/build'
GEN = f'{REPO}/work/gen'
XX = f'{WORK}/res/drawable-xxhdpi-v4'
BNW = f'{REPO}/work/naiwa_assets/bignaiwa_fruits'
NXL = f'{REPO}/work/naiwa_assets'
AAPT2 = '/home/z/tools/android-14/aapt2'
TMP = f'{REPO}/work/aapt_gen'

os.makedirs(GEN, exist_ok=True)
os.makedirs(f'{TMP}/res/drawable', exist_ok=True)

BG = (255, 251, 239)        # cream
INK = (254, 206, 14)        # naiwa yellow

def C(path):
    return Image.open(path).convert('RGBA')

def sprite(name):
    return C(f'{BNW}/{name}.webp')

def nxl(name):
    return C(f'{NXL}/{name}.webp')

def find_font(size, bold=True):
    cands = (['/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf',
              '/usr/share/fonts/truetype/chinese/NotoSansSC-SemiBold.ttf',
              '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'] if bold else
             ['/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
              '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'])
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def desat(im, amount=0.5):
    """Blend toward grayscale by amount."""
    g = im.convert('LA').convert('RGBA')
    return Image.blend(im, g, amount)

def fit(im, box):
    im2 = im.copy()
    im2.thumbnail((box, box), Image.LANCZOS)
    return im2

def glow_disc(size, color=(254, 206, 14), alpha=110, soft=0.9):
    d = Image.new('L', (size, size), 0)
    dd = ImageDraw.Draw(d)
    r = int(size / 2 * soft)
    dd.ellipse([size//2 - r, size//2 - r, size//2 + r, size//2 + r], fill=alpha)
    d = d.filter(ImageFilter.GaussianBlur(size * 0.10))
    disc = Image.new('RGBA', (size, size), color + (0,))
    disc.putalpha(d)
    return disc

def shadow_ellipse(w, h, alpha=70, blur=6):
    s = Image.new('L', (w, h), 0)
    sd = ImageDraw.Draw(s)
    sd.ellipse([w*0.18, h*0.62, w*0.82, h*0.92], fill=alpha)
    s = s.filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new('RGBA', (w, h), (120, 95, 30, 0))
    sh.putalpha(s)
    return sh

def tab_icon(name, size=60, selected=False):
    """Bottom nav icon: BigNaiWa sprite; nor = desat + smaller, pre = vivid + glow."""
    im = sprite(name)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    if selected:
        canvas.alpha_composite(glow_disc(size, alpha=95))
        body = fit(im, int(size * 0.84))
        canvas.alpha_composite(shadow_ellipse(size, size, 60, 5))
    else:
        body = fit(desat(im, 0.55), int(size * 0.70))
        body = body.copy()
        a = body.split()[3].point(lambda p: int(p * 0.92))
        body.putalpha(a)
    canvas.alpha_composite(body, ((size - body.width) // 2, (size - body.height) // 2 - (2 if selected else 0)))
    return canvas

def svc_icon(name, size=78):
    """Service filter chip icon: vivid sprite + soft glow, slight drop shadow."""
    im = sprite(name)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(glow_disc(size, alpha=60))
    canvas.alpha_composite(shadow_ellipse(size, size, 50, 5))
    body = fit(im, int(size * 0.88))
    canvas.alpha_composite(body, ((size - body.width) // 2, (size - body.height) // 2))
    return canvas

def naiwa_face(size):
    """Square face crop from naiwa (2).jpeg."""
    src = C(f'{REPO}/naiwa (2).jpeg')
    s = min(src.size)
    l = (src.width - s) // 2
    t = (src.height - s) // 2
    return src.crop((l, t, l + s, t + s)).resize((size, size), Image.LANCZOS)

def circle_masked(im, size=None):
    """Ellipse-mask an image (kept aspect via prior resize)."""
    w, h = im.size
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, w - 1, h - 1], fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out

# ============ 1. welcome_bg_pic: PURE gradient (no content -> no distortion) ============
W, H = 1082, 1922  # incl 1px 9-patch border
img = Image.new('RGB', (W, H), BG)
top = Image.new('L', (W, H), 0)
td = ImageDraw.Draw(top)
for y in range(H):
    td.line([(0, y), (W, y)], fill=int(44 * (y / H)))
img = Image.composite(Image.new('RGB', (W, H), (255, 243, 205)), img, top)
# soft radial glow where the animation badge sits (center ~ y 960*... badge at 640..1400)
glow = Image.new('L', (W, H), 0)
gd = ImageDraw.Draw(glow)
gd.ellipse([190, 420, 892, 1500], fill=80)
glow = glow.filter(ImageFilter.GaussianBlur(200))
img = Image.composite(Image.new('RGB', (W, H), (255, 255, 255)), img, glow)
# subtle bottom warm band
band = Image.new('L', (W, H), 0)
bd = ImageDraw.Draw(band)
for y in range(1500, H):
    bd.line([(0, y), (W, y)], fill=int(70 * (y - 1500) / (H - 1500)))
img = Image.composite(Image.new('RGB', (W, H), (255, 236, 170)), img, band)
# full-stretch 9-patch markers (pure gradient: safe at any aspect)
px = img.load()
for x in range(W):
    px[x, 0] = (255, 255, 255)
    px[x, H - 1] = (255, 255, 255)
for y in range(H):
    px[0, y] = (255, 255, 255)
    px[W - 1, y] = (255, 255, 255)
for x in range(1, W - 1):
    px[x, 0] = (0, 0, 0)
for y in range(1, H - 1):
    px[0, y] = (0, 0, 0)
img.save(f'{TMP}/res/drawable/welcome_bg_pic.9.png')
print("1. welcome_bg_pic.9.png -> pure gradient (stretch-safe)")

def compile_9patches(names):
    r = subprocess.run([AAPT2, 'compile', '--dir', f'{TMP}/res', '-o', f'{TMP}/compiled.zip'],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print("aapt2 compile FAILED:", r.stderr[:400])
        raise SystemExit(1)
    zf = zipfile.ZipFile(f'{TMP}/compiled.zip')
    for name in names:
        flat = zf.read(f'drawable_{name}.9.png.flat')
        i = flat.find(b'\x89PNG')
        png = flat[i:]
        iend = png.find(b'IEND')
        png = png[:iend + 8]
        out = f'{GEN}/{name}.9.png'
        open(out, 'wb').write(png)
        im = Image.open(out)
        print(f"   compiled {name}.9.png: {im.size} {im.mode} {len(png)}B")

compile_9patches(['welcome_bg_pic'])
import shutil
shutil.copyfile(f'{GEN}/welcome_bg_pic.9.png', f'{XX}/welcome_bg_pic.9.png')

# ============ 2. bottom tab icons (BigNaiWa sprites) ============
TAB_MAP = {
    'icon_tab_main_nor':    ('03-orange',    False),
    'icon_tab_main_pre':    ('03-orange',    True),
    'icon_tab_message_nor': ('05-kiwi',      False),
    'icon_tab_message_pre': ('05-kiwi',      True),
    'icon_tab_servicee_nor':('08-pineapple', False),
    'icon_tab_service_pre': ('08-pineapple', True),
    'icon_tab_me_nor':      ('07-peach',     False),
    'icon_tab_me_pre':      ('07-peach',     True),
    'icon_tab_notice_nor':  ('09-coconut',   False),
    'icon_tab_notice_pre':  ('09-coconut',   True),
    'icon_tab_notes_normal':('02-cherry',    False),
    'icon_tab_notes_pressed': ('02-cherry',  True),
}
for name, (sprite_name, sel) in TAB_MAP.items():
    tab_icon(sprite_name, 60, sel).save(f'{XX}/{name}.png')
print(f"2. {len(TAB_MAP)} tab icons -> BigNaiWa sprites")

# ============ 3. service filter icons ============
SVC_MAP = {
    'icon_service_all':    '11-watermelon',   # 神奶蛙 = 全部
    'icon_service_study':  '04-lemon',        # 小鸡 = 学习
    'icon_service_office': '06-tomato',       # 马 = 工作
    'icon_service_life':   '01-grape',        # 葡萄蛋 = 生活
    'icon_service_social': '10-halfmelon',    # 大笑半奶蛙 = 社交
    'icon_service_game':   '07-peach',        # 踢腿兔 = 娱乐
}
for name, sprite_name in SVC_MAP.items():
    svc_icon(sprite_name, 78).save(f'{XX}/{name}.png')
print(f"3. {len(SVC_MAP)} service filter icons -> BigNaiWa sprites")

# ============ 4a. home header logo: naiwa head + wordmark (348x60) ============
LW, LH = 348, 60
logo = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
head = circle_masked(naiwa_face(52))
# naiwa-yellow ring around the head
ring = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
ImageDraw.Draw(ring).ellipse([1, 1, 54, 54], outline=(254, 206, 14, 255), width=3)
logo.alpha_composite(ring, (2, 2))
logo.alpha_composite(head, (5, 5))
f_logo = find_font(38, bold=True)
d = ImageDraw.Draw(logo)
text = 'i大工 · 奶蛙版'
# white text with dark soft shadow (visible on any header bg)
tb = d.textbbox((0, 0), text, font=f_logo)
tw, th = tb[2] - tb[0], tb[3] - tb[1]
tx, ty = 66, (LH - th) // 2 - tb[1]
sh = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
ds = ImageDraw.Draw(sh)
ds.text((tx + 2, ty + 2), text, font=f_logo, fill=(90, 60, 0, 160))
sh = sh.filter(ImageFilter.GaussianBlur(1.5))
logo.alpha_composite(sh)
d.text((tx, ty), text, font=f_logo, fill=(255, 255, 255, 255))
# small naiwa-yellow underline
d.rounded_rectangle([tx + 2, ty + th + 4, tx + tw - 2, ty + th + 8], radius=2, fill=(254, 206, 14, 255))
logo.save(f'{XX}/icon_first_page_logo.png')
print("4a. icon_first_page_logo -> naiwa wordmark 348x60")

# ============ 4b. about page logo (300x277) ============
face300 = circle_masked(naiwa_face(250))
about = Image.new('RGBA', (300, 277), (0, 0, 0, 0))
halo = glow_disc(280, alpha=70)
about.alpha_composite(halo, (10, 0))
about.alpha_composite(face300, (25, 13))
ImageDraw.Draw(about).ellipse([25, 13, 275, 263], outline=(254, 206, 14, 255), width=5)
about.save(f'{XX}/icon_about_whistle_logo.png')
print("4b. icon_about_whistle_logo -> naiwa face 300x277")

# ============ 4c. contacts icons (66x54) ============
for name, sel in [('icon_contacts_nor', False), ('icon_contacts_pre', True)]:
    im = nxl('naiwa_1_a') if sel else desat(nxl('naiwa_1_a'), 0.55)
    canvas = Image.new('RGBA', (66, 54), (0, 0, 0, 0))
    if sel:
        canvas.alpha_composite(glow_disc(54, alpha=90), (6, 0))
    body = fit(im, 50 if sel else 44)
    canvas.alpha_composite(body, ((66 - body.width) // 2, (54 - body.height) // 2))
    canvas.save(f'{XX}/{name}.png')
print("4c. contacts nor/pre -> naiwa_1_a face")

# ============ 4d. favorite/collect stars (60x60) ============
# nor: naiwa_1_f (举旗冠军) desaturated; true(checked): vivid + glow
for name, src, sel in [('icon_collect_notice_nor', nxl('naiwa_1_f'), False),
                       ('icon_collect_notice_true', nxl('naiwa_1_f'), True)]:
    im = src if sel else desat(src, 0.55)
    canvas = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
    if sel:
        canvas.alpha_composite(glow_disc(60, alpha=100))
        body = fit(im, 54)
    else:
        body = fit(im, 46)
    canvas.alpha_composite(body, ((60 - body.width) // 2, (60 - body.height) // 2))
    canvas.save(f'{XX}/{name}.png')
print("4d. collect notice nor/true -> naiwa_1_f flag bearer")

# ============ 4e. sex badges (48x48): boy / girl naiwa heads ============
for name, ring_color, bg_tint in [('icon_sex_boy', (96, 165, 250, 255), (215, 235, 255)),
                                  ('icon_sex_girl', (250, 128, 171, 255), (255, 228, 238))]:
    canvas = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
    disc = Image.new('RGBA', (48, 48), bg_tint + (255,))
    disc = circle_masked(disc)
    canvas.alpha_composite(disc)
    face = circle_masked(naiwa_face(40))
    canvas.alpha_composite(face, (4, 4))
    ImageDraw.Draw(canvas).ellipse([1, 1, 46, 46], outline=ring_color, width=3)
    canvas.save(f'{XX}/{name}.png')
print("4e. sex boy/girl -> naiwa face badges")

# ============ 4f. identity flags (48x48): teacher/bachelor/master ============
FLAG_STYLE = {
    'icon_flag_teacher':  ((214, 48, 49, 255), '师'),     # red
    'icon_flag_bachelor': ((254, 206, 14, 255), '本'),    # naiwa yellow
    'icon_flag_master':   ((156, 88, 211, 255), '硕'),    # purple
    'icon_class_teacher_p': ((239, 126, 101, 255), '导'), # coral
}
ff = find_font(26, bold=True)
for name, (color, ch) in FLAG_STYLE.items():
    canvas = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
    disc = circle_masked(Image.new('RGBA', (48, 48), (255, 251, 239, 255)))
    canvas.alpha_composite(disc)
    face = circle_masked(naiwa_face(48))
    face = desat(face, 0.25)
    a = face.split()[3].point(lambda p: int(p * 0.55))
    face.putalpha(a)
    canvas.alpha_composite(face)
    ImageDraw.Draw(canvas).ellipse([1, 1, 46, 46], outline=color, width=4)
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), ch, font=ff)
    cw, chh = bb[2] - bb[0], bb[3] - bb[1]
    # character badge bottom-right
    badge = Image.new('RGBA', (26, 26), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([0, 0, 25, 25], fill=color)
    bch = ch
    bf = find_font(18, bold=True)
    bb2 = bd.textbbox((0, 0), bch, font=bf)
    bd.text(((26 - (bb2[2] - bb2[0])) // 2 - bb2[0], (26 - (bb2[3] - bb2[1])) // 2 - bb2[1]), bch, font=bf, fill=(255, 255, 255, 255))
    canvas.alpha_composite(badge, (23, 23))
    canvas.save(f'{XX}/{name}.png')
print("4f. identity flags -> naiwa + char badges")

# ============ 4g. gift coin (138x147) & score (42x42) ============
coin = Image.new('RGBA', (138, 147), (0, 0, 0, 0))
coin.alpha_composite(glow_disc(140, alpha=60), (0, 4))
disc = Image.new('RGBA', (132, 132), (250, 214, 56, 255))
disc = circle_masked(disc)
# inner ring detail (coin)
ImageDraw.Draw(disc).ellipse([6, 6, 125, 125], outline=(214, 160, 20, 255), width=5)
coin.alpha_composite(disc, (3, 6))
cf = circle_masked(naiwa_face(104))
coin.alpha_composite(cf, (17, 20))
ImageDraw.Draw(coin).ellipse([3, 6, 135, 138], outline=(214, 160, 20, 255), width=4)
coin.save(f'{XX}/icon_coin_gift_home_header.png')

score = Image.new('RGBA', (42, 42), (0, 0, 0, 0))
score.alpha_composite(circle_masked(Image.new('RGBA', (40, 40), (250, 214, 56, 255))), (1, 1))
sf = circle_masked(naiwa_face(32))
score.alpha_composite(sf, (5, 5))
ImageDraw.Draw(score).ellipse([1, 1, 40, 40], outline=(200, 150, 20, 255), width=2)
score.save(f'{XX}/icon_current_score.png')
print("4g. gift coin + score -> naiwa gold coins")

# ============ 4h. chat glyphs ============
# icon_chat_group_v 36x36 (yellow glyph): naiwa mini face
g = Image.new('RGBA', (36, 36), (0, 0, 0, 0))
g.alpha_composite(circle_masked(naiwa_face(34)), (1, 1))
ImageDraw.Draw(g).ellipse([1, 1, 34, 34], outline=(254, 206, 14, 255), width=2)
g.save(f'{XX}/icon_chat_group_v.png')
# icon_create_conversation 60x60: naiwa_1_a + plus badge
cc = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
body = fit(nxl('naiwa_1_a'), 46)
cc.alpha_composite(body, ((60 - body.width) // 2, (60 - body.height) // 2))
pb = ImageDraw.Draw(cc)
pb.ellipse([40, 40, 59, 59], fill=(254, 206, 14, 255), outline=(255, 255, 255, 255), width=2)
pb.line([46, 50, 53, 50], fill=(90, 60, 0, 255), width=3)
pb.line([49, 47, 49, 54], fill=(90, 60, 0, 255), width=3)
cc.save(f'{XX}/icon_create_conversation.png')
print("4h. chat group + create conversation -> naiwa")

# ============ summary + self-check ============
print("\n=== replaced files check ===")
names = list(TAB_MAP) + list(SVC_MAP) + [
    'icon_first_page_logo', 'icon_about_whistle_logo',
    'icon_contacts_nor', 'icon_contacts_pre',
    'icon_collect_notice_nor', 'icon_collect_notice_true',
    'icon_sex_boy', 'icon_sex_girl',
    'icon_flag_teacher', 'icon_flag_bachelor', 'icon_flag_master', 'icon_class_teacher_p',
    'icon_coin_gift_home_header', 'icon_current_score',
    'icon_chat_group_v', 'icon_create_conversation',
]
bad = 0
for n in names:
    p = f'{XX}/{n}.png'
    if not os.path.exists(p):
        print('MISSING', n); bad += 1; continue
    im = Image.open(p)
    if im.width < 30 or im.height < 30:
        print('TOO SMALL', n, im.size); bad += 1
print(f"GEN ASSETS V4 DONE: {len(names)} icon files + welcome bg, bad={bad}")
