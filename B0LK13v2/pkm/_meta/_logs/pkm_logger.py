#!/usr/bin/env python3
"""
PKM Activity Logger
SQLite-based logging system for tracking all PKM edits and actions.

Usage:
    python pkm_logger.py log --action create --target "path/to/file.md" --summary "Created new note"
    python pkm_logger.py log --action edit --target "path/to/file.md" --summary "Updated content" --changes "Added section X"
    python pkm_logger.py query --last 10
    python pkm_logger.py query --action edit --since "2026-01-01"
    python pkm_logger.py stats
    python pkm_logger.py export --format json --output logs_export.json
"""

import sqlite3
import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Database path
DB_PATH = Path(__file__).parent / "pkm_activity.db"

# Action types
ACTIONS = ["create", "edit", "move", "delete", "archive", "link", "rename", "view"]

# Schema version for migrations
SCHEMA_VERSION = 1


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main activity log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            target_path TEXT NOT NULL,
            target_name TEXT,
            summary TEXT,
            changes TEXT,
            tags TEXT,
            area TEXT,
            scope TEXT,
            file_hash TEXT,
            file_size INTEGER,
            session_id TEXT,
            user TEXT DEFAULT 'system',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Index for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_timestamp 
        ON activity_log(timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_action 
        ON activity_log(action)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_target 
        ON activity_log(target_path)
    """)
    
    # Statistics table for aggregated metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            creates INTEGER DEFAULT 0,
            edits INTEGER DEFAULT 0,
            moves INTEGER DEFAULT 0,
            deletes INTEGER DEFAULT 0,
            archives INTEGER DEFAULT 0,
            links INTEGER DEFAULT 0,
            renames INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0
        )
    """)
    
    # Session tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            action_count INTEGER DEFAULT 0,
            description TEXT
        )
    """)
    
    # Schema version tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_info (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        INSERT OR REPLACE INTO schema_info (key, value) 
        VALUES ('version', ?)
    """, (str(SCHEMA_VERSION),))
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")


def compute_file_hash(filepath: str) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        path = Path(filepath)
        if path.exists() and path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except Exception:
        pass
    return None


def get_file_size(filepath: str) -> Optional[int]:
    """Get file size in bytes."""
    try:
        path = Path(filepath)
        if path.exists() and path.is_file():
            return path.stat().st_size
    except Exception:
        pass
    return None


