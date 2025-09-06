"""
Configuration management for the HK Strategy Dashboard.
Handles environment variables, database configuration, and application settings.
"""

import os
import logging
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DashboardConfig:
    """Centralized configuration management for the dashboard application."""
    
    def __init__(self):
        self._config = {}
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """Load all configuration sections."""
        self._config = {
            'app': self._load_app_config(),
            'database': self._load_database_config(),
            'redis': self._load_redis_config(),
            'charts': self._load_chart_config(),
            'cache': self._load_cache_config(),
            'logging': self._load_logging_config()
        }
    
    def _load_app_config(self) -> Dict[str, Any]:
        """Load application-specific configuration."""
        return {
            'page_title': "HK Strategy Multi-Portfolio Dashboard",
            'page_icon': "📈",
            'layout': "wide",
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': os.getenv('APP_VERSION', '1.0.0')
        }
    
    def _load_database_config(self) -> Dict[str, Any]:
        """Load database connection configuration."""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'hk_strategy'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer'),
            'connection_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20'))
        }
    
    def _load_redis_config(self) -> Dict[str, Any]:
        """Load Redis configuration for caching."""
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD'),
            'enabled': os.getenv('REDIS_ENABLED', 'False').lower() == 'true',
            'ttl_default': int(os.getenv('REDIS_TTL_DEFAULT', '900'))  # 15 minutes
        }
    
    def _load_chart_config(self) -> Dict[str, Any]:
        """Load chart styling and configuration."""
        return {
            'theme': os.getenv('CHART_THEME', 'plotly'),
            'color_palette': [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ],
            'height_default': 500,
            'width_default': 800,
            'show_toolbar': True,
            'responsive': True
        }
    
    def _load_cache_config(self) -> Dict[str, Any]:
        """Load caching configuration."""
        return {
            'price_data_ttl': int(os.getenv('CACHE_PRICE_TTL', '900')),  # 15 minutes
            'company_data_ttl': int(os.getenv('CACHE_COMPANY_TTL', '3600')),  # 1 hour
            'analysis_ttl': int(os.getenv('CACHE_ANALYSIS_TTL', '1800')),  # 30 minutes
            'enabled': os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
        }
    
    def _load_logging_config(self) -> Dict[str, Any]:
        """Load logging configuration."""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file_enabled': os.getenv('LOG_FILE_ENABLED', 'False').lower() == 'true',
            'file_path': os.getenv('LOG_FILE_PATH', 'logs/dashboard.log'),
            'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', '10485760')),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """Get configuration value by section and optional key."""
        if section not in self._config:
            raise KeyError(f"Configuration section '{section}' not found")
        
        if key is None:
            return self._config[section]
        
        if key not in self._config[section]:
            raise KeyError(f"Configuration key '{key}' not found in section '{section}'")
        
        return self._config[section][key]
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        db_config = self._config['database']
        password_part = f":{db_config['password']}" if db_config['password'] else ""
        return (f"postgresql://{db_config['user']}{password_part}@"
                f"{db_config['host']}:{db_config['port']}/{db_config['name']}")
    
    def validate_environment(self) -> tuple[bool, list]:
        """Validate required environment variables are set."""
        required_vars = [
            'DB_HOST', 'DB_NAME', 'DB_USER'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        return len(missing_vars) == 0, missing_vars


# Global configuration instance
_config_instance = None

def get_config() -> DashboardConfig:
    """Get global configuration instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = DashboardConfig()
    return _config_instance

def load_config() -> Dict[str, Any]:
    """Load application configuration from environment and files."""
    config = get_config()
    return {
        'app': config.get('app'),
        'database': config.get('database'),
        'redis': config.get('redis'),
        'charts': config.get('charts'),
        'cache': config.get('cache'),
        'logging': config.get('logging')
    }

def get_database_config() -> Dict[str, Any]:
    """Get database connection configuration."""
    return get_config().get('database')

def get_redis_config() -> Dict[str, Any]:
    """Get Redis connection configuration."""
    return get_config().get('redis')

def get_chart_config() -> Dict[str, Any]:
    """Get default chart styling and configuration."""
    return get_config().get('charts')

def validate_environment() -> bool:
    """Validate required environment variables are set."""
    is_valid, missing_vars = get_config().validate_environment()
    if not is_valid:
        logging.error(f"Missing required environment variables: {missing_vars}")
    return is_valid

def setup_logging() -> None:
    """Setup application logging based on configuration."""
    log_config = get_config().get('logging')
    
    level = getattr(logging, log_config['level'].upper(), logging.INFO)
    format_str = log_config['format']
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_str))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if enabled
    if log_config['file_enabled']:
        try:
            from logging.handlers import RotatingFileHandler
            os.makedirs(os.path.dirname(log_config['file_path']), exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_config['file_path'],
                maxBytes=log_config['max_file_size'],
                backupCount=log_config['backup_count']
            )
            file_handler.setFormatter(logging.Formatter(format_str))
            logging.getLogger().addHandler(file_handler)
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")