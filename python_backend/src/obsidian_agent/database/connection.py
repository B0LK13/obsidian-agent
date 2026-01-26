"""Database connection management"""

from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseConnection:
    """Database connection manager"""

    def __init__(self, db_path: Path, echo: bool = False):
        self.db_path = db_path
        self.engine = self._create_engine(db_path, echo)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def _create_engine(self, db_path: Path, echo: bool):
        """Create SQLAlchemy engine"""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        return engine
    
    def initialize_database(self) -> None:
        """Create all tables and FTS5 index"""
        Base.metadata.create_all(self.engine)
        
        # Create FTS5 virtual table for full-text search
        with self.engine.connect() as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                    title, content,
                    content='notes',
                    content_rowid='rowid'
                )
            """)
            
            # Create triggers to keep FTS5 in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_fts_insert AFTER INSERT ON notes BEGIN
                    INSERT INTO notes_fts(rowid, title, content)
                    VALUES (new.rowid, new.title, new.content);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_fts_delete AFTER DELETE ON notes BEGIN
                    DELETE FROM notes_fts WHERE rowid = old.rowid;
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS notes_fts_update AFTER UPDATE ON notes BEGIN
                    UPDATE notes_fts SET title = new.title, content = new.content
                    WHERE rowid = new.rowid;
                END
            """)
            
            conn.commit()
    
    @contextmanager
    def get_session(self):
        """Get a database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connection"""
        self.engine.dispose()
