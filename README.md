# 奶蛙 i大工 🐛 (NaiWa-iDUT)

> 把「i大工」（大连理工大学校园 App）做成**奶龙/奶蛙主题**的定制版
>
> 入场动画复刻自 [中国奶龙大学.com](https://xn--fiqs8srwb9iv6f6w9n.com/)（奶龙正在护送你前往中国奶龙大学）

## 成品下载

| 文件 | 说明 |
|---|---|
| `i大工_奶蛙版_3.3.12.apk` | 奶蛙主题定制版（本仓库直接下载，或到 [Releases](../../releases) 下载） |
| `i大工_3.3.12.75026.apk` | 原版 App（未修改） |

**版本**：基于 i大工 3.3.12.75026 · 签名密钥为本项目自签（`nailong`，见下方"安装说明"）

## 改了什么

### 1. 启动动画（复刻中国奶龙大学网站的入场动画）
- 冷启动时：奶龙米色（`#FFFBEF`）渐变背景接管原来的**纯蓝屏**
- 欢迎页播放 12 帧帧动画，复刻网站的开场动画三要素：
  - 白底圆盘徽章 + **旋转的文字环**（每帧 30°，来自网站的 `ring.webp`）
  - 中心的奶龙**呼吸缩放**（来自网站的 `core.webp`）
  - 外圈**进度环**从 0% 填满一圈（奶龙黄 `#FECE0E`）
  - 标题「中国奶龙大学」+ 副标题「奶龙正在护送你前往…」（省略号逐帧跳动，和网站一样）
- 总时长 ≈ 2.5 秒（与网站的 2.6 秒开场对齐），随后正常进入 App
- 实现方式：smali 级补丁 `WelcomeActivity.n()` 强制播放 `anim_loading_view`（帧序列文件被替换为奶龙动画帧），并把 `welcome_layout` 的背景改为透明、`welcome_image` 的 scaleType 改为 centerInside

### 2. 背景与图标（换成仓库里的两张图）
- App 主页面背景 `main_page_bg.jpg` ← `naiwa.png`（905×1439 的奶蛙图）
- App 图标全套替换 ← `naiwa (2).jpeg`（1080×1080）：
  - `ic_launcher` 全密度（mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi）
  - `ic_app_launcher` / `ic_app_launcher_round`（清单里实际引用的图标）
  - 自适应图标 foreground（抠图后的奶蛙，从白色背景边缘泛洪提取）/ background（奶龙黄纯色 + 径向光晕）
- 首次启动引导页（`assets/UserGuide/feature_guide_0~3.png`）重绘为奶蛙风格 4 页

### 3. 配色（大工蓝 → 奶龙黄）
提取两张图的主色：**奶龙黄 `#FECE0E`**（与网站 `--ink` 一致），配奶油底 `#FFFBEF`、深棕字 `#3A2C00`。

- `idg_theme_color` `#0073BD`（大工蓝·全局主题色）→ `#FECE0E`
- `idg_btn_bg_nor`、进度条、选择器、按钮、文字色等 **61 个蓝/绿系颜色**，按 HSL 色相平移到奶龙黄色系（保留明暗层次：深蓝→深琥珀，浅蓝→浅黄；灰度色保持不变以免破坏对比度）
- 共替换 **119 处**颜色值（`resources.arsc` + 42 个二进制 XML）

## 目录结构

```
├── i大工_奶蛙版_3.3.12.apk     # 成品
├── i大工_3.3.12.75026.apk      # 原版
├── naiwa.png / naiwa (2).jpeg  # 素材原图
├── theme/                      # 生成的主题资源
│   ├── frames/                 # 12 帧启动动画（480×640 透明底）
│   ├── icons/                  # 图标套件
│   ├── welcome_bg_pic.9.png    # 新欢迎页 9-patch（带 npTc 块）
│   ├── main_page_bg.jpg        # 主页背景
│   ├── feature_guide_*.png     # 引导页
│   ├── ring.webp / core.webp   # 网站动画素材
│   └── naiwa_cut.png           # 抠图后的奶蛙（透明底）
├── patches/                    # 全部构建脚本（Python）
└── preview/                    # 预览图
```

## 构建流水线（可复现）

```bash
# 依赖: JDK 17+, apktool 2.12, zipalign + apksigner (Android build-tools 34), Python 3 + PIL

APK="i大工_3.3.12.75026.apk"

# 1. 解码 smali（-r 保留原始资源，因 resources.arsc 含非法样式串 apktool 无法完整解码）
apktool d -r -f -o apk_work "$APK"

# 2. 生成全部主题素材（动画帧/9-patch/图标/背景/引导页）
python3 patches/gen_assets.py     # 需要 theme/ring.webp, theme/core.webp
python3 patches/gen_assets2.py    # 需要 naiwa (2).jpeg / naiwa.png

# 3. 应用素材到解码目录
python3 patches/apply_assets.py

# 4. smali 补丁：强制播放启动动画 + 消除退场闪烁
python3 patches/patch_smali.py

# 5. welcome_layout 二进制补丁：根布局背景透明 + scaleType=centerInside
python3 patches/patch_axml.py

# 6. 全局配色替换（HSL 蓝绿→奶龙黄）
python3 patches/recolor.py

# 7. 重建 + 对齐 + 签名
apktool b apk_work -o unsigned.apk
zipalign -f -p 4 unsigned.apk aligned.apk
keytool -genkeypair -keystore naiwa.keystore -alias nailong \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass <密码> -dname "CN=NaiLong, O=ChinaNaiLongUniversity"
apksigner sign --ks naiwa.keystore --out i大工_奶蛙版_3.3.12.apk aligned.apk
```

## 安装说明

1. 下载 `i大工_奶蛙版_3.3.12.apk`
2. **先卸载**手机上已装的官方 i大工（签名不同无法覆盖安装；卸载会清除本地登录数据）
3. 允许"安装未知来源应用"后安装
4. 打开 App 即可看到奶龙护送你上学 🐛

## 技术笔记

- 分析工具：[REA (Reverse Engineer Anything)](https://github.com/morluto/rea) + jadx-headless-mcp，用于定位启动 Activity（`com.ruijie.whistle.module.welcome.view.WelcomeActivity`）、主题（`WelcomeActivityTheme` → windowBackground = `welcome_bg_pic`）与主色（`idg_theme_color`）
- 该 App 为微哨（Ruijie Weishao）平台应用，多数业务界面是 H5（服务端下发），原生层能改的启动动画/图标/主页背景/原生控件配色均已奶蛙化；H5 页面颜色不受本地资源控制
- 9-patch 替换时从原 PNG 复制了 `npTc` 块并保持全拉伸标记，保证 windowBackground 拉伸行为与原版一致
- 签名为项目自签名（非官方签名），如官方后续热更/校验签名可能失效

## 声明

本项目仅供学习交流与个人娱乐（奶龙太可爱了）。与大连理工大学、微哨/锐捷无任何关联；奶龙形象版权归其权利人所有；请于 24 小时内自觉删除并支持官方版本（等等，这句好像是盗版免责声明的话术 —— 总之理性玩梗，快乐护送）。
