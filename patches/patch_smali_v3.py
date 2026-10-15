#!/usr/bin/env python3
"""Smali patches v3 for NaiWa theme (works on work/smali_work):
1. WelcomeActivity.n(): nop the skip-welcome branch (always show welcome — fixes v1 white screen)
2. WelcomeActivity.n(): root visible + animation started via View.post(AnimStarter),
   wrapped in try-catch so any failure cannot crash the app
3. WelcomeActivity.n(): welcome duration 1500ms -> 2600ms (website timing)
4. b/a/a/a/a/c/e.smali: nop the alpha animator (avoid exit blink)
5. NEW class com/naiwa/theme/AnimStarter.smali (Runnable: safely starts AnimationDrawable)
"""
import os, re

SW = '/home/z/my-project/NaiWa-iDUT/work/smali_work'
WELCOME = f'{SW}/smali_classes2/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali'
E_CLASS = f'{SW}/smali_classes2/b/a/a/a/a/c/e.smali'
ANIM = f'{SW}/smali_classes2/com/naiwa/theme/AnimStarter.smali'

src = open(WELCOME).read()

# ---- Patch 1: always show welcome (nop the skip branch) ----
# Replace the `if-eqz v2, :cond_XXX` line itself with two nops so that
# setContentView(welcome_layout) ALWAYS runs (first launch included).
m = re.search(
    r"(    :cond_\w+\n    :goto_\w+\n)(    if-eqz v2, :cond_\w+\n)(\n    \.line 21\n    :try_start_\w+\n    sget v1, Lcom/ruijie/whistle/R\$layout;->welcome_layout:I)",
    src)
assert m, "patch1 anchor not found"
src = src.replace(m.group(0), m.group(1) + "    nop\n    nop\n" + m.group(3), 1)
print("patch 1 (always show welcome): OK")

# ---- Patch 2: insert visibility + animation code ----
p2_old = """    iput-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->e:Landroid/widget/ImageView;

    .line 28
    new-instance v1, Lcom/nostra13/universalimageloader/core/DisplayImageOptions$Builder;"""
p2_new = """    iput-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->e:Landroid/widget/ImageView;

    # ===== NaiWa v3: show root + play intro animation (fail-safe) =====
    iget-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->i:Landroid/view/View;

    const/4 v2, 0x0

    invoke-virtual {v1, v2}, Landroid/view/View;->setVisibility(I)V

    :try_start_nai
    iget-object v1, p0, Lcom/ruijie/whistle/module/welcome/view/WelcomeActivity;->c:Landroid/widget/ImageView;

    const v2, 0x7f08005f

    invoke-virtual {v1, v2}, Landroid/widget/ImageView;->setImageResource(I)V

    new-instance v2, Lcom/naiwa/theme/AnimStarter;

    invoke-direct {v2, v1}, Lcom/naiwa/theme/AnimStarter;-><init>(Landroid/widget/ImageView;)V

    invoke-virtual {v1, v2}, Landroid/view/View;->post(Ljava/lang/Runnable;)Z

    nop
    :try_end_nai
    .catchall {:try_start_nai .. :try_end_nai} :catch_nai
    # ===== end NaiWa v3 =====

    .line 28
    new-instance v1, Lcom/nostra13/universalimageloader/core/DisplayImageOptions$Builder;"""
assert p2_old in src, "patch2 anchor not found"
src = src.replace(p2_old, p2_new, 1)
print("patch 2 (visible + animation via post): OK")

# ---- Patch 2b: catch handler at method end ----
m2b = re.search(
    r"(    :goto_\w+\n    return-void\n)(\.end method\n\n\.method public onBackPressed\(\)V)",
    src)
assert m2b, "patch2b anchor not found"
catch = """
    :catch_nai
    move-exception v1

    const-string v2, "mq"

    const-string v3, "NaiWa anim patch failed"

    invoke-static {v2, v3}, Lb/a/a/b/i/d1;->b(Ljava/lang/String;Ljava/lang/String;)I

    return-void
"""
src = src.replace(m2b.group(0), m2b.group(1) + catch + m2b.group(2), 1)
print("patch 2b (catch handler): OK")

# ---- Patch 3: duration 1500ms -> 2600ms ----
p3_old = """    const-wide/16 v2, 0x5dc

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z"""
p3_new = """    const-wide/16 v2, 0xa28

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z"""
assert p3_old in src, "patch3 anchor not found"
src = src.replace(p3_old, p3_new, 1)
print("patch 3 (2600ms): OK")

open(WELCOME, 'w').write(src)

# ---- Patch 4: e.smali nop animator start ----
esrc = open(E_CLASS).read()
p4_old = """    invoke-virtual {v1}, Landroid/animation/ObjectAnimator;->start()V"""
p4_new = """    nop

    nop

    nop"""
assert p4_old in esrc, "patch4 anchor not found"
esrc = esrc.replace(p4_old, p4_new, 1)
open(E_CLASS, 'w').write(esrc)
print("patch 4 (no blink): OK")

# ---- Patch 5: AnimStarter class ----
os.makedirs(f'{SW}/smali_classes2/com/naiwa/theme', exist_ok=True)
ANIM_SRC = """.class public Lcom/naiwa/theme/AnimStarter;
.super Ljava/lang/Object;
.source "AnimStarter.java"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field private final a:Landroid/widget/ImageView;


# direct methods
.method public constructor <init>(Landroid/widget/ImageView;)V
    .registers 2

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, Lcom/naiwa/theme/AnimStarter;->a:Landroid/widget/ImageView;

    return-void
.end method


# virtual methods
.method public run()V
    .registers 3

    :try_start_0
    iget-object v0, p0, Lcom/naiwa/theme/AnimStarter;->a:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v1

    check-cast v1, Landroid/graphics/drawable/AnimationDrawable;

    invoke-virtual {v1}, Landroid/graphics/drawable/AnimationDrawable;->isRunning()Z

    move-result v0

    if-nez v0, :cond_4

    invoke-virtual {v1}, Landroid/graphics/drawable/AnimationDrawable;->start()V

    :cond_4
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catch_5

    return-void

    :catch_5
    move-exception v0

    invoke-virtual {v0}, Ljava/lang/Throwable;->printStackTrace()V

    return-void
.end method
"""
open(ANIM, 'w').write(ANIM_SRC)
print("patch 5 (AnimStarter class): OK")
print("\nSMALI PATCHES V3 DONE")
