from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={404: {"description": "Workflow not found"}},
)

class WorkflowNode(BaseModel):
    """Represents a node in a workflow."""
    class_type: str = Field(..., description="The type of node")
    inputs: Dict[str, Any] = Field(default={}, description="Input parameters for the node")

class WorkflowNodesResponse(BaseModel):
    """Response model for workflow nodes."""
    nodes: Dict[str, WorkflowNode] = Field(..., description="Dictionary of nodes in the workflow")

class WorkflowsListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[str] = Field(..., description="List of available workflow names")

@router.get(
    "/{name}/nodes", 
    summary="Get workflow nodes in normalized format",
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
    Get information about nodes in a specified workflow in normalized format.
    
    - **name**: Name of the workflow to get information about
    """
    try:
        workflow = workflow_registry.get_workflow(name)
        return WorkflowNodesResponse(
            nodes={
                node_id: WorkflowNode(
                    class_type=node["class_type"] if "class_type" in node else "",
                    inputs=node.get("inputs", {})
                )
                for node_id, node in workflow.workflow.items()
            }
        )
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