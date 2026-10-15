# 奶蛙 i大工 🐛 (NaiWa-iDUT)

> 把「i大工」（大连理工大学校园 App）做成**奶龙/奶蛙主题**的定制版
>
> 入场动画复刻自 [中国奶龙大学.com](https://xn--fiqs8srwb9iv6f6w9n.com/)（奶龙正在护送你前往中国奶龙大学）

## 成品下载

| 文件 | 说明 |
|---|---|
| `i大工_奶蛙版_3.3.12.apk` | **v2.0 奶蛙主题定制版**（本仓库直接下载，或到 [Releases](../../releases) 下载 ASCII 文件名版本） |
| `i大工_3.3.12.75026.apk` | 原版 App（未修改） |

**版本**：基于 i大工 3.3.12.75026 · 签名密钥为本项目自签（v2 重新生成，需卸载 v1 后安装）

## v2.0 修复了什么（相对 v1.0）

用户实测 v1 后反馈三个问题，v2 全部修复：

| v1 问题 | 根因 | v2 修复 |
|---|---|---|
| 启动白屏、无动画 | AnimationDrawable 在 View attach 前 start；布局三个 ImageView 都无 src，动画一旦没起来就是纯色屏 | welcome_layout 整体重写：`welcome_image` 直接带 `src=anim_loading_view`（**XML 静态兜底**，代码全挂也有画面）；动画经 `View.post(AnimStarter)` 在 attach 后启动；try-catch 异常安全；时长 2.6s |
| 主页面看不到 naiwa 图 | `MainActivity` 实际用 `activity_main` 布局，背景是**纯色** `background_color_fb`；被替换的 `main_page_bg` 只被一个旧布局引用，从未显示；且 ServiceFragment 根布局还有一层不透明底色 | `activity_main` 根背景改为 `@drawable/main_page_bg`（naiwa 9-patch 居中不变形）；`fragment_tab_service` 根背景改透明；arsc 引用 .jpg→.png |
| 还有大量蓝色 | v1 只改了颜色**数值**（119 处），**191 张蓝色 PNG 图片**（loading 转圈/浏览器图标/复选框/开关/顶栏）完全没碰 | 像素级 HSL 色相平移：**291 张图片、505 万像素**蓝/绿→奶龙黄（保留明度与 alpha；9-patch 的 npTc 块完整保留）；颜色值宽网重扫 127 处，蓝灰文本色→暖棕 |

## 改了什么（v2 全量）

### 1. 启动动画（复刻中国奶龙大学网站的入场动画）
- 冷启动窗口背景：奶龙米色渐变 **9-patch（aapt2 正确编译，带 npTc/npOl）**，替代原纯蓝屏
- 欢迎页 12 帧帧动画三要素：
  - 白底圆盘徽章 + **旋转的文字环**（每帧 30°，来自网站的 `ring.webp`）
  - 中心的奶龙**呼吸缩放**（来自网站的 `core.webp`）
  - 外圈**进度环**从 0% 填满一圈（奶龙黄 `#FECE0E`）
  - 标题「中国奶龙大学」+ 副标题「奶龙正在护送你前往…」
- 总时长 ≈ 2.6 秒
- 实现：`WelcomeActivity.n()` smali 补丁（nop 跳过分支 + AnimStarter post 启动 + try-catch），`welcome_layout.xml` 由自研二进制 AXML 生成器整体重写（根布局默认可见 + 静态首帧兜底 + 顶部奶蛙图标）

### 2. 背景与图标
- **主页面背景**：`activity_main` 根布局背景 ← `main_page_bg`（`naiwa.png` 重制的标准 9-patch：奶蛙居中固定、四周拉伸，任意屏幕不变形）+ `fragment_tab_service` 透明化
- App 图标全套 ← `naiwa (2).jpeg`：`ic_launcher` 全密度、`ic_app_launcher`/`_round`（清单实际引用）、自适应图标 foreground/background
- 首次启动引导页 4 张奶蛙风格重绘

### 3. 配色（大工蓝 → 奶龙黄，像素级全覆盖）
主色 **奶龙黄 `#FECE0E`**（与网站 `--ink` 一致），奶油底 `#FFFBEF`、深棕字 `#3A2C00`。

- 颜色值：`idg_theme_color` `#0073BD`→`#FECE0E` 精确映射；127 处 arsc/XML 颜色值宽网替换（蓝/青 hue 175-275 且 s>0.12；蓝灰→暖棕）
- **图片：291 张 PNG/WebP 像素级色相平移**（蓝/绿→奶龙黄，保留明度层次、透明度与 npTc 块）
- 纯白/纯黑像素保留（维持对比度）
- 服务器下发的 H5 页面颜色无法本地修改（如校园资讯详情页）

## 目录结构

```
├── i大工_奶蛙版_3.3.12.apk     # 成品 (v2)
├── i大工_3.3.12.75026.apk      # 原版
├── naiwa.png / naiwa (2).jpeg  # 素材原图
├── theme/                      # 生成的主题资源
│   ├── frames/                 # 12 帧启动动画（480×640 透明底）
│   ├── icons/                  # 图标套件
│   ├── welcome_bg_pic.9.png    # 欢迎页 9-patch（aapt2 编译）
│   ├── main_page_bg.9.png      # 主页背景 9-patch（aapt2 编译）
│   ├── feature_guide_*.png     # 引导页
│   ├── ring.webp / core.webp   # 网站动画素材
│   └── naiwa_cut.png           # 抠图后的奶蛙（透明底）
├── patches/                    # 全部构建脚本（Python，v2）
│   ├── build_all.sh            # 一键流水线
│   ├── gen_assets_v2.py        # 素材生成（aapt2 编译 9-patch）
│   ├── gen_welcome_layout.py   # 二进制 AXML 生成器（welcome_layout 重写）
│   ├── patch_layouts.py        # activity_main/fragment_tab_service 背景补丁
│   ├── patch_smali_v2.py       # smali 补丁（AnimStarter + try-catch + 2.6s）
│   ├── recolor_v2.py           # 颜色值宽网替换（arsc + XML）
│   ├── recolor_images.py       # 像素级图片重着色（npTc 保留）
│   ├── assemble_apk.py         # APK 组装（按原压缩方式）
│   └── arsc_parser.py          # ARSC/AXML 解析库
└── preview/                    # 预览图
```

## 构建流水线（可复现）

```bash
# 依赖: JDK 17+, aapt2 + zipalign + apksigner (Android build-tools 34), Python3 + PIL + numpy,
#       smali/baksmali 2.5.2 (Maven Central: org.smali:{smali,baksmali,dexlib2,util} + guava + jcommander + antlr-runtime)

APK="i大工_3.3.12.75026.apk"

# 1. 解包：unzip + baksmali 反编译两个 dex（-r 保留资源方式，arsc 含非法样式串 apktool 无法完整解码）
unzip "$APK" -d orig
java -cp $SMALI_CP org.jf.baksmali.Main disassemble orig/classes.dex -o smali_work/smali_classes
java -cp $SMALI_CP org.jf.baksmali.Main disassemble orig/classes2.dex -o smali_work/smali_classes2

# 2. 生成素材（9-patch 经 aapt2 编译，含正确 npTc/npOl）
python3 patches/gen_assets_v2.py

# 3. 重写 welcome_layout.xml（二进制 AXML 生成器 + 自校验）
python3 patches/gen_welcome_layout.py

# 4. 主页面背景引用补丁
python3 patches/patch_layouts.py

# 5. smali 补丁：AnimStarter post 启动动画 + try-catch + 2600ms
python3 patches/patch_smali_v2.py

# 6. 全局配色（值 + 像素）
python3 patches/recolor_v2.py      # arsc + XML 颜色值（含 .jpg→.png 引用）
python3 patches/recolor_images.py  # 291 张图片像素级

# 7. 重组 dex + 组装 + 对齐 + 签名
java -cp $SMALI_CP org.jf.smali.Main assemble smali_work/smali_classes -o new_classes.dex
java -cp $SMALI_CP org.jf.smali.Main assemble smali_work/smali_classes2 -o new_classes2.dex
python3 patches/assemble_apk.py
zipalign -f -p 4 unsigned.apk aligned.apk
keytool -genkeypair -keystore naiwa.keystore -alias nailong -keyalg RSA -keysize 2048 \
  -validity 10000 -storepass <密码> -dname "CN=NaiLong, O=ChinaNaiLongUniversity"
apksigner sign --ks naiwa.keystore --out i大工_奶蛙版_3.3.12.apk aligned.apk
```

或直接 `bash patches/build_all.sh`（自动执行 2-8 步）。

## 安装说明

1. 下载 `i大工_奶蛙版_3.3.12.apk`（或 Release 里的 `iDaGong_NaiWa_v2.0.apk`）
2. **先卸载**手机上的官方 i大工 **和 v1.0 奶蛙版**（v2 重新生成了签名密钥，无法覆盖安装；卸载会清除本地登录数据）
3. 允许"安装未知来源应用"后安装
4. 打开 App，奶龙护送你上学 🐛

## 技术笔记

- 分析工具：[REA (Reverse Engineer Anything)](https://github.com/morluto/rea) + 自研 ARSC/AXML 二进制解析器（`patches/arsc_parser.py`），用于定位启动 Activity（`com.ruijie.whistle.module.welcome.view.WelcomeActivity`）、主题（`WelcomeActivityTheme` → windowBackground = `welcome_bg_pic`）与主色（`idg_theme_color`）
- **npTc 9-patch 格式逆向**：通过 aapt2 对照实验确定了编译后 9-patch 的二进制布局（div 偏移 LE / 值 BE / ARGB 颜色数组），v2 的 9-patch 全部走 aapt2 编译，不再手搓
- 该 App 为微哨（Ruijie Weishao）平台应用，多数业务界面是 H5（服务端下发）：原生层能改的启动动画/图标/主页背景/原生控件与图片配色均已奶蛙化；**H5 页面颜色不受本地资源控制**
- 9-patch 像素重着色时 npTc/npOl 块提取后重新插回，保证拉伸行为与原版一致
- 签名为项目自签（非官方签名），如官方后续热更/校验签名可能失效

## 声明

本项目仅供学习交流与个人娱乐（奶龙太可爱了）。与大连理工大学、微哨/锐捷无任何关联；奶龙形象版权归其权利人所有；请于 24 小时内自觉删除并支持官方版本（等等，这句好像是盗版免责声明的话术 —— 总之理性玩梗，快乐护送）。
