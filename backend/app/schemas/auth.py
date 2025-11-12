"""Auth schemas."""
from pydantic import BaseModel
from app.schemas.user import UserResponse


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Schema for authentication response."""
    user: UserResponse
    message: str = "Authentication successful"
