import json
import uuid
from datetime import datetime
import redis
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from app.config import settings

class Task(BaseModel):
    id: str
    workflow_name: str
    parameters: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    
    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to a dict suitable for Redis storage"""
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "parameters": json.dumps(self.parameters),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": json.dumps(self.result) if self.result else None
        }
    
    @classmethod
    def from_redis_dict(cls, data: Dict[str, str]) -> "Task":
        """Create Task from Redis dictionary"""
        parsed = {**data}
        if "parameters" in parsed:
            parsed["parameters"] = json.loads(parsed["parameters"])
        if parsed.get("result"):
            parsed["result"] = json.loads(parsed["result"])
        parsed["created_at"] = datetime.fromisoformat(parsed["created_at"])
        parsed["updated_at"] = datetime.fromisoformat(parsed["updated_at"])
        return cls(**parsed)

class TaskManager:
    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = None):
        """Initialize the task manager with Redis connection
        
        Args:
            redis_url: Optional Redis URL (defaults to settings.REDIS_URL)
            ttl: Optional TTL in seconds (defaults to settings.TASK_TTL_SECONDS)
        """
        self.redis = redis.Redis.from_url(
            redis_url or settings.REDIS_URL, 
            decode_responses=True
        )
        self.ttl = ttl or settings.TASK_TTL_SECONDS
        
    def create_task(self, workflow_name: str, parameters: Dict[str, Any]) -> Task:
        """Create a new task and store it in Redis
        
        Args:
            workflow_name: Name of the workflow to execute
            parameters: Parameters to pass to the workflow
            
        Returns:
            Task: The created task object
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = Task(
            id=task_id,
            workflow_name=workflow_name,
            parameters=parameters,
            status="queued",
            created_at=now,
            updated_at=now
        )
        
        try:
            key = f"task:{task_id}"
            self.redis.hset(key, mapping=task.to_redis_dict())
            self.redis.expire(key, self.ttl)
            return task
        except redis.RedisError as e:
            print(f"Redis error: {e}")
            return task
        
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Update a task's status and optionally store results
        
        Args:
            task_id: ID of the task to update
            status: New status for the task
            result: Optional results data
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        key = f"task:{task_id}"
        
        try:
            task_data = self.redis.hgetall(key)
            if not task_data:
                return False
                
            task = Task.from_redis_dict(task_data)
            
            task.status = status
            task.updated_at = datetime.utcnow()
            if result:
                task.result = result
                
            self.redis.hset(key, mapping=task.to_redis_dict())
            return True
        except redis.RedisError as e:
            print(f"Redis update error: {e}")
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
                return None
                
            return Task.from_redis_dict(task_data)
        except redis.RedisError as e:
            print(f"Redis get error: {e}")
            return None