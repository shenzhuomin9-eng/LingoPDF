<div align="center">

# 🌐 LingoPDF

**批量 PDF 翻译 · 保留原排版 · 免费开源**

将英文论文、报告、文档批量翻译成中文（也支持日/韩/法/德/俄/西等语言），翻译后的 PDF 保留原始排版——公式、图表、双栏结构原样不动。

[中文](#中文) | [English](#english)

</div>

---

# 中文

## 📖 这是什么

LingoPDF 是一个 **批量 PDF 翻译工具**。你可以把多个 PDF 文件拖进去，一键翻译成你需要的语言，翻译后的 PDF 保留原始排版——标题、段落、公式、图表、双栏布局都不会乱。

**适合谁用：**
- 🎓 读英文论文的科研人员——批量翻译成中文，排版不乱，阅读体验好
- 💼 需要翻译外文报告的上班族——拖进去就走，不用一个个复制粘贴到翻译软件
- 🌍 任何需要把 PDF 文档从一种语言翻译成另一种语言的人

**核心亮点：**
- 🆓 **默认 Google 免费翻译**——不需要任何 API Key，拖入即翻，速度快
- 🎨 **排版保留**——翻译后 PDF 的版面和原文一致，公式图表不乱
- 📚 **批量处理**——一次拖入多个文件，队列逐个翻译
- 🔌 **三种引擎可选**——Google 免费 / API 高质量 / 本地离线

## 界面截图

### 主界面
![主界面](docs/main-interface-zh.png)

### 设置 — 三种翻译引擎
![设置](docs/settings-zh.png)

## ✨ 功能

- 📚 **批量翻译** — 拖拽多个 PDF，实时进度与日志
- 🎨 **排版保留** — 本地版面检测模型，公式/图表/双栏原样保留
- 🆓 **Google 免费引擎（推荐）** — 快速、免费、无需 API Key，拖入即翻译
- 🚀 **API 模式** — 自带 OpenAI 兼容 API Key（DeepSeek、GLM、Qwen 等），质量最高
- 🔌 **本地离线** — Argos 本地模型，断网可用（首次下载约 250MB）
- 🌐 **双语界面** — 英文 / 中文一键切换
- 📁 **原路径输出** — 译文 PDF 保存到源文件所在目录
- 🔐 **隐私安全** — API Key 仅存本机，不进仓库

## 🚀 快速开始（Windows）

### 方式一：双击 `start.bat`（推荐）

1. 从 GitHub 下载项目（绿色 **Code → Download ZIP**）
2. 解压到任意位置
3. **双击 `start.bat`**
4. 浏览器自动打开 `http://127.0.0.1:8377`
5. 开始翻译！

> ✅ **无需安装 Python**——项目已内置完整运行环境（`.venv`），下载即用。

### 方式二：桌面快捷方式

1. 双击项目文件夹里的 **`create_shortcut.bat`** — 在桌面创建快捷方式
2. 以后**双击桌面的 "LingoPDF" 图标**即可启动

> 两种方式都会自动打开浏览器，关闭窗口即停止服务。

## 怎么翻译

1. 把 PDF 文件拖到上传区
2. 选择源语言/目标语言（默认：英语 → 中文）
3. 点击 **▶ 开始翻译**
4. 翻译完成后点击下载

就这么简单。默认 Google 引擎免费且无需任何配置。

## 🔐 安全说明

- API Key 只存于 `~/.linguapdf/config.json`（仓库目录之外），不会被 git 追踪
- 前端读取时自动打码为 `****xxxx`，截图不泄密
- 代码中无任何硬编码密钥
- 服务默认只监听 `127.0.0.1`

## 📄 许可

MIT — 基于 [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) & [Argos Translate](https://github.com/argosopentech/argos-translate)

---

# English

## 📖 What is this

LingoPDF is a **batch PDF translation tool**. Drag in multiple PDF files, translate them into your target language with one click, and the translated PDF preserves the original layout — headings, paragraphs, formulas, charts, and multi-column structures stay intact.

**Who is it for:**
- 🎓 Researchers reading English papers — batch translate to your language with layout preserved
- 💼 Professionals translating foreign reports — drag and go, no copy-pasting into translation apps
- 🌍 Anyone who needs to translate PDF documents from one language to another

**Key highlights:**
- 🆓 **Google Free translation by default** — no API key needed, fast, just drag and translate
- 🎨 **Layout preserved** — translated PDF matches the original's layout, formulas and charts intact
- 📚 **Batch processing** — drag multiple files at once, queue translates one by one
- 🔌 **Three engines available** — Google Free / API high-quality / Local offline

## Screenshots

### Main Interface
![Main Interface](docs/main-interface.png)

### Settings — 3 Translation Engines
![Settings](docs/settings.png)

## ✨ Features

- 📚 **Batch Translation** — Drag & drop multiple PDFs, translate with real-time progress & logs
- 🎨 **Layout Preserved** — Local layout detection model keeps formulas, charts & columns intact
- 🆓 **Google Free (Recommended)** — Fast, free, no API key needed — just drag and translate
- 🚀 **API Mode** — Bring your own OpenAI-compatible API key (DeepSeek, GLM, Qwen, etc.) for best quality
- 🔌 **Local Offline** — Argos Translate model works without internet (download once, ~250MB)
- 🌐 **Bilingual UI** — English / 中文, one-click switch
- 📁 **Original Path Output** — Translated PDF saved next to the source file
- 🔐 **Privacy** — API Key stored locally only, never in the repo

## 🚀 Quick Start (Windows)

### Method 1: Double-click `start.bat` (Recommended)

1. Download the project from GitHub (green **Code → Download ZIP**)
2. Extract to any location
3. **Double-click `start.bat`**
4. Browser opens automatically at `http://127.0.0.1:8377`
5. Start translating!

> ✅ **No Python installation needed** — the project ships with a bundled runtime environment (`.venv`), ready to use out of the box.

### Method 2: Desktop Shortcut

1. Double-click **`create_shortcut.bat`** in the project folder — creates a desktop shortcut
2. **Double-click the "LingoPDF" icon** on your desktop to launch anytime

> Both methods auto-open the browser. Close the window to stop the service.

## How to Translate

1. Drag PDF file(s) into the upload area
2. Select source/target language (default: English → Chinese)
3. Click **▶ Start Translation**
4. Download the translated PDF when done

It's that simple. The default Google engine is free and requires no configuration.

## 📄 License

MIT — Built on [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) & [Argos Translate](https://github.com/argosopentech/argos-translate)

<div align="center">
<sub>⭐ Star on GitHub if this helps you</sub><br>
<sub>如果帮到了你，欢迎 ⭐ Star</sub>
</div>