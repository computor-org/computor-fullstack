from datetime import datetime
from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional, List, Literal
from sqlalchemy.orm import Session
from ctutor_backend.interface.course_content_types import CourseContentTypeGet
from ctutor_backend.interface.deployments import GitLabConfig, GitLabConfigGet
from ctutor_backend.interface.base import BaseEntityGet, EntityInterface, ListQuery
from ctutor_backend.model.course import CourseContent
from ctutor_backend.model.course import CourseContentKind, CourseContentType, CourseMember, CourseSubmissionGroup, CourseSubmissionGroupMember
from ctutor_backend.model.auth import User
from ..types import Ltree


# Deployment History Models
class DeploymentHistoryAction(BaseModel):
    """Single deployment history action entry."""
    action: Literal["deployed", "unassigned", "reassigned", "archived", "updated", "failed"] = Field(
        description="Type of deployment action"
    )
    timestamp: datetime = Field(
        description="When the action occurred"
    )
    example_id: Optional[str] = Field(
        default=None,
        description="Example ID involved in the action"
    )
    example_version: Optional[str] = Field(
        default=None,
        description="Example version at time of action"
    )
    previous_example_id: Optional[str] = Field(
        default=None,
        description="Previous example ID (for reassignment)"
    )
    previous_example_version: Optional[str] = Field(
        default=None,
        description="Previous example version (for reassignment)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the action (optional)"
    )
    performed_by: Optional[str] = Field(
        default=None,
        description="User ID who performed the action"
    )
    workflow_id: Optional[str] = Field(
        default=None,
        description="Temporal workflow ID if applicable"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if action failed"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class DeploymentHistory(BaseModel):
    """Complete deployment history for a CourseContent."""
    actions: List[DeploymentHistoryAction] = Field(
        default_factory=list,
        description="List of deployment actions in chronological order"
    )
    last_successful_deployment: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last successful deployment"
    )
    last_successful_example_id: Optional[str] = Field(
        default=None,
        description="Example ID of last successful deployment"
    )
    last_successful_example_version: Optional[str] = Field(
        default=None,
        description="Example version of last successful deployment"
    )
    
    def add_action(self, action: DeploymentHistoryAction) -> None:
        """Add a new action to the history."""
        self.actions.append(action)
        
        # Update last successful deployment if applicable
        if action.action == "deployed" and not action.error_message:
            self.last_successful_deployment = action.timestamp
            self.last_successful_example_id = action.example_id
            self.last_successful_example_version = action.example_version
    
    def get_latest_action(self) -> Optional[DeploymentHistoryAction]:
        """Get the most recent action."""
        return self.actions[-1] if self.actions else None
    
    model_config = ConfigDict(use_enum_values=True)


class CourseContentProperties(BaseModel):
    gitlab: Optional[GitLabConfig] = None
    deployment_history: Optional[DeploymentHistory] = Field(
        default=None,
        description="Complete deployment history for this content"
    )
    
    model_config = ConfigDict(
        extra='allow',
    )

class CourseContentPropertiesGet(BaseModel):
    gitlab: Optional[GitLabConfigGet] = None
    deployment_history: Optional[DeploymentHistory] = Field(
        default=None,
        description="Complete deployment history for this content"
    )

    model_config = ConfigDict(
        extra='allow',
    )
    
class CourseContentCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    properties: Optional[CourseContentProperties] = None
    version_identifier: Optional[str] = None  # Made optional - will be deprecated
    position: float = 0
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None
    # Example assignment fields
    example_id: Optional[str] = None
    example_version: Optional[str] = None
    deployment_status: Optional[str] = None
    deployed_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)

class CourseContentGet(BaseEntityGet):
    id: str
    archived_at: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    course_content_kind_id: str
    properties: Optional[CourseContentPropertiesGet] = None
    version_identifier: Optional[str] = None  # Made optional - will be deprecated
    position: float
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None
    
    # Example assignment fields
    example_id: Optional[str] = None
    example_version: Optional[str] = None
    deployment_status: Optional[str] = None
    deployed_at: Optional[datetime] = None

    course_content_type: Optional[CourseContentTypeGet] = None

    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
class CourseContentList(BaseModel):
    id: str
    title: Optional[str] = None
    path: str
    course_id: str
    course_content_type_id: str
    course_content_kind_id: str
    version_identifier: Optional[str] = None  # Made optional - will be deprecated
    position: float
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None
    
    # Example assignment fields
    example_id: Optional[str] = None
    example_version: Optional[str] = None
    deployment_status: Optional[str] = None
    deployed_at: Optional[datetime] = None
    
    course_content_type: Optional[CourseContentTypeGet] = None
    
    @field_validator('path', mode='before')
    @classmethod
    def cast_str_to_ltree(cls, value):
        return str(value)

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
class CourseContentUpdate(BaseModel):
    path: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    course_content_type_id: Optional[str] = None
    properties: Optional[CourseContentProperties] = None
    version_identifier: Optional[str] = None
    position: Optional[float] = None
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

