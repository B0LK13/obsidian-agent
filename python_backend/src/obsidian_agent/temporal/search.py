"""Temporal search and time-based analytics."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TimeGranularity(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass
class TimeRange:
    start: datetime
    end: datetime
    
    @classmethod
    def last_days(cls, days: int) -> "TimeRange":
        end = datetime.now()
        start = end - timedelta(days=days)
        return cls(start=start, end=end)
    
    @classmethod
    def this_week(cls) -> "TimeRange":
        now = datetime.now()
        start = now - timedelta(days=now.weekday())
        return cls(start=start.replace(hour=0, minute=0, second=0), end=now)
    
    @classmethod
    def this_month(cls) -> "TimeRange":
        now = datetime.now()
        start = now.replace(day=1, hour=0, minute=0, second=0)
        return cls(start=start, end=now)


@dataclass
class TemporalResult:
    notes: list[dict[str, Any]]
    time_range: TimeRange
    stats: dict[str, Any] = field(default_factory=dict)


class TemporalSearch:
    """Search and analyze notes by time."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
    
    async def search(self, time_range: TimeRange, query: str | None = None) -> TemporalResult:
        """Search notes within a time range."""
        notes = []
        for md_file in self.vault_path.rglob("*.md"):
            stat = md_file.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
            if time_range.start <= modified <= time_range.end:
                content = md_file.read_text(encoding="utf-8")
                if query is None or query.lower() in content.lower():
                    notes.append({
                        "path": str(md_file.relative_to(self.vault_path)),
                        "title": md_file.stem,
                        "modified": modified.isoformat(),
                        "size": stat.st_size,
                    })
        
        notes.sort(key=lambda n: n["modified"], reverse=True)
        return TemporalResult(notes=notes, time_range=time_range, stats={"count": len(notes)})
    
    async def get_activity(self, time_range: TimeRange, granularity: TimeGranularity = TimeGranularity.DAY) -> dict[str, int]:
        """Get note activity over time."""
        activity = {}
        for md_file in self.vault_path.rglob("*.md"):
            modified = datetime.fromtimestamp(md_file.stat().st_mtime)
            if time_range.start <= modified <= time_range.end:
                if granularity == TimeGranularity.DAY:
                    key = modified.strftime("%Y-%m-%d")
                elif granularity == TimeGranularity.WEEK:
                    key = modified.strftime("%Y-W%W")
                elif granularity == TimeGranularity.MONTH:
                    key = modified.strftime("%Y-%m")
                else:
                    key = modified.strftime("%Y")
                activity[key] = activity.get(key, 0) + 1
        return activity
    
    async def get_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recently modified notes."""
        result = await self.search(TimeRange.last_days(365))
        return result.notes[:limit]
    
    async def get_created_on(self, date: datetime) -> list[dict[str, Any]]:
        """Get notes created on a specific date."""
        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)
        result = await self.search(TimeRange(start=start, end=end))
        return result.notes
    
    async def get_stats(self, time_range: TimeRange) -> dict[str, Any]:
        """Get statistics for a time range."""
        result = await self.search(time_range)
        total_size = sum(n.get("size", 0) for n in result.notes)
        return {
            "note_count": len(result.notes),
            "total_size_bytes": total_size,
            "avg_size_bytes": total_size // len(result.notes) if result.notes else 0,
            "time_range": {"start": time_range.start.isoformat(), "end": time_range.end.isoformat()},
        }
