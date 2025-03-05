from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={404: {"description": "Workflow not found"}},
)

class ComfyUIWorkflowNode(BaseModel):
    """Represents a node in a ComfyUI workflow."""
    id: int = Field(..., description="Node ID")
    type: str = Field(..., description="Node type")
    inputs: List[Dict[str, Any]] = Field(default=[], description="Node inputs")
    outputs: List[Dict[str, Any]] = Field(default=[], description="Node outputs")
    widgets_values: Optional[List[Any]] = Field(None, description="Widget values if any")

class WorkflowNodesResponse(BaseModel):
    """Response model for workflow nodes."""
    nodes: Dict[str, ComfyUIWorkflowNode] = Field(
        ..., description="Dictionary of nodes in the workflow"
    )

class WorkflowsListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[str] = Field(..., description="List of available workflow names")

@router.get(
    "/{name}/nodes", 
    summary="Get workflow nodes",
    response_model=WorkflowNodesResponse,
    responses={
        200: {"description": "Successful response with workflow nodes"},
        404: {"description": "Workflow not found"}
    }
)
async def get_workflow_nodes(
    name: str = Path(..., description="Name of the workflow to get information about")
):
    """
    Get information about nodes in a specified workflow.
    
    - **name**: Name of the workflow to get information about
    """
    try:
        workflow = workflow_registry.get_workflow(name)
        
        nodes = {}
        for node in workflow.workflow["nodes"]:
            nodes[str(node["id"])] = node
        
        return WorkflowNodesResponse(nodes=nodes)
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "", 
    summary="List available workflows",
    response_model=WorkflowsListResponse,
    responses={
        200: {"description": "Successful response with list of workflows"}
    }
)
async def list_workflows():
    """
    Get a list of all available workflows.
    """
    workflows = workflow_registry.get_workflow_names()
    return WorkflowsListResponse(workflows=workflows)