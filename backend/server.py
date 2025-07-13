from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
import logging
import uuid
from pathlib import Path
import jwt
import bcrypt
import re

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT configuration
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']
JWT_EXPIRATION_HOURS = int(os.environ['JWT_EXPIRATION_HOURS'])

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

# Password validation function
def validate_password(password: str) -> bool:
    """Validate password strength - minimum 8 characters, at least one uppercase letter, one lowercase letter, and one number"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  # At least one uppercase letter
        return False
    if not re.search(r'[a-z]', password):  # At least one lowercase letter
        return False
    if not re.search(r'[0-9]', password):  # At least one number
        return False
    return True

# Password hashing functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

# JWT token functions
def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Pydantic models
class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"  # Default role

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str  # "mentor" or "student"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: datetime

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

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

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_doc = await db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return User(**user_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
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

# Authentication routes
@api_router.post("/auth/register", response_model=LoginResponse)
async def register(user_data: UserRegistration):
    """Register a new user"""
    # Validate password strength
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number"
        )
    
    # Validate role
    if user_data.role not in ["mentor", "student"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'mentor' or 'student'"
        )
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(user_id, user_data.email)
    
    # Return response (exclude password from user response)
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        created_at=user_doc["created_at"]
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """Login user"""
    # Find user by email
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user_doc["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(user_doc["id"], user_doc["email"])
    
    # Return response (exclude password from user response)
    user_response = UserResponse(
        id=user_doc["id"],
        email=user_doc["email"],
        name=user_doc["name"],
        role=user_doc["role"],
        created_at=user_doc["created_at"]
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "BuildBytes LMS API", "version": "1.0.0"}

@api_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at
    )

@api_router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
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