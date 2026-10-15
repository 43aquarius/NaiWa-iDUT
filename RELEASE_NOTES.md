# 奶蛙 i大工 v5.0 —— 开屏动画真正回来了 + 「关于i大工奶蛙」页面 🐸

## v5.0 修复与新增（响应实测反馈）

### 1. 开屏动画内容消失 · 根治 🎬
- **根因（v2-v4 遗留）**：欢迎页代码里 `ImageLoader.displayImage(服务器欢迎图, welcome_image)` 与我们的帧动画**抢同一个 ImageView**，动画从未真正站稳 —— v3 时代靠 9-patch 里烤入的静态奶蛙"遮掩"了问题，v4 把静态内容移除后真相暴露（只剩纯渐变背景）
- **修复（三重保险）**：
  1. **消除竞争**：nop 掉服务器欢迎图加载，welcome_image 完全归奶蛙动画
  2. **动画重生**：12 帧重制 —— 奶蛙从 25% 弹性放大入场（过冲回弹）→ 轻呼吸定格，帧间差异从 ~2% 提升到 9.6~57（肉眼可见的动画）；oneshot=true 播完定格在满血奶蛙
  3. **静态兜底**：布局 src 直接指向定格帧 PNG（普通位图，绝无失败路径）——就算动画 API 全挂，开屏也有完整奶蛙
- AnimStarter v2：getDrawable 为空时自动重挂动画资源再启动（null-safe + instance-of 校验）
- 构图下移：奶蛙主体避开顶部 80dp 徽章区，不再重叠

### 2. 「关于i大工奶蛙」页面 📄
- 「我的」页菜单「关于i大工」旁新增「关于i大工奶蛙」入口
- 页面内容（纯代码构建 UI，无新增资源依赖）：
  - 奶蛙 logo + 标题「关于i大工奶蛙」+ 副标题「i大工 · 奶蛙主题二创版 v5.0」
  - **GitHub 开源项目卡片**：github.com/43aquaris/NaiWa-iDUT（点击跳转仓库）
  - **免责声明卡片**：非官方二创、仅供娱乐、与大连理工大学及官方开发者无关、素材版权归原作者、后果自负、侵权联系删除
  - 底部标注「非官方二次创作 · 仅供娱乐 · 与官方无关」

### 3. 提交身份修正 ✍️
- 全部主题版本提交统一以 43aquarius 名义（178629746+43aquarius@users.noreply.github.com），并修正 v4 误用的机器身份

### 4. 工程质量
- build_v5.sh 一键流水线：v4 全部步骤 + v5 素材/布局/smali/manifest 注入 + APK 内终检（布局 src、oneshot、Manifest 注册、displayImage nop、菜单项、帧弹入比例）
- manifest 二进制注入器（幂等）+ 自校验 walk；smali 新类（AboutNaiWaActivity / n$nw / AnimStarter v2）汇编 + 反汇编往返验证
- 签名 verify 通过；视觉预览 VLM 评审 PASS

### 5. 保留 v4/v3/v2 全部成果
- 纯渐变开屏背景（无拉伸变形）、底部导航/服务页/34 处合成大奶蛙图标、我的页面奶蛙背景、127 色值 + 323 图重着色、头像与空状态奶蛙化、2600ms 开屏时长

## 素材来源
- 合成大奶蛙（yhsome.github.io/BigNaiWa）· 奶蛙消消乐（chenckx0614.github.io/naiwaxxl）· 原帧素材（theme/frames）

## 仅供娱乐 · 非官方二创 · 与官方无关
