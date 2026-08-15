<div align="center">

# 🌐 LingoPDF

**Batch PDF Translation · Layout Preserved · Free & Open Source**

Translate PDFs in bulk while keeping the original layout. No API key required.

[English](#english) | [中文](#中文)

</div>

---

# English

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

### Method 1: Double-click `start.bat`

1. Download & extract the project
2. Open the project folder
3. **Double-click `start.bat`**
4. Browser opens automatically at `http://127.0.0.1:8377`

### Method 2: Desktop Shortcut

1. Double-click **`create_shortcut.bat`** in the project folder — creates a desktop shortcut
2. **Double-click the "LingoPDF" icon** on your desktop to launch anytime

> Both methods auto-detect Python, install dependencies on first run, and open the browser.

## How to Translate

1. Drag PDF file(s) into the upload area
2. Select source/target language (default: English → Chinese)
3. Click **▶ Start Translation**
4. Download the translated PDF when done

It's that simple. The default Google engine is free and requires no configuration.

## 🐳 Docker

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

## 📄 License

MIT — Built on [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) & [Argos Translate](https://github.com/argosopentech/argos-translate)

---

# 中文

## 界面截图

### 主界面
![主界面](docs/main-interface-zh.png)

### 设置 -- 三种翻译引擎
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

### 方式一：双击 `start.bat`

1. 下载并解压项目
2. 打开项目文件夹
3. **双击 `start.bat`**
4. 浏览器自动打开 `http://127.0.0.1:8377`

### 方式二：桌面快捷方式

1. 双击项目文件夹里的 **`create_shortcut.bat`** — 在桌面创建快捷方式
2. 以后**双击桌面的 "LingoPDF" 图标**即可启动

> 两种方式都会自动检测 Python、首次运行自动安装依赖、自动打开浏览器。

## 怎么翻译

1. 把 PDF 文件拖到上传区
2. 选择源语言/目标语言（默认：英语 → 中文）
3. 点击 **▶ 开始翻译**
4. 翻译完成后点击下载

就这么简单。默认 Google 引擎免费且无需任何配置。

## 📄 许可

MIT — 基于 [pdf2zh](https://github.com/Byaidu/PDFMathTranslate) & [Argos Translate](https://github.com/argosopentech/argos-translate)

<div align="center">
<sub>⭐ Star on GitHub if this helps you</sub><br>
<sub>如果帮到了你，欢迎 ⭐ Star</sub>
</div>