class CourseContentQuery(ListQuery):
    id: Optional[str] = None
    title: Optional[str] = None
    path: Optional[str] = None
    course_id: Optional[str] = None
    course_content_type_id: Optional[str] = None
    version_identifier: Optional[str] = None
    properties: Optional[CourseContentProperties] = None
    archived: Optional[bool] = None
    position: Optional[float] = None
    max_group_size: Optional[int] = None
    max_test_runs: Optional[int] = None
    max_submissions: Optional[int] = None
    execution_backend_id: Optional[str] = None

def course_content_search(db: Session, query, params: Optional[CourseContentQuery]):
    if params.id != None:
        query = query.filter(CourseContent.id == params.id)
    if params.title != None:
        query = query.filter(CourseContent.title == params.title)
    if params.path != None:

        if params.path.endswith(".") or params.path.startswith("."):
            params.path = params.path.strip(".")

        query = query.filter(CourseContent.path == Ltree(params.path))

    if params.course_id != None:
        query = query.filter(CourseContent.course_id == params.course_id)
    if params.course_content_type_id != None:
        query = query.filter(CourseContent.course_content_type_id == params.course_content_type_id)
    if params.version_identifier != None:
        query = query.filter(CourseContent.version_identifier == params.version_identifier)
    if params.position != None:
        query = query.filter(CourseContent.position == params.position)
    if params.max_group_size != None:
        query = query.filter(CourseContent.max_group_size == params.max_group_size)
    if params.max_test_runs != None:
        query = query.filter(CourseContent.max_test_runs == params.max_test_runs)
    if params.max_submissions != None:
        query = query.filter(CourseContent.max_submissions == params.max_submissions)
    if params.execution_backend_id != None:
        query = query.filter(CourseContent.execution_backend_id == params.execution_backend_id)

    if params.archived != None and params.archived != False:
        query = query.filter(CourseContent.archived_at != None)
    else:
        query = query.filter(CourseContent.archived_at == None)
        
    return query

def post_create(course_content: CourseContent, db: Session):
    
    course_members = (
        db.scalars(db.query(CourseMember.id)
        .join(User, User.id == CourseMember.user_id)
        .join(CourseContentType, CourseContentType.id == course_content.course_content_type_id)
        .join(CourseContentKind, CourseContentKind.id == CourseContentType.course_content_kind_id)
        .filter(
            CourseMember.course_id == course_content.course_id,
            CourseContentKind.submittable == True,
            course_content.max_group_size == 1,
            User.user_type == "user"
        )).all()
    )

    for course_member in course_members:
        submission_group = CourseSubmissionGroup(
            course_id=course_content.course_id,
            course_content_id=course_content.id,
            max_group_size=course_content.max_group_size,
            max_test_runs=course_content.max_test_runs,
            max_submissions=course_content.max_submissions
        )
        
        db.add(submission_group)
        db.commit()
        db.refresh(submission_group)
        
        submission_group_member = CourseSubmissionGroupMember(
            course_submission_group_id = submission_group.id,
            course_member_id = course_member
        )

        db.add(submission_group_member)
        db.commit()
        db.refresh(submission_group_member)

def post_update(updated_item: CourseContent, old_item: CourseContentGet, db: Session):
    """Handle path updates for course content descendants after parent is updated"""
    # Check if path has changed
    if str(old_item.path) != str(updated_item.path):
        old_path = str(old_item.path)
        new_path = str(updated_item.path)
        
        try:
            # Find all descendants using text() to avoid relationship loading issues
            from sqlalchemy import text
            descendants = db.query(CourseContent).filter(
                text("course_content.path::text LIKE :pattern"),
                CourseContent.course_id == updated_item.course_id
            ).params(pattern=f'{old_path}.%').all()
            
            # Update paths of all descendants using direct SQL update
            for descendant in descendants:
                old_descendant_path = str(descendant.path)
                
                # Replace the old parent path with the new parent path
                if old_descendant_path.startswith(old_path + '.'):
                    # Remove the old parent path and add the new parent path
                    relative_path = old_descendant_path[len(old_path):]  # includes the leading '.'
                    new_descendant_path = new_path + relative_path
                    
                    # Use direct SQL update to ensure it gets committed
                    db.execute(
                        text("UPDATE course_content SET path = :new_path WHERE id = :content_id"),
                        {"new_path": new_descendant_path, "content_id": descendant.id}
                    )
            
            # Force commit the descendant changes immediately
            db.commit()
            
            # Refresh the updated_item to ensure it's still attached to the session
            db.refresh(updated_item)
                
        except Exception as e:
            print(f"Error in post_update: {e}")
            db.rollback()
            raise

class CourseContentInterface(EntityInterface):
    create = CourseContentCreate
    get = CourseContentGet
    list = CourseContentGet  # Use CourseContentGet for list to include relationships
    update = CourseContentUpdate
    query = CourseContentQuery
    search = course_content_search
    endpoint = "course-contents"
    model = CourseContent
    cache_ttl = 300  # 5 minutes cache for course content data
    post_create = post_create
    post_update = post_update