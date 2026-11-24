"""曲库检索：按 ID / 曲名 / 歌手查找单曲。

V-Archive 的曲库是整表 JSON，这里在内存里建一份轻量索引：
- ``by_id``：songid → 条目
- ``all``：按曲名排序的条目列表
- 曲名与歌手统一小写、去符号后参与匹配，避免手打大小写与标点差异。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import DMSongDB, DMSongDBEntry

#: 曲名归一化时忽略的字符（空白、常见标点与装饰符号）。
_STRIP = re.compile(r"[\s\-_~!@#$%^&*()+=|\\/<>?.,:;'\"\[\]{}`　·・.]+")
#: 曲名末尾的版本后缀，例如 "V" / "Feat. XXX"。
_TRAILING = re.compile(r"\s*[\(（\[【].*?[\)）\]】]\s*$")


def normalize(text: str) -> str:
    """统一大小写、全半角并去标点，用于宽松匹配。"""
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return _STRIP.sub("", text).strip()


@dataclass(frozen=True)
class SongHit:
    entry: DMSongDBEntry
    score: int
    """匹配得分，越大越可信。"""


class SongIndex:
    """曲库索引；``search`` 返回按相关度降序的候选。"""

    def __init__(self, db: DMSongDB) -> None:
        self.db = db
        self.by_id: dict[int, DMSongDBEntry] = {}
        self.all: list[DMSongDBEntry] = list(db.root)
        self._norm_title: dict[int, str] = {}
        self._norm_composer: dict[int, str] = {}
        self.rebuild()

    def rebuild(self) -> None:
        self.by_id = {e.songid: e for e in self.all}
        self._norm_title = {e.songid: normalize(e.title) for e in self.all}
        self._norm_composer = {e.songid: normalize(e.composer) for e in self.all}

    def get(self, songid: int) -> DMSongDBEntry | None:
        return self.by_id.get(int(songid))

    def search(self, query: str, *, limit: int = 10) -> list[SongHit]:
        """按 songid → 全等曲名 → 前缀 → 子串 → 歌手的顺序收集候选。"""
        query = (query or "").strip()
        if not query:
            return []

        # 1. 纯数字：既可能是 songid，也可能是纯数字曲名，两种都收集。
        hits: dict[int, int] = {}
        if query.isdigit():
            sid = int(query)
            if sid in self.by_id:
                hits[sid] = 100

        needle = normalize(query)
        if not needle:
            return self._hits(hits, limit)

        for entry in self.all:
            sid = entry.songid
            title = self._norm_title.get(sid, "")
            if not title:
                continue
            score = 0
            if title == needle:
                score = 95
            elif title.startswith(needle):
                score = 80
            elif needle in title:
                score = 60
            else:
                # 曲名去掉括号后缀再试一次，方便搜 "Your Priestess" 这类带副标题的曲目。
                stripped = _TRAILING.sub("", entry.title).strip()
                if stripped and (norm_stripped := normalize(stripped)) and norm_stripped == needle:
                    score = 85
                elif self._norm_composer.get(sid, "") == needle:
                    score = 50
                elif needle and needle in self._norm_composer.get(sid, ""):
                    score = 40
            if score:
                # 同分时短曲名更可能是目标曲目。
                hits[sid] = max(hits.get(sid, 0), score - min(len(title) // 20, 5))
        return self._hits(hits, limit)

    def _hits(self, scores: dict[int, int], limit: int) -> list[SongHit]:
        entries = [(sid, s) for sid, s in scores.items() if sid in self.by_id]
        entries.sort(key=lambda item: (-item[1], len(self.by_id[item[0]].title), item[0]))
        return [SongHit(self.by_id[sid], score) for sid, score in entries[:limit]]
