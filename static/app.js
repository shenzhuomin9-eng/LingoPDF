/* ═══════════════ LingoPDF 前端逻辑 ═══════════════ */

const $ = (id) => document.getElementById(id);

const state = {
  cfg: {},
  files: [],        // {name, size, path(File)}
  jobId: null,
  polling: null,
  logSeq: 0,
  uiLang: "en",    // 界面语言: en | zh
};

/* ── i18n 国际化 ─────────────────────────── */

const I18N = {
  en: {
    tagline: "Batch PDF Translation · Layout Preserved · API / Free / Offline",
    clickToChange: "Click to change settings",
    Settings: "Settings",
    dropHere: "Drop files here, or",
    browse: "browse files",
    dropHint1: "Supports PDF / DOCX / PPTX batch upload · Max 200MB per file",
    dropHint2: "DOCX/PPTX requires LibreOffice installed",
    sourceLang: "Source",
    targetLang: "Target",
    swapLangs: "Swap languages",
    clear: "Clear",
    downloadAll: "⬇ Download All",
    start: "▶ Start Translation",
    uploading: "⏳ Uploading...",
    cancel: "■ Cancel",
    fileList: "File List",
    ready: "Ready",
    detectedLang: "Source: ",
    runLog: "Run Log",
    collapse: "Collapse",
    expand: "Expand",
    footerText: "Layout preserved by local detection model · Switch engines anytime · API Key stored locally only",
    settingsTitle: "⚙ Translation Settings",
    close: "Close",
    engineLabel: "Translation Engine",
    engineApi: "API Translation",
    engineApiDesc: "OpenAI-compatible API<br>Highest quality · Requires API Key",
    recommended: "Recommended",
    engineGoogle: "Google Free",
    engineGoogleDesc: "Free web API<br>No Key needed · Requires internet",
    engineLocal: "Local Offline",
    engineLocalDesc: "Argos local model<br>Works offline · Medium quality",
    apiBaseUrl: "API Base URL",
    apiKeyHint: "(stored locally only, never uploaded)",
    apiKeySaved: "Saved (type a new value to overwrite)",
    modelName: "Model Name",
    testConn: "🔌 Test Connection",
    testing: "⏳ Testing...",
    connecting: "Connecting...",
    argosChecking: "Checking local model status...",
    argosDownload: "⬇ Download en→zh model (~250MB, one-time)",
    argosHint: "Once installed, the local model runs fully offline. Quality is lower than API but sufficient for everyday documents.",
    threadLabel: "Concurrent Threads",
    threadHint: "(API engine concurrency)",
    dualOutput: "Also output bilingual side-by-side version (<name>_dual.pdf)",
    outputDirLabel: "Output Directory",
    outputDirHint: "(empty = same folder as source file)",
    outputDirPh: "Leave empty for source folder",
    resetDefaults: "Reset Defaults",
    saveSettings: "Save Settings",
    // 状态
    pending: "Pending",
    remove: "Remove",
    filesUnit: "files",
    converting: "Converting…",
    translating: "Translating…",
    done: "Done",
    failed: "Failed",
    canceled: "Canceled",
    // 徽章
    engineApiBadge: "API Translation",
    engineGoogleBadge: "Google Free",
    engineArgosBadge: "Local Offline",
    // 消息
    settingsSaved: "Settings saved ✓",
    skippedFiles: (n) => `Skipped ${n} unsupported file(s)`,
    configLoadFailed: "Failed to load config: ",
    noApiKey: "API engine selected — please configure base_url and api_key in Settings",
    cancelSent: "Cancel request sent",
    removeBlocked: "Cannot remove files during active job",
    resetConfirm: "Reset all settings to defaults? (including saved API Key)",
    resetDone: "Settings reset to defaults",
    argosNotInstalled: "argostranslate library not installed",
    argosRunCmd: "Please run: pip install argostranslate then restart",
    argosReady: "✓ Local model ready",
    argosInstalled: (p) => `Installed: ${p} · Fully offline`,
    argosNotReady: "⏳ Local model not yet installed",
    argosDownloadHint: "Click the button below to download (internet needed once)",
    downloading: "⏳ Downloading, please wait...",
    uploadFailed: (m) => m,
    detecting: "Detecting",
    // 进度
    translating2: (d, t) => `Translating ${d}/${t}`,
    finished: (ok, fail, elapsed) => `Done · ✅ ${ok} ok / ❌ ${fail} failed · ${elapsed}`,
    jobEnded: (ok, fail) => `—— Job ended: ✅ ${ok} / ❌ ${fail} ——`,
    jobStarted: (n) => `Job started: ${n} file(s)`,
    noLibreOffice: "⚠ LibreOffice not detected, non-PDF files will be skipped",
    libreOfficeFound: (n) => `LibreOffice: ${n}`,
    loadingModel: "Loading layout detection model (~5-10s)...",
    modelLoaded: "Layout model loaded",
    modelLoadFailed: (e) => `Model load failed: ${e}`,
    translatingFile: (n) => `[${n}] Converting to PDF...`,
    // 下载
    dlTranslated: "⬇ Download",
    dlDual: "⬇ Bilingual",
  },
  zh: {
    tagline: "批量 PDF 翻译 · 保留原排版 · 支持 API / 免费 / 本地离线",
    clickToChange: "点击更改设置",
    Settings: "设置",
    dropHere: "拖拽文件到这里，或",
    browse: "浏览文件",
    dropHint1: "支持 PDF / DOCX / PPTX 批量上传 · 单文件 ≤ 200MB",
    dropHint2: "DOCX/PPTX 需要本机安装 LibreOffice",
    sourceLang: "源语言",
    targetLang: "目标语言",
    swapLangs: "交换语言",
    clear: "清空",
    downloadAll: "⬇ 全部下载",
    start: "▶ 开始翻译",
    uploading: "⏳ 上传中...",
    cancel: "■ 取消",
    fileList: "文件列表",
    ready: "就绪",
    detectedLang: "源语言：",
    runLog: "运行日志",
    collapse: "收起",
    expand: "展开",
    footerText: "排版保留由本地版面检测模型完成 · 翻译引擎可随时切换 · API Key 仅存本机",
    settingsTitle: "⚙ 翻译设置",
    close: "关闭",
    engineLabel: "翻译引擎",
    engineApi: "API 翻译",
    engineApiDesc: "OpenAI 兼容接口<br>质量最高 · 需 API Key",
    recommended: "推荐",
    engineGoogle: "Google 免费",
    engineGoogleDesc: "免费网页接口<br>无需 Key · 需联网",
    engineLocal: "本地离线",
    engineLocalDesc: "Argos 本地模型<br>断网可用 · 质量中等",
    apiBaseUrl: "API Base URL",
    apiKeyHint: "（仅保存在本机，不会上传到任何地方）",
    apiKeySaved: "已保存（输入新值可覆盖）",
    modelName: "模型名称",
    testConn: "🔌 测试连接",
    testing: "⏳ 测试中...",
    connecting: "正在连接...",
    argosChecking: "检查本地模型状态...",
    argosDownload: "⬇ 下载 en→zh 模型（约 250MB，仅一次）",
    argosHint: "本地模型安装后完全离线运行，不再需要网络。质量不如 API，但日常文档够用。",
    threadLabel: "并发线程数",
    threadHint: "（API 引擎的并发请求粒度）",
    dualOutput: "同时输出双语对照版 (<原名>_dual.pdf，左右/上下对照)",
    outputDirLabel: "输出目录",
    outputDirHint: "（留空 = 输出到源文件原路径）",
    outputDirPh: "留空则与源文件同目录",
    resetDefaults: "恢复默认",
    saveSettings: "保存设置",
    pending: "等待中",
    remove: "移除",
    filesUnit: "个",
    converting: "转 PDF…",
    translating: "翻译中…",
    done: "完成",
    failed: "失败",
    canceled: "已取消",
    engineApiBadge: "API 翻译",
    engineGoogleBadge: "Google 免费",
    engineArgosBadge: "本地离线",
    settingsSaved: "设置已保存 ✓",
    skippedFiles: (n) => `跳过 ${n} 个不支持的文件`,
    configLoadFailed: "加载配置失败: ",
    noApiKey: "当前引擎为 API 翻译，请先在设置中配置 base_url 和 api_key",
    cancelSent: "已发送取消请求",
    removeBlocked: "任务进行中，无法移除文件",
    resetConfirm: "恢复全部设置为默认值？（包含已保存的 API Key）",
    resetDone: "已恢复默认",
    argosNotInstalled: "⚠ argostranslate 库未安装",
    argosRunCmd: "请执行: pip install argostranslate 后重启服务",
    argosReady: "✓ 本地模型已就绪",
    argosInstalled: (p) => `已安装: ${p} · 完全离线可用`,
    argosNotReady: "⏳ 尚未安装本地模型",
    argosDownloadHint: "点击下方按钮下载（仅首次需要联网）",
    downloading: "⏳ 下载中，请稍候...",
    uploadFailed: (m) => m,
    detecting: "检测中",
    translating2: (d, t) => `翻译中 ${d}/${t}`,
    finished: (ok, fail, elapsed) => `完成 · ✅ ${ok} 成功 / ❌ ${fail} 失败 · ${elapsed}`,
    jobEnded: (ok, fail) => `—— 任务结束：✅ ${ok} / ❌ ${fail} ——`,
    jobStarted: (n) => `任务开始：${n} 个文件`,
    noLibreOffice: "⚠ 未检测到 LibreOffice，非 PDF 文件将跳过",
    libreOfficeFound: (n) => `LibreOffice: ${n}`,
    loadingModel: "加载版面检测模型（首次约 5-10 秒）...",
    modelLoaded: "版面模型加载完成",
    modelLoadFailed: (e) => `模型加载失败: ${e}`,
    translatingFile: (n) => `[${n}] 正在转为 PDF...`,
    dlTranslated: "⬇ 下载",
    dlDual: "⬇ 对照版",
  },
};

function t(key, ...args) {
  const dict = I18N[state.uiLang] || I18N.en;
  const val = dict[key] ?? I18N.en[key] ?? key;
  return typeof val === "function" ? val(...args) : val;
}

function applyI18n() {
  try {
    document.documentElement.lang = state.uiLang;
    const dict = I18N[state.uiLang] || I18N.en;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const val = dict[key] || I18N.en[key] || key;
      if (el.childElementCount > 0) {
        // i18n 值含 HTML 标签（如 <br>）——说明该元素的完整内容由 i18n 提供，
        // 直接用 innerHTML 替换全部内容（引擎描述卡片属于此类）
        if (/<[a-z/][a-z0-9]*>/i.test(val)) {
          el.innerHTML = val;
        } else {
          // 元素有子元素（如 label 包裹 select）——只替换第一个文本节点
          let firstText = null;
          for (const node of el.childNodes) {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
              firstText = node;
              break;
            }
          }
          if (firstText) {
            // 保留与子元素之间的空格分隔
            firstText.textContent = val + " ";
          } else {
            el.insertBefore(document.createTextNode(val), el.firstChild);
          }
        }
      } else {
        el.innerHTML = val;
      }
    });
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      el.title = dict[el.getAttribute("data-i18n-title")] || "";
    });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      el.placeholder = dict[el.getAttribute("data-i18n-ph")] || "";
    });
    updateEngineBadge();
    if (!state.polling && state.files.length === 0) {
      $("progressText").textContent = t("ready");
    }
  } catch (err) {
    console.error("[i18n applyI18n error]", err);
  }
}

