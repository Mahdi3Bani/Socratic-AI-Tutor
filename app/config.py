import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings and configuration"""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Socratic AI Tutor"
    PROJECT_VERSION: str = "1.0.0"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    def validate_openai_key(self) -> bool:
        """Validate that OpenAI API key is provided"""
        return bool(
            self.OPENAI_API_KEY and self.OPENAI_API_KEY != "your_openai_api_key_here"
        )


# Global settings instance
settings = Settings()

# Update the model to GPT-4 if not already
