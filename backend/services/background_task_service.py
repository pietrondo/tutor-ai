import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    STUDY_PLAN_GENERATION = "study_plan_generation"
    PDF_INDEXING = "pdf_indexing"
    SLIDE_GENERATION = "slide_generation"

class BackgroundTask(BaseModel):
    id: str
    task_type: TaskType
    status: TaskStatus
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    course_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BackgroundTaskService:
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.tasks_file = "data/background_tasks.json"
        self._load_tasks()
        logger.info("Background Task Service initialized")

    def _load_tasks(self):
        """Load existing tasks from file"""
        try:
            import os
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = BackgroundTask(**task_data)
                        # Convert completed tasks back from string if needed
                        if isinstance(task.created_at, str):
                            task.created_at = datetime.fromisoformat(task.created_at)
                        if task.started_at and isinstance(task.started_at, str):
                            task.started_at = datetime.fromisoformat(task.started_at)
                        if task.completed_at and isinstance(task.completed_at, str):
                            task.completed_at = datetime.fromisoformat(task.completed_at)
                        self.tasks[task.id] = task
                logger.info(f"Loaded {len(self.tasks)} existing tasks")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")

    def _save_tasks(self):
        """Save tasks to file"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            data = {
                'tasks': [task.dict() for task in self.tasks.values()]
            }
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")

    def create_task(self, task_type: TaskType, course_id: Optional[str] = None,
                   user_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Create a new background task"""
        task_id = str(uuid.uuid4())
        task = BackgroundTask(
            id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            course_id=course_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Created background task {task_id} of type {task_type}")
        return task_id

    def update_task_status(self, task_id: str, status: TaskStatus, progress: float = None,
                          message: str = "", result: Dict[str, Any] = None, error: str = None):
        """Update task status and progress"""
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return False

        task = self.tasks[task_id]
        task.status = status

        if progress is not None:
            task.progress = min(100.0, max(0.0, progress))

        if message:
            task.message = message

        if result:
            task.result = result

        if error:
            task.error = error

        # Update timestamps
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()

        self._save_tasks()
        logger.info(f"Updated task {task_id}: status={status}, progress={task.progress}%")
        return True

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_tasks_by_course(self, course_id: str) -> List[BackgroundTask]:
        """Get all tasks for a specific course"""
        return [task for task in self.tasks.values() if task.course_id == course_id]

    def get_tasks_by_type(self, task_type: TaskType) -> List[BackgroundTask]:
        """Get all tasks of a specific type"""
        return [task for task in self.tasks.values() if task.task_type == task_type]

    def get_running_tasks(self) -> List[BackgroundTask]:
        """Get all currently running tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task.status != TaskStatus.RUNNING:
            return False

        # Cancel the asyncio task if it exists
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        self.update_task_status(task_id, TaskStatus.CANCELLED, message="Task cancelled by user")
        return True

    def cleanup_old_tasks(self, days: int = 7):
        """Remove tasks older than specified days"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        tasks_to_remove = []

        for task_id, task in self.tasks.items():
            if task.completed_at and task.completed_at.timestamp() < cutoff_date:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

        if tasks_to_remove:
            self._save_tasks()
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

    async def run_background_task(self, task_id: str, coro):
        """Run a task in the background"""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return

        task = self.tasks[task_id]

        try:
            # Update status to running
            self.update_task_status(task_id, TaskStatus.RUNNING, progress=0.0, message="Starting task...")

            # Run the coroutine
            result = await coro

            # Mark as completed
            self.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                progress=100.0,
                message="Task completed successfully",
                result=result
            )

        except asyncio.CancelledError:
            self.update_task_status(task_id, TaskStatus.CANCELLED, message="Task was cancelled")
        except Exception as e:
            logger.error(f"Background task {task_id} failed: {e}")
            self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                message=f"Task failed: {str(e)}",
                error=str(e)
            )
        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def submit_task(self, task_id: str, coro):
        """Submit a task to run in the background"""
        if task_id not in self.tasks:
            return False

        # Create and store the asyncio task
        asyncio_task = asyncio.create_task(self.run_background_task(task_id, coro))
        self.running_tasks[task_id] = asyncio_task

        logger.info(f"Submitted background task {task_id}")
        return True

# Global instance
background_task_service = BackgroundTaskService()