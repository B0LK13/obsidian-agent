"""Tests for cost tracking."""

import pytest
from pkm_agent.llm.cost_tracker import CostTracker, PRICING
from pkm_agent.llm.base import Usage

def test_cost_calculation(test_database):
    """Test calculating costs."""
    tracker = CostTracker(test_database)
    
    # Test OpenAI GPT-4o
    usage = Usage(prompt_tokens=1000, completion_tokens=1000)
    cost = tracker._calculate_cost("openai", "gpt-4o", usage)
    
    # 1000 input / 1M * 5.00 = 0.005
    # 1000 output / 1M * 15.00 = 0.015
    # Total = 0.02
    assert abs(cost - 0.02) < 0.0001
    
    # Test Ollama (Free)
    cost = tracker._calculate_cost("ollama", "llama3", usage)
    assert cost == 0.0

def test_tracking(test_database):
    """Test tracking usage."""
    tracker = CostTracker(test_database)
    usage = Usage(prompt_tokens=1000, completion_tokens=1000)
    
    tracker.track_usage("openai", "gpt-4o-mini", usage)
    
    total = tracker.get_total_cost()
    assert total > 0
    
    daily = tracker.get_daily_costs()
    assert len(daily) == 1
    assert daily[0]["tokens"] == 2000

def test_budget_check(test_database):
    """Test budget enforcement."""
    tracker = CostTracker(test_database)
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=0)
    
    # Spend $5 (1M tokens * $5)
    tracker.track_usage("openai", "gpt-4o", usage)
    
    # Check limit $1
    assert not tracker.check_budget(1.0)
    
    # Check limit $10
    assert tracker.check_budget(10.0)
