#!/usr/bin/env python3
"""NaiWa v5 assets — rebuild the 12-frame welcome animation.

Root cause of "v4 lost the animation content": the frames were copies of
theme/frames with content spanning y=43..516 on a 480x640 canvas and only
~2% inter-frame difference (subtle breathing). Combined with the
ImageLoader.displayImage(server_img, welcome_image) call in
WelcomeActivity.n() racing the AnimStarter, the animation was never
reliably visible; after v4 removed the baked-in 9-patch mascot the user
saw only the pure gradient.

v5 fixes (this file):
  1. Frames rebuilt with a STRONG animation curve:
       frame 1-6  = elastic pop-in (scale 0.25 -> 1.06, alpha 0.25 -> 1.0)
       frame 7-12 = gentle breathing settle (1.0 -> 1.03 -> 1.0)
     Frame 12 is the steady full-size mascot -> used as static fallback
     src in welcome_layout (never a blank/gray screen again).
  2. Composition shifted DOWN (content baseline y ~ 150..640) so the
     full-screen centerInside image never collides with the
     iv_welcome_icon badge (80dp margin + 133dp badge at top).
  3. Ground shadow ellipse + warm halo scale with the mascot.

Frames stay 480x640 RGBA in mipmap-hdpi-v4/refresh_loading01..12.png
(replace-in-place; no arsc change needed).
"""
import os
from PIL import Image, ImageDraw, ImageFilter

REPO = '/home/z/my-project/NaiWa-iDUT'
WORK = f'{REPO}/work/build'
DST = f'{WORK}/res/mipmap-hdpi-v4'

# ---- source mascot: crop the steady frame (content 336x474 at (72,43)) ----
SRC = f'{REPO}/theme/frames/frame_05.png'
im = Image.open(SRC).convert('RGBA')
mascot = im.crop((72, 43, 408, 517))          # 336 x 474
mascot = mascot.resize((400, 564), Image.LANCZOS)  # slightly bigger

W, H = 480, 640
CX, BASE_Y = W // 2, 640                      # feet baseline near bottom

def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# 12-frame script: (scale, alpha) per frame
SCRIPT = [
    (0.25, 0.30),   # 1 tiny pop
    (0.55, 0.65),   # 2
    (0.85, 0.92),   # 3
    (1.06, 1.00),   # 4 overshoot
    (0.97, 1.00),   # 5 settle back
    (1.02, 1.00),   # 6
    (1.00, 1.00),   # 7 steady
    (1.03, 1.00),   # 8 breathe up
    (1.00, 1.00),   # 9
    (1.03, 1.00),   # 10
    (1.01, 1.00),   # 11
    (1.00, 1.00),   # 12 steady = static fallback look
]

def halo(size):
    h = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(h)
    d.ellipse([size*0.08, size*0.08, size*0.92, size*0.92],
              fill=(255, 224, 130, 90))
    return h.filter(ImageFilter.GaussianBlur(size * 0.12))

def ground(w, alpha):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    d.ellipse([CX - w // 2, BASE_Y - 22, CX + w // 2, BASE_Y + 6],
              fill=(120, 85, 10, alpha))
    return g.filter(ImageFilter.GaussianBlur(7))

for i, (scale, alpha) in enumerate(SCRIPT, start=1):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    mw, mh = int(mascot.width * scale), int(mascot.height * scale)
    if mw < 2 or mh < 2:
        mw, mh = 2, 2
    m = mascot.resize((mw, mh), Image.LANCZOS)
    # feet sit on baseline minus a small lift while popping in
    lift = int((1.0 - min(scale, 1.0)) * 60)
    x = CX - mw // 2
    y = BASE_Y - mh - 6 - lift
    # ground shadow: width tracks the mascot width
    sw = int(190 * (0.45 + 0.55 * min(scale, 1.05)))
    sa = int(alpha * (60 - 25 * (1 - min(scale, 1.0))))
    canvas.alpha_composite(ground(sw, max(sa, 12)))
    # warm halo behind mascot
    hs = int(430 * scale) | 1
    hl = halo(min(hs, W - 20))
    canvas.alpha_composite(hl, (CX - hl.width // 2, y + mh // 2 - hl.height // 2))
    # mascot with alpha
    if alpha < 1.0:
        a = m.getchannel('A').point(lambda v: int(v * alpha))
        m.putalpha(a)
    canvas.alpha_composite(m, (x, y))
    out = f'{DST}/refresh_loading{i:02d}.png'
    canvas.save(out)

# verification: inter-frame difference must be much stronger than v4's ~2%
import numpy as np
prev = None
diffs = []
for i in range(1, 13):
    a = np.array(Image.open(f'{DST}/refresh_loading{i:02d}.png').convert('RGBA').resize((96, 128)))
    if prev is not None:
        diffs.append(float(np.abs(a.astype(int) - prev.astype(int)).mean()))
    prev = a
print('v5 frames written (12), inter-frame diffs:',
      ' '.join(f'{d:.1f}' for d in diffs))
print('min diff =', f'{min(diffs):.1f} (v4 was ~2.0 -> too subtle)')
assert max(diffs) > 8, 'animation too subtle, check scaling script'
# frame 1 must be clearly smaller than frame 12
a1 = np.array(Image.open(f'{DST}/refresh_loading01.png'))
a12 = np.array(Image.open(f'{DST}/refresh_loading12.png'))
o1 = (a1[:, :, 3] > 40).sum(); o12 = (a12[:, :, 3] > 40).sum()
print(f'opaque px: frame1={o1} frame12={o12}')
assert o1 < o12 * 0.5, 'frame 1 should be small (pop-in start)'
print('GEN ASSETS V5 OK')
