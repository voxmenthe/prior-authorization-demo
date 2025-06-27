#!/usr/bin/env python3
"""
Example script demonstrating the configuration system for different environments.

Usage:
    # Default (development)
    python examples/test_config.py
    
    # Test environment
    ENVIRONMENT=test python examples/test_config.py
    
    # Production environment  
    ENVIRONMENT=production python examples/test_config.py
"""

import os
import sys
sys.path.append('.')

from src.core.config import ConfigManager
from src.core.llm_client import LlmClient


def main():
    print("=== Decision Tree Generation System - Configuration Demo ===\n")
    
    # Show current environment configuration
    print("📋 Current Configuration:")
    print(ConfigManager.get_model_info())
    print()
    
    # Initialize client with environment-based config
    try:
        client = LlmClient()
        print("✅ LlmClient initialized successfully!")
        print(f"   Environment: {client.config.environment.value}")
        print(f"   Primary Model: {client.model_name}")
        print(f"   Fallback Model: {client.fallback_model}")
        print(f"   Timeout: {client.config.timeout_seconds}s")
        print(f"   Max Retries: {client.config.max_retries}")
        print(f"   Caching Enabled: {client.config.enable_caching}")
        print(f"   Log Level: {client.config.log_level}")
        print()
        
        # Show all environment configurations
        print("📚 All Available Configurations:")
        print("-" * 50)
        for env in ["test", "development", "production"]:
            print(f"\n{env.upper()}:")
            print(ConfigManager.get_model_info(env))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())