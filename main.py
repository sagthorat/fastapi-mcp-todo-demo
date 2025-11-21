"""
FastAPI ToDo List Application
----------------------------
A simple web app to manage a ToDo list with SQLite backend.
Supports CRUD operations and provides interactive API docs.
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

from fastapi_mcp import FastApiMCP

# Database setup (SQLite + SQLAlchemy)
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy model for todos table
class TodoItem(Base):
    __tablename__ = "todos"

    todo_id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    completed = Column(Boolean, default=False)

# Create the database table
Base.metadata.create_all(bind=engine)

# Pydantic models for request and response validation
class TodoBase(BaseModel):
    content: str
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    todo_id: int

    class Config:
        from_attributes = True

# Dependency to manage database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app instance with metadata
app = FastAPI(
    title="Todo API",
    description="A simple Todo API built with FastAPI",
    version="1.0.0"
)

# Root route with HTML response
@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>Welcome to the Todo API server by MCP!</h2>"

# GET route – returns all todos (with optional pagination)
@app.get("/todos/", response_model=List[Todo], operation_id="get_all_todos")
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all todo items with optional pagination."""
    todos = db.query(TodoItem).offset(skip).limit(limit).all()
    return todos

# GET route – returns a single todo by ID
@app.get("/todos/{todo_id}", response_model=Todo, operation_id="get_todo")
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo item by ID."""
    todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

# POST route – create a new todo
@app.post("/todos/", response_model=Todo, operation_id="create_todo")
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    db_todo = TodoItem(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

# PUT route – update an existing todo by ID
@app.put("/todos/{todo_id}", response_model=Todo, operation_id="update_todo")
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    """Update an existing todo item."""
    db_todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo

# DELETE route – delete a todo by ID
@app.delete("/todos/{todo_id}", operation_id="delete_todo")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item."""
    db_todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted successfully"}

#### LOCAL DEPLOYMENT
# if __name__ == "__main__":
#     import uvicorn
#     mcp = FastApiMCP(app, include_operations=[
#         "get_all_todos",
#         "get_todo",
#         "create_todo",
#         "update_todo",
#         "delete_todo"
#     ])
#     mcp.mount_http()
#     uvicorn.run(app, host="127.0.0.1", port=8000)

#### RENDER DEPLOYMENT

import uvicorn
mcp = FastApiMCP(app, include_operations=[
    "get_all_todos",
    "get_todo",
    "create_todo",
    "update_todo",
    "delete_todo"
])
mcp.mount()

