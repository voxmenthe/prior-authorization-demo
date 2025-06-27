"""Configuration management for the Decision Tree Generation System."""

import os
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Environment types for configuration."""
    TEST = "test"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


@dataclass
class ModelConfig:
    """Configuration for LLM model selection and fallback behavior."""
    primary_model: str
    fallback_model: str
    description: str


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: Environment
    model_config: ModelConfig
    api_key: str
    
    # Additional settings that might differ by environment
    max_retries: int = 3
    timeout_seconds: int = 10  # Shorter timeout to prevent hangs
    enable_caching: bool = True
    log_level: str = "INFO"


class ConfigManager:
    """Manages configuration across different environments."""
    
    # Model configurations for different environments
    MODEL_CONFIGS = {
        Environment.TEST: ModelConfig(
            primary_model="gemini-2.5-flash-lite-preview-06-17",
            fallback_model="gemini-2.5-flash-preview-05-20",
            description="Optimized for test speed and cost efficiency"
        ),
        Environment.DEVELOPMENT: ModelConfig(
            primary_model="gemini-2.5-flash-lite-preview-06-17",
            fallback_model="gemini-2.5-flash-preview-05-20",
            description="Optimized for speed in development - using fastest model"
        ),
        Environment.PRODUCTION: ModelConfig(
            primary_model="gemini-2.5-pro-preview-06-05",
            fallback_model="gemini-2.5-flash-preview-05-20", 
            description="High-quality results for production use"
        )
    }
    
    @classmethod
    def get_config(cls, environment: str = None) -> AppConfig:
        """
        Get configuration for the specified environment.
        
        Args:
            environment (str, optional): Environment name. If None, determined from env vars.
            
        Returns:
            AppConfig: Configuration object for the environment
            
        Raises:
            ValueError: If environment is invalid or API key is missing
        """
        # Determine environment
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            env_enum = Environment(environment)
        except ValueError:
            valid_envs = [e.value for e in Environment]
            raise ValueError(f"Invalid environment '{environment}'. Valid options: {valid_envs}")
        
        # Get model configuration
        model_config = cls.MODEL_CONFIGS[env_enum]
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("GOOGLE_API_KEY environment variable not set or is still a placeholder.")
        
        # Environment-specific settings
        settings = cls._get_environment_settings(env_enum)
        
        return AppConfig(
            environment=env_enum,
            model_config=model_config,
            api_key=api_key,
            **settings
        )
    
    @classmethod
    def _get_environment_settings(cls, environment: Environment) -> Dict[str, Any]:
        """Get environment-specific settings."""
        
        base_settings = {
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "30")),
            "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper()
        }
        
        # Environment-specific overrides
        if environment == Environment.TEST:
            base_settings.update({
                "timeout_seconds": 15,  # Shorter timeout for tests
                "enable_caching": False,  # Disable caching in tests for consistency
                "log_level": "WARNING"  # Reduce test noise
            })
        elif environment == Environment.PRODUCTION:
            base_settings.update({
                "timeout_seconds": 60,  # Longer timeout for production
                "max_retries": 5,  # More retries for production reliability
                "log_level": "ERROR"  # Only log errors in production
            })
        
        return base_settings
    
    @classmethod
    def get_model_info(cls, environment: str = None) -> str:
        """
        Get a human-readable description of model configuration.
        
        Args:
            environment (str, optional): Environment name
            
        Returns:
            str: Description of model configuration
        """
        # For info display, just get the model config without validating API key
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            env_enum = Environment(environment)
        except ValueError:
            valid_envs = [e.value for e in Environment]
            raise ValueError(f"Invalid environment '{environment}'. Valid options: {valid_envs}")
        
        model_config = cls.MODEL_CONFIGS[env_enum]
        return (
            f"Environment: {env_enum.value}\n"
            f"Primary Model: {model_config.primary_model}\n"
            f"Fallback Model: {model_config.fallback_model}\n"
            f"Description: {model_config.description}"
        )


# Convenience function for getting current config
def get_config() -> AppConfig:
    """Get configuration for the current environment."""
    return ConfigManager.get_config()


# For testing/debugging
if __name__ == "__main__":
    print("=== Model Configurations ===")
    for env in Environment:
        print(f"\n{env.value.upper()}:")
        print(ConfigManager.get_model_info(env.value))