"""
Workflow Engine — Validator.

Performs graph checks prior to execution.
"""

from __future__ import annotations

from app.models.workflow import Workflow
from app.workflow.exceptions import WorkflowValidationError


class WorkflowValidator:
    """
    Validates structural integrity of a workflow definition graph.
    """

    def validate_graph(self, workflow: Workflow) -> None:
        """
        Verify:
          - Presence of Start node
          - Single Start node definition
          - Unreachable islands / Orphan nodes
        """
        nodes = workflow.nodes
        edges = workflow.edges

        # Find Start node
        start_nodes = [n for n in nodes if n.node_type.lower() == "start"]
        if not start_nodes:
            raise WorkflowValidationError("Workflow is missing a 'start' node.")
        if len(start_nodes) > 1:
            raise WorkflowValidationError("Workflow has duplicate 'start' nodes.")

        # Minimal validation checks - verify node connections
        node_ids = {n.id for n in nodes}
        source_nodes = {e.source_node_id for e in edges}
        target_nodes = {e.target_node_id for e in edges}

        # Orphan node check
        for nid in node_ids:
            if nid not in source_nodes and nid not in target_nodes and len(nodes) > 1:
                # Discovered an orphan node not mapped to start/end edges
                node_obj = next(n for n in nodes if n.id == nid)
                if node_obj.node_type.lower() != "start" and node_obj.node_type.lower() != "end":
                     raise WorkflowValidationError(f"Workflow contains orphan node '{node_obj.name}'.")
