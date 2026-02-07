"""Cost tracking for LLM usage."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date

from pkm_agent.data.database import Database
from pkm_agent.llm.base import Usage

logger = logging.getLogger(__name__)


# Standard pricing (USD per 1M tokens) as of Jan 2026
# This should be configurable in a real system
PRICING = {
    "openai": {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    "anthropic": {
        "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    },
    "ollama": {
        # Local models are free
        "*": {"input": 0.0, "output": 0.0},
    }
}


@dataclass
class CostRecord:
    """Record of LLM cost."""
    id: int
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    timestamp: datetime


class CostTracker:
    """Tracks LLM usage and costs."""

    def __init__(self, db: Database):
        self.db = db
        self._init_table()

    def _init_table(self):
        """Initialize cost table."""
        with self.db._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_costs_timestamp ON llm_costs(timestamp)
            """)

    def track_usage(self, provider: str, model: str, usage: Usage) -> float:
        """Track usage and return cost."""
        cost = self._calculate_cost(provider, model, usage)
        
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO llm_costs (provider, model, tokens_input, tokens_output, cost_usd)
                VALUES (?, ?, ?, ?, ?)
            """, (provider, model, usage.prompt_tokens, usage.completion_tokens, cost))
            
        return cost

    def _calculate_cost(self, provider: str, model: str, usage: Usage) -> float:
        """Calculate cost for usage."""
        if provider == "ollama":
            return 0.0
            
        provider_pricing = PRICING.get(provider, {})
        
        # Exact match
        model_pricing = provider_pricing.get(model)
        
        # Fallback to wildcard or fuzzy match if needed
        if not model_pricing:
            # Try to find base model name
            for key, val in provider_pricing.items():
                if key in model:
                    model_pricing = val
                    break
        
        if not model_pricing:
            # Default to zero if unknown model
            # logger.warning(f"Unknown pricing for {provider}/{model}")
            return 0.0
            
        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output"]
        
        return input_cost + output_cost

    def get_total_cost(self, since: datetime | None = None) -> float:
        """Get total cost since timestamp."""
        with self.db._get_connection() as conn:
            if since:
                row = conn.execute("""
                    SELECT SUM(cost_usd) FROM llm_costs WHERE timestamp >= ?
                """, (since.isoformat(),)).fetchone()
            else:
                row = conn.execute("SELECT SUM(cost_usd) FROM llm_costs").fetchone()
                
            return row[0] if row and row[0] else 0.0

    def get_daily_costs(self, days: int = 30) -> list[dict]:
        """Get daily cost breakdown."""
        with self.db._get_connection() as conn:
            rows = conn.execute("""
                SELECT date(timestamp) as day, SUM(cost_usd) as cost, SUM(tokens_input + tokens_output) as tokens
                FROM llm_costs
                WHERE timestamp >= date('now', ?)
                GROUP BY date(timestamp)
                ORDER BY day DESC
            """, (f"-{days} days",)).fetchall()
            
            return [dict(row) for row in rows]
            
    def check_budget(self, daily_limit: float | None = None) -> bool:
        """Check if daily budget is exceeded. Returns True if within budget."""
        if daily_limit is None or daily_limit <= 0:
            return True
            
        today_start = datetime.combine(date.today(), datetime.min.time())
        spent_today = self.get_total_cost(since=today_start)
        
        return spent_today < daily_limit
