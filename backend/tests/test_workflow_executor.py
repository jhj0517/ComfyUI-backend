import pytest
from pathlib import Path
from app.workflows.base import WorkflowExecutor
from app.exceptions import WorkflowNotFoundError

def test_load_workflow():
    """Test loading a valid workflow file"""
    workflow_path = Path("workflows/basic.json")
    executor = WorkflowExecutor(workflow_path)
    assert executor.workflow is not None
    assert "3" in executor.workflow 
    assert executor.workflow["3"]["class_type"] == "KSampler"

def test_workflow_not_found():
    """Test error when workflow file doesn't exist"""
    with pytest.raises(WorkflowNotFoundError):
        WorkflowExecutor("workflows/nonexistent.json")

def test_get_nodes_by_type():
    """Test finding nodes by their class type"""
    workflow_path = Path("workflows/basic.json")
    executor = WorkflowExecutor(workflow_path)
    
    samplers = executor.get_nodes_by_type("KSampler")
    assert len(samplers) == 1
    assert "3" in samplers 