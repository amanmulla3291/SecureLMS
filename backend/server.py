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

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None

class Submission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    student_id: str
    file_name: Optional[str] = None
    file_data: Optional[str] = None  # Base64 encoded file data
    file_type: Optional[str] = None
    text_content: Optional[str] = None
    feedback: Optional[str] = None
    status: str = "submitted"  # submitted, approved, needs_revision
    grade: Optional[float] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # mentor user id

class SubmissionCreate(BaseModel):
    task_id: str
    file_name: Optional[str] = None
    file_data: Optional[str] = None
    file_type: Optional[str] = None
    text_content: Optional[str] = None

class SubmissionUpdate(BaseModel):
    feedback: Optional[str] = None
    status: Optional[str] = None
    grade: Optional[float] = None

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_category_id: str
    title: str
    description: str
    resource_type: str  # "link", "pdf", "document", "video"
    url: Optional[str] = None
    file_name: Optional[str] = None
    file_data: Optional[str] = None  # Base64 encoded file data
    file_type: Optional[str] = None
    created_by: str  # mentor user id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceCreate(BaseModel):
    subject_category_id: str
    title: str
    description: str
    resource_type: str
    url: Optional[str] = None
    file_name: Optional[str] = None
    file_data: Optional[str] = None
    file_type: Optional[str] = None

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    url: Optional[str] = None
    file_name: Optional[str] = None
    file_data: Optional[str] = None
    file_type: Optional[str] = None

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: str
    project_id: Optional[str] = None
    subject: str
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    recipient_id: str
    project_id: Optional[str] = None
    subject: str
    content: str

class MessageUpdate(BaseModel):
    is_read: bool

class Certificate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    project_id: str
    student_name: str
    project_title: str
    subject_category_name: str
    completion_date: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str  # mentor user id
    certificate_data: Optional[str] = None  # Base64 encoded PDF data

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

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: User = Depends(require_mentor)
):
    """Update a task (mentor only)"""
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in task_update.dict().items() if v is not None}
    
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": update_data}
    )
    
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**updated_task)

@api_router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_mentor)
):
    """Delete a task (mentor only)"""
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.tasks.delete_one({"id": task_id})
    return {"message": "Task deleted successfully"}

