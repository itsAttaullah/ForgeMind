"""Long-term memory stores (summarized facts/strategies only)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from forgemind.core.memory import LongTermMemoryItem
from forgemind.memory.retention import sanitize_metadata, truncate_text

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text)}


def score_item(query: str, item: LongTermMemoryItem) -> float:
    """Simple token-overlap score in ``[0, 1]``."""

    q = _tokens(query)
    if not q:
        return 0.0
    blob = f"{item.key} {item.content} {item.kind}"
    t = _tokens(blob)
    if not t:
        return 0.0
    overlap = len(q & t)
    return overlap / len(q)


class InMemoryLongTermStore:
    """Process-local long-term memory index."""

    def __init__(self, *, max_content_chars: int = 2000) -> None:
        self._items: dict[str, LongTermMemoryItem] = {}
        self._max_content_chars = max_content_chars

    async def upsert(self, item: LongTermMemoryItem) -> LongTermMemoryItem:
        cleaned = item.model_copy(
            update={
                "content": truncate_text(item.content, self._max_content_chars),
                "metadata": sanitize_metadata(dict(item.metadata)),
            }
        )
        self._items[cleaned.key] = cleaned
        return cleaned

    async def delete(self, key: str) -> None:
        self._items.pop(key, None)

    async def get(self, key: str) -> LongTermMemoryItem | None:
        item = self._items.get(key)
        return None if item is None else item.model_copy(deep=True)

    async def list_items(self) -> list[LongTermMemoryItem]:
        return [item.model_copy(deep=True) for item in self._items.values()]

    def replace_all(self, items: list[LongTermMemoryItem]) -> None:
        """Replace the entire index (used by file-backed loaders)."""

        self._items = {item.key: item for item in items}

    def export_items(self) -> list[LongTermMemoryItem]:
        """Return a shallow list of stored items for persistence."""

        return list(self._items.values())

    async def retrieve(self, query: str, *, limit: int = 5) -> list[LongTermMemoryItem]:
        scored: list[tuple[float, LongTermMemoryItem]] = []
        for item in self._items.values():
            score = score_item(query, item)
            if score <= 0:
                continue
            scored.append((score, item.model_copy(update={"score": score}, deep=True)))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]


class JsonFileLongTermStore:
    """Persist long-term items in a single JSON document."""

    def __init__(
        self,
        path: str | Path,
        *,
        max_content_chars: int = 2000,
    ) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._max_content_chars = max_content_chars
        self._memory = InMemoryLongTermStore(max_content_chars=max_content_chars)
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        loaded = [LongTermMemoryItem.model_validate(entry) for entry in items]
        self._memory.replace_all(loaded)

    def _dump(self) -> None:
        payload = {"items": [item.model_dump(mode="json") for item in self._memory.export_items()]}
        self._path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    async def upsert(self, item: LongTermMemoryItem) -> LongTermMemoryItem:
        cleaned = await self._memory.upsert(item)
        self._dump()
        return cleaned

    async def delete(self, key: str) -> None:
        await self._memory.delete(key)
        self._dump()

    async def get(self, key: str) -> LongTermMemoryItem | None:
        return await self._memory.get(key)

    async def list_items(self) -> list[LongTermMemoryItem]:
        return await self._memory.list_items()

    async def retrieve(self, query: str, *, limit: int = 5) -> list[LongTermMemoryItem]:
        return await self._memory.retrieve(query, limit=limit)
