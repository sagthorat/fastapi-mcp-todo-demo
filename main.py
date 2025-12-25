
"""
FastAPI ToDo List Application
----------------------------
A simple web app to manage a ToDo list with SQLite backend.
Supports CRUD operations and provides interactive API docs.
"""

# Import required libraries and modules

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel


# Import MCP integration for FastAPI (for deployment/management)
from fastapi_mcp import FastApiMCP


# Database setup (SQLite + SQLAlchemy)
# ------------------------------------
# - Uses SQLite for local file-based storage
# - SQLAlchemy ORM for database interaction
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy model for the 'todos' table
class TodoItem(Base):
    __tablename__ = "todos"

    todo_id = Column(Integer, primary_key=True, index=True)  # Unique ID for each todo
    content = Column(String, index=True)                     # The todo text/content
    completed = Column(Boolean, default=False)               # Completion status


# Create the database table if it doesn't exist
Base.metadata.create_all(bind=engine)


# Pydantic models for request and response validation
class TodoBase(BaseModel):
    content: str                      # The todo text/content
    completed: bool = False           # Completion status (default: False)

class TodoCreate(TodoBase):
    pass  # Inherits all fields from TodoBase for creation

class Todo(TodoBase):
    todo_id: int                      # Unique ID for each todo

    class Config:
        from_attributes = True        # Allows ORM mode for SQLAlchemy integration


# Dependency to manage database sessions
# Ensures each request gets its own DB session and closes it after use
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI app instance with metadata for docs
app = FastAPI(
    title="Todo API",
    description="A simple Todo API built with FastAPI",
    version="1.0.0"
)


# Root route with HTML response (welcome page)
@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>Welcome to the Todo API server by MCP!</h2>"


# GET /todos/ - Returns all todos (with optional pagination)
@app.get("/todos/", response_model=List[Todo], operation_id="get_all_todos")
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all todo items with optional pagination."""
    todos = db.query(TodoItem).offset(skip).limit(limit).all()
    return todos


# GET /todos/{todo_id} - Returns a single todo by its ID
@app.get("/todos/{todo_id}", response_model=Todo, operation_id="get_todo")
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo item by ID."""
    todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# POST /todos/ - Create a new todo item
@app.post("/todos/", response_model=Todo, operation_id="create_todo")
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    db_todo = TodoItem(**todo.model_dump())  # Convert Pydantic model to SQLAlchemy model
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)  # Refresh to get the new ID
    return db_todo


# PUT /todos/{todo_id} - Update an existing todo by its ID
@app.put("/todos/{todo_id}", response_model=Todo, operation_id="update_todo")
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    """Update an existing todo item."""
    db_todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Update fields from the request
    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo


# DELETE /todos/{todo_id} - Delete a todo by its ID
@app.delete("/todos/{todo_id}", operation_id="delete_todo")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item."""
    db_todo = db.query(TodoItem).filter(TodoItem.todo_id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted successfully"}


#### DEPLOYMENT SECTION ####
# Uncomment the following block for local development/testing:
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

# For Render or production deployment, use the following:
import uvicorn
mcp = FastApiMCP(app, include_operations=[
    "get_all_todos",
    "get_todo",
    "create_todo",
    "update_todo",
    "delete_todo"
])
mcp.mount()

