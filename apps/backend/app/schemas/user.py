from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)