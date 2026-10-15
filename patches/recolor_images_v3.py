#!/usr/bin/env python3
"""Pixel-level blue->naiwa-yellow recolor for ALL res images (png/webp).
- hue-shifts blue/cyan and green pixels to naiwa yellow, preserving L and alpha
- preserves npTc/npOl chunks of compiled 9-patches (re-inserts after PIL save)
- recolors npTc solid fill colors if blue
- skips files explicitly replaced by the theme (frames/icons/bgs/guides)
"""
import os, struct, sys
import numpy as np
from PIL import Image

WORK = '/home/z/my-project/NaiWa-iDUT/work/build'
NAI_HUE_DEG = 47.0

SKIP = {
    'mipmap-hdpi-v4/refresh_loading01.png', 'mipmap-hdpi-v4/refresh_loading02.png',
    'mipmap-hdpi-v4/refresh_loading03.png', 'mipmap-hdpi-v4/refresh_loading04.png',
    'mipmap-hdpi-v4/refresh_loading05.png', 'mipmap-hdpi-v4/refresh_loading06.png',
    'mipmap-hdpi-v4/refresh_loading07.png', 'mipmap-hdpi-v4/refresh_loading08.png',
    'mipmap-hdpi-v4/refresh_loading09.png', 'mipmap-hdpi-v4/refresh_loading10.png',
    'mipmap-hdpi-v4/refresh_loading11.png', 'mipmap-hdpi-v4/refresh_loading12.png',
    'drawable-xxhdpi-v4/welcome_bg_pic.9.png', 'drawable-xxhdpi-v4/main_page_bg.png',
    'mipmap-mdpi-v4/ic_launcher.png', 'mipmap-hdpi-v4/ic_launcher.png',
    'mipmap-xhdpi-v4/ic_launcher.png', 'mipmap-xxhdpi-v4/ic_launcher.png',
    'mipmap-xxxhdpi-v4/ic_launcher.png', 'mipmap-xxhdpi-v4/ic_app_launcher.png',
    'mipmap-xxhdpi-v4/ic_app_launcher_round.png', 'mipmap-xxhdpi-v4/ic_launcher_foreground.png',
    'mipmap-xxhdpi-v4/ic_launcher_background.png',
    # v3 additions: mine panel + avatars + empty-state mascot art (preserve exact art)
    'drawable-xxhdpi-v4/bg_mine_panel.9.png',
    'drawable-xxhdpi-v4/custom_head_bg_default.png',
    'drawable-xxhdpi-v4/custom_head_bg_boy.png',
    'drawable-xxhdpi-v4/custom_head_bg_girl.png',
    'drawable-xxhdpi-v4/custom_head_bg_org.png',
    'drawable-xxhdpi-v4/custom_head_bg_parent.png',
    'drawable-xxhdpi-v4/app_def.png',
    'drawable-xxhdpi-v4/icon_chatlist_empty.png',
    'drawable-xxhdpi-v4/icon_app_or_file_empty.png',
    'drawable-xxhdpi-v4/icon_custom_org_empty.png',
    'drawable-xxhdpi-v4/icon_connect_book_or_search_result_empty.png',
    'drawable-xxhdpi-v4/icon_my_collected_notice_empty.png',
    'drawable-xxhdpi-v4/icon_my_received_notice_empty.png',
    'drawable-xxhdpi-v4/icon_my_sended_notice_empty.png',
    'drawable-xxhdpi-v4/icon_notice_delay_read_state_empty.png',
    'drawable-xxhdpi-v4/icon_notice_readed_empty.png',
    'drawable-xxhdpi-v4/icon_notice_unreaded_empty.png',
}

