from pydantic import BaseModel, EmailStr, Field


class RoleCreate(BaseModel):
    name:        str           = Field(..., min_length=1, max_length=100)
    description: str | None   = None
    is_system:   bool          = False


class RoleUpdate(BaseModel):
    name:        str | None   = Field(None, min_length=1, max_length=100)
    description: str | None   = None


class RoleResponse(BaseModel):
    id:          str
    name:        str
    description: str | None
    is_system:   bool

    model_config = {"from_attributes": True}


class PermissionCreate(BaseModel):
    code:        str  = Field(..., min_length=1, max_length=100, pattern=r"^\w+:\w+$")
    resource:    str  = Field(..., min_length=1, max_length=100)
    action:      str  = Field(..., min_length=1, max_length=50)
    description: str | None = None


class PermissionUpdate(BaseModel):
    description: str | None = None


class PermissionResponse(BaseModel):
    id:          str
    code:        str
    resource:    str
    action:      str
    description: str | None

    model_config = {"from_attributes": True}


class AssignRolesRequest(BaseModel):
    role_ids: list[str] = Field(..., min_length=1)


class UserRoleResponse(BaseModel):
    user_id: str
    roles:   list[RoleResponse]


class AdminUpdateUserRequest(BaseModel):
    first_name:     str | None    = Field(None, min_length=1, max_length=100)
    last_name:      str | None    = Field(None, min_length=1, max_length=100)
    middle_name:    str | None    = Field(None, max_length=100)
    recovery_email: EmailStr | None = None


class AdminSetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminCreateUserRequest(BaseModel):
    first_name:     str           = Field(..., min_length=1, max_length=100)
    last_name:      str           = Field(..., min_length=1, max_length=100)
    middle_name:    str | None    = Field(None, max_length=100)
    email:          str           = Field(..., max_length=255)
    password:       str           = Field(..., min_length=8, max_length=128)
    role_ids:       list[str]     = Field(default_factory=list)


class NotificationResponse(BaseModel):
    id:         str
    event:      str
    title:      str
    body:       str | None
    link:       str | None
    is_read:    bool
    user_id:    str | None
    created_at: str

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id:          str
    user_id:     str | None
    action:      str
    entity_type: str | None
    entity_id:   str | None
    detail:      str | None
    ip_address:  str | None
    created_at:  str
    user_email:  str | None = None

    model_config = {"from_attributes": True}
