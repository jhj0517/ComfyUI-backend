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
        self.normalized_nodes = self.normalize_nodes()
    
    def _load_workflow(self) -> Dict[str, Any]:
        """Load workflow from JSON file"""
        try:
            with open(self.workflow_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise WorkflowValidationError(f"Invalid workflow JSON: {str(e)}")

    def normalize_workflow(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert the workflow nodes to a normalized dictionary with string IDs as keys

        For example:
        {
            "1": {
                "id": 1,
                "type": "ComfyUI.node_input_image",
                "inputs": [],
                "outputs": [],
                "widgets_values": []
            },
            "2": {
                "id": 2,
                "type": "ComfyUI.node_input_image",
                "inputs": [],
                "outputs": [],
                "widgets_values": []
            }
        }

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of normalized nodes
        """
        if "nodes" not in self.workflow or not isinstance(self.workflow["nodes"], list):
            raise ValueError("Invalid workflow format: 'nodes' list not found")
            
        normalized = {}
        for node in self.workflow["nodes"]:
            node_id = str(node["id"])
            normalized[node_id] = node
            
        return normalized
        
    def modify_node(self, node_id: str, updates: Dict[str, Any]) -> None:
        """
        Modify a node in the workflow by updating its parameters
        
        Args:
            node_id: The ID of the node to modify
            updates: A dictionary of parameter names and values to update
            
        Raises:
            ValueError: If the node is not found in the workflow
        """
        node = None
        for n in self.workflow["nodes"]:
            if str(n["id"]) == node_id:
                node = n
                break
        
        if node is None:
            raise ValueError(f"Node {node_id} not found in workflow")
        
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
    
    def get_nodes_by_type(self, class_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all nodes of a specific type"""
        return {
            node_id: node 
            for node_id, node in self.normalized_nodes.items() 
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
                if node_id in self.normalized_nodes:
                    node = self.normalized_nodes[node_id]
                    if "widgets_values" in node and isinstance(node["widgets_values"], list):
                        for key, value in updates.items():
                            widget_index = None
                            if "inputs" in node and isinstance(node["inputs"], list):
                                for i, input_def in enumerate(node["inputs"]):
                                    if "widget" in input_def and input_def["widget"].get("name") == key:
                                        widget_index = i
                                        break
                            
                            # Update the widget value if found
                            if widget_index is not None and widget_index < len(node["widgets_values"]):
                                node["widgets_values"][widget_index] = value
        
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