const STATUS_LABEL = {
  pending: () => t("pending"),
  converting: () => t("converting"),
  translating: () => t("translating"),
  done: () => t("done"),
  failed: () => t("failed"),
  canceled: () => t("canceled"),
};

const ENGINE_LABEL = {
  openai: () => t("engineApiBadge"),
  google: () => t("engineGoogleBadge"),
  argos: () => t("engineArgosBadge"),
};

/* ── 工具 ─────────────────────────── */

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1024 / 1024).toFixed(1) + " MB";
}

function fmtTime(sec) {
  return sec >= 60 ? `${Math.floor(sec / 60)}分${Math.round(sec % 60)}秒` : `${sec.toFixed(1)}秒`;
}

function toast(msg, type = "") {
  const el = $("toast");
  el.textContent = msg;
  el.className = `toast ${type}`;
  el.hidden = false;
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.hidden = true), 3200);
}

async function api(path, opts = {}) {
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    let detail = resp.statusText;
    try { detail = (await resp.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

/* ── 配置 ─────────────────────────── */

async function loadConfig() {
  state.cfg = await api("/api/config");
  $("cfgBaseUrl").value = state.cfg.base_url || "";
  $("cfgApiKey").value = state.cfg.api_key || "";
  $("cfgApiKey").dataset.masked = state.cfg.has_api_key ? "1" : "";
  $("cfgApiKey").placeholder = state.cfg.has_api_key ? t("apiKeySaved") : "sk-...";
  $("cfgModel").value = state.cfg.model || "";
  $("cfgThread").value = state.cfg.thread || 4;
  $("threadVal").textContent = state.cfg.thread || 4;
  $("cfgOutputDir").value = state.cfg.output_dir || "";
  $("langIn").value = state.cfg.lang_in || "en";
  $("langOut").value = state.cfg.lang_out || "zh";
  state.uiLang = state.cfg.ui_lang || "en";
  $("uiLang").value = state.uiLang;
  applyI18n();
  setEngineUI(state.cfg.engine || "openai");
  updateEngineBadge();
}

function setEngineUI(engine) {
  document.querySelectorAll(".engine-card").forEach((c) =>
    c.classList.toggle("active", c.dataset.engine === engine)
  );
  $("openaiFields").hidden = engine !== "openai";
  $("argosFields").hidden = engine !== "argos";
}

function updateEngineBadge() {
  const engine = document.querySelector(".engine-card.active")?.dataset.engine || state.cfg.engine;
  const badge = $("engineBadge");
  badge.textContent = `⚙ ${ENGINE_LABEL[engine]?.() || engine}`;
  badge.className = "engine-badge " + (engine === "openai" ? "is-openai" : engine === "argos" ? "is-argos" : "");
}

async function saveSettings() {
  const engine = document.querySelector(".engine-card.active").dataset.engine;
  // 保存语言方向（也持久化）
  const payload = {
    engine,
    lang_in: $("langIn").value,
    lang_out: $("langOut").value,
    model: $("cfgModel").value.trim(),
    thread: parseInt($("cfgThread").value, 10),
    output_dir: $("cfgOutputDir").value.trim(),
  };
  if ($("cfgBaseUrl").value.trim()) payload.base_url = $("cfgBaseUrl").value.trim();
  const key = $("cfgApiKey").value;
  if (key && !key.includes("*")) payload.api_key = key.trim();

  state.cfg = await api("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  closeSettings();
  toast(t("settingsSaved"), "ok");
  updateEngineBadge();
}

/* ── 设置抽屉 ─────────────────────────── */

function openSettings() {
  $("settingsOverlay").hidden = false;
  $("settingsDrawer").hidden = false;
  if ((document.querySelector(".engine-card.active")?.dataset.engine) === "argos") refreshArgos();
}

function closeSettings() {
  $("settingsOverlay").hidden = true;
  $("settingsDrawer").hidden = true;
}

async function refreshArgos() {
  const info = await api("/api/engines");
  const st = info.argos;
  const el = $("argosStatus");
  if (!st.library_installed) {
    el.innerHTML = `<span style="color:var(--yellow)">${t("argosNotInstalled")}</span><br>
      <span class="small muted">${t("argosRunCmd")}</span>`;
    $("btnArgosInstall").hidden = true;
    return;
  }
  const hasZh = st.installed.some((p) => p === "en->zh");
  if (hasZh) {
    el.innerHTML = `<span style="color:var(--green)">${t("argosReady")}</span>
      <span class="small muted">${t("argosInstalled", st.installed.join(", "))}</span>`;
    $("btnArgosInstall").hidden = true;
  } else {
    el.innerHTML = `<span style="color:var(--yellow)">${t("argosNotReady")}</span>
      <span class="small muted">${t("argosDownloadHint")}</span>`;
    $("btnArgosInstall").hidden = false;
  }
}

async function installArgos() {
  const btn = $("btnArgosInstall");
  btn.disabled = true;
  btn.textContent = t("downloading");
  try {
    const r = await api("/api/engines/argos/install?lang_in=en&lang_out=zh");
    toast(r.message, r.ok ? "ok" : "bad");
  } catch (e) {
    toast(e.message, "bad");
  } finally {
    btn.disabled = false;
    btn.textContent = t("argosDownload");
    refreshArgos();
  }
}

async function testConnection() {
  const btn = $("btnTestConn");
  const msg = $("testConnMsg");
  btn.disabled = true;
  btn.textContent = t("testing");
  msg.hidden = false;
  msg.className = "test-msg";
  msg.textContent = t("connecting");
  try {
    const engine = document.querySelector(".engine-card.active").dataset.engine;
    const payload = {
      engine,
      lang_in: $("langIn").value,
      lang_out: $("langOut").value,
    };
    if (engine === "openai") {
      payload.base_url = $("cfgBaseUrl").value.trim() || state.cfg.base_url;
      payload.model = $("cfgModel").value.trim() || state.cfg.model;
      const key = $("cfgApiKey").value;
      if (key && !key.includes("*")) payload.api_key = key.trim();
    }
    const r = await api("/api/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    msg.className = "test-msg " + (r.ok ? "ok" : "bad");
    msg.textContent = (r.ok ? "✓ " : "✗ ") + r.message;
  } catch (e) {
    msg.className = "test-msg bad";
    msg.textContent = "✗ " + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = t("testConn");
  }
}

/* ── 文件选择 ─────────────────────────── */

function addFiles(fileList) {
  const ok = [".pdf", ".docx", ".pptx", ".doc", ".ppt"];
  let skipped = 0;
  for (const f of fileList) {
    const ext = "." + f.name.split(".").pop().toLowerCase();
    if (!ok.includes(ext)) { skipped++; continue; }
    if (state.files.some((x) => x.name === f.name && x.size === f.size)) continue;
    // 在原始 File 对象上挂自定义属性，切勿用展开符 {...f} 复制 File
    // （会丢失 File 的内部 blob 数据与原型，导致 FormData/上传失效）
    f.detectedLang = null;
    f.detectStatus = "pending";
    state.files.push(f);
  }
  if (skipped) toast(t("skippedFiles", skipped), "bad");
  renderFiles();
  // 延迟启动语言检测，避免阻塞 UI
  setTimeout(() => detectAllFilesLanguage(), 200);
}

/* ── 文件语言检测 ─────────────────────────── */

const LANG_FLAGS = {
  en: "🇬🇧", zh: "🇨🇳", ja: "🇯🇵", ko: "🇰🇷", ru: "🇷🇺",
};

async function detectFileLanguage(file, index) {
  try {
    state.files[index].detectStatus = 'detecting';
    
    const formData = new FormData();
    formData.append('file', file, file.name);
    
    const response = await fetch('/api/detect-lang', {
      method: 'POST',
      body: formData,
    });
    
    if (response.ok) {
      const result = await response.json();
      state.files[index].detectedLang = result;
      state.files[index].detectStatus = 'done';
    } else {
      console.error('Detect failed:', response.status);
      state.files[index].detectStatus = 'failed';
    }
  } catch (err) {
    console.error('Detect error:', err);
    state.files[index].detectStatus = 'failed';
  } finally {
    renderFiles();
  }
}

async function detectAllFilesLanguage() {
  for (let i = 0; i < state.files.length; i++) {
    const file = state.files[i];
    if (file instanceof File && !file.detectedLang) {
      detectFileLanguage(file, i); // 不await，并行检测
    }
  }
}

function renderFiles() {
  const list = $("fileList");
  list.innerHTML = "";
  state.files.forEach((f, i) => {
    const row = document.createElement("div");
    row.className = "file-row";
    row.dataset.idx = i;
    // 语言徽章 — 仅显示已检测的语言或检测中状态
    let langBadge = "";
    if (f.detectStatus === 'detecting') {
      langBadge = `&nbsp;<span class="detected-lang-badge muted">⟳ 检测中</span>`;
    } else if (f.detectedLang && f.detectedLang.detected) {
      const flag = LANG_FLAGS[f.detectedLang.detected] || "🌐";
      const langName = f.detectedLang.detected_name || f.detectedLang.detected;
      langBadge = `&nbsp;<span class="detected-lang-badge">${flag}${langName}</span>`;
    }
    row.innerHTML = `
      <span class="file-icon">📕</span>
      <div class="file-info">
        <div class="file-name">${escapeHtml(f.name)}${langBadge}</div>
        <div class="file-meta">${fmtSize(f.size)}</div>
      </div>
      <span class="status-chip status-pending">${t("pending")}</span>
      <button class="btn-icon" title="${t("remove")}" data-rm="${i}">✕</button>`;
    list.appendChild(row);
  });
  $("filesCard").hidden = state.files.length === 0;
  $("fileCount").textContent = state.files.length ? `· ${state.files.length} ${t("filesUnit")}` : "";
  updateStartButton();
  $("btnClear").disabled = state.files.length === 0;
}

function updateStartButton() {
  // 只有真实 File 对象（本轮新选择的文件）才允许发起翻译
  const hasNew = state.files.some((f) => f instanceof File);
  $("btnStart").disabled = !hasNew || !!state.polling;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ── 源语言检测 ─────────────────────────── */

const LANG_DISPLAY = {
  en: "🇬🇧 English",
  zh: "🇨🇳 Chinese",
  ja: "🇯🇵 Japanese",
  ko: "🇰🇷 Korean",
  ru: "🇷🇺 Russian",
};

async function detectLang(fileName, fileSize) {
  try {
    const fd = new FormData();
    const file = new Blob([new ArrayBuffer(0)], { type: "application/octet-stream" });
    // We need the actual file blob, not empty
    // Let's try the API with the uploaded pdf path instead
    return null; // will be detected after upload via job_id
  } catch (e) {
    logger.error("[detectLang] error:", e);
    return null;
  }
}

/* ── 翻译任务 ─────────────────────────── */

async function startTranslation() {
  if (!state.files.length) return;
  const btn = $("btnStart");
  btn.disabled = true;
  btn.textContent = t("uploading");

  // 保存当前语言方向
  await api("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lang_in: $("langIn").value, lang_out: $("langOut").value }),
  }).catch(() => {});

  const fd = new FormData();
  state.files.forEach((f) => fd.append("files", f, f.name));

  try {
    const r = await api("/api/translate", { method: "POST", body: fd });
    state.jobId = r.job_id;
    state.logSeq = 0;
    $("logCard").hidden = false;
    $("logPanel").innerHTML = "";
    $("logPanel").classList.remove("collapsed");
    $("logPanel").hidden = false;
    $("btnToggleLog").textContent = t("collapse");
    $("btnCancel").hidden = false;
    $("btnDownloadAll").hidden = true;
    setControlsDuringJob(false);
    startPolling();
  } catch (e) {
    toast(e.message, "bad");
    btn.disabled = false;
    btn.textContent = t("start");
  }
}

function setControlsDuringJob(running) {
  $("btnCancel").hidden = !running;
  $("btnClear").disabled = running;
  $("langIn").disabled = running;
  $("langOut").disabled = running;
  $("fileInput").disabled = running;
  if (!running) {
    $("btnStart").textContent = t("start");
    updateStartButton();
  }
}

function startPolling() {
  stopPolling();
  state.polling = setInterval(pollStatus, 1200);
  pollStatus();
}

function stopPolling() {
  if (state.polling) { clearInterval(state.polling); state.polling = null; }
}

async function pollStatus() {
  if (!state.jobId) return;
  let job;
  try {
    job = await api(`/api/jobs/${state.jobId}?since_log=${state.logSeq}`);
  } catch {
    return;
  }

  // 更新文件行
  job.files.forEach((f, i) => {
    const row = $(`fileList`).children[i];
    if (!row) return;
    const chip = row.querySelector(".status-chip");
    chip.className = "status-chip status-" + f.status;
    chip.textContent = STATUS_LABEL[f.status]?.() || f.status;
    const meta = row.querySelector(".file-meta");
    if (f.status === "done") {
      const outPaths = f.outputs.map(o => o.name).join(", ");
      meta.innerHTML = `${fmtSize(f.size)} · ${fmtTime(f.elapsed)} · <span class="out-path">📄 ${escapeHtml(outPaths)}</span>`;
    } else if (f.status === "failed") {
      row.classList.add("has-error");
      meta.innerHTML = `${fmtSize(f.size)} · <span class="err">${escapeHtml(f.error || "Failed")}</span>`;
    }
    // 下载按钮
    let actions = row.querySelector(".file-actions");
    if (!actions && f.status === "done") {
      actions = document.createElement("div");
      actions.className = "file-actions";
      f.outputs.forEach((o, oi) => {
        const a = document.createElement("a");
        a.className = "dl-link";
        a.href = `/api/jobs/${job.id}/files/${i}/${oi}`;
        a.download = o.name;
        a.textContent = o.name.includes("_dual") ? t("dlDual") : t("dlTranslated");
        actions.appendChild(a);
      });
      const rm = row.querySelector("[data-rm]");
      if (rm) rm.replaceWith(actions);
    }
  });

  // 全局进度
  const p = job.progress;
  const pct = p.total ? Math.round((p.done / p.total) * 100) : 0;
  const fill = $("globalProgress");
  fill.style.width = pct + "%";
  fill.classList.toggle("done-all", job.status === "finished" && pct === 100);
  $("progressText").textContent =
    job.status === "running"
      ? `${t("translating2", p.done, p.total)} · ✅${p.ok} ❌${p.failed}`
      : job.status === "finished"
        ? t("finished", p.ok, p.failed, fmtTime(job.elapsed))
        : STATUS_LABEL[job.status]?.() || job.status;

  // 日志
  appendLogs(job.logs);

  // 结束
  if (["finished", "canceled", "failed"].includes(job.status)) {
    stopPolling();
    setControlsDuringJob(false);
    const anyOk = p.ok > 0;
    $("btnDownloadAll").hidden = !anyOk;
    appendLogs([{ level: "good", msg: t("jobEnded", p.ok, p.failed) }]);
    // 完成通知
    if (p.ok > 0) {
      toast(state.uiLang === "zh"
        ? `翻译完成！✅ ${p.ok} 个文件已保存，可点击下载`
        : `Translation done! ✅ ${p.ok} file(s) saved, click to download`, "ok");
    }
  }
}

function appendLogs(logs) {
  const panel = $("logPanel");
  let atBottom = panel.scrollTop + panel.clientHeight >= panel.scrollHeight - 30;
  logs.forEach((l) => {
    state.logSeq = Math.max(state.logSeq, l.seq);
    const line = document.createElement("div");
    line.className = "log-line " + l.level;
    const tsNum = Number(l.ts);
    const ts = (tsNum > 0 ? new Date(tsNum * 1000) : new Date()).toLocaleTimeString(
      state.uiLang === "zh" ? "zh-CN" : "en-US",
      { hour12: false }
    );
    line.innerHTML = `<span class="log-ts">${ts}</span><span class="log-msg">${escapeHtml(l.msg)}</span>`;
    panel.appendChild(line);
  });
  if (atBottom) panel.scrollTop = panel.scrollHeight;
  while (panel.children.length > 500) panel.removeChild(panel.firstChild);
}

async function cancelJob() {
  if (!state.jobId) return;
  try {
    await api(`/api/jobs/${state.jobId}/cancel`, { method: "POST" });
    toast(t("cancelSent"), "ok");
  } catch (e) {
    toast(e.message, "bad");
  }
}

/* ── 事件绑定 ─────────────────────────── */

function bindEvents() {
  // 拖拽
  const dz = $("dropZone");
  dz.addEventListener("click", () => !$("fileInput").disabled && $("fileInput").click());
  $("btnBrowse").addEventListener("click", (e) => { e.stopPropagation(); $("fileInput").click(); });
  $("fileInput").addEventListener("change", (e) => { addFiles(e.target.files); e.target.value = ""; });
  ["dragenter", "dragover"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("dragover"); })
  );
  dz.addEventListener("drop", (e) => addFiles(e.dataTransfer.files));

  // 文件列表
  $("fileList").addEventListener("click", (e) => {
    const rm = e.target.closest("[data-rm]");
    if (!rm) return;
    if (state.polling) { toast(t("removeBlocked"), "bad"); return; }
    state.files.splice(parseInt(rm.dataset.rm, 10), 1);
    renderFiles();
    if (!state.files.length) $("filesCard").hidden = true;
  });
  $("btnClear").addEventListener("click", () => {
    if (state.polling) return;
    state.files = [];
    state.jobId = null;
    $("btnDownloadAll").hidden = true;
    renderFiles();
    $("filesCard").hidden = true;
  });

  // 翻译
  $("btnStart").addEventListener("click", startTranslation);
  $("btnCancel").addEventListener("click", cancelJob);
  $("btnDownloadAll").addEventListener("click", () => {
    if (state.jobId) window.location.href = `/api/jobs/${state.jobId}/download-all`;
  });

  // 语言
  $("btnSwap").addEventListener("click", () => {
    const a = $("langIn").value;
    $("langIn").value = $("langOut").value;
    $("langOut").value = a;
  });

  // 设置
  $("btnSettings").addEventListener("click", openSettings);
  $("engineBadge").addEventListener("click", openSettings);
  $("btnCloseSettings").addEventListener("click", closeSettings);
  $("settingsOverlay").addEventListener("click", closeSettings);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSettings(); });
  $("btnSaveSettings").addEventListener("click", saveSettings);
  $("btnResetConfig").addEventListener("click", async () => {
    if (!confirm(t("resetConfirm"))) return;
    await api("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ base_url: "", api_key: "", model: "deepseek-chat", engine: "google", thread: 4, dual: false, output_dir: "", ui_lang: "en" }),
    });
    await loadConfig();
    toast(t("resetDone"), "ok");
  });
  $("btnTestConn").addEventListener("click", testConnection);
  $("btnArgosInstall").addEventListener("click", installArgos);
  $("cfgThread").addEventListener("input", (e) => ($("threadVal").textContent = e.target.value));

  // 引擎卡片选择
  document.querySelectorAll(".engine-card").forEach((c) =>
    c.addEventListener("click", () => {
      setEngineUI(c.dataset.engine);
      updateEngineBadge();
      if (c.dataset.engine === "argos") refreshArgos();
    })
  );

  // 界面语言切换
  $("uiLang").addEventListener("change", (e) => {
    try {
      state.uiLang = e.target.value;
      try { localStorage.setItem("linguapdf_lang", state.uiLang); } catch {}
      applyI18n();
      // 更新动态 placeholder（applyI18n 不处理 #cfgApiKey 的动态 placeholder）
      $("cfgApiKey").placeholder = state.cfg.has_api_key ? t("apiKeySaved") : "sk-...";
      // 清空已有日志面板（旧日志是旧语言生成的，保留会混乱）
      const panel = $("logPanel");
      if (panel) panel.innerHTML = "";
      toast(state.uiLang === "zh" ? "已切换至中文" : "Switched to English", "ok");
      (async () => {
        try {
          const resp = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ui_lang: state.uiLang }),
          });
          if (resp.ok) state.cfg = await resp.json();
        } catch {}
      })();
    } catch (err) {
      toast("Error: " + err.message, "bad");
      console.error("[i18n switch error]", err);
    }
  });

  // 日志
  $("btnToggleLog").addEventListener("click", () => {
    const p = $("logPanel");
    p.classList.toggle("collapsed");
    p.hidden = p.classList.contains("collapsed");
    $("btnToggleLog").textContent = p.hidden ? t("expand") : t("collapse");
  });
}

/* ── 恢复最近任务（页面刷新后不丢失进行中/刚完成的任务）──────── */

async function resumeLatestJob() {
  try {
    const jobs = await api("/api/jobs");
    // 只恢复正在运行的任务，已完成的不再显示
    const latest = jobs.find((j) =>
      ["queued", "running"].includes(j.status) &&
      Date.now() / 1000 - j.created_at < 7200
    );
    if (!latest) return;
    const job = await api(`/api/jobs/${latest.id}`);
    state.files = job.files.map((f) => ({ name: f.name, size: f.size }));
    state.jobId = job.id;
    state.logSeq = 0;
    renderFiles();
    $("filesCard").hidden = false;
    $("logCard").hidden = false;
    setControlsDuringJob(true);
    startPolling();
  } catch {
    /* 静默失败 */
  }
}

/* ── 启动 ─────────────────────────── */

bindEvents();
loadConfig()
  .catch((e) => toast(t("configLoadFailed") + e.message, "bad"))
  .finally(resumeLatestJob);

/* ── 浏览器关闭即关服务 ─────────────────────────── */
// 原理: 页面可见时定期发心跳，页面关闭/隐藏超过阈值则触发 shutdown
// 刷新页面不会误关（刷新会立即重新加载、心跳恢复）

let heartbeatTimer = null;
let lastHeartbeat = Date.now();
let shutdownTriggered = false;

function startHeartbeat() {
  if (heartbeatTimer) clearInterval(heartbeatTimer);
  heartbeatTimer = setInterval(() => {
    fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
    lastHeartbeat = Date.now();
  }, 2000);
}

function triggerShutdown() {
  if (shutdownTriggered) return;
  shutdownTriggered = true;
  // sendBeacon 在页面卸载时仍能可靠发送
  navigator.sendBeacon("/api/shutdown");
}

// 页面即将关闭 → 通知后端关闭
window.addEventListener("beforeunload", () => {
  // 只有真正关闭才触发，刷新时 beforeunload 也会触发但 sendBeacon 会被后端刷新覆盖
  triggerShutdown();
});

// 页面隐藏（切到其他标签/最小化浏览器）→ 不立即关，但停止心跳
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    // 重新可见 → 恢复心跳，取消 shutdown 标记
    shutdownTriggered = false;
    startHeartbeat();
  }
});

startHeartbeat();
