"""Core configuration for the application."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Countdowns"
    
    # Database
    DATABASE_URL: str
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:3000/api"
    
    # Storage
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    UPLOAD_DIR: str = "/app/uploads"
    
    # S3/MinIO
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "countdowns-uploads"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    
    # File Upload Limits
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_VIDEO_SIZE_MB: int = 50
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Session
    SESSION_SECRET_KEY: str = "change-me-in-production"
    
    # Timezone
    DEFAULT_TIMEZONE: str = "Europe/Warsaw"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Leap Year Policy for Feb 29
    LEAP_POLICY: str = "feb28"  # 'feb28' or 'mar01'
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def max_image_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024
    
    @property
    def max_video_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
