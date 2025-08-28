"""
Configuration Manager for HK Strategy Portfolio Dashboard

This module handles secure loading of configuration from YAML files and environment variables.
It provides a centralized way to manage all application settings while keeping sensitive
data out of the codebase.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

class ConfigurationError(Exception):
    """Raised when there's an issue with configuration loading or validation."""
    pass

class ConfigManager:
    """
    Secure configuration manager that loads settings from YAML files and environment variables.
    
    Priority order:
    1. Environment variables (highest priority)
    2. YAML configuration file
    3. Default values (lowest priority)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default path.
        """
        self.config_data = {}
        self.config_file_path = config_path or self._get_default_config_path()
        
        # Load environment variables from .env file if it exists
        self._load_env_file()
        
        # Load configuration
        self._load_configuration()
        
        # Validate critical settings
        self._validate_configuration()
        
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Look for config file relative to the project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "app_config.yaml"
        return str(config_path)
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        project_root = Path(__file__).parent.parent
        env_file_path = project_root / "config" / ".env"
        
        if env_file_path.exists():
            load_dotenv(env_file_path)
            logging.info("Loaded environment variables from .env file")
    
    def _load_configuration(self):
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as file:
                    self.config_data = yaml.safe_load(file) or {}
                logging.info(f"Configuration loaded from {self.config_file_path}")
            else:
                logging.warning(f"Configuration file not found: {self.config_file_path}")
                logging.info("Using environment variables and defaults")
                self.config_data = {}
                
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def _validate_configuration(self):
        """Validate that critical configuration values are present and valid."""
        required_settings = [
            ("database", "password"),
            ("security", "secret_key")
        ]
        
        warnings = []
        errors = []
        
        for section, key in required_settings:
            value = self.get(f"{section}.{key}")
            if not value or value in ["CHANGE_ME_TO_YOUR_SECURE_PASSWORD", "CHANGE_ME_TO_A_RANDOM_SECRET_KEY"]:
                errors.append(f"Missing or invalid {section}.{key}")
        
        # Check for default passwords that should be changed
        db_password = self.get("database.password")
        if db_password in ["trading123", "password", "admin"]:
            warnings.append("Database password appears to be a default value - consider changing it")
        
        if warnings:
            for warning in warnings:
                logging.warning(f"Configuration warning: {warning}")
        
        if errors:
            error_msg = "Configuration errors found:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ConfigurationError(error_msg)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.host')
            default: Default value to return if key is not found
            
        Returns:
            Configuration value or default
        """
        # First check environment variables (highest priority)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # Then check YAML configuration
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Handle null values
        if value.lower() in ['null', 'none', '']:
            return None
        
        # Return as string
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration as a dictionary."""
        return {
            'host': self.get('database.host', 'localhost'),
            'port': self.get('database.port', 5432),
            'database': self.get('database.name', 'hk_strategy'),
            'user': self.get('database.user', 'trader'),
            'password': self.get('database.password'),
            'min_connections': self.get('database.min_connections', 1),
            'max_connections': self.get('database.max_connections', 10),
            'connection_timeout': self.get('database.connection_timeout', 30)
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration as a dictionary."""
        return {
            'host': self.get('redis.host', 'localhost'),
            'port': self.get('redis.port', 6379),
            'db': self.get('redis.database', 0),
            'password': self.get('redis.password'),
            'socket_timeout': self.get('redis.socket_timeout', 5),
            'connection_timeout': self.get('redis.connection_timeout', 10),
            'max_connections': self.get('redis.max_connections', 50)
        }
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        # First check if DATABASE_URL environment variable is set
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        
        # Build URL from individual components
        config = self.get_database_config()
        
        if not config['password']:
            raise ConfigurationError("Database password not configured")
        
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        # First check if REDIS_URL environment variable is set
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            return redis_url
        
        # Build URL from individual components
        config = self.get_redis_config()
        
        if config['password']:
            return f"redis://:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
        else:
            return f"redis://{config['host']}:{config['port']}/{config['db']}"
    
    def is_debug_mode(self) -> bool:
        """Check if application is running in debug mode."""
        return self.get('app.debug', False) or os.getenv('DEBUG', 'false').lower() == 'true'
    
    def get_log_level(self) -> str:
        """Get logging level."""
        return self.get('app.log_level', 'INFO')
    
    def get_app_settings(self) -> Dict[str, Any]:
        """Get application settings."""
        return {
            'name': self.get('app.name', 'HK Strategy Portfolio Dashboard'),
            'version': self.get('app.version', '1.0.0'),
            'environment': self.get('app.environment', 'production'),
            'debug': self.is_debug_mode(),
            'host': self.get('app.host', '0.0.0.0'),
            'port': self.get('app.port', 8501),
            'log_level': self.get_log_level()
        }
    
    def reload(self):
        """Reload configuration from file."""
        self._load_configuration()
        self._validate_configuration()
        logging.info("Configuration reloaded")

# Global configuration instance
config = None

def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = ConfigManager()
    return config

def initialize_config(config_path: Optional[str] = None) -> ConfigManager:
    """Initialize the global configuration instance."""
    global config
    config = ConfigManager(config_path)
    return config