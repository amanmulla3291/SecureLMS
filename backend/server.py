from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import logging
import uuid
from pathlib import Path
import json
from jose import JWTError, jwt
import requests


# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Auth0 configuration
AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']
AUTH0_AUDIENCE = os.environ['AUTH0_AUDIENCE']
AUTH0_CLIENT_ID = os.environ['AUTH0_CLIENT_ID']

# Create FastAPI app
app = FastAPI(title="BuildBytes LMS API")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str  # "mentor" or "student"
    auth0_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SubjectCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    color: Optional[str] = "#3B82F6"  # Default blue color
    icon: Optional[str] = None
    created_by: str  # mentor user id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SubjectCategoryCreate(BaseModel):
    name: str
    description: str
    color: Optional[str] = "#3B82F6"
    icon: Optional[str] = None

class SubjectCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    subject_category_id: str
    assigned_students: List[str] = []
    created_by: str  # mentor user id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectCreate(BaseModel):
    title: str
    description: str
    subject_category_id: str
    assigned_students: List[str] = []

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    description: str
    deadline: Optional[datetime] = None
    status: str = "not_started"  # not_started, in_progress, submitted, approved, needs_revision
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: str
    deadline: Optional[datetime] = None

# Auth0 token verification
async def get_current_user(token: str = Depends(security)):
    try:
        # Get the signing key from Auth0
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks_response = requests.get(jwks_url)
        jwks = jwks_response.json()
        
        # Decode the token without verification first to get the header
        unverified_header = jwt.get_unverified_header(token.credentials)
        
        # Find the correct key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        
        if rsa_key:
            # Verify and decode the token
            payload = jwt.decode(
                token.credentials,
                rsa_key,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            
            # Get user info from database or create if not exists
            user_doc = await db.users.find_one({"auth0_id": payload["sub"]})
            
            if not user_doc:
                # Create new user from Auth0 data
                user_data = {
                    "id": str(uuid.uuid4()),
                    "email": payload.get("email", ""),
                    "name": payload.get("name", ""),
                    "role": "student",  # Default role
                    "auth0_id": payload["sub"],
                    "created_at": datetime.utcnow()
                }
                await db.users.insert_one(user_data)
                user_doc = user_data
            
            return User(**user_doc)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Helper function to check if user is mentor
async def require_mentor(current_user: User = Depends(get_current_user)):
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can access this endpoint"
        )
    return current_user

# API Routes
@api_router.get("/")
async def root():
    return {"message": "BuildBytes LMS API", "version": "1.0.0"}

@api_router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str = Form(...),
    current_user: User = Depends(require_mentor)
):
    """Update user role (mentor only)"""
    if role not in ["mentor", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    
    return {"message": f"User role updated to {role}"}

# Subject Categories CRUD
@api_router.get("/subject-categories", response_model=List[SubjectCategory])
async def get_subject_categories(current_user: User = Depends(get_current_user)):
    """Get all subject categories"""
    categories = await db.subject_categories.find().to_list(1000)
    return [SubjectCategory(**category) for category in categories]

@api_router.post("/subject-categories", response_model=SubjectCategory)
async def create_subject_category(
    category: SubjectCategoryCreate,
    current_user: User = Depends(require_mentor)
):
    """Create a new subject category (mentor only)"""
    category_data = category.dict()
    category_data["id"] = str(uuid.uuid4())
    category_data["created_by"] = current_user.id
    category_data["created_at"] = datetime.utcnow()
    
    category_obj = SubjectCategory(**category_data)
    await db.subject_categories.insert_one(category_obj.dict())
    
    return category_obj

@api_router.get("/subject-categories/{category_id}", response_model=SubjectCategory)
async def get_subject_category(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific subject category"""
    category = await db.subject_categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Subject category not found")
    
    return SubjectCategory(**category)

@api_router.put("/subject-categories/{category_id}", response_model=SubjectCategory)
async def update_subject_category(
    category_id: str,
    category_update: SubjectCategoryUpdate,
    current_user: User = Depends(require_mentor)
):
    """Update a subject category (mentor only)"""
    category = await db.subject_categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Subject category not found")
    
    # Check if current user created this category
    if category["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update categories you created")
    
    # Update only provided fields
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    
    await db.subject_categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    
    updated_category = await db.subject_categories.find_one({"id": category_id})
    return SubjectCategory(**updated_category)

@api_router.delete("/subject-categories/{category_id}")
async def delete_subject_category(
    category_id: str,
    current_user: User = Depends(require_mentor)
):
    """Delete a subject category (mentor only)"""
    category = await db.subject_categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Subject category not found")
    
    # Check if current user created this category
    if category["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete categories you created")
    
    # Check if category has associated projects
    projects = await db.projects.find({"subject_category_id": category_id}).to_list(1)
    if projects:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with associated projects"
        )
    
    await db.subject_categories.delete_one({"id": category_id})
    return {"message": "Subject category deleted successfully"}

# Projects CRUD
@api_router.get("/projects", response_model=List[Project])
async def get_projects(
    subject_category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get projects (filtered by subject category if provided)"""
    filter_dict = {}
    if subject_category_id:
        filter_dict["subject_category_id"] = subject_category_id
    
    # Students can only see projects assigned to them
    if current_user.role == "student":
        filter_dict["assigned_students"] = current_user.id
    
    projects = await db.projects.find(filter_dict).to_list(1000)
    return [Project(**project) for project in projects]

@api_router.post("/projects", response_model=Project)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(require_mentor)
):
    """Create a new project (mentor only)"""
    # Verify subject category exists
    category = await db.subject_categories.find_one({"id": project.subject_category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Subject category not found")
    
    project_data = project.dict()
    project_data["id"] = str(uuid.uuid4())
    project_data["created_by"] = current_user.id
    project_data["created_at"] = datetime.utcnow()
    
    project_obj = Project(**project_data)
    await db.projects.insert_one(project_obj.dict())
    
    return project_obj

# Tasks CRUD
@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get tasks (filtered by project if provided)"""
    filter_dict = {}
    if project_id:
        filter_dict["project_id"] = project_id
    
    tasks = await db.tasks.find(filter_dict).to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(require_mentor)
):
    """Create a new task (mentor only)"""
    # Verify project exists
    project = await db.projects.find_one({"id": task.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task_data = task.dict()
    task_data["id"] = str(uuid.uuid4())
    task_data["created_at"] = datetime.utcnow()
    
    task_obj = Task(**task_data)
    await db.tasks.insert_one(task_obj.dict())
    
    return task_obj

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    if current_user.role == "mentor":
        # Mentor stats
        total_categories = await db.subject_categories.count_documents({})
        total_projects = await db.projects.count_documents({})
        total_students = await db.users.count_documents({"role": "student"})
        
        return {
            "total_categories": total_categories,
            "total_projects": total_projects,
            "total_students": total_students,
            "user_role": "mentor"
        }
    else:
        # Student stats
        assigned_projects = await db.projects.count_documents({"assigned_students": current_user.id})
        completed_tasks = await db.tasks.count_documents({"status": "approved"})
        
        return {
            "assigned_projects": assigned_projects,
            "completed_tasks": completed_tasks,
            "user_role": "student"
        }

# Include the API router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)