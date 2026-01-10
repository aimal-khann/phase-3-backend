from sqlmodel import Session, select
from typing import Optional
import datetime as dt
from ..models.task import Task
from ..db.session import sync_engine

# --- 1. CORE TASK FUNCTIONS ---

def add_task(user_id: str, title: str, description: Optional[str] = None,
             priority: str = "medium", due_date: Optional[str] = None, tags: Optional[str] = None):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        parsed_date = None
        if due_date:
            try: parsed_date = dt.datetime.strptime(due_date, "%Y-%m-%d")
            except: pass
            
        task = Task(
            user_id=user_id, 
            title=title, 
            description=description, 
            priority=priority, 
            due_date=parsed_date, 
            tags=tags, 
            status="pending"
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        
        return {
            "status": "success", 
            "message": f"Task '{title}' added.", 
            "task": {"id": str(task.id), "title": task.title, "status": task.status}
        }

def list_tasks(user_id: str, status: Optional[str] = None):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        query = select(Task).where(Task.user_id == user_id)
        if status and status != "all": 
            query = query.where(Task.status == status)
            
        tasks = session.exec(query).all()
        
        # Serialize tasks to avoid datetime issues
        task_list = []
        for t in tasks:
            task_list.append({
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
            
        return {"status": "success", "tasks": task_list}

def delete_task(user_id: str, task_title: str):
    with Session(sync_engine) as session:
        if not user_id or not task_title: raise ValueError("Missing required fields")
        
        task = session.exec(select(Task).where(Task.user_id == user_id, Task.title == task_title)).first()
        if not task: return {"status": "error", "message": "Task not found."}
        
        session.delete(task)
        session.commit()
        return {"status": "success", "message": f"Task '{task_title}' deleted."}

def update_task_by_title(
    user_id: str, 
    current_title: str, 
    new_title: Optional[str] = None, 
    description: Optional[str] = None, 
    priority: Optional[str] = None, 
    status: Optional[str] = None, 
    due_date: Optional[str] = None, 
    tags: Optional[str] = None
):
    with Session(sync_engine) as session:
        if not user_id or not current_title: return {"status": "error", "message": "Missing fields"}
        
        task = session.exec(select(Task).where(Task.user_id == user_id, Task.title == current_title)).first()
        if not task: return {"status": "error", "message": "Task not found."}
        
        if new_title: task.title = new_title
        if description: task.description = description
        if priority: task.priority = priority
        if status: task.status = status
        if tags: task.tags = tags
        if due_date: 
            try: task.due_date = dt.datetime.strptime(due_date, "%Y-%m-%d")
            except: pass
            
        task.updated_at = dt.datetime.utcnow()
        session.add(task)
        session.commit()
        
        return {"status": "success", "message": f"Task '{current_title}' updated.", "task": {"title": task.title}}

# --- 2. ANALYTICS ---

def get_analytics(user_id: str):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        total = len(tasks)
        completed = len([t for t in tasks if t.status == "completed"])
        pending = len([t for t in tasks if t.status == "pending"])
        
        # Calculate score
        score = int((completed / total * 100) if total > 0 else 0)
        
        return {
            "status": "success", 
            "analytics": {
                "tasks_total": total, 
                "tasks_completed": completed, 
                "tasks_pending": pending,
                "productivity_score": score
            }
        }

# --- 3. BULK ACTIONS (Restored to fix your error) ---

def delete_all_tasks(user_id: str):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        count = len(tasks)
        for t in tasks: session.delete(t)
        session.commit()
        return {"status": "success", "message": f"Deleted {count} tasks."}

def complete_all_tasks(user_id: str):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        count = 0
        for t in tasks: 
            t.status = "completed"
            session.add(t)
            count += 1
        session.commit()
        return {"status": "success", "message": f"Marked {count} tasks completed."}

def mark_all_tasks_incomplete(user_id: str):
    with Session(sync_engine) as session:
        if not user_id: raise ValueError("user_id is required")
        
        tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
        count = 0
        for t in tasks: 
            t.status = "pending"
            session.add(t)
            count += 1
        session.commit()
        return {"status": "success", "message": f"Marked {count} tasks pending."}