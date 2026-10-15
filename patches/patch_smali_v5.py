#!/usr/bin/env python3
"""Smali patches v5 for NaiWa theme (works on work/smali_work).

Carries forward v3 patches 1-4 (always-show welcome, anim via post,
2600ms, no exit blink) with these v5 changes:
  5'. AnimStarter v2: null-safe (re-sets the animation-list if the
      drawable got cleared), instance-of check instead of raw check-cast.
  6.  WelcomeActivity.n(): NOP the ImageLoader.displayImage(server_bg,
      welcome_image) call — the server ad image raced our animation and
      was the reason the splash mascot never showed (v2-v4).
  7.  "我的" fragment (b/a/a/a/k/e/n.smali) m(): insert a
      "关于i大工奶蛙" row right after "关于i大工".
  8.  Copy in new classes: n$nw listener + com/naiwa/theme/AboutNaiWaActivity.
"""
import os, re, shutil

SW = '/home/z/my-project/NaiWa-iDUT/work/smali_work'
WELCOME = f'{SW}/smali_classes2/com/ruijie/whistle/module/welcome/view/WelcomeActivity.smali'
E_CLASS = f'{SW}/smali_classes2/b/a/a/a/a/c/e.smali'
MINE = f'{SW}/smali_classes2/b/a/a/a/k/e/n.smali'
ANIM = f'{SW}/smali_classes2/com/naiwa/theme/AnimStarter.smali'
NW_LISTENER = f'{SW}/smali_classes2/b/a/a/a/k/e/n$nw.smali'
ABOUT = f'{SW}/smali_classes2/com/naiwa/theme/AboutNaiWaActivity.smali'
PATCHES = '/home/z/my-project/NaiWa-iDUT/patches'

src = open(WELCOME).read()

# ---- Patch 1: always show welcome (nop the skip branch) ----
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

# ---- Patch 6 (NEW v5): NOP the server-image displayImage race ----
# The original code loads the "school welcome background" from the server
# straight into welcome_image (field c). That overwrote/hid our animation.
p6_old = """    invoke-virtual {v4, v5, v6, v0, v7}, Lcom/nostra13/universalimageloader/core/ImageLoader;->displayImage(Ljava/lang/String;Landroid/widget/ImageView;Lcom/nostra13/universalimageloader/core/DisplayImageOptions;Lcom/nostra13/universalimageloader/core/listener/ImageLoadingListener;)V"""
p6_new = """    nop

    nop

    nop

    nop

    nop"""
assert p6_old in src, "patch6 anchor (displayImage) not found"
src = src.replace(p6_old, p6_new, 1)
print("patch 6 (nop server-image displayImage): OK")

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

# ---- Patch 5: AnimStarter v2 class (null-safe + retry) ----
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

    if-nez v1, :cond_has

    const v1, 0x7f08005f

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setImageResource(I)V

    invoke-virtual {v0}, Landroid/widget/ImageView;->getDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v1

    :cond_has
    if-nez v1, :cond_check

    return-void

    :cond_check
    instance-of v0, v1, Landroid/graphics/drawable/AnimationDrawable;

    if-eqz v0, :cond_end

    check-cast v1, Landroid/graphics/drawable/AnimationDrawable;

    invoke-virtual {v1}, Landroid/graphics/drawable/AnimationDrawable;->isRunning()Z

    move-result v0

    if-nez v0, :cond_end

    invoke-virtual {v1}, Landroid/graphics/drawable/AnimationDrawable;->start()V

    :cond_end
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
print("patch 5 (AnimStarter v2, null-safe): OK")

# ---- Patch 7: "关于i大工奶蛙" row in the Mine fragment list ----
msrc = open(MINE).read()
p7_old = """    const-string v2, "\\u5173\\u4e8ei\\u5927\\u5de5"

    invoke-virtual {p0, v1, v2, v3, v4}, Lb/a/a/a/k/e/n;->l(ILjava/lang/String;Ljava/lang/String;Lb/a/a/b/f/h;)Lb/a/a/a/k/e/n$g;

    move-result-object v1

    invoke-interface {v0, v1}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 10"""
p7_new = """    const-string v2, "\\u5173\\u4e8ei\\u5927\\u5de5"

    invoke-virtual {p0, v1, v2, v3, v4}, Lb/a/a/a/k/e/n;->l(ILjava/lang/String;Ljava/lang/String;Lb/a/a/b/f/h;)Lb/a/a/a/k/e/n$g;

    move-result-object v1

    invoke-interface {v0, v1}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    # ===== NaiWa v5: 关于i大工奶蛙 =====
    iget-object v0, p0, Lb/a/a/a/k/e/n;->z:Ljava/util/List;

    sget v1, Lcom/ruijie/whistle/R$drawable;->icon_mine_about:I

    new-instance v4, Lb/a/a/a/k/e/n$nw;

    const/16 v2, 0x1f4

    invoke-direct {v4, p0, v2}, Lb/a/a/a/k/e/n$nw;-><init>(Lb/a/a/a/k/e/n;I)V

    const-string v2, "\\u5173\\u4e8ei\\u5927\\u5de5\\u5976\\u86d9"

    invoke-virtual {p0, v1, v2, v3, v4}, Lb/a/a/a/k/e/n;->l(ILjava/lang/String;Ljava/lang/String;Lb/a/a/b/f/h;)Lb/a/a/a/k/e/n$g;

    move-result-object v1

    invoke-interface {v0, v1}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    # ===== end NaiWa v5 =====

    .line 10"""
assert p7_old in msrc, "patch7 anchor (关于i大工) not found"
msrc = msrc.replace(p7_old, p7_new, 1)
open(MINE, 'w').write(msrc)
print("patch 7 (关于i大工奶蛙 row): OK")

# ---- Patch 8a: n$nw listener class (starts AboutNaiWaActivity) ----
NW_SRC = """.class public Lb/a/a/a/k/e/n$nw;
.super Lb/a/a/b/f/h;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lb/a/a/a/k/e/n;->m()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x1
    name = "nw"
.end annotation


# instance fields
.field public final synthetic c:Lb/a/a/a/k/e/n;


# direct methods
.method public constructor <init>(Lb/a/a/a/k/e/n;I)V
    .registers 3

    iput-object p1, p0, Lb/a/a/a/k/e/n$nw;->c:Lb/a/a/a/k/e/n;

    invoke-direct {p0, p2}, Lb/a/a/b/f/h;-><init>(I)V

    return-void
.end method


# virtual methods
.method public a(Landroid/view/View;)V
    .registers 5

    iget-object p1, p0, Lb/a/a/a/k/e/n$nw;->c:Lb/a/a/a/k/e/n;

    new-instance v0, Landroid/content/Intent;

    iget-object v1, p0, Lb/a/a/a/k/e/n$nw;->c:Lb/a/a/a/k/e/n;

    iget-object v1, v1, Lb/a/a/b/b/k;->h:Landroid/app/Activity;

    const-class v2, Lcom/naiwa/theme/AboutNaiWaActivity;

    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    invoke-virtual {p1, v0}, Landroidx/fragment/app/Fragment;->startActivity(Landroid/content/Intent;)V

    return-void
.end method
"""
open(NW_LISTENER, 'w').write(NW_SRC)
print("patch 8a (n$nw listener): OK")

# ---- Patch 8b: AboutNaiWaActivity (copied from about_naiwa dir) ----
shutil.copyfile(f'{PATCHES}/about_naiwa/AboutNaiWaActivity.smali', ABOUT)
print("patch 8b (AboutNaiWaActivity): OK")
print("\nSMALI PATCHES V5 DONE")
