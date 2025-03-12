from pathlib import Path
from typing import Dict, List
import os

from .base import WorkflowExecutor
from ..exceptions import WorkflowNotFoundError
from ..config import comfyui_fastapi_root


class WorkflowRegistry:
    def __init__(self):
        self.workflows: Dict[str, WorkflowExecutor] = {}
        self.workflows_dir = Path(os.path.join(comfyui_fastapi_root, "workflows"))
    
    def load_workflows(self):
        """Load all workflow JSON files from the workflows directory. Reload workflows in case new ones were added"""
        self.workflows.clear()
        for workflow_file in self.workflows_dir.glob("*.json"):
            workflow_name = workflow_file.stem
            self.workflows[workflow_name] = WorkflowExecutor(workflow_file)
    
    def get_workflow(self, name: str) -> WorkflowExecutor:
        """Get a workflow executor by name"""
        if name not in self.workflows:
            self.load_workflows()  
            
        if name not in self.workflows:
            raise WorkflowNotFoundError(f"Workflow '{name}' not found")
            
        return self.workflows[name]
    
    def get_workflow_names(self) -> List[str]:
        return list(self.workflows.keys())

workflow_registry = WorkflowRegistry()
workflow_registry.load_workflows() 