# Submissions CRUD
@api_router.get("/submissions", response_model=List[Submission])
async def get_submissions(
    task_id: Optional[str] = None,
    student_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get submissions"""
    filter_dict = {}
    
    # Role-based filtering
    if current_user.role == "student":
        filter_dict["student_id"] = current_user.id
    elif student_id:
        filter_dict["student_id"] = student_id
    
    if task_id:
        filter_dict["task_id"] = task_id
    
    submissions = await db.submissions.find(filter_dict).to_list(1000)
    return [Submission(**submission) for submission in submissions]

@api_router.post("/submissions", response_model=Submission)
async def create_submission(
    submission: SubmissionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new submission"""
    # Verify task exists
    task = await db.tasks.find_one({"id": submission.task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Students can only submit for themselves
    if current_user.role == "student":
        submission_data = submission.dict()
        submission_data["id"] = str(uuid.uuid4())
        submission_data["student_id"] = current_user.id
        submission_data["submitted_at"] = datetime.utcnow()
        
        submission_obj = Submission(**submission_data)
        await db.submissions.insert_one(submission_obj.dict())
        
        return submission_obj
    else:
        raise HTTPException(status_code=403, detail="Only students can create submissions")

@api_router.put("/submissions/{submission_id}", response_model=Submission)
async def update_submission(
    submission_id: str,
    submission_update: SubmissionUpdate,
    current_user: User = Depends(require_mentor)
):
    """Update a submission (mentor only - for feedback and grading)"""
    submission = await db.submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in submission_update.dict().items() if v is not None}
    update_data["reviewed_at"] = datetime.utcnow()
    update_data["reviewed_by"] = current_user.id
    
    await db.submissions.update_one(
        {"id": submission_id},
        {"$set": update_data}
    )
    
    updated_submission = await db.submissions.find_one({"id": submission_id})
    return Submission(**updated_submission)

@api_router.get("/submissions/{submission_id}", response_model=Submission)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific submission"""
    submission = await db.submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Students can only view their own submissions
    if current_user.role == "student" and submission["student_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Submission(**submission)

# Resources CRUD
@api_router.get("/resources", response_model=List[Resource])
async def get_resources(
    subject_category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get resources"""
    filter_dict = {}
    if subject_category_id:
        filter_dict["subject_category_id"] = subject_category_id
    
    resources = await db.resources.find(filter_dict).to_list(1000)
    return [Resource(**resource) for resource in resources]

@api_router.post("/resources", response_model=Resource)
async def create_resource(
    resource: ResourceCreate,
    current_user: User = Depends(require_mentor)
):
    """Create a new resource (mentor only)"""
    # Verify subject category exists
    category = await db.subject_categories.find_one({"id": resource.subject_category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Subject category not found")
    
    resource_data = resource.dict()
    resource_data["id"] = str(uuid.uuid4())
    resource_data["created_by"] = current_user.id
    resource_data["created_at"] = datetime.utcnow()
    
    resource_obj = Resource(**resource_data)
    await db.resources.insert_one(resource_obj.dict())
    
    return resource_obj

@api_router.put("/resources/{resource_id}", response_model=Resource)
async def update_resource(
    resource_id: str,
    resource_update: ResourceUpdate,
    current_user: User = Depends(require_mentor)
):
    """Update a resource (mentor only)"""
    resource = await db.resources.find_one({"id": resource_id})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check if current user created this resource
    if resource["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update resources you created")
    
    # Update only provided fields
    update_data = {k: v for k, v in resource_update.dict().items() if v is not None}
    
    await db.resources.update_one(
        {"id": resource_id},
        {"$set": update_data}
    )
    
    updated_resource = await db.resources.find_one({"id": resource_id})
    return Resource(**updated_resource)

@api_router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: str,
    current_user: User = Depends(require_mentor)
):
    """Delete a resource (mentor only)"""
    resource = await db.resources.find_one({"id": resource_id})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check if current user created this resource
    if resource["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete resources you created")
    
    await db.resources.delete_one({"id": resource_id})
    return {"message": "Resource deleted successfully"}

# Messages CRUD
@api_router.get("/messages", response_model=List[Message])
async def get_messages(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get messages"""
    filter_dict = {
        "$or": [
            {"sender_id": current_user.id},
            {"recipient_id": current_user.id}
        ]
    }
    
    if project_id:
        filter_dict["project_id"] = project_id
    
    messages = await db.messages.find(filter_dict).to_list(1000)
    return [Message(**message) for message in messages]

@api_router.post("/messages", response_model=Message)
async def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new message"""
    # Verify recipient exists
    recipient = await db.users.find_one({"id": message.recipient_id})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Verify project exists if specified
    if message.project_id:
        project = await db.projects.find_one({"id": message.project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    message_data = message.dict()
    message_data["id"] = str(uuid.uuid4())
    message_data["sender_id"] = current_user.id
    message_data["created_at"] = datetime.utcnow()
    
    message_obj = Message(**message_data)
    await db.messages.insert_one(message_obj.dict())
    
    return message_obj

@api_router.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a message (mark as read)"""
    message = await db.messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only recipient can mark message as read
    if message["recipient_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update messages sent to you")
    
    # Update only provided fields
    update_data = {k: v for k, v in message_update.dict().items() if v is not None}
    
    await db.messages.update_one(
        {"id": message_id},
        {"$set": update_data}
    )
    
    updated_message = await db.messages.find_one({"id": message_id})
    return Message(**updated_message)

@api_router.get("/messages/{message_id}", response_model=Message)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific message"""
    message = await db.messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender or recipient can view message
    if message["sender_id"] != current_user.id and message["recipient_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Message(**message)

@api_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a message"""
    message = await db.messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender can delete message
    if message["sender_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete messages you sent")
    
    await db.messages.delete_one({"id": message_id})
    return {"message": "Message deleted successfully"}

# Progress tracking endpoints
@api_router.get("/progress/{student_id}")
async def get_student_progress(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get student progress"""
    # Students can only view their own progress
    if current_user.role == "student" and student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get assigned projects for student
    projects = await db.projects.find({"assigned_students": student_id}).to_list(1000)
    
    progress_data = []
    for project in projects:
        # Get tasks for this project
        tasks = await db.tasks.find({"project_id": project["id"]}).to_list(1000)
        
        # Calculate completion percentage
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task["status"] == "approved"])
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get latest submission
        latest_submission = await db.submissions.find_one(
            {"student_id": student_id, "task_id": {"$in": [task["id"] for task in tasks]}},
            sort=[("submitted_at", -1)]
        )
        
        progress_data.append({
            "project_id": project["id"],
            "project_title": project["title"],
            "subject_category_id": project["subject_category_id"],
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": completion_percentage,
            "last_submission_date": latest_submission["submitted_at"] if latest_submission else None
        })
    
    return {"student_id": student_id, "progress": progress_data}

@api_router.get("/progress/overview")
async def get_progress_overview(current_user: User = Depends(require_mentor)):
    """Get overview of all students' progress (mentor only)"""
    students = await db.users.find({"role": "student"}).to_list(1000)
    
    overview_data = []
    for student in students:
        # Get assigned projects for student
        projects = await db.projects.find({"assigned_students": student["id"]}).to_list(1000)
        
        total_projects = len(projects)
        completed_projects = 0
        
        for project in projects:
            # Get tasks for this project
            tasks = await db.tasks.find({"project_id": project["id"]}).to_list(1000)
            
            # Check if all tasks are completed
            if tasks and all(task["status"] == "approved" for task in tasks):
                completed_projects += 1
        
        overview_data.append({
            "student_id": student["id"],
            "student_name": student["name"],
            "student_email": student["email"],
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "completion_percentage": (completed_projects / total_projects * 100) if total_projects > 0 else 0
        })
    
    return {"overview": overview_data}

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