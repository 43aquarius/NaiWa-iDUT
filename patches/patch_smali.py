#!/usr/bin/env python3
"""Apply smali patches for NaiLong theme:
1. WelcomeActivity.n(): always show welcome screen (nop the skip branch)
2. WelcomeActivity.n(): play anim_loading_view on welcome_image + make content visible
3. b/a/a/a/a/c/e.smali: nop the alpha animator start (avoid blink)
"""
import re

WS = '/home/z/my-project/workspace'
WELCOME = f'{WS}/apk_work/smali_classes2/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali'
E_CLASS = f'{WS}/apk_work/smali_classes2/b/a/a/a/a/c/e.smali'

# ============ Patch 1 + 2: WelcomeActivity.n() ============
src = open(WELCOME).read()
orig_len = len(src)

# --- Patch 1: nop the "skip welcome if no cached image" branch ---
# The branch is:  if-eqz v2, :cond_3   (v2 = has-cached-image flag)
p1_old = """    :cond_2
    :goto_1
    if-eqz v2, :cond_3

    .line 21
    :try_start_0
    sget v1, Lcom/ruijie/whistle/R$layout;->welcome_layout:I"""
p1_new = """    :cond_2
    :goto_1
    nop
    nop

    .line 21
    :try_start_0
    sget v1, Lcom/ruijie/whistle/R$layout;->welcome_layout:I"""
assert p1_old in src, "patch1 anchor not found"
src = src.replace(p1_old, p1_new, 1)
print("patch 1 (always show welcome): OK")

# --- Patch 2: insert animation code after iv_welcome_txt findViewById ---
p2_old = """    iput-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->e:Landroid/widget/ImageView;

    .line 28
    new-instance v1, Lcom/nostra13/universalimageloader/core/DisplayImageOptions$Builder;"""
p2_new = """    iput-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->e:Landroid/widget/ImageView;

    # ===== NaiLong theme patch: play intro animation on welcome_image =====
    iget-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->c:Landroid/widget/ImageView;

    const v2, 0x7f08005f

    invoke-virtual {v1, v2}, Landroid/widget/ImageView;->setImageResource(I)V

    iget-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->c:Landroid/widget/ImageView;

    invoke-virtual {v1}, Landroid/widget/ImageView;->getDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v2

    check-cast v2, Landroid/graphics/drawable/AnimationDrawable;

    invoke-virtual {v2}, Landroid/graphics/drawable/AnimationDrawable;->start()V

    iget-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->i:Landroid/view/View;

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Landroid/view/View;->setVisibility(I)V

    # ===== end NaiLong patch =====

    .line 28
    new-instance v1, Lcom/nostra13/universalimageloader/core/DisplayImageOptions$Builder;"""
assert p2_old in src, "patch2 anchor not found"
src = src.replace(p2_old, p2_new, 1)
print("patch 2 (play animation): OK")

open(WELCOME, 'w').write(src)
print(f"WelcomeActivity.smali: {orig_len} -> {len(src)} bytes")

# ============ Patch 3: e.smali - nop animator start ============
esrc = open(E_CLASS).read()
p3_old = """    invoke-virtual {v1}, Landroid/animation/ObjectAnimator;->start()V"""
p3_new = """    nop
    nop
    nop"""
assert p3_old in esrc, "patch3 anchor not found"
esrc = esrc.replace(p3_old, p3_new, 1)
open(E_CLASS, 'w').write(esrc)
print("patch 3 (no blink): OK")
print("\nSMALI PATCHES DONE")
