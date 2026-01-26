"""Backup management with versioning."""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass
class BackupConfig:
    backup_dir: Path
    max_backups: int = 10
    compress: bool = True

@dataclass
class BackupInfo:
    id: str
    created_at: datetime
    path: Path
    size_bytes: int

class BackupManager:
    def __init__(self, vault_path: Path, config: BackupConfig):
        self.vault_path = vault_path
        self.config = config
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, name: str | None = None) -> BackupInfo:
        timestamp = datetime.now()
        backup_id = name or timestamp.strftime("%Y%m%d_%H%M%S")
        if self.config.compress:
            backup_path = self.config.backup_dir / f"{backup_id}.zip"
            shutil.make_archive(str(backup_path.with_suffix("")), "zip", self.vault_path)
        else:
            backup_path = self.config.backup_dir / backup_id
            shutil.copytree(self.vault_path, backup_path)
        size = backup_path.stat().st_size
        self._cleanup_old_backups()
        return BackupInfo(id=backup_id, created_at=timestamp, path=backup_path, size_bytes=size)
    
    async def restore_backup(self, backup_id: str, target: Path | None = None) -> bool:
        target = target or self.vault_path
        backup_path = self._find_backup(backup_id)
        if not backup_path:
            return False
        if backup_path.suffix == ".zip":
            shutil.unpack_archive(backup_path, target)
        else:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(backup_path, target)
        return True
    
    def list_backups(self) -> list[BackupInfo]:
        backups = []
        for path in self.config.backup_dir.iterdir():
            if path.suffix == ".zip" or path.is_dir():
                stat = path.stat()
                backups.append(BackupInfo(id=path.stem, created_at=datetime.fromtimestamp(stat.st_mtime), path=path, size_bytes=stat.st_size))
        return sorted(backups, key=lambda b: b.created_at, reverse=True)
    
    def _find_backup(self, backup_id: str) -> Path | None:
        for ext in [".zip", ""]:
            path = self.config.backup_dir / f"{backup_id}{ext}"
            if path.exists():
                return path
        return None
    
    def _cleanup_old_backups(self) -> None:
        backups = self.list_backups()
        while len(backups) > self.config.max_backups:
            oldest = backups.pop()
            if oldest.path.is_file():
                oldest.path.unlink()
            else:
                shutil.rmtree(oldest.path)
