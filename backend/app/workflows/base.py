from typing import Dict, Any, Optional
import json
from pathlib import Path
from urllib import request
from ..config import settings
from ..exceptions import WorkflowNotFoundError, WorkflowValidationError

class WorkflowExecutor:
    def __init__(self, workflow_path: str):
        self.workflow_path = Path(workflow_path)
        if not self.workflow_path.exists():
            raise WorkflowNotFoundError(f"Workflow file not found: {workflow_path}")
        
        self.workflow = self._load_workflow()
    
    def _load_workflow(self) -> Dict[str, Any]:
        """Load workflow from JSON file"""
        try:
            with open(self.workflow_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise WorkflowValidationError(f"Invalid workflow JSON: {str(e)}")

    def modify_node(self, node_id: str, updates: Dict[str, Any]) -> None:
        """Modify a specific node's inputs in the workflow"""
        if node_id not in self.workflow:
            raise ValueError(f"Node {node_id} not found in workflow")
        
        node = self.workflow[node_id]
        if "inputs" not in node:
            node["inputs"] = {}
        
        node["inputs"].update(updates)
    
    def get_nodes_by_type(self, class_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all nodes of a specific type"""
        return {
            node_id: node 
            for node_id, node in self.workflow.items() 
            if node.get("class_type") == class_type
        }
    
    def execute(self, modifications: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Execute the workflow with given modifications
        
        Args:
            modifications: Dict[node_id, Dict[param_name, value]]
            Example:
            {
                "3": {"seed": 42, "steps": 20},
                "6": {"text": "a photo of a cat"}
            }
        """
        workflow = self.workflow.copy()
        
        if modifications:
            for node_id, updates in modifications.items():
                if node_id in workflow:
                    if "inputs" not in workflow[node_id]:
                        workflow[node_id]["inputs"] = {}
                    workflow[node_id]["inputs"].update(updates)
        
        self._queue_prompt(workflow)
    
    def _queue_prompt(self, prompt: Dict[str, Any]) -> None:
        """Send the workflow to ComfyUI API"""
        data = json.dumps({"prompt": prompt}).encode('utf-8')
        req = request.Request(f"{settings.COMFY_API_URL}/prompt", data=data)
        request.urlopen(req) 