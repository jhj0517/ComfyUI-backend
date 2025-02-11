from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from .workflows.workflow_registry import workflow_registry
from .exceptions import WorkflowNotFoundError, WorkflowValidationError

app = FastAPI(title="ComfyUI API Wrapper")

class GenerationRequest(BaseModel):
    workflow_name: str
    modifications: Dict[str, Dict[str, Any]]

@app.post("/generate")
async def generate(request: GenerationRequest):
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

@app.get("/workflows/{name}/nodes")
async def get_workflow_nodes(name: str):
    """Get information about nodes in a workflow"""
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 