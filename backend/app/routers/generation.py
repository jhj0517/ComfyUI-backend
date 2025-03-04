from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, RootModel
from typing import Dict, Any, Optional
from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError, WorkflowValidationError

router = APIRouter(
    prefix="/generate",
    tags=["generation"],
    responses={404: {"description": "Workflow not found"}},
)
class GenerationRequest(BaseModel):
    """Request model for workflow generation."""
    workflow_name: str = Field(..., description="Name of the workflow file to execute")
    modifications: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Json of modifications to apply to the workflow",
        example={
            "node_1": {
                "param1": "value1",
                "param2": 42
            },
            "node_2": {
                "param3": "value3"
            }
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
                "workflow_name": "basic",
                "modifications": {
                    "4": {
                        "text": "a photo of a cat"
                    },
                    "7": {
                        "seed": 42
                    }
                }
            }
        }

@router.post("", summary="Generate output from a workflow", response_model_exclude_none=True)
async def generate(request: GenerationRequest = Body(..., description="Generation request parameters")):
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