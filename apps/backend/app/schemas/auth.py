from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)