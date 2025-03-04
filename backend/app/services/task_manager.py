import json
import uuid
from datetime import datetime
import redis
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from enum import Enum, auto
import functools

from app.config import settings
from app.logging import get_logger

logger = get_logger()


class TaskStatus(str, Enum):
    """Task status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to a dictionary."""
        return {"status": self.value} 


class Task(BaseModel):
    id: str
    workflow_name: str
    parameters: Dict[str, Any]
    status: TaskStatus
    progress: int = 0  
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    prompt_id: Optional[str] = None
    
    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to a dict suitable for Redis storage"""
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "parameters": json.dumps(self.parameters),
            "status": self.status.value,
            "progress": str(self.progress),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": json.dumps(self.result) if self.result else "",
            "prompt_id": self.prompt_id if self.prompt_id else ""
        }
    
    @classmethod
    def from_redis_dict(cls, data: Dict[str, str]) -> "Task":
        """Create a Task instance from Redis data"""
        return cls(
            id=data["id"],
            workflow_name=data["workflow_name"],
            parameters=json.loads(data["parameters"]) if data["parameters"] else {},
            status=TaskStatus(data["status"]),
            progress=int(data["progress"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            result=json.loads(data["result"]) if data["result"] else None,
            prompt_id=data["prompt_id"] if data["prompt_id"] else None
        )

class TaskManager:
    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = None):
        """Initialize the task manager with Redis
        
        Args:
            redis_url: Optional Redis URL (defaults to settings.REDIS_URL)
            ttl: Optional TTL in seconds (defaults to settings.TASK_TTL_SECONDS)
        """
        self.redis = redis.Redis.from_url(
            redis_url or settings.REDIS_URL, 
            decode_responses=True
        )
        self.ttl = ttl or settings.TASK_TTL_SECONDS
        logger.info(f"Redis for task initialized to {redis_url or settings.REDIS_URL}")
        
    def create_task(self, workflow_name: str, parameters: Dict[str, Any]) -> Task:
        """
        Create a new task and store it in Redis.
        
        Args:
            workflow_name: Name of the workflow
            parameters: Parameters for the workflow
            
        Returns:
            Task: The newly created task
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            id=task_id,
            workflow_name=workflow_name,
            parameters=parameters,
            status=TaskStatus.QUEUED,
            progress=0,
            created_at=now,
            updated_at=now
        )
        
        try:
            key = f"task:{task_id}"
            self.redis.hset(key, mapping=task.to_redis_dict())
            self.redis.expire(key, self.ttl)
            logger.debug(f"Created task {task_id} for workflow {workflow_name}")
            return task
        except redis.RedisError as e:
            logger.error(f"Redis error creating task: {e}")
            return task
    
    def update_task_progress(self, task_id: str, progress: int) -> bool:
        """
        Update a task's progress percentage.
        
        Args:
            task_id: ID of the task to update
            progress: Progress percentage (0-100)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        key = f"task:{task_id}"
        
        try:
            task_data = self.redis.hgetall(key)
            if not task_data:
                logger.warning(f"Task {task_id} not found for progress update")
                return False
                
            task = Task.from_redis_dict(task_data)
            
            task.progress = max(0, min(100, progress))  
            task.updated_at = datetime.now()
            
            self.redis.hset(key, mapping=task.to_redis_dict())
            logger.debug(f"Updated task {task_id} progress to {progress}%")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error updating task progress: {e}")
            return False
        
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status and optionally the result of a task.
        
        Args:
            task_id: Task ID
            status: New task status (string value matching TaskStatus enum)
            result: Optional result data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            task_key = f"task:{task_id}"
            task_data = self.redis.hgetall(task_key)
            
            if not task_data:
                logger.warning(f"Task {task_id} not found for status update")
                return False
            
            status_enum = status if isinstance(status, TaskStatus) else TaskStatus(status)
            
            task_data["status"] = status_enum.value
            task_data["updated_at"] = datetime.now().isoformat()
            
            if result is not None:
                task_data["result"] = json.dumps(result)
            
            self.redis.hset(task_key, mapping=task_data)
            self.redis.expire(task_key, self.ttl)
            
            logger.debug(f"Updated task {task_id} status to {status_enum.value}")
            return True
        except Exception as e:
            logger.error(f"Redis error updating task status: {e}")
            return False
            
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task data by ID
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Optional[Task]: Task object if found, None otherwise
        """
        key = f"task:{task_id}"
        
        try:
            task_data = self.redis.hgetall(key)
            if not task_data:
                logger.debug(f"Task {task_id} not found")
                return None
                
            return Task.from_redis_dict(task_data)
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving task: {e}")
            return None

    def get_task_by_prompt_id(self, prompt_id: str) -> Optional[Task]:
        """Get task by prompt_id
        
        Args:
            prompt_id: The ComfyUI prompt ID to search for
            
        Returns:
            Optional[Task]: Task object if found, None otherwise
        """
        try:
            # Get all task keys
            task_keys = self.redis.keys("task:*")
            
            for key in task_keys:
                task_data = self.redis.hgetall(key)
                if task_data.get("prompt_id") == prompt_id:
                    return Task.from_redis_dict(task_data)
                
            logger.debug(f"No task found with prompt_id {prompt_id}")
            return None
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving task by prompt_id: {e}")
            return None

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from Redis
        
        Returns:
            List[Task]: List of all tasks
        """
        try:
            task_keys = self.redis.keys("task:*")
            tasks = []
            
            for key in task_keys:
                task_data = self.redis.hgetall(key)
                if task_data:
                    tasks.append(Task.from_redis_dict(task_data))
                    
            return tasks
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving all tasks: {e}")
            return []


@functools.lru_cache(maxsize=1)
def get_task_manager(redis_url: Optional[str] = None, ttl: Optional[int] = None) -> TaskManager:
    """
    Get the TaskManager singleton instance.
    
    This function uses lru_cache to ensure only one instance is created.
    
    Args:
        redis_url: Optional Redis URL (defaults to settings.REDIS_URL)
        ttl: Optional TTL in seconds (defaults to settings.TASK_TTL_SECONDS)
    
    Returns:
        TaskManager: The singleton instance
    """
    return TaskManager(redis_url, ttl)

get_task_manager()
