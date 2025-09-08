import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
from ..models import Task
from ..deps import get_session
from sqlmodel import Session

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent = 2
        self._semaphore = asyncio.Semaphore(2)
    
    async def submit_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        task_func: Callable,
        session: Session
    ) -> str:
        """Submit a task for execution"""
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = Task(
            id=task_id,
            type=task_type,
            data=task_data,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        session.add(task)
        session.commit()
        
        # Submit for execution
        asyncio.create_task(self._execute_task(task_id, task_func, session))
        
        return task_id
    
    async def _execute_task(
        self,
        task_id: str,
        task_func: Callable,
        session: Session
    ):
        """Execute a task with resource limits"""
        async with self._semaphore:
            try:
                # Update status to running
                task = session.get(Task, task_id)
                if task:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.utcnow()
                    session.commit()
                
                # Execute the task
                result = await task_func()
                
                # Update status to completed
                task = session.get(Task, task_id)
                if task:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    task.result = result
                    session.commit()
                
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                
                # Update status to failed
                task = session.get(Task, task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.utcnow()
                    task.error = str(e)
                    session.commit()
    
    def get_task_status(self, task_id: str, session: Session) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = session.get(Task, task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error
        }
    
    def cancel_task(self, task_id: str, session: Session) -> bool:
        """Cancel a task"""
        task = session.get(Task, task_id)
        if not task or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        session.commit()
        
        # Cancel the asyncio task if it's running
        if task_id in self._tasks:
            self._tasks[task_id].cancel()
            del self._tasks[task_id]
        
        return True
    
    def cleanup_old_tasks(self, session: Session, days: int = 7):
        """Clean up old completed/failed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_tasks = session.query(Task).filter(
            Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]),
            Task.completed_at < cutoff_date
        ).all()
        
        for task in old_tasks:
            session.delete(task)
        
        session.commit()
        logger.info(f"Cleaned up {len(old_tasks)} old tasks")


# Global task manager instance
task_manager = TaskManager()
