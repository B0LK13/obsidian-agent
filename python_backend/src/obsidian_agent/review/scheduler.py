"""Spaced repetition scheduler using SM-2 algorithm."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from obsidian_agent.review.flashcard import Flashcard, ReviewRating

logger = logging.getLogger(__name__)


@dataclass
class ReviewSchedule:
    """Schedule for upcoming reviews."""
    due_today: list[Flashcard] = field(default_factory=list)
    due_tomorrow: list[Flashcard] = field(default_factory=list)
    due_this_week: list[Flashcard] = field(default_factory=list)
    overdue: list[Flashcard] = field(default_factory=list)
    
    @property
    def total_due(self) -> int:
        return len(self.due_today) + len(self.overdue)


class SpacedRepetitionScheduler:
    """SM-2 based spaced repetition scheduler."""
    
    MIN_EASE = 1.3
    MAX_EASE = 3.0
    INITIAL_INTERVAL = 1.0
    GRADUATING_INTERVAL = 4.0
    
    def __init__(self):
        self._ease_modifiers = {
            ReviewRating.AGAIN: -0.2,
            ReviewRating.HARD: -0.15,
            ReviewRating.GOOD: 0.0,
            ReviewRating.EASY: 0.15,
        }
        self._interval_modifiers = {
            ReviewRating.AGAIN: 0.0,
            ReviewRating.HARD: 1.2,
            ReviewRating.GOOD: 1.0,
            ReviewRating.EASY: 1.3,
        }
    
    def process_review(self, card: Flashcard, rating: ReviewRating) -> Flashcard:
        """Process a review and update the card's schedule."""
        now = datetime.now()
        card.last_reviewed = now
        card.review_count += 1
        
        if rating >= ReviewRating.GOOD:
            card.correct_count += 1
        
        # Update ease factor
        card.ease_factor = max(
            self.MIN_EASE,
            min(self.MAX_EASE, card.ease_factor + self._ease_modifiers[rating])
        )
        
        # Calculate new interval
        if rating == ReviewRating.AGAIN:
            card.interval_days = self.INITIAL_INTERVAL
        elif card.review_count == 1:
            card.interval_days = self.INITIAL_INTERVAL
        elif card.review_count == 2:
            card.interval_days = self.GRADUATING_INTERVAL
        else:
            card.interval_days = card.interval_days * card.ease_factor * self._interval_modifiers[rating]
        
        # Set next review date
        card.next_review = now + timedelta(days=card.interval_days)
        
        return card
    
    def get_schedule(self, cards: list[Flashcard], now: datetime | None = None) -> ReviewSchedule:
        """Get the review schedule for a list of cards."""
        now = now or datetime.now()
        today_end = now.replace(hour=23, minute=59, second=59)
        tomorrow_end = today_end + timedelta(days=1)
        week_end = today_end + timedelta(days=7)
        
        schedule = ReviewSchedule()
        
        for card in cards:
            if card.next_review is None:
                schedule.due_today.append(card)
            elif card.next_review < now:
                schedule.overdue.append(card)
            elif card.next_review <= today_end:
                schedule.due_today.append(card)
            elif card.next_review <= tomorrow_end:
                schedule.due_tomorrow.append(card)
            elif card.next_review <= week_end:
                schedule.due_this_week.append(card)
        
        return schedule
    
    def estimate_retention(self, card: Flashcard, days_since_review: float) -> float:
        """Estimate retention probability using forgetting curve."""
        if card.interval_days == 0:
            return 0.0
        stability = card.interval_days * card.ease_factor
        return 0.9 ** (days_since_review / stability)
    
    def get_optimal_review_time(self, card: Flashcard, target_retention: float = 0.9) -> datetime:
        """Calculate optimal review time for target retention."""
        import math
        stability = card.interval_days * card.ease_factor
        days_until_target = stability * math.log(target_retention) / math.log(0.9)
        base_time = card.last_reviewed or datetime.now()
        return base_time + timedelta(days=days_until_target)
    
    def get_stats(self, cards: list[Flashcard]) -> dict[str, Any]:
        """Get statistics for a collection of cards."""
        if not cards:
            return {"total": 0}
        
        total_reviews = sum(c.review_count for c in cards)
        total_correct = sum(c.correct_count for c in cards)
        avg_ease = sum(c.ease_factor for c in cards) / len(cards)
        
        return {
            "total": len(cards),
            "total_reviews": total_reviews,
            "total_correct": total_correct,
            "accuracy": total_correct / total_reviews if total_reviews else 0,
            "average_ease": avg_ease,
            "mature_cards": sum(1 for c in cards if c.interval_days >= 21),
            "young_cards": sum(1 for c in cards if c.interval_days < 21),
        }
