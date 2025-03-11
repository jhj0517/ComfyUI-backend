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
