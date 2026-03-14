from uuid import UUID
from pydantic import BaseModel, EmailStr

from utils.enums import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.staff

    def __init__(self, **data):
        super().__init__(**data)
        # Validate password length
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    role: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

    def __init__(self, **data):
        super().__init__(**data)
        # Validate password length
        if len(self.new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
