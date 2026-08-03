"""Unit tests for Agent Engine planning."""
from app.models.goal import Goal
from app.agent_engine.planner import Planner


def test_agent_planner():
    planner = Planner()
    goal = Goal(title="Test Goal", objective="Establish high-level database tests.")
    
    plan = planner.plan_goal(goal)
    assert len(plan) == 2
    assert plan[0]["title"] == "Analyze: Test Goal"
    assert plan[1]["title"] == "Resolve Objective"
