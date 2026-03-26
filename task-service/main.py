from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import os, uuid

app = FastAPI(title="Task Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://taskuser:taskpass@localhost:5432/taskflow")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title       = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(String, default="pending")
    assigned_to = Column(String, nullable=True)
    created_by  = Column(String, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    created_by: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class AssignRequest(BaseModel):
    assigned_to: str

@app.get("/health")
def health():
    return {"status": "task-service running"}

@app.post("/tasks", status_code=201)
def create_task(req: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=req.title,
        description=req.description,
        created_by=req.created_by
    )
    db.add(task)
    db.commit()
    return {"message": "Task created", "task_id": task.id}

@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [{"id": t.id, "title": t.title, "status": t.status,
             "assigned_to": t.assigned_to, "created_by": t.created_by} for t in tasks]

@app.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": task.id, "title": task.title, "description": task.description,
            "status": task.status, "assigned_to": task.assigned_to}

@app.put("/tasks/{task_id}")
def update_task(task_id: str, req: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if req.title:       task.title = req.title
    if req.description: task.description = req.description
    if req.status:      task.status = req.status
    db.commit()
    return {"message": "Task updated successfully"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

@app.post("/tasks/{task_id}/assign")
def assign_task(task_id: str, req: AssignRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.assigned_to = req.assigned_to
    task.status = "assigned"
    db.commit()
    return {"message": f"Task assigned to {req.assigned_to}"}
