from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, WebSocket, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import asyncio
import time
import json
import threading
from uuid import uuid4

from ..workflows.workflow_registry import workflow_registry
from ..exceptions import WorkflowNotFoundError, WorkflowValidationError, WorkflowModificationError
from ..services.task_manager import Task, get_task_manager, TaskStatus as Status
from ..services.comfy_client import get_comfy_client
from ..config import settings
from ..logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/generation", tags=["generation"])
task_manager = get_task_manager()
comfy_client = get_comfy_client()

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

class TaskResponse(BaseModel):
    """Response model for task creation and status."""
    task_id: str = Field(..., description="Unique ID for tracking the task")
    status: str = Field(..., description="Current task status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Additional information about the task")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data when task is completed")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "progress": 25,
                "message": "Workflow successfully queued"
            }
        }

@router.post("", summary="Queue a workflow for generation", response_model=TaskResponse)
async def generate(
    request: GenerationRequest = Body(..., description="Generation request parameters")
):
    """
    Queue a workflow for generation.
    Creates a task and queues the workflow with ComfyUI, then returns immediately.
    
    Args:
        request: The generation request containing workflow name and modifications
    
    Returns:
        Task information with ID for tracking progress
    """
    try:
        logger.info(f"Queuing workflow: {request.workflow_name}")
        
        task = task_manager.create_task(request.workflow_name, request.modifications)  # hold entire workflow
                
        try:
            workflow = workflow_registry.get_workflow(request.workflow_name)
            modified_workflow = workflow.update_workflow(request.modifications)
            
            prompt_id = comfy_client.queue_prompt(modified_workflow, task.id)
            logger.info(f"Task queued with Prompt ID: {prompt_id}, Task ID: {task.id}")
            
            task_manager.update_prompt_id(task.id, prompt_id)
            task_manager.update_task_status(task.id, Status.PROCESSING.value)
            
            return {
                "task_id": task.id,
                "status": "queued",
                "progress": 0,
                "message": "Workflow successfully queued. Use the /generation/tasks/{task_id} endpoint to track progress."
            }
            
        except WorkflowNotFoundError:
            logger.error(f"Workflow {request.workflow_name} not found")
            task_manager.update_task_status(
                task.id, 
                Status.FAILED.value, 
                {"error": f"Workflow '{request.workflow_name}' not found"}
            )
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow '{request.workflow_name}' not found"
            )
        except WorkflowModificationError as e:
            logger.error(f"Error modifying workflow: {e}")
            task_manager.update_task_status(
                task.id, 
                Status.FAILED.value, 
                {"error": f"Error modifying workflow: {str(e)}"}
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Error modifying workflow: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error generating output: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating output: {str(e)}"
        )

@router.get("/tasks/{task_id}", summary="Get task status", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Get the current status of a task.
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        Task information including status, progress, and results if completed
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    
    response = {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress
    }
    
    if task.status == Status.COMPLETED.value and task.result:
        response["result"] = task.result
        response["message"] = "Task completed successfully"
    elif task.status == Status.FAILED.value and task.result and "error" in task.result:
        response["message"] = task.result["error"]
    elif task.status == Status.PROCESSING.value:
        response["message"] = "Task is currently processing"
    elif task.status == Status.QUEUED.value:
        response["message"] = "Task is queued and waiting to be processed"
    
    return response 

@router.get("/tasks", summary="List all tasks")
async def list_tasks():
    """
    Get a list of all tasks.
    
    Returns:
        List of all tasks with their status
    """
    tasks = task_manager.get_all_tasks()
    
    return [
        {
            "task_id": task.id,
            "workflow_name": task.workflow_name,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
        for task in tasks
    ] 