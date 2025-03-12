import pytest
from pathlib import Path
from app.workflows.base import WorkflowExecutor
from app.exceptions import WorkflowNotFoundError
import os

from .conftest import comfyui_fastapi_dir


def test_load_workflow():
    """Test loading a valid workflow file"""
    print("\n\n\n\ncomfyui_fastapi_dir: ", comfyui_fastapi_dir, "\n\n\n\n")
    workflow_path = Path(os.path.join(comfyui_fastapi_dir, "workflows/basic.json"))
    assert workflow_path.exists(), "Workflow file does not exist"

    executor = WorkflowExecutor(workflow_path)
    assert executor.workflow is not None
    assert "3" in executor.workflow 
    assert executor.workflow["3"]["class_type"] == "KSampler"
