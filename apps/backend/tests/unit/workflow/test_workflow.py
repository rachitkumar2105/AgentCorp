"""Unit tests for Workflow Engine validation."""
import pytest
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge
from app.workflow.validator import WorkflowValidator
from app.workflow.exceptions import WorkflowValidationError


def test_workflow_validator_missing_start():
    validator = WorkflowValidator()
    
    wf = Workflow(name="Empty Test")
    wf.nodes = [
        WorkflowNode(id=1, node_type="task", name="Node 1")
    ]
    wf.edges = []
    
    with pytest.raises(WorkflowValidationError, match="Workflow is missing a 'start' node"):
        validator.validate_graph(wf)


def test_workflow_validator_duplicate_start():
    validator = WorkflowValidator()
    
    wf = Workflow(name="Duplicate Start Test")
    wf.nodes = [
        WorkflowNode(id=1, node_type="start", name="Start 1"),
        WorkflowNode(id=2, node_type="start", name="Start 2")
    ]
    wf.edges = []
    
    with pytest.raises(WorkflowValidationError, match="Workflow has duplicate 'start' nodes"):
        validator.validate_graph(wf)