def log_activity(
    action: str,
    target_path: str,
    summary: str = "",
    changes: str = "",
    tags: List[str] = None,
    area: str = "",
    scope: str = "",
    session_id: str = "",
    user: str = "system"
) -> int:
    """
    Log an activity to the database.
    
    Returns the ID of the inserted record.
    """
    if action not in ACTIONS:
        raise ValueError(f"Invalid action: {action}. Must be one of {ACTIONS}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    target_name = Path(target_path).name if target_path else ""
    tags_str = ",".join(tags) if tags else ""
    file_hash = compute_file_hash(target_path)
    file_size = get_file_size(target_path)
    
    cursor.execute("""
        INSERT INTO activity_log 
        (timestamp, action, target_path, target_name, summary, changes, 
         tags, area, scope, file_hash, file_size, session_id, user)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, action, target_path, target_name, summary, changes,
        tags_str, area, scope, file_hash, file_size, session_id, user
    ))
    
    record_id = cursor.lastrowid
    
    # Update daily stats
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(f"""
        INSERT INTO daily_stats (date, {action}s, total)
        VALUES (?, 1, 1)
        ON CONFLICT(date) DO UPDATE SET
            {action}s = {action}s + 1,
            total = total + 1
    """, (date,))
    
    conn.commit()
    conn.close()
    
    print(f"[{timestamp}] Logged: {action} -> {target_path}")
    return record_id


def query_activities(
    action: str = None,
    target: str = None,
    since: str = None,
    until: str = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Query activity logs with filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM activity_log WHERE 1=1"
    params = []
    
    if action:
        query += " AND action = ?"
        params.append(action)
    
    if target:
        query += " AND target_path LIKE ?"
        params.append(f"%{target}%")
    
    if since:
        query += " AND timestamp >= ?"
        params.append(since)
    
    if until:
        query += " AND timestamp <= ?"
        params.append(until)
    
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return results


def get_statistics(period: str = "all") -> Dict[str, Any]:
    """Get activity statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total counts by action
    cursor.execute("""
        SELECT action, COUNT(*) as count 
        FROM activity_log 
        GROUP BY action
    """)
    stats["by_action"] = {row["action"]: row["count"] for row in cursor.fetchall()}
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM activity_log")
    stats["total"] = cursor.fetchone()["total"]
    
    # Daily stats for last 7 days
    cursor.execute("""
        SELECT * FROM daily_stats 
        ORDER BY date DESC 
        LIMIT 7
    """)
    stats["daily"] = [dict(row) for row in cursor.fetchall()]
    
    # Most active files
    cursor.execute("""
        SELECT target_path, COUNT(*) as count 
        FROM activity_log 
        GROUP BY target_path 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats["most_active_files"] = [dict(row) for row in cursor.fetchall()]
    
    # Recent activity summary
    cursor.execute("""
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM activity_log
        GROUP BY date(timestamp)
        ORDER BY date DESC
        LIMIT 30
    """)
    stats["activity_by_date"] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return stats


def export_logs(
    format: str = "json",
    output: str = None,
    since: str = None,
    until: str = None
) -> str:
    """Export logs to file."""
    activities = query_activities(since=since, until=until, limit=10000)
    
    if format == "json":
        content = json.dumps(activities, indent=2, default=str)
    elif format == "csv":
        if not activities:
            content = ""
        else:
            headers = activities[0].keys()
            lines = [",".join(headers)]
            for act in activities:
                lines.append(",".join(str(act.get(h, "")) for h in headers))
            content = "\n".join(lines)
    elif format == "markdown":
        lines = ["# PKM Activity Log Export", "", f"Generated: {datetime.now().isoformat()}", ""]
        for act in activities:
            lines.append(f"## [{act['timestamp']}] {act['action'].upper()}")
            lines.append(f"- **Target:** {act['target_path']}")
            lines.append(f"- **Summary:** {act['summary']}")
            if act['changes']:
                lines.append(f"- **Changes:** {act['changes']}")
            lines.append("")
        content = "\n".join(lines)
    else:
        raise ValueError(f"Unknown format: {format}")
    
    if output:
        Path(output).write_text(content, encoding="utf-8")
        print(f"Exported to: {output}")
    
    return content


def start_session(description: str = "") -> str:
    """Start a new logging session."""
    conn = get_connection()
    cursor = conn.cursor()
    
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    cursor.execute("""
        INSERT INTO sessions (session_id, started_at, description)
        VALUES (?, ?, ?)
    """, (session_id, datetime.now().isoformat(), description))
    
    conn.commit()
    conn.close()
    
    print(f"Session started: {session_id}")
    return session_id


def end_session(session_id: str):
    """End a logging session."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count actions in session
    cursor.execute("""
        SELECT COUNT(*) as count FROM activity_log WHERE session_id = ?
    """, (session_id,))
    count = cursor.fetchone()["count"]
    
    cursor.execute("""
        UPDATE sessions 
        SET ended_at = ?, action_count = ?
        WHERE session_id = ?
    """, (datetime.now().isoformat(), count, session_id))
    
    conn.commit()
    conn.close()
    
    print(f"Session ended: {session_id} ({count} actions)")


def print_table(data: List[Dict], columns: List[str] = None):
    """Print data as a formatted table."""
    if not data:
        print("No results found.")
        return
    
    if columns is None:
        columns = list(data[0].keys())
    
    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            val = str(row.get(col, ""))[:50]
            widths[col] = max(widths[col], len(val))
    
    # Print header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in data:
        line = " | ".join(str(row.get(col, ""))[:50].ljust(widths[col]) for col in columns)
        print(line)


def main():
    parser = argparse.ArgumentParser(description="PKM Activity Logger")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    
    # Log command
    log_parser = subparsers.add_parser("log", help="Log an activity")
    log_parser.add_argument("--action", "-a", required=True, choices=ACTIONS)
    log_parser.add_argument("--target", "-t", required=True, help="Target file path")
    log_parser.add_argument("--summary", "-s", default="", help="Summary of the action")
    log_parser.add_argument("--changes", "-c", default="", help="Detailed changes")
    log_parser.add_argument("--tags", nargs="+", default=[], help="Tags")
    log_parser.add_argument("--area", default="", help="Area (system, projects, etc.)")
    log_parser.add_argument("--scope", default="", help="Scope (major, minor, etc.)")
    log_parser.add_argument("--session", default="", help="Session ID")
    log_parser.add_argument("--user", default="system", help="User identifier")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query activities")
    query_parser.add_argument("--action", "-a", choices=ACTIONS, help="Filter by action")
    query_parser.add_argument("--target", "-t", help="Filter by target path (partial match)")
    query_parser.add_argument("--since", help="Filter from date (ISO format)")
    query_parser.add_argument("--until", help="Filter until date (ISO format)")
    query_parser.add_argument("--last", "-n", type=int, default=20, help="Number of results")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export logs")
    export_parser.add_argument("--format", "-f", choices=["json", "csv", "markdown"], default="json")
    export_parser.add_argument("--output", "-o", help="Output file path")
    export_parser.add_argument("--since", help="Export from date")
    export_parser.add_argument("--until", help="Export until date")
    
    # Session commands
    session_parser = subparsers.add_parser("session", help="Session management")
    session_parser.add_argument("action", choices=["start", "end"])
    session_parser.add_argument("--id", help="Session ID (for end)")
    session_parser.add_argument("--description", "-d", default="", help="Session description")
    
    args = parser.parse_args()
    
    # Ensure database exists
    if args.command != "init" and not DB_PATH.exists():
        init_database()
    
    if args.command == "init":
        init_database()
    
    elif args.command == "log":
        log_activity(
            action=args.action,
            target_path=args.target,
            summary=args.summary,
            changes=args.changes,
            tags=args.tags,
            area=args.area,
            scope=args.scope,
            session_id=args.session,
            user=args.user
        )
    
    elif args.command == "query":
        results = query_activities(
            action=args.action,
            target=args.target,
            since=args.since,
            until=args.until,
            limit=args.last
        )
        print_table(results, ["timestamp", "action", "target_name", "summary"])
    
    elif args.command == "stats":
        stats = get_statistics()
        print("\n=== PKM Activity Statistics ===\n")
        print(f"Total Actions: {stats['total']}")
        print("\nBy Action Type:")
        for action, count in stats.get("by_action", {}).items():
            print(f"  {action}: {count}")
        print("\nMost Active Files:")
        for item in stats.get("most_active_files", [])[:5]:
            print(f"  {item['target_path']}: {item['count']} actions")
        print("\nLast 7 Days:")
        print_table(stats.get("daily", []), ["date", "creates", "edits", "moves", "total"])
    
    elif args.command == "export":
        content = export_logs(
            format=args.format,
            output=args.output,
            since=args.since,
            until=args.until
        )
        if not args.output:
            print(content)
    
    elif args.command == "session":
        if args.action == "start":
            start_session(args.description)
        elif args.action == "end":
            if not args.id:
                print("Error: --id required for ending session")
            else:
                end_session(args.id)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
