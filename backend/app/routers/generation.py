from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError, WorkflowValidationError

router = APIRouter(
    prefix="/generate",
    tags=["generation"],
    responses={404: {"description": "Workflow not found"}},
)

class GenerationRequest(BaseModel):
    workflow_name: str
    modifications: Dict[str, Dict[str, Any]]

@router.post("", summary="Generate output from a workflow")
async def generate(request: GenerationRequest):
    """
    Generate output by executing a specified workflow with optional modifications.
    
    - **workflow_name**: Name of the workflow to execute
    - **modifications**: Dictionary of modifications to apply to the workflow
    """
    try:
        workflow = workflow_registry.get_workflow(request.workflow_name)
        workflow.execute(modifications=request.modifications)
        return {"status": "success", "message": "Generation queued"}
    except WorkflowNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkflowValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 