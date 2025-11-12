"""Authentication service for Google OAuth."""
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.models.user import User
from sqlalchemy.orm import Session

# Initialize OAuth
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class AuthService:
    """Service for authentication logic."""
    
    @staticmethod
    async def get_or_create_user_from_google(
        user_info: Dict[str, Any],
        db: Session
    ) -> User:
        """
        Get or create user from Google OAuth user info.
        
        Args:
            user_info: Google user info from OAuth
            db: Database session
            
        Returns:
            User model
        """
        user_repo = UserRepository(db)
        
        # Try to find existing user by OAuth sub
        user = user_repo.get_by_oauth_sub("google", user_info["sub"])
        
        if not user:
            # Try to find by email
            user = user_repo.get_by_email(user_info["email"])
            
            if not user:
                # Create new user
                user_data = UserCreate(
                    email=user_info["email"],
                    name=user_info.get("name", user_info["email"]),
                    oauth_provider="google",
                    oauth_sub=user_info["sub"],
                    avatar_url=user_info.get("picture")
                )
                user = user_repo.create(user_data)
        
        return user
