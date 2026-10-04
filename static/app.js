"use strict";
const $ = id => document.getElementById(id);
const state = {cfg: {}, files: [], job: null, jobId: null, busy: false, picking: false, timer: null,
  polling: false, logSeq: 0, uiLang: "zh", drawerEngine: "google", selection: 0};
const I18N = {
  zh: {
    brandSub:"文档翻译工作台",localService:"本机运行",settings:"设置",heroTitle:'让语言，<span>不再是阅读的边界。</span>',heroDesc:"批量翻译论文与文档。保留排版，也保留你的阅读节奏。",
    addDocuments:"添加文档",dropTitle:"把文档拖到这里",dropDesc:"或点击选择本地文件 · 每个文件不超过 200 MB",pickLocal:"选择本地文件",pathImport:"按原路径导入 ↗",pathNote:"点击选择会记住原目录；浏览器拖放不会提供真实路径。",pathLabel:"粘贴原文件的完整路径，每行一个",pathTip:"可直接从文件资源管理器“复制文件地址”。",import:"导入文件",
    queue:"文档队列",clear:"清空列表",emptyTitle:"还没有待翻译的文档",emptyDesc:"添加文件后，选择语言并开始翻译。",resultsReady:"译文已就绪",resultsHint:"按照显示的保存位置保存，已有文件不会覆盖。",downloadZip:"下载文件 / ZIP",saveAll:"下载全部到原目录",saveFallback:"保存全部译文",activity:"运行记录",collapse:"收起",expand:"展开",
    translateSettings:"翻译选项",sourceLang:"源语言",targetLang:"目标语言",swap:"交换语言",engine:"翻译引擎",engineChange:"在设置中更换翻译引擎",skipRefs:"参考文献保留原文",skipRefsHint:"自动保护文献区域，正文照常翻译",dual:"双语对照 PDF",dualHint:"额外生成原文与译文交替页",start:"开始翻译",cancel:"停止翻译",retry:"重试失败 / 已停止的文件",startNote:"保留公式、图表与双栏排版",
    tipTitle:"为专注阅读而设计",tipBody:"论文推荐 API 引擎；日常文档可使用 Google 免费翻译。Word 与 PowerPoint 需要 LibreOffice。",tipFooter:"原文件始终保留",footer:"跨越语言，保留思考。",privacy:"密钥仅存本机 · 联网引擎会发送待译正文",settingsTitle:"让翻译适合你",close:"关闭设置",
    google:"Google 免费",openai:"API 翻译",argos:"本地离线",googleDesc:"无需密钥 · 需要联网",apiDesc:"学术阅读推荐 · OpenAI 兼容接口",argosDesc:"Argos 本地模型 · 无需联网",keyHint:"仅存本机，读取时显示掩码。",model:"模型名称",installModel:"下载当前语言对模型",testConn:"测试当前引擎",threads:"API 请求并发总额",threadsHint:"通常 4–8 即可；过高可能触发服务限流。",
    outputDir:"统一保存目录（可选）",outputHint:"留空时按各原目录保存；无原路径的上传保存到项目 outputs/LingoPDF。指定目录也会创建 LingoPDF 子文件夹。",libreoffice:"LibreOffice 程序路径（可选）",libreofficeHint:"留空自动检测，用于 Word / PowerPoint 转 PDF。",settingsNote:"翻译结果与原文件独立保存。参考文献保护默认开启，可在主界面调整。",reset:"恢复常用选项",saveSettings:"保存设置",
    pending:"待翻译",converting:"转换中",translating:"翻译中",done:"已完成",failed:"失败",canceled:"已停止",queued:"排队中",remove:"移除文件",mono:"下载译文 ↗",bilingual:"双语对照 ↗",unknownPath:"浏览器上传 · 原路径不可用",uploading:"正在准备文件…",saved:"设置已保存",testing:"正在测试…",stopping:"正在停止…",picking:"等待选择…",saving:"正在保存…",savedCount:"已保存 {n} 个 PDF",fallback:"部分浏览器上传文件已保存到项目 outputs/LingoPDF。",noPaths:"请先输入原文件路径",sameLang:"源语言与目标语言需要不同",invalidFiles:"部分文件无效或超过 200MB，已跳过",newBatch:"已建立新的文档队列",ready:"就绪，等待开始",
    finished:"完成 {ok} · 失败 {failed} · 用时 {elapsed}",running:"已处理 {done} / {total} 个文件",cancelSummary:"任务已停止 · 完成 {ok} · 失败 {failed}",recovering:"连接暂时中断，正在恢复…",knownDest:"保存位置：各原文件所在目录 / LingoPDF",unknownDest:"浏览器上传未提供原路径，保存到项目 outputs / LingoPDF。可用本地选择保留原路径。",customDest:"统一保存至：",refsKept:"文献保护 {n} 页",noRetry:"没有可重试的文件，请重新导入。",argosMissing:"未安装 Argos；请安装 requirements.txt 中的可选依赖。",modelReady:"当前语言对本地模型已就绪。",modelMissing:"当前语言对尚未安装模型。",loadFailed:"加载失败：",savedError:"{n} 个文件未保存，请检查目录权限。",resetDone:"常用选项已恢复，API 凭据保留",noNew:"请添加新文件后开始翻译"
  },
  en: {
    brandSub:"DOCUMENT WORKSPACE",localService:"Running locally",settings:"Settings",heroTitle:'Make language <span>an open door.</span>',heroDesc:"Translate papers and documents in batches. Keep the layout. Stay in your reading flow.",
    addDocuments:"Add documents",dropTitle:"Drop your documents here",dropDesc:"or click to choose local files · Up to 200 MB per file",pickLocal:"Choose local files",pathImport:"Import by original path ↗",pathNote:"Click to select and keep the source folder. Browser drops do not expose the original path.",pathLabel:"Paste absolute source file paths, one per line",pathTip:"Use “Copy as path” in File Explorer.",import:"Import files",
    queue:"Document queue",clear:"Clear queue",emptyTitle:"A fresh space for your documents",emptyDesc:"Add files, choose your languages, and start translating.",resultsReady:"Your translations are ready",resultsHint:"Save to the displayed destination. Existing files stay intact.",downloadZip:"Download files / ZIP",saveAll:"Save all to source folders",saveFallback:"Save all translations",activity:"Activity",collapse:"Collapse",expand:"Expand",
    translateSettings:"Translation options",sourceLang:"From",targetLang:"To",swap:"Swap languages",engine:"Translation engine",engineChange:"Change translation engine in settings",skipRefs:"Keep references original",skipRefsHint:"Protect bibliography, translate the body",dual:"Bilingual PDF",dualHint:"Also create alternating original / translated pages",start:"Start translation",cancel:"Stop translation",retry:"Retry failed / stopped files",startNote:"Formulas, figures and columns preserved",
    tipTitle:"Made for focused reading",tipBody:"Use an API engine for academic papers, or Google Free for everyday documents. Word and PowerPoint require LibreOffice.",tipFooter:"Your originals stay intact",footer:"Every language. Every idea.",privacy:"Keys stay local · Online engines receive body text",settingsTitle:"Make translation yours",close:"Close settings",
    google:"Google Free",openai:"API Translation",argos:"Local Offline",googleDesc:"No key needed · Internet required",apiDesc:"For academic reading · OpenAI-compatible",argosDesc:"Argos local model · Works offline",keyHint:"Stored locally and masked when read.",model:"Model name",installModel:"Download this language pair",testConn:"Test selected engine",threads:"Total concurrent API requests",threadsHint:"Usually 4–8 is enough. Higher values may trigger rate limits.",
    outputDir:"Shared output folder (optional)",outputHint:"Leave blank for each source folder. Browser uploads use outputs/LingoPDF in the project. A custom folder also gets a LingoPDF subfolder.",libreoffice:"LibreOffice executable (optional)",libreofficeHint:"Auto-detected when blank. Required for Word / PowerPoint.",settingsNote:"Results are saved separately from your originals. Reference protection is on by default and can be adjusted in the workspace.",reset:"Reset common options",saveSettings:"Save settings",
    pending:"Ready",converting:"Converting",translating:"Translating",done:"Complete",failed:"Failed",canceled:"Stopped",queued:"Queued",remove:"Remove file",mono:"Translation ↗",bilingual:"Bilingual ↗",unknownPath:"Browser upload · source path unavailable",uploading:"Preparing documents…",saved:"Settings saved",testing:"Testing…",stopping:"Stopping…",picking:"Waiting for selection…",saving:"Saving…",savedCount:"Saved {n} PDF(s)",fallback:"Some browser uploads were saved to outputs/LingoPDF in the project.",noPaths:"Enter source file paths first",sameLang:"Choose different source and target languages",invalidFiles:"Unsupported, empty or oversized files were skipped",newBatch:"Started a fresh document queue",ready:"Ready to translate",
    finished:"{ok} complete · {failed} failed · {elapsed}",running:"Processed {done} / {total} documents",cancelSummary:"Stopped · {ok} complete · {failed} failed",recovering:"Connection interrupted. Reconnecting…",knownDest:"Destination: each source folder / LingoPDF",unknownDest:"Browser uploads use project outputs / LingoPDF. Choose local files to preserve the source folder.",customDest:"Save all into: ",refsKept:"References protected on {n} page(s)",noRetry:"No retryable sources. Import the files again.",argosMissing:"Argos is not installed. Install the optional requirements dependency.",modelReady:"The local model for this language pair is ready.",modelMissing:"The current language pair needs a local model.",loadFailed:"Could not load: ",savedError:"{n} file(s) could not be saved. Check folder permissions.",resetDone:"Common options restored; API credentials kept",noNew:"Add new files before starting"
  }
};
const t = (key, values = {}) => (I18N[state.uiLang][key] || key).replace(/\{(\w+)\}/g, (_, k) => values[k] ?? `{${k}}`);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const sizeText = n => n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`;
const timeText = n => n < 60 ? `${n.toFixed(1)} ${state.uiLang === "zh" ? "秒" : "s"}` : `${Math.floor(Math.round(n)/60)} ${state.uiLang === "zh" ? "分" : "min"} ${Math.round(n)%60} ${state.uiLang === "zh" ? "秒" : "s"}`;

function toast(message, type = "") {
  const el = $("toast"); el.textContent = message; el.className = `toast ${type}`; el.hidden = false;
  clearTimeout(el.timer); el.timer = setTimeout(() => el.hidden = true, 5500);
}
async function api(path, options = {}) {
  const response = await fetch(path, options);
  let data; try { data = await response.json(); } catch { throw Error(`HTTP ${response.status}`); }
  if (!response.ok) throw Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data));
  return data;
}
const post = (path, body) => api(path, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});

function applyI18n() {
  document.documentElement.lang = state.uiLang;
  document.title = state.uiLang === "zh" ? "LingoPDF · 文档翻译工作台" : "LingoPDF · Document workspace";
  document.querySelectorAll("[data-i18n]").forEach(el => el.innerHTML = t(el.dataset.i18n));
  document.querySelectorAll("[data-i18n-title]").forEach(el => el.title = t(el.dataset.i18nTitle));
  $("btnSwap").setAttribute("aria-label", t("swap")); $("btnCloseSettings").setAttribute("aria-label", t("close"));
  $("dropZone").setAttribute("aria-label", t("dropTitle"));
  updateEngine(); renderFiles(); $("btnToggleLog").textContent = t($("logPanel").hidden ? "expand" : "collapse");
}
function updateDestination() {
  const known = state.files.length && state.files.every(f => f.source_path);
  const outputDir = state.job ? state.job.output_dir : state.cfg.output_dir;
  $("destinationHint").textContent = outputDir ? t("customDest") + outputDir + " / LingoPDF" : t(known ? "knownDest" : "unknownDest");
  if (!$("btnDownloadAll").disabled) $("btnDownloadAll").textContent = t(known && !outputDir ? 'saveAll' : 'saveFallback');
}
function updateEngine() {
  const engine = state.cfg.engine || "google";
  $("engineName").textContent = t(engine);
  $("engineHint").textContent = engine === "openai" ? (state.cfg.model || "") : t(engine === "google" ? "googleDesc" : "argosDesc");
  updateDestination();
}
function selectEngine(engine) {
  state.drawerEngine = engine;
  document.querySelectorAll(".engine-card").forEach(el => {
    el.classList.toggle("active", el.dataset.engine === engine);
    el.setAttribute("aria-pressed", String(el.dataset.engine === engine));
  });
  $("openaiFields").hidden = engine !== "openai"; $("argosFields").hidden = engine !== "argos"; $("testConnMsg").hidden = true;
}
function fillSettings() {
  const cfg = state.cfg;
  $("cfgBaseUrl").value = cfg.base_url || ""; $("cfgApiKey").value = cfg.api_key || ""; $("cfgModel").value = cfg.model || "deepseek-chat";
  $("cfgThread").value = cfg.thread || 4; $("threadVal").textContent = cfg.thread || 4;
  $("cfgOutputDir").value = cfg.output_dir || ""; $("cfgLibreOffice").value = cfg.libreoffice_path || "";
  selectEngine(cfg.engine || "google");
}
async function loadConfig() {
  state.cfg = await api("/api/config"); state.uiLang = state.cfg.ui_lang || "zh"; $("uiLang").value = state.uiLang;
  $("langIn").value = state.cfg.lang_in || "en"; $("langOut").value = state.cfg.lang_out || "zh";
  $("skipReferences").checked = state.cfg.skip_references !== false; $("dualOutput").checked = !!state.cfg.dual;
  fillSettings(); applyI18n();
}
let priorFocus;
function openSettings() {
  priorFocus = document.activeElement; fillSettings(); $("settingsOverlay").hidden = false; $("settingsDrawer").hidden = false;
  document.body.style.overflow = "hidden"; $("btnCloseSettings").focus();
  if (state.drawerEngine === "argos") refreshArgos();
}
function closeSettings() {
  $("settingsOverlay").hidden = true; $("settingsDrawer").hidden = true; document.body.style.overflow = ""; priorFocus?.focus();
}
async function saveSettings() {
  const button = $("btnSaveSettings"); button.disabled = true;
  try {
    const payload = {engine:state.drawerEngine, base_url:$("cfgBaseUrl").value.trim(), model:$("cfgModel").value.trim(),
      thread:Number($("cfgThread").value), output_dir:$("cfgOutputDir").value.trim(), libreoffice_path:$("cfgLibreOffice").value.trim(),
      lang_in:$("langIn").value, lang_out:$("langOut").value, dual:$("dualOutput").checked, skip_references:$("skipReferences").checked, ui_lang:state.uiLang};
    const key = $("cfgApiKey").value; if (!key.includes("*")) payload.api_key = key.trim();
    state.cfg = await post("/api/config", payload); updateEngine(); closeSettings(); toast(t("saved"), "ok");
  } catch (error) { toast(error.message, "bad"); } finally { button.disabled = false; }
}
async function refreshArgos() {
  try {
    const info = await api("/api/engines"); const pair = `${$("langIn").value}->${$("langOut").value}`;
    const installed = info.argos.library_installed; const ready = info.argos.installed?.includes(pair);
    $("argosStatus").textContent = t(!installed ? "argosMissing" : ready ? "modelReady" : "modelMissing");
    $("btnArgosInstall").hidden = !installed || ready;
  } catch (error) { $("argosStatus").textContent = error.message; }
}
async function testConnection() {
  const btn = $("btnTestConn"); btn.disabled = true; btn.textContent = t("testing");
  $("testConnMsg").hidden = false; $("testConnMsg").textContent = t("testing");
  try {
    const data = await post("/api/test-connection", {engine:state.drawerEngine, base_url:$("cfgBaseUrl").value.trim(),
      api_key:$("cfgApiKey").value.trim(), model:$("cfgModel").value.trim(), lang_in:$("langIn").value, lang_out:$("langOut").value});
    $("testConnMsg").className = `test-msg ${data.ok ? "ok" : "bad"}`; $("testConnMsg").textContent = `${data.ok ? "✓" : "×"} ${data.message}`;
  } catch (error) { $("testConnMsg").className = "test-msg bad"; $("testConnMsg").textContent = error.message; }
  finally { btn.disabled = false; btn.textContent = t("testConn"); }
}

function stopPolling() { clearTimeout(state.timer); state.timer = null; }
function clearJob() {
  stopPolling(); state.job = null; state.jobId = null; state.logSeq = 0; state.selection++;
  $("logPanel").replaceChildren(); $("logCard").hidden = true; $("savedPanel").hidden = true;
  try { sessionStorage.removeItem("lingopdf_job"); } catch {}
}
function addFiles(files) {
  if (state.busy) return;
  const valid = []; let rejected = false;
  for (const file of files) {
    if (!/\.(pdf|docx|pptx|doc|ppt)$/i.test(file.name) || file.size <= 0 || file.size > 200 * 1048576) { rejected = true; continue; }
    const identity = file.source_path || `${file.name}|${file.size}|${file.lastModified || 0}`;
    if ((!state.job && state.files.some(f => f.identity === identity)) || valid.some(f => f.identity === identity)) continue;
    valid.push(file instanceof File ? {name:file.name, size:file.size, blob:file, identity} : {...file, identity, source_id:file.id});
  }
  if (valid.length) {
    if (state.job) { clearJob(); state.files = []; toast(t("newBatch")); }
    state.files.push(...valid); renderFiles();
  }
  if (rejected) toast(t("invalidFiles"), "bad");
}
async function importPaths() {
  if (state.busy) return;
  const paths = $("sourcePaths").value.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  if (!paths.length) { toast(t("noPaths"), "bad"); return; }
  const btn = $("btnImportPaths"); btn.disabled = true; const generation = state.selection;
  try {
    const data = await post("/api/local-files", {paths});
    if (generation === state.selection) { addFiles(data.files); $("pathPanel").hidden = true; $("sourcePaths").value = ""; }
  } catch (error) { toast(error.message, "bad"); } finally { btn.disabled = false; }
}
async function pickLocal() {
  if (state.busy) return;
  if (state.picking) {
    try { await post('/api/local-files/pick-cancel', {}); } catch (error) { toast(error.message, 'bad'); }
    return;
  }
  state.picking = true;
  updateControls();
  const generation = state.selection;
  try { const data = await post("/api/local-files/pick", {}); if (generation === state.selection) addFiles(data.files); }
  catch (error) { $("pathPanel").hidden = false; $("sourcePaths").focus(); toast(error.message, "bad"); }
  finally { state.picking = false; updateControls(); }
}
function renderFiles() {
  const container = $("fileList"); container.replaceChildren();
  state.files.forEach((source, i) => {
    const result = state.job?.files[i]; const status = result?.status || "pending"; const f = result || source;
    const row = document.createElement("div"); row.className = "file-row";
    const refText = f.reference_pages ? ` · ${t("refsKept", {n:f.reference_pages})}` : "";
    const meta = status === "failed" ? `<span class="err">${esc(f.error || t("failed"))}</span>` : `${sizeText(f.size)}${f.elapsed ? ` · ${timeText(f.elapsed)}` : ""}${refText}`;
    const path = f.source_path || source.source_path;
    row.innerHTML = `<span class="file-icon">${esc(f.name.split('.').pop().toUpperCase())}</span>
      <div class="file-info"><div class="file-name" title="${esc(f.name)}">${esc(f.name)}</div><div class="file-meta">${meta}</div>
      <span class="source-path ${path ? "known" : ""}" title="${esc(path || t("unknownPath"))}">${path ? esc(path) : t("unknownPath")}</span>
      ${status === "translating" ? `<div class="file-progress"><div class="file-progress-fill" style="width:${Math.max(3,Math.min(99,(f.progress||0)*100))}%"></div></div>` : ""}</div>
      <span class="status-chip status-${status}">${t(status)}${status === "translating" ? ` ${Math.min(99,Math.round((f.progress||0)*100))}%` : ""}</span>`;
    if (f.outputs?.length) {
      const actions = document.createElement("div"); actions.className = "file-actions";
      f.outputs.forEach((output, oi) => {
        const link = document.createElement("a"); link.className = "dl-link"; link.href = `/api/jobs/${state.jobId}/files/${i}/${oi}`;
        link.download = output.name; link.textContent = t(output.name.includes("_dual") ? "bilingual" : "mono"); actions.append(link);
      }); row.append(actions);
    } else if (!state.job) {
      const remove = document.createElement("button"); remove.className = "btn-icon"; remove.textContent = "×";
      remove.title = t("remove"); remove.setAttribute("aria-label", `${t("remove")} ${f.name}`); remove.disabled = state.busy;
      remove.addEventListener("click", () => { if (state.busy) return; state.files.splice(i,1); state.selection++; renderFiles(); }); row.append(remove);
    }
    container.append(row);
  });
  $("fileCount").textContent = state.files.length; $("emptyState").hidden = state.files.length > 0;
  $("progressPanel").hidden = !state.job; $("resultsBar").hidden = !state.job || state.busy || !state.job.files.some(f => f.outputs?.length);
  $("btnRetry").hidden = state.busy || !state.job?.files.some(f => ["failed","canceled"].includes(f.status));
  if (state.job) {
    const p = state.job.progress; const pct = Math.min(state.busy ? 99 : 100, Math.round((p.fraction ?? p.done / Math.max(p.total,1)) * 100));
    $("globalProgress").style.width = pct + "%"; $("progressPercent").textContent = pct + "%";
    $("progressText").textContent = t(state.busy ? "running" : state.job.status === "canceled" ? "cancelSummary" : "finished", {...p, elapsed:timeText(state.job.elapsed || 0)});
  }
  updateDestination(); updateControls();
}
function updateControls() {
  const ready = state.files.length > 0 && !state.job && state.files.every(f => f.blob || f.source_id);
  $("btnStart").disabled = state.busy || state.picking || !ready; $("btnStart").innerHTML = `<span>${t(state.busy ? "uploading" : "start")}</span><span>→</span>`;
  $("btnStart").hidden = state.busy; $("btnCancel").hidden = !state.busy || !state.jobId;
  $("btnClear").disabled = state.busy || state.picking || !state.files.length;
  ["langIn","langOut","btnSwap","fileInput","btnPathImport","btnImportPaths","btnSettings","engineBadge","skipReferences","dualOutput"].forEach(id => $(id).disabled = state.busy || state.picking);
  $("dropZone").setAttribute("aria-disabled", String(state.busy));
  $("dropZone").setAttribute("aria-busy", String(state.picking));
  $("dropZone").querySelector('h3').textContent = t(state.picking ? 'picking' : 'dropTitle');
  $("dropZone").querySelector('p').textContent = state.picking
    ? (state.uiLang === 'zh' ? '再次点击这里取消选择' : 'Click here again to cancel selection') : t('dropDesc');
}
async function startTranslation() {
  if (state.busy) return;
  if (!state.files.length || state.job) { toast(t("noNew"), "bad"); return; }
  if ($("langIn").value === $("langOut").value) { toast(t("sameLang"), "bad"); return; }
  state.busy = true; updateControls(); $("btnStart").hidden = false; $("btnStart").textContent = t("uploading");
  const data = new FormData(); const entries = []; let uploads = 0;
  for (const file of state.files) {
    if (file.source_id) entries.push({id:file.source_id});
    else { data.append("files", file.blob, file.name); entries.push({upload:uploads++}); }
  }
  data.append("entries", JSON.stringify(entries)); data.append("lang_in", $("langIn").value); data.append("lang_out", $("langOut").value);
  data.append("dual", String($("dualOutput").checked)); data.append("skip_references", String($("skipReferences").checked));
  try {
    const result = await api("/api/translate", {method:"POST", body:data}); state.jobId = result.job_id; state.logSeq = 0;
    try { sessionStorage.setItem("lingopdf_job", state.jobId); } catch {}
    $("logCard").hidden = false; $("logPanel").replaceChildren(); $("logPanel").hidden = false;
    $("btnToggleLog").textContent = t("collapse"); $("savedPanel").hidden = true; updateControls(); pollStatus();
  } catch (error) { state.busy = false; toast(error.message, "bad"); updateControls(); }
}
function appendLogs(logs) {
  const panel = $("logPanel"); const atBottom = panel.scrollTop + panel.clientHeight >= panel.scrollHeight - 30;
  for (const log of logs) {
    if (Number.isFinite(log.seq)) state.logSeq = Math.max(state.logSeq, log.seq);
    const row = document.createElement("div"); row.className = `log-line ${log.level || "info"}`;
    row.innerHTML = `<span class="log-ts">${new Date((log.ts || Date.now()/1000)*1000).toLocaleTimeString(state.uiLang === "zh" ? "zh-CN" : "en-GB",{hour12:false})}</span><span class="log-msg">${esc(log.msg)}</span>`;
    panel.append(row);
  }
  while (panel.children.length > 500) panel.firstChild.remove(); if (atBottom) panel.scrollTop = panel.scrollHeight;
}
async function pollStatus() {
  if (!state.jobId || state.polling) return; state.polling = true; const id = state.jobId;
  try {
    const job = await api(`/api/jobs/${id}?since_log=${state.logSeq}`); if (id !== state.jobId) return;
    state.job = job; state.busy = ["queued","running","canceling"].includes(job.status); appendLogs(job.logs || []); renderFiles();
    if (!state.busy) { stopPolling(); $("btnCancel").disabled = false; $("btnCancel").textContent = t("cancel"); if (job.progress.ok) toast(t("resultsReady"), "ok"); }
  } catch (error) {
    if (id === state.jobId) {
      $("progressText").textContent = t("recovering");
      if (error.message.includes("不存在") || error.message.includes("404")) { state.busy = false; clearJob(); renderFiles(); toast(error.message, "bad"); }
    }
  } finally { state.polling = false; if (state.busy && state.jobId === id) state.timer = setTimeout(pollStatus,1200); }
}
async function cancelJob() {
  if (!state.jobId) return; const btn = $("btnCancel"); btn.disabled = true; btn.textContent = t("stopping");
  try { await post(`/api/jobs/${state.jobId}/cancel`,{}); }
  catch (error) { toast(error.message,"bad"); btn.disabled = false; btn.textContent = t("cancel"); }
}
function retryFiles() {
  const retry = state.files.filter((_, i) => ["failed","canceled"].includes(state.job?.files[i].status));
  if (!retry.length || retry.some(f => !f.blob && !f.source_id)) { toast(t("noRetry"),"bad"); return; }
  clearJob(); state.files = retry; renderFiles(); startTranslation();
}
async function saveAll() {
  const jobId = state.jobId;
  const btn = $("btnDownloadAll"); btn.disabled = true; btn.textContent = t("saving");
  try {
    const result = await post(`/api/jobs/${jobId}/save-all`,{});
    if (jobId !== state.jobId) return;
    const panel = $("savedPanel"); panel.hidden = false; panel.replaceChildren();
    const title = document.createElement("strong"); title.textContent = t("savedCount",{n:result.saved.length}); panel.append(title);
    for (const folder of result.folders) { const line = document.createElement("p"); line.textContent = folder; panel.append(line); }
    if (result.saved.some(f => f.fallback)) { const line = document.createElement("p"); line.textContent = t("fallback"); panel.append(line); }
    for (const error of result.errors) { const line = document.createElement("p"); line.className = "err"; line.textContent = `${error.name}: ${error.error}`; panel.append(line); }
    toast(result.errors.length ? t("savedError",{n:result.errors.length}) : t("savedCount",{n:result.saved.length}), result.errors.length ? "bad" : "ok");
  } catch (error) { toast(error.message,"bad"); } finally { btn.disabled = false; updateDestination(); }
}
async function resumeJob() {
  try {
    const jobs = await api("/api/jobs"); let remembered; try { remembered = sessionStorage.getItem("lingopdf_job"); } catch {}
    const latest = jobs.find(j => j.id === remembered) || jobs.find(j => ["queued","running","canceling"].includes(j.status)); if (!latest) return;
    const job = await api(`/api/jobs/${latest.id}`); state.jobId = job.id;
    state.files = job.files.map(f => ({...f, identity:f.source_path || f.name, source_id:f.source_id})); state.job = job;
    $("langIn").value = job.lang_in; $("langOut").value = job.lang_out;
    $("dualOutput").checked = !!job.dual; $("skipReferences").checked = job.skip_references !== false;
    state.busy = ["queued","running","canceling"].includes(job.status); $("logCard").hidden = false; renderFiles(); pollStatus();
  } catch (error) { toast(t("loadFailed") + error.message,"bad"); }
}

$("dropZone").addEventListener("click", pickLocal);
$("dropZone").addEventListener("keydown", event => { if (["Enter"," "].includes(event.key)) { event.preventDefault(); if (!event.repeat && !state.busy) pickLocal(); } });
$("fileInput").addEventListener("change", event => { addFiles(event.target.files); event.target.value = ""; });
["dragenter","dragover"].forEach(name => $("dropZone").addEventListener(name, event => { event.preventDefault(); if (!state.busy) $("dropZone").classList.add("dragover"); }));
["dragleave","drop"].forEach(name => $("dropZone").addEventListener(name, event => { event.preventDefault(); $("dropZone").classList.remove("dragover"); }));
$("dropZone").addEventListener("drop", event => addFiles(event.dataTransfer.files));
$("btnPathImport").addEventListener("click", () => { $("pathPanel").hidden = !$("pathPanel").hidden; if (!$("pathPanel").hidden) $("sourcePaths").focus(); });
$("btnImportPaths").addEventListener("click", importPaths);
$("btnClear").addEventListener("click", () => { if (state.busy) return; clearJob(); state.files = []; renderFiles(); });
$("btnStart").addEventListener("click", startTranslation); $("btnCancel").addEventListener("click", cancelJob);
$("btnRetry").addEventListener("click", retryFiles); $("btnDownloadAll").addEventListener("click", saveAll);
$("btnZip").addEventListener("click", () => { if (state.jobId) window.location.href = `/api/jobs/${state.jobId}/download-all`; });
$("btnSwap").addEventListener("click", () => { const source = $("langIn").value; $("langIn").value = $("langOut").value; $("langOut").value = source; });
$("btnSettings").addEventListener("click", openSettings); $("engineBadge").addEventListener("click", openSettings);
$("btnCloseSettings").addEventListener("click", closeSettings); $("settingsOverlay").addEventListener("click", closeSettings);
$("btnSaveSettings").addEventListener("click", saveSettings); $("btnTestConn").addEventListener("click", testConnection);
$("cfgThread").addEventListener("input", event => $("threadVal").textContent = event.target.value);
document.querySelectorAll(".engine-card").forEach(card => card.addEventListener("click", () => { selectEngine(card.dataset.engine); if (state.drawerEngine === "argos") refreshArgos(); }));
$("btnResetConfig").addEventListener("click", async () => {
  try { state.cfg = await post("/api/config",{engine:"google",thread:4,dual:false,skip_references:true,output_dir:"",libreoffice_path:""});
    $("skipReferences").checked = true; $("dualOutput").checked = false; fillSettings(); updateEngine(); toast(t("resetDone"),"ok"); }
  catch (error) { toast(error.message,"bad"); }
});
$("btnArgosInstall").addEventListener("click", async () => {
  const btn = $("btnArgosInstall"); btn.disabled = true;
  try { const result = await api(`/api/engines/argos/install?lang_in=${$("langIn").value}&lang_out=${$("langOut").value}`,{method:"POST"}); toast(result.message,result.ok?"ok":"bad"); await refreshArgos(); }
  catch (error) { toast(error.message,"bad"); } finally { btn.disabled = false; }
});
$("uiLang").addEventListener("change", async () => { state.uiLang = $("uiLang").value; applyI18n(); try { state.cfg = await post("/api/config",{ui_lang:state.uiLang}); } catch (error) { toast(error.message,"bad"); } });
$("btnToggleLog").addEventListener("click", () => { $("logPanel").hidden = !$("logPanel").hidden; $("btnToggleLog").textContent = t($("logPanel").hidden ? "expand" : "collapse"); });
document.addEventListener("keydown", event => {
  if ($("settingsDrawer").hidden) return;
  if (event.key === "Escape") { event.preventDefault(); closeSettings(); }
  if (event.key === "Tab") {
    const focusable = [...$("settingsDrawer").querySelectorAll('button,input,select,textarea')].filter(el => !el.disabled && el.getClientRects().length);
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});
loadConfig().then(resumeJob).catch(error => toast(t("loadFailed") + error.message,"bad"));
// Switching tabs never stops work. Actual page close requests a deferred shutdown.
const heartbeat = () => fetch('/api/heartbeat',{method:'POST'}).catch(() => {}); heartbeat(); setInterval(heartbeat,2000);
window.addEventListener('pagehide', event => { if (!event.persisted && !state.busy && !state.picking) navigator.sendBeacon('/api/shutdown'); });
