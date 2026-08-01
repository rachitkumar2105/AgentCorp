"""
Agent Engine — Loop Actions Selector.
"""

from __future__ import annotations

from enum import Enum


class ActionType(str, Enum):
    """
    Normalised action type enum keys.
    """

    THINK = "THINK"
    SEARCH_KNOWLEDGE = "SEARCH_KNOWLEDGE"
    SEARCH_MEMORY = "SEARCH_MEMORY"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    RUN_WORKFLOW = "RUN_WORKFLOW"
    ASK_USER = "ASK_USER"
    RESPOND = "RESPOND"
    REFLECT = "REFLECT"
    FINISH = "FINISH"
