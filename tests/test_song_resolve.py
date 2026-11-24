"""曲目解析（songid / 曲名 / 歌手 → 唯一曲目）的回归测试。

不依赖网络：用一份手写的迷你曲库覆盖真实查分时踩过的坑：

- ``dj info 4B 441``：songid 必须直接命中，不能被当成曲名去匹配
  （旧实现里 "#441" 会连带出 "AD2222"、两首 "2" 会彼此纠缠）。
- ``dj info 4B #2``：候选列表里显示的 ``#2`` 抄回来也要能用。
- 同名不同曲（两首 "Alone"）：曲名一样时必须让用户确认，而不是静默选一首。
- 歌手查询（Nauts 有多首）：列出该歌手的歌，绝不随便挑一首。

运行：``python -m pytest tests`` 或直接 ``python tests/test_song_resolve.py``。
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "qqbot_djmax"
SUB_DIR = PKG_DIR / "djmax_bests"

#: 迷你曲库：只保留解析逻辑真正用到的字段。
_SONGS = [
    (1, "2Nite", "ND Lee"),
    (2, "Alone", "Marshmello"),
    (4, "Armored Phantom", "ned"),
    (226, "고백, 꽃, 늑대 part.2", "ReX"),
    (298, "설레임 Part.2", "ND Lee"),
    (301, "AD2222", "CROOVE"),
    (302, "AD2222 ~Extended Mix~", "CROOVE"),
    (332, "D2", "FIRST AID"),
    (396, "Leave me alone", "NieN"),
    (441, "Alone", "Nauts"),
    (442, "WHY", "Nauts"),
    (443, "DON'T DIE", "Nauts"),
    (500, "Void", "Kobayashi Tetsuya"),
    (501, "Voyage", "makou"),
]


def _stub_package() -> None:
    """绕开包内 ``__init__`` 对 nonebot 的依赖，只装载检索模块。"""
    for name, path in (("qqbot_djmax", PKG_DIR), ("qqbot_djmax.djmax_bests", SUB_DIR)):
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    sys.path[:0] = [str(ROOT)]


_stub_package()
from qqbot_djmax.djmax_bests import song_index  # noqa: E402
from qqbot_djmax.djmax_bests.models import DMSongDB  # noqa: E402


def _entry(songid: int, title: str, composer: str) -> dict:
    return {
        "title": songid,
        "name": title,
        "composer": composer,
        "dlcCode": "RV",
        "newTab": False,
        "patterns": {mode: {"NM": {"level": 5}} for mode in ("4B", "5B", "6B", "8B")},
    }


def _index() -> song_index.SongIndex:
    db = DMSongDB.model_validate([_entry(sid, title, comp) for sid, title, comp in _SONGS])
    return song_index.SongIndex(db)


def _entry_of(query: str, *, hint: str | None = None):
    return song_index.resolve(_index(), query, hint=hint).entry


def test_songid_hits_directly():
    assert _entry_of("441").songid == 441
    assert _entry_of("2").songid == 2
    assert _entry_of("4").songid == 4  # 是 songid，不是键数；键数在命令层已经剥掉


def test_songid_with_hash_prefix():
    """候选列表里显示成 "#441"，用户抄回来必须照样能用。"""
    assert _entry_of("#441").songid == 441
    assert _entry_of("＃2").songid == 2


def test_unknown_number_is_not_matched_as_title():
    """库里没有 9999 号时不能退化成"把它当曲名子串"随便挑一首。"""
    result = song_index.resolve(_index(), "9999")
    assert result.entry is None


def test_duplicate_titles_need_confirmation():
    result = song_index.resolve(_index(), "Alone")
    assert result.entry is None
    assert {h.entry.songid for h in result.hits[:2]} == {2, 441}


def test_duplicate_titles_resolved_by_songid_hint():
    """``dj info 4B 441``：曲名分支 + songid 提示 → 441，而不是默认第一首。"""
    assert _entry_of("441", hint="441").songid == 441
    assert _entry_of("2", hint="2").songid == 2


def test_unique_exact_title_wins_without_confirmation():
    assert _entry_of("D2").songid == 332
    assert _entry_of("Leave me alone").songid == 396


def test_exact_title_beats_near_duplicate():
    """AD2222 与 AD2222 ~Extended Mix~ 同时存在时，全等曲名优先。"""
    assert _entry_of("AD2222").songid == 301
    assert _entry_of("AD2222 ~Extended Mix~").songid == 302
    assert _entry_of("AD2222 ~Extended").songid == 302  # 括号后缀可省略


def test_prefix_shared_by_several_titles_is_ambiguous():
    """前缀命中两三首、又没有全等时，不能凭分差就替用户选。"""
    result = song_index.resolve(_index(), "Vo")
    assert result.entry is None
    assert {h.entry.songid for h in result.hits[:2]} == {500, 501}


def test_single_composer_match_wins():
    assert _entry_of("Marshm").songid == 2


def test_multi_song_composer_lists_its_songs():
    result = song_index.resolve(_index(), "Nauts")
    assert result.entry is None
    assert {h.entry.songid for h in result.hits} >= {441, 442, 443}
    # 候选里全是这位歌手的歌，不会被别的曲名命中混进来
    assert all(h.entry.composer == "Nauts" for h in result.hits)


def test_short_substring_is_ambiguous():
    result = song_index.resolve(_index(), "V")
    assert result.entry is None


def test_missing_song():
    assert song_index.resolve(_index(), "不存在的曲子").entry is None


if __name__ == "__main__":
    checks = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for check in checks:
        check()
        print(f"  ok {check.__name__}")
    print("ok djmax song resolve")
