from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from urllib import request
from ..config import settings
from ..exceptions import WorkflowNotFoundError, WorkflowValidationError, WorkflowModificationError

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
        """
        Modify a specific node's inputs in the workflow
        
        For ComfyUI format:
        - Updates widget values for inputs with widgets
        """
        # Find the node with the matching ID
        for node in self.workflow["nodes"]:
            if str(node["id"]) == node_id:
                # Update widget values if they exist
                if "widgets_values" in node and isinstance(node["widgets_values"], list):
                    for key, value in updates.items():
                        # Find the widget index for this key
                        widget_index = None
                        if "inputs" in node and isinstance(node["inputs"], list):
                            for i, input_def in enumerate(node["inputs"]):
                                if "widget" in input_def and input_def["widget"].get("name") == key:
                                    widget_index = i
                                    break
                        
                        # Update the widget value if found
                        if widget_index is not None and widget_index < len(node["widgets_values"]):
                            node["widgets_values"][widget_index] = value
                return
            
        # If we get here, the node wasn't found
        raise ValueError(f"Node {node_id} not found in workflow")
    
    def get_nodes_by_type(self, class_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all nodes of a specific type"""
        return {
            str(node["id"]): node
            for node in self.workflow["nodes"]
            if node.get("type") == class_type
        }
    
    def update_workflow(self, modifications: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Apply modifications to the workflow and return the updated workflow
        
        Args:
            modifications: Dict[node_id, Dict[param_name, value]]
            Example:
            {
                "3": {"seed": 42, "steps": 20},
                "6": {"text": "a photo of a cat"}
            }
            
        Returns:
            Dict[str, Any]: The updated workflow
        """
        workflow = self.workflow.copy()
        
        if modifications:
            for node_id, updates in modifications.items():
                for node in workflow["nodes"]:
                    if str(node["id"]) == node_id:
                        if "widgets_values" in node and isinstance(node["widgets_values"], list):
                            for key, value in updates.items():
                                widget_index = None
                                if "inputs" in node and isinstance(node["inputs"], list):
                                    for i, input_def in enumerate(node["inputs"]):
                                        if "widget" in input_def and input_def["widget"].get("name") == key:
                                            widget_index = i
                                            break
                                
                                if widget_index is not None and widget_index < len(node["widgets_values"]):
                                    node["widgets_values"][widget_index] = value
                        break
        
        return workflow

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
        workflow = self.update_workflow(modifications)
        self._queue_prompt(workflow)
    
    def _queue_prompt(self, prompt: Dict[str, Any]) -> None:
        """Send the workflow to ComfyUI API"""
        data = json.dumps({"prompt": prompt}).encode('utf-8')
        req = request.Request(f"{settings.COMFY_API_URL}/prompt", data=data)
        request.urlopen(req) 