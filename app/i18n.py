"""后端日志国际化。

根据 ui_lang 配置返回中/英文日志消息。
前端日志面板直接显示这些消息，所以后端也要翻译。
"""

from __future__ import annotations

_MSGS = {
    "en": {
        "job_start": "Job started: {n} file(s)",
        "job_end": "Job ended: ✅ {ok} / ❌ {fail}",
        "no_libreoffice": "⚠ LibreOffice not detected, non-PDF files will be skipped",
        "converting": "[{name}] Converting to PDF...",
        "convert_failed": "LibreOffice conversion failed",
        "no_libreoffice_err": "LibreOffice required to convert this format",
        "translating": "Translating: {name}",
        "engine_label": {
            "openai": "API ({model})",
            "google": "Google Free",
            "argos": "Local Offline",
        },
        "start_translate": "Started translation (engine: {engine}): {name}",
        "loading_model": "Loading layout detection model (~5-10s)...",
        "model_loaded": "Layout model loaded",
        "translate_done": "Translation complete: {name} → {n} file(s) ({elapsed}s)",
        "translate_error": "Translation error: {error}",
        "cancel_sent": "Job canceled by user",
        "cancelled": "Canceled",
        "lang_mismatch": "⚠ Detected file language is {detected}, but source language is set to {source}. Translation may produce poor results.",
        "lang_mismatch_same": "⚠ File appears to be already in {detected}, same as target language {target}. The file may already be translated — re-translating can cause garbled output.",
    },
    "zh": {
        "job_start": "任务开始：{n} 个文件",
        "job_end": "任务结束：✅ {ok} / ❌ {fail}",
        "no_libreoffice": "⚠ 未检测到 LibreOffice，非 PDF 文件将跳过",
        "converting": "[{name}] 正在转为 PDF...",
        "convert_failed": "LibreOffice 转 PDF 失败",
        "no_libreoffice_err": "需要 LibreOffice 才能转换该格式",
        "translating": "翻译中：{name}",
        "engine_label": {
            "openai": "API（{model}）",
            "google": "Google 免费接口",
            "argos": "本地离线模型",
        },
        "start_translate": "开始翻译（引擎: {engine}）: {name}",
        "loading_model": "加载版面检测模型（首次约 5-10 秒）...",
        "model_loaded": "版面模型加载完成",
        "translate_done": "翻译完成: {name} → {n} 个文件 ({elapsed}s)",
        "translate_error": "翻译出错: {error}",
        "cancel_sent": "用户取消了任务",
        "cancelled": "已取消",
        "lang_mismatch": "⚠ 检测到文件语言为{detected}，但源语言设置为{source}，翻译效果可能不佳。",
        "lang_mismatch_same": "⚠ 文件似乎是{detected}，与目标语言{target}相同。该文件可能已经是翻译版——重复翻译可能导致乱码。",
    },
}


def get_lang() -> str:
    """读取当前界面语言配置。"""
    from . import config as cfg
    return cfg.load_config().get("ui_lang", "en")


def msg(key: str, **kwargs) -> str:
    """返回当前语言的日志消息。"""
    lang = get_lang()
    d = _MSGS.get(lang, _MSGS["en"])
    template = d.get(key, _MSGS["en"].get(key, key))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template