def rgb_to_hls_np(rgb):
    """rgb: (..., 3) float 0-1. Returns h(0-360), l, s arrays."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    l = (mx + mn) / 2
    delta = mx - mn
    s = np.where(delta == 0, 0.0, np.where(l > 0.5, delta / (2 - mx - mn + 1e-9), delta / (mx + mn + 1e-9)))
    h = np.zeros_like(l)
    m = delta != 0
    dm = np.where(m, delta, 1.0)
    h = np.where(m & (mx == r), ((g - b) / dm) % 6, h)
    h = np.where(m & (mx == g), (b - r) / dm + 2, h)
    h = np.where(m & (mx == b), (r - g) / dm + 4, h)
    h = (h * 60) % 360
    return h, l, s

def hls_to_rgb_np(h_deg, l, s):
    h = ((h_deg % 360) / 360.0 * 6)[..., None]     # (N,1)
    l2 = l[..., None]
    s2 = s[..., None]
    c = (1 - np.abs(2 * l2 - 1)) * s2
    x = c * (1 - np.abs(h % 2 - 1))
    z = np.zeros_like(c)
    rgb = np.select(
        [h < 1, h < 2, h < 3, h < 4, h < 5, h >= 5],
        [np.concatenate([c, x, z], -1), np.concatenate([x, c, z], -1), np.concatenate([z, c, x], -1),
         np.concatenate([z, x, c], -1), np.concatenate([x, z, c], -1), np.concatenate([c, z, x], -1)])
    m = l2 - c / 2
    return rgb + m

def shift_pixels_np(arr):
    """arr: HxWx4 uint8 RGBA. Returns (new_arr, changed_count)."""
    a = arr[..., 3]
    rgb = arr[..., :3].astype(np.float32) / 255.0
    h, l, s = rgb_to_hls_np(rgb)
    blue = (h >= 175) & (h <= 275) & (s > 0.12) & (l > 0.05) & (l < 0.99) & (a > 8)
    green = (h >= 75) & (h < 175) & (s > 0.25) & (l > 0.05) & (l < 0.99) & (a > 8)
    mask = blue | green
    cnt = int(mask.sum())
    if cnt == 0:
        return arr, 0
    # vivid for saturated sources, muted for weak/slate (matches recolor_v2)
    ns = np.where(s[mask] > 0.45,
                  np.clip(0.55 + 0.4 * s[mask], 0.75, 0.98),
                  np.clip(s[mask] * 0.8, 0.15, 0.50))
    new_rgb_mask = hls_to_rgb_np(np.full(cnt, NAI_HUE_DEG, dtype=np.float32), l[mask], ns)
    new_rgb = rgb.copy()
    new_rgb[mask] = new_rgb_mask
    out = np.zeros_like(arr)
    out[..., :3] = (np.clip(new_rgb, 0, 1) * 255).astype(np.uint8)
    out[..., 3] = a
    return out, cnt

def extract_chunks(png):
    pos = 8
    chunks = []
    while pos < len(png):
        ln = struct.unpack_from('>I', png, pos)[0]
        typ = png[pos+4:pos+8]
        chunks.append((typ, png[pos:pos+12+ln]))
        pos += 12 + ln
    return chunks

def rebuild_png(chunks, png):
    # replace IDAT etc: keep non-image chunks, regenerate from PIL output
    out = bytearray()
    for typ, data in chunks:
        if typ == b'IDAT':
            continue
        if typ in (b'npTc', b'npOl'):
            out.extend(data)
    return bytes(out)

def shift_argb(v):
    r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
    import colorsys
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    hd = h * 360
    if (175 <= hd <= 275 and s > 0.12 or 75 <= hd < 175 and s > 0.25) and 0.05 < l < 0.99:
        ns = min(max(0.55 + 0.4 * s, 0.75), 0.98) if s > 0.45 else min(max(s * 0.8, 0.15), 0.50)
        nr, ng, nb = colorsys.hls_to_rgb(NAI_HUE_DEG/360, l, ns)
        a = (v >> 24) & 255
        return (a << 24) | (int(nr*255) << 16) | (int(ng*255) << 8) | int(nb*255)
    return None

def recolor_nptc_colors(chunk):
    """chunk = npTc chunk data (without len/type). Shifts fill colors in place."""
    nX, nY, nC = chunk[1], chunk[2], chunk[3]
    colorsOff = struct.unpack_from('<I', chunk, 28)[0]
    changed = 0
    for i in range(nC):
        off = colorsOff + 4 * i
        if off + 4 > len(chunk):
            break
        v = struct.unpack_from('<I', chunk, off)[0]
        if v == 0x00000001:  # NO_COLOR
            continue
        if (v >> 24) == 0:
            continue
        nv = shift_argb(v)
        if nv is not None:
            struct.pack_into('<I', chunk, off, nv)
            changed += 1
    return changed

processed = 0
total_changed_px = 0
skipped_nine = 0
for root, dirs, fnames in os.walk(f'{WORK}/res'):
    for fn in fnames:
        rel = os.path.relpath(os.path.join(root, fn), f'{WORK}/res')
        if rel.replace(os.sep, '/') in SKIP:
            continue
        p = os.path.join(root, fn)
        if not fn.endswith(('.png', '.webp')):
            continue
        try:
            im = Image.open(p)
            if im.mode not in ('RGBA', 'RGB', 'PA', 'LA', 'P'):
                continue
            has_alpha = im.mode in ('RGBA', 'LA', 'PA', 'P')
            im2 = im.convert('RGBA')
        except Exception:
            continue
        arr = np.asarray(im2).copy()
        new_arr, cnt = shift_pixels_np(arr)
        if cnt == 0:
            continue
        # 9-patch: preserve npTc/npOl chunks
        raw = open(p, 'rb').read()
        chunks = extract_chunks(raw)
        nptc = [d for t, d in chunks if t == b'npTc']
        npol = [d for t, d in chunks if t == b'npOl']
        out_im = Image.fromarray(new_arr, 'RGBA')
        buf_path = p + '.tmp.png'
        out_im.save(buf_path, optimize=False)
        newraw = bytearray(open(buf_path, 'rb').read())
        if nptc or npol:
            # insert preserved chunks before first IDAT
            insert = bytearray()
            for d in npol:
                insert.extend(d)
            for d in nptc:
                if nptc and d is nptc[0]:
                    # recolor fill colors in npTc
                    dbyte = bytearray(d)
                    # d includes len+type+data; data starts at 12
                    c = recolor_nptc_colors(dbyte[12:])
                    if c:
                        print(f"  npTc colors shifted: {rel} ({c})")
                    d = bytes(dbyte)
                insert.extend(d)
            idat_pos = newraw.find(b'IDAT') - 4
            if idat_pos > 0:
                newraw[idat_pos:idat_pos] = insert
        open(p, 'wb').write(bytes(newraw))
        os.remove(buf_path)
        processed += 1
        total_changed_px += cnt
        frac = cnt / (arr.shape[0] * arr.shape[1])
        if frac > 0.02:
            print(f"  {rel}: {cnt} px shifted ({frac:.0%})")

print(f"\nrecolored {processed} images ({total_changed_px} pixels total)")
