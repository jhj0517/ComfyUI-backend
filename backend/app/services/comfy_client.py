import json
import urllib.request
import uuid
import websocket
import threading
import logging
import functools
import time

from ..config import settings
from ..logging import get_logger
from ..services.task_manager import get_task_manager, TaskStatus

logger = get_logger()

class ComfyUIClient:
    """Client for interacting with ComfyUI server via WebSocket."""
    
    def __init__(self):
        """Initialize the ComfyUI client with a WebSocket connection to track progress."""
        self.server_address = f"{settings.COMFY_API_HOST}:{settings.COMFY_API_PORT}"
        self.client_id = settings.COMFY_CLIENT_ID or str(uuid.uuid4())
        self.task_manager = get_task_manager()
        
        # Start WebSocket connection in a background thread
        self._start_websocket()
        logger.info(f"Websocket connection started for {self.server_address}")
    
    def _start_websocket(self):
        """Start a WebSocket connection in a background thread."""
        def websocket_thread():
            while True:
                try:
                    ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
                    logger.info(f"Connecting to ComfyUI WebSocket at {ws_url}")
                    
                    # Create WebSocket connection
                    self.ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=self._on_ws_open,
                        on_message=self._on_ws_message,
                        on_error=self._on_ws_error,
                        on_close=self._on_ws_close
                    )
                    
                    self.ws.run_forever()

                    # Fallback to reconnect
                    logger.warning("WebSocket connection closed, reconnecting in 5 seconds...")
                    import time
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Error in WebSocket thread: {e}")
                    import time
                    time.sleep(5)
        
        # Start the thread
        thread = threading.Thread(target=websocket_thread, daemon=True)
        thread.start()
    
    def _on_ws_open(self, ws):
        """Called when WebSocket connection is established."""
        logger.info("WebSocket connection established with ComfyUI")
        
        # Subscribe to events
        ws.send(json.dumps({
            "type": "subscribe",
            "data": {"events": ["progress", "executing", "execution_cached"]}
        }))
    
    def _on_ws_message(self, ws, message):
        """
        Process WebSocket messages and update task status in Redis.
        This is the callback that actually tracks the progress of the workflow.
        """
        try:
            if isinstance(message, str):
                data = json.loads(message)
                
                prompt_id = None
                if data['type'] == 'executing':
                    prompt_id = data['data'].get('prompt_id')
                
                if not prompt_id:
                    return
                
                task = self.task_manager.get_task_by_prompt_id(prompt_id)
                
                if not task:
                    logger.debug(f"No task found for prompt_id {prompt_id}")
                    return
                
                task_id = task.id
                
                if data['type'] == 'progress':
                    msg_data = data['data']
                    progress = int((msg_data['value'] / msg_data['max']) * 100)
                    self.task_manager.update_task_progress(task_id, progress)
                    logger.debug(f"Updated progress for task {task_id}: {progress}%")
                
                elif data['type'] == 'executing' and data['data']['node'] is None:
                    logger.info(f"Execution complete for prompt {prompt_id}, task {task_id}")
                    
                    history = self.get_history(prompt_id)
                    if history and prompt_id in history:
                        self.task_manager.update_task_status(task_id, TaskStatus.COMPLETED.value)
                        logger.info(f"Results processed for task {task_id}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_ws_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closure."""
        logger.warning(f"WebSocket connection closed: {close_msg} (code: {close_status_code})")
    
    def queue_prompt(self, prompt, task_id=None):
        """
        Queue a prompt for execution on ComfyUI.
        
        Args:
            prompt: The workflow to execute
            task_id: Optional task ID for logging purposes
            
        Returns:
            str: Prompt ID from ComfyUI
        """
        # Format the request payload
        payload = {
            "prompt": prompt,
            "client_id": self.client_id
        }
        
        headers = {'Content-Type': 'application/json'}
        data = json.dumps(payload).encode('utf-8')
        
        try:
            # Send the request
            req = urllib.request.Request(
                f"http://{self.server_address}/prompt",
                data=data,
                headers=headers
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())
                prompt_id = result['prompt_id']
                
                if task_id:
                    logger.info(f"Queued prompt {prompt_id} for task {task_id}")
                else:
                    logger.info(f"Queued prompt {prompt_id}")
                    
                return prompt_id
        except Exception as e:
            logger.error(f"Error queueing prompt: {e}")
            raise
    
    def get_history(self, prompt_id):
        """Get execution history for a prompt_id."""
        try:
            with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
                return json.loads(response.read())
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return None

@functools.lru_cache(maxsize=1)
def get_comfy_client() -> ComfyUIClient:
    """
    Get the ComfyUIClient singleton instance.
    
    This function uses lru_cache to ensure only one instance is created.
    
    Returns:
        ComfyUIClient: The singleton instance
    """
    time.sleep(10)
    return ComfyUIClient()

get_comfy_client()
        
