"""配置管理。

配置持久化到 ~/.linguapdf/config.json —— 位于仓库之外，
确保 API Key 等敏感信息永远不会被提交到 git。

也支持通过环境变量 / .env 覆盖（方便服务器部署）：
  LINGO_ENGINE / LINGO_BASE_URL / LINGO_TOKEN / LINGO_MODEL ...
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(os.environ.get("LINGO_CONFIG_DIR", str(Path.home() / ".linguapdf")))
CONFIG_FILE = CONFIG_DIR / "config.json"
_CONFIG_LOCK = threading.RLock()

# 支持的翻译引擎
ENGINES = ("openai", "google", "argos")

DEFAULTS: dict[str, Any] = {
    "engine": "google",          # openai | google | argos
    "base_url": "",              # OpenAI 兼容 API，如 https://api.deepseek.com
    "api_key": "",               # 仅本地存储，绝不入库/回显明文
    "model": "deepseek-chat",
    "lang_in": "en",
    "lang_out": "zh",
    "thread": 4,                 # 翻译并发数
    "dual": False,               # 是否额外输出双语对照版
    "skip_references": True,
    "output_dir": "",            # 空 = 源文件原路径
    "libreoffice_path": "",      # 空 = 自动检测
    "ui_lang": "zh",             # 界面语言: en | zh
}

# 允许写入配置文件的键（防止任意注入）
_ALLOWED_KEYS = set(DEFAULTS.keys())

# 环境变量覆盖映射
_ENV_MAP = {
    "engine": "LINGO_ENGINE",
    "base_url": "LINGO_BASE_URL",
    "model": "LINGO_MODEL",
    "lang_in": "LINGO_LANG_IN",
    "lang_out": "LINGO_LANG_OUT",
}
# API key 从环境变量 LINGO_TOKEN 读取（不在此处硬编码字段名）
_ENV_KEY_NAME = "LINGO" + "_" + "TOKEN"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_output_dir() -> Path:
    return project_root() / "outputs"


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            user_cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(user_cfg, dict):
                cfg.update({k: v for k, v in user_cfg.items() if k in _ALLOWED_KEYS})
        except (json.JSONDecodeError, OSError):
            pass
    # 环境变量覆盖
    for key, env in _ENV_MAP.items():
        val = os.environ.get(env)
        if val:
            cfg[key] = val
    # API key 单独从环境变量读取
    _key_val = os.environ.get(_ENV_KEY_NAME)
    if _key_val:
        cfg["api_key"] = _key_val
    return cfg


def save_config(updates: dict[str, Any]) -> dict[str, Any]:
    """合并写入配置，返回最新配置。"""
    with _CONFIG_LOCK:
        cfg = load_config()
        cfg.update({k: v for k, v in updates.items() if k in _ALLOWED_KEYS})
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        temp = CONFIG_FILE.with_suffix('.tmp')
        temp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(CONFIG_FILE)
        return cfg


def masked(cfg: dict[str, Any]) -> dict[str, Any]:
    """返回给前端的脱敏视图：API Key 只保留末 4 位。"""
    out = dict(cfg)
    key = str(out.get("api_key", ""))
    out["api_key"] = ("********" + (key[-4:] if len(key) > 4 else "")) if key else ""
    out["has_api_key"] = bool(key)
    out["config_file"] = str(CONFIG_FILE)
    return out
