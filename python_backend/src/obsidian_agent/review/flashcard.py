"""Flashcard system for spaced repetition learning."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ReviewRating(int, Enum):
    AGAIN = 0
    HARD = 1
    GOOD = 2
    EASY = 3


@dataclass
class Flashcard:
    """A flashcard for spaced repetition."""
    id: str
    front: str
    back: str
    source_note: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_reviewed: datetime | None = None
    next_review: datetime | None = None
    interval_days: float = 1.0
    ease_factor: float = 2.5
    review_count: int = 0
    correct_count: int = 0
    
    @classmethod
    def create(cls, front: str, back: str, source_note: str | None = None) -> "Flashcard":
        return cls(id=str(uuid4()), front=front, back=back, source_note=source_note)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "front": self.front, "back": self.back,
            "source_note": self.source_note, "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "interval_days": self.interval_days, "ease_factor": self.ease_factor,
            "review_count": self.review_count, "correct_count": self.correct_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Flashcard":
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("last_reviewed"):
            data["last_reviewed"] = datetime.fromisoformat(data["last_reviewed"])
        if data.get("next_review"):
            data["next_review"] = datetime.fromisoformat(data["next_review"])
        return cls(**data)


@dataclass
class FlashcardDeck:
    """A collection of flashcards."""
    id: str
    name: str
    cards: list[Flashcard] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_card(self, card: Flashcard) -> None:
        self.cards.append(card)
    
    def remove_card(self, card_id: str) -> bool:
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                self.cards.pop(i)
                return True
        return False
    
    def get_due_cards(self, now: datetime | None = None) -> list[Flashcard]:
        now = now or datetime.now()
        return [c for c in self.cards if c.next_review is None or c.next_review <= now]
    
    def save(self, path: Path) -> None:
        data = {"id": self.id, "name": self.name, "cards": [c.to_dict() for c in self.cards]}
        path.write_text(json.dumps(data, indent=2))
    
    @classmethod
    def load(cls, path: Path) -> "FlashcardDeck":
        data = json.loads(path.read_text())
        deck = cls(id=data["id"], name=data["name"])
        deck.cards = [Flashcard.from_dict(c) for c in data.get("cards", [])]
        return deck


@dataclass
class ReviewSession:
    """A review session for flashcards."""
    deck: FlashcardDeck
    cards_to_review: list[Flashcard] = field(default_factory=list)
    current_index: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    results: list[tuple[str, ReviewRating]] = field(default_factory=list)
    
    def start(self) -> None:
        self.cards_to_review = self.deck.get_due_cards()
        self.current_index = 0
        self.started_at = datetime.now()
    
    @property
    def current_card(self) -> Flashcard | None:
        if 0 <= self.current_index < len(self.cards_to_review):
            return self.cards_to_review[self.current_index]
        return None
    
    def answer(self, rating: ReviewRating) -> Flashcard | None:
        card = self.current_card
        if card:
            self.results.append((card.id, rating))
            self.current_index += 1
            if self.current_index >= len(self.cards_to_review):
                self.completed = True
        return self.current_card
    
    @property
    def progress(self) -> float:
        if not self.cards_to_review:
            return 1.0
        return self.current_index / len(self.cards_to_review)
    
    def get_stats(self) -> dict[str, Any]:
        correct = sum(1 for _, r in self.results if r >= ReviewRating.GOOD)
        return {
            "total": len(self.cards_to_review),
            "reviewed": len(self.results),
            "correct": correct,
            "accuracy": correct / len(self.results) if self.results else 0,
        }
