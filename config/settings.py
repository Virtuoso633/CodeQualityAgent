"""
Configuration settings for CodeQualityAgent
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    
    # Model Configuration
    primary_model: str = Field("gemini/gemini-2.5-flash", env="CODEIQ_PRIMARY_MODEL")
    complex_model: str = Field("gemini/gemini-2.5-pro", env="CODEIQ_COMPLEX_MODEL") 
    fallback_model: str = Field("openai/gpt-4o-mini", env="CODEIQ_FALLBACK_MODEL")
    
    # Application Settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    max_repo_size_mb: int = Field(500, env="MAX_REPO_SIZE_MB")
    
    # Database
    database_url: str = Field("sqlite:///./codeiq.db", env="DATABASE_URL")
    
    # Web Interface
    web_host: str = Field("0.0.0.0", env="WEB_HOST")
    web_port: int = Field(8000, env="WEB_PORT")
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Supported programming languages
SUPPORTED_LANGUAGES = {
    "python": {
        "extensions": [".py"],
        "tree_sitter_language": "python",
        "ast_parser": True
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".ts", ".tsx"],  
        "tree_sitter_language": "javascript",
        "ast_parser": False
    },
    "java": {
        "extensions": [".java"],
        "tree_sitter_language": "java", 
        "ast_parser": False
    }
}

# Quality check categories
QUALITY_CATEGORIES = {
    "security": {
        "name": "Security Issues",
        "description": "Potential security vulnerabilities and risks",
        "priority": 1
    },
    "performance": {
        "name": "Performance Issues", 
        "description": "Performance bottlenecks and inefficiencies",
        "priority": 2
    },
    "maintainability": {
        "name": "Maintainability Issues",
        "description": "Code duplication, complexity, and maintainability concerns", 
        "priority": 3
    },
    "testing": {
        "name": "Testing Gaps",
        "description": "Missing or inadequate test coverage",
        "priority": 4
    },
    "documentation": {
        "name": "Documentation Issues",
        "description": "Missing or inadequate documentation",
        "priority": 5
    }
}
