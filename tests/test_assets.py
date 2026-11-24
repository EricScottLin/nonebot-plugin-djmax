"""DJMAX 插件基础测试。

不依赖网络，也不要求素材已就位：只覆盖解析、检索与素材定位这些纯逻辑。
运行：``python -m pytest tests`` 或直接 ``python tests/test_basic.py``。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "qqbot_djmax")]

# 没有 NoneBot 运行时也能导入解析函数：这些模块不依赖 nonebot。
import importlib.util


def _load(name: str):
    """按文件路径加载模块，绕开包内 ``__init__`` 对 nonebot 的依赖。"""
    path = ROOT / "qqbot_djmax" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_djmax_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# --- 素材定位 ---------------------------------------------------------------


def test_assets_root_none_when_missing(tmp_path, monkeypatch):
    assets = _load("assets")
    monkeypatch.setenv("DJMAX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("DJMAX_ASSETS_DIR", raising=False)
    monkeypatch.delenv("DJMAX_ASSETS_URL", raising=False)
    # 仓库里不带素材，且数据目录是空的 -> 未就绪
    assert assets.assets_root() is None


def test_assets_root_accepts_local_dir(tmp_path, monkeypatch):
    assets = _load("assets")
    root = tmp_path / "assets"
    (root / "fonts").mkdir(parents=True)
    for name in ("Respect_bd.ttf", "Respect_rg.ttf", "Respect_lt.ttf"):
        (root / "fonts" / name).write_bytes(b"stub")
    (root / "bests_generator" / "assets").mkdir(parents=True)

    monkeypatch.setenv("DJMAX_ASSETS_DIR", str(root))
    assert assets.assets_root() == root


def test_assets_incomplete_dir_rejected(tmp_path, monkeypatch):
    assets = _load("assets")
    root = tmp_path / "assets"
    (root / "fonts").mkdir(parents=True)
    (root / "fonts" / "Respect_bd.ttf").write_bytes(b"stub")  # 缺另外两个字体
    monkeypatch.setenv("DJMAX_ASSETS_DIR", str(root))
    monkeypatch.setenv("DJMAX_DATA_DIR", str(tmp_path / "empty"))
    assert assets.assets_root() is None


def test_ensure_assets_error_message_is_actionable(tmp_path, monkeypatch):
    assets = _load("assets")
    monkeypatch.setenv("DJMAX_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("DJMAX_ASSETS_DIR", raising=False)
    monkeypatch.delenv("DJMAX_ASSETS_URL", raising=False)
    import asyncio

    try:
        asyncio.run(assets.ensure_assets())
    except RuntimeError as exc:
        message = str(exc)
        assert "DJMAX_ASSETS_URL" in message and "DJMAX_ASSETS_DIR" in message
    else:  # pragma: no cover
        raise AssertionError("素材缺失时应当报错")


# --- 曲库检索 ---------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    class _MP:
        """极简 monkeypatch 替身，避免测试依赖 pytest。"""

        def __init__(self):
            self._saved: dict[str, str | None] = {}

        def setenv(self, key, value):
            import os

            self._saved.setdefault(key, os.environ.get(key))
            os.environ[key] = value

        def delenv(self, key, raising=True):
            import os

            self._saved.setdefault(key, os.environ.get(key))
            os.environ.pop(key, None)

        def undo(self):
            import os

            for key, value in self._saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    checks = [
        test_assets_root_none_when_missing,
        test_assets_root_accepts_local_dir,
        test_assets_incomplete_dir_rejected,
        test_ensure_assets_error_message_is_actionable,
    ]
    for check in checks:
        with tempfile.TemporaryDirectory() as folder:
            mp = _MP()
            try:
                check(Path(folder), mp)
            finally:
                mp.undo()
        print(f"  ok {check.__name__}")
    print("ok djmax assets resolution")
