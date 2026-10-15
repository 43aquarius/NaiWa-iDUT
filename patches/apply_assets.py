#!/usr/bin/env python3
"""Apply generated assets to apk_work (the apktool -r decoded tree)"""
import shutil, os

WS = '/home/z/my-project/workspace'
WORK = f'{WS}/apk_work'
GEN = f'{WS}/gen'

def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"  {os.path.basename(src)} -> {dst.replace(WORK + '/', '')}")

# 1. welcome 9-patch
cp(f'{GEN}/welcome_bg_pic.9.png', f'{WORK}/res/drawable-xxhdpi-v4/welcome_bg_pic.9.png')

# 2. main page background
cp(f'{GEN}/main_page_bg.jpg', f'{WORK}/res/drawable-xxhdpi-v4/main_page_bg.jpg')

# 3. animation frames -> refresh_loading01..12 (mipmap-hdpi)
for i in range(12):
    cp(f'{GEN}/frames/frame_{i:02d}.png', f'{WORK}/res/mipmap-hdpi-v4/refresh_loading{i+1:02d}.png')

# 4. icons
cp(f'{GEN}/ic_launcher_mdpi.png', f'{WORK}/res/mipmap-mdpi-v4/ic_launcher.png')
cp(f'{GEN}/ic_launcher_hdpi.png', f'{WORK}/res/mipmap-hdpi-v4/ic_launcher.png')
cp(f'{GEN}/ic_launcher_xhdpi.png', f'{WORK}/res/mipmap-xhdpi-v4/ic_launcher.png')
cp(f'{GEN}/ic_launcher_xxhdpi.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher.png')
cp(f'{GEN}/ic_launcher_xxxhdpi.png', f'{WORK}/res/mipmap-xxxhdpi-v4/ic_launcher.png')
cp(f'{GEN}/ic_app_launcher.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher.png')
cp(f'{GEN}/ic_app_launcher_round.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_app_launcher_round.png')
cp(f'{GEN}/ic_launcher_foreground.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_foreground.png')
cp(f'{GEN}/ic_launcher_background.png', f'{WORK}/res/mipmap-xxhdpi-v4/ic_launcher_background.png')

# 5. welcome text image
cp(f'{GEN}/icon_login_welcome_txt.png', f'{WORK}/res/drawable-xxhdpi-v4/icon_login_welcome_txt.png')

# 6. UserGuide images
for i in range(4):
    cp(f'{GEN}/feature_guide_{i}.png', f'{WORK}/assets/UserGuide/feature_guide_{i}.png')

print("\nASSET APPLICATION DONE")
