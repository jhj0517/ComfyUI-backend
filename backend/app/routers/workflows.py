from fastapi import APIRouter, HTTPException
from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={404: {"description": "Workflow not found"}},
)

@router.get("/{name}/nodes", summary="Get workflow nodes")
async def get_workflow_nodes(name: str):
    """
    Get information about nodes in a specified workflow.
    
    - **name**: Name of the workflow to get information about
    """
    try:
        workflow = workflow_registry.get_workflow(name)
        return {
            "nodes": {
                node_id: {
                    "class_type": node["class_type"],
                    "inputs": node.get("inputs", {})
                }
                for node_id, node in workflow.workflow.items()
            }
        }
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("", summary="List available workflows")
async def list_workflows():
    """
    Get a list of all available workflows.
    """
    workflows = workflow_registry.get_workflow_names()
    return {"workflows": workflows} 