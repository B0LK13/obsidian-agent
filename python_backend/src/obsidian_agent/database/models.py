"""SQLAlchemy models"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Note(Base):
    """Note model"""

    __tablename__ = "notes"

    id = Column(String, primary_key=True)
    path = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    content = Column(Text)
    created_at = Column(Float)  # Unix timestamp
    modified_at = Column(Float, index=True)
    indexed_at = Column(Float)
    checksum = Column(String)  # MD5 hash for change detection
    metadata = Column(JSON)  # YAML frontmatter and other metadata

    # Relationships
    outgoing_links = relationship("Link", foreign_keys="Link.source_note_id", back_populates="source")
    incoming_links = relationship("Link", foreign_keys="Link.target_note_id", back_populates="target")
    tags = relationship("Tag", back_populates="note")

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, path={self.path}, title={self.title})>"


class Link(Base):
    """Link between notes"""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_note_id = Column(String, ForeignKey("notes.id"), nullable=False)
    target_note_id = Column(String, ForeignKey("notes.id"), nullable=False)
    link_type = Column(String)  # 'internal', 'external', 'embed'
    link_text = Column(String)  # The text of the link
    
    # Relationships
    source = relationship("Note", foreign_keys=[source_note_id], back_populates="outgoing_links")
    target = relationship("Note", foreign_keys=[target_note_id], back_populates="incoming_links")

    # Indexes
    __table_args__ = (
        Index("idx_source_target", source_note_id, target_note_id),
    )

    def __repr__(self) -> str:
        return f"<Link(source={self.source_note_id}, target={self.target_note_id}, type={self.link_type})>"


class Tag(Base):
    """Tag associated with a note"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String, ForeignKey("notes.id"), nullable=False)
    tag = Column(String, nullable=False, index=True)

    # Relationships
    note = relationship("Note", back_populates="tags")

    # Indexes
    __table_args__ = (
        Index("idx_note_tag", note_id, tag),
    )

    def __repr__(self) -> str:
        return f"<Tag(note={self.note_id}, tag={self.tag})>"
