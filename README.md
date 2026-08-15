<div align="center">

# 🌐 LingoPDF

**Batch PDF Translation · Layout Preserved · Ready to Use**

[English](#english) | [中文](#中文)

</div>

---

# English

## ✨ Features

- 📚 **Batch Translation** — Drag & drop multiple files, queue translation with real-time progress & logs
- 🎨 **Layout Preserved** — Local layout detection model (ONNX) reflows PDF, keeping formulas, charts & columns intact
- 🔀 **Three Engines** — Switch between quality / cost / offline at any time:

| Engine | Quality | Internet | API Key | Description |
|---|---|---|---|---|
| 🚀 **API** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | Any OpenAI-compatible API: DeepSeek, GLM, Qwen, OpenAI... |
| 🆓 **Google Free** | ⭐⭐⭐ | ✅ | ❌ | Free Google Translate web endpoint, zero config |
| 🔌 **Local Offline** | ⭐⭐ | ❌ | ❌ | Argos Translate local model (~250MB), fully offline |

> Layout preservation is identical across all engines — it's handled by the local model, independent of translation source.

- 📄 **Multi-format** — PDF direct; DOCX/PPTX auto-converted via LibreOffice
- 👯 **Bilingual Version** — Optional `_dual.pdf` side-by-side output
- 🌐 **i18n UI** — English (default) / 中文, one-click switch, preference saved
- 📁 **Original Path Output** — Translated PDF saved next to source file by default
- 🔐 **Privacy** — API Key stored locally in `~/.linguapdf/config.json`, masked in UI, zero hardcoded secrets in repo
- 🖱️ **One-Click Launch** — Double-click `start.bat` on Windows, auto-detects Python, installs deps, opens browser

## 🚀 Quick Start

### Windows (One-Click)

1. Download & extract the project
2. Double-click **`start.bat`** — auto-installs dependencies, starts server, opens browser
3. Or double-click **`create_shortcut.bat`** to create a desktop shortcut

### Command Line

```bash
pip install -r requirements.txt
python run.py
# Open http://127.0.0.1:8377
```

**Easiest path (no API Key needed):** The default engine is **Google Free** — just drag a PDF and click Start.

## 📸 Screenshots

### Main Interface
```
┌─────────────────────────────────────────────┐
│  🌐 LingoPDF          [English▾] [⚙ Google]  │
│  Batch PDF Translation · Layout Preserved    │
├─────────────────────────────────────────────┤
│                                             │
│        📄 Drop files here, or browse        │
│        Supports PDF / DOCX / PPTX           │
│                                             │
├─────────────────────────────────────────────┤
│  Source [English▾] ⇄ Target [中文▾]         │
│              [Clear] [▶ Start Translation]   │
├─────────────────────────────────────────────┤
│  File List · 1 file                         │
│  📕 paper.pdf  ✅ Done  📄 paper_zh.pdf  ⬇   │
└─────────────────────────────────────────────┘
```

### Settings (3 Engines)
```
┌─────────────────────────────────────────────┐
│  ⚙ Translation Settings                  ✕   │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐│
│  │ 🚀 API Translation      [Recommended]   ││
│  │    Highest quality · Requires API Key   ││
│  ├─────────────────────────────────────────┤│
│  │ 🆓 Google Free                          ││
│  │    No Key · Requires internet           ││
│  ├─────────────────────────────────────────┤│
│  │ 🔌 Local Offline                        ││
│  │    Works offline · Medium quality       ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y libreoffice && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8377
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8377"]
```

Environment variables (see `.env.example`):
```
LINGO_ENGINE=google
LINGO_LANG_IN=en
LINGO_LANG_OUT=zh
```

## 🔐 Security

- API Key only stored in `~/.linguapdf/config.json` (outside repo)
- UI masks key as `****xxxx`, never leaked in screenshots
- Zero hardcoded secrets — verify with: `git grep -E "sk-[A-Za-z0-9]{20,}"`
- Server listens on `127.0.0.1` only by default

## 🗂️ Project Structure

```
LingoPDF/
├── app/
│   ├── main.py         # FastAPI routes
│   ├── config.py       # Config (~/.linguapdf + env vars)
│   ├── translator.py   # 3-engine core (wraps pdf2zh)
│   └── jobs.py         # Batch job manager
├── static/             # Frontend (vanilla HTML/CSS/JS)
├── start.bat           # One-click launcher (Windows)
├── run.py              # CLI entry point
└── requirements.txt
```

## 📄 License

[MIT](LICENSE) · Built on [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) · [Argos Translate](https://github.com/argosopentech/argos-translate)

---

# 中文

## ✨ 功能

- 📚 **批量翻译** — 拖拽上传多个文件，队列逐个翻译，实时进度与日志
- 🎨 **排版保留** — 本地版面检测模型（ONNX）重排 PDF，公式/图表/双栏原样保留
- 🔀 **三种引擎** — 质量/成本/离线按需切换：

| 引擎 | 质量 | 联网 | API Key | 说明 |
|---|---|---|---|---|
| 🚀 **API 翻译** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | 任意 OpenAI 兼容接口：DeepSeek、GLM、Qwen、OpenAI… |
| 🆓 **Google 免费** | ⭐⭐⭐ | ✅ | ❌ | 免费 Google 翻译网页接口，零配置 |
| 🔌 **本地离线** | ⭐⭐ | ❌ | ❌ | Argos 本地模型（~250MB），完全断网可用 |

> 三种引擎排版效果完全一致——排版由本地模型负责，与翻译来源无关。

- 📄 **多格式** — PDF 直译；DOCX/PPTX 自动经 LibreOffice 转 PDF
- 👯 **双语对照** — 可选输出 `_dual.pdf`，原文译文左右/上下对照
- 🌐 **界面国际化** — 默认英文，支持中/英一键切换，偏好持久化
- 📁 **原路径输出** — 译文 PDF 默认保存到源文件所在目录
- 🔐 **隐私安全** — API Key 仅存本机，前端打码，仓库零硬编码密钥
- 🖱️ **一键启动** — Windows 双击 `start.bat`，自动安装依赖、启动服务、打开浏览器

## 🚀 快速开始

### Windows 一键启动

1. 下载并解压项目
2. 双击 **`start.bat`** — 自动检测 Python、安装依赖、启动服务、打开浏览器
3. 或双击 **`create_shortcut.bat`** 创建桌面快捷方式

### 命令行启动

```bash
pip install -r requirements.txt
python run.py
# 浏览器打开 http://127.0.0.1:8377
```

**最简体验**（无需任何 Key）：默认引擎就是 **Google 免费** — 拖入 PDF，点击开始翻译即可。

### 本地离线模式

设置 → 引擎选「本地离线」→ 点击下载 `en→zh` 模型（约 250MB，仅首次联网）→ 之后完全断网可翻译。

## 📸 界面预览

### 主界面
```
┌─────────────────────────────────────────────┐
│  🌐 LingoPDF          [English▾] [⚙ Google]  │
│  批量 PDF 翻译 · 保留原排版                    │
├─────────────────────────────────────────────┤
│                                             │
│        📄 拖拽文件到这里，或浏览文件           │
│        支持 PDF / DOCX / PPTX 批量上传       │
│                                             │
├─────────────────────────────────────────────┤
│  源语言 [English▾] ⇄ 目标语言 [中文▾]        │
│              [清空] [▶ 开始翻译]               │
├─────────────────────────────────────────────┤
│  文件列表 · 1 个文件                         │
│  📕 paper.pdf  ✅ 完成  📄 paper_zh.pdf  ⬇   │
└─────────────────────────────────────────────┘
```

## 🐳 Docker 部署

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y libreoffice && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8377
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8377"]
```

## 🔐 安全说明

- API Key 只存于 `~/.linguapdf/config.json`（仓库目录之外），不会被 git 追踪
- 前端读取时自动打码为 `****xxxx`，截图不泄密
- 代码中无任何硬编码密钥
- 服务默认只监听 `127.0.0.1`

## 📋 发布到 GitHub 步骤

```bash
# 1. 初始化 git 仓库
cd LingoPDF
git init
git add .
git commit -m "Initial release: LingoPDF - Batch PDF Translator"

# 2. 在 GitHub 创建新仓库 (github.com/new)
#    仓库设置：Public, 不要勾选 README/LICENSE/.gitignore（我们已有）

# 3. 关联远程仓库并推送
git remote add origin https://github.com/你的用户名/LingoPDF.git
git branch -M main
git push -u origin main

# 4. 发布 Release (可选)
#    GitHub 仓库页面 → Releases → Draft a new release
#    Tag: v1.0.0, Title: "LingoPDF v1.0 - 首个开源版本"
```

## 📄 许可

[MIT](LICENSE) · 翻译排版基于 [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) · 本地翻译基于 [Argos Translate](https://github.com/argosopentech/argos-translate)

<div align="center">
<sub>If this project helps you, please ⭐ Star on GitHub</sub>
<br>
<sub>如果这个项目帮到了你，欢迎 ⭐ Star</sub>
</div>