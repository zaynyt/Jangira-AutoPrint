"""Logging configuration for Jangira AutoPrint"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from app.config import LOG_FILE, LOG_LEVEL, LOG_MAX_SIZE, LOG_BACKUP_COUNT

class JangiraLogger:
    """Centralized logging for the application"""
    
    _instance: Optional['JangiraLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize logger with file and console handlers"""
        self._logger = logging.getLogger("JangiraAutoPrint")
        self._logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler with rotation
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=LOG_MAX_SIZE,
                backupCount=LOG_BACKUP_COUNT
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to create file handler: {e}")
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
    
    @staticmethod
    def get_logger() -> logging.Logger:
        """Get the logger instance"""
        if JangiraLogger._logger is None:
            JangiraLogger()
        return JangiraLogger._logger
    
    @staticmethod
    def info(msg: str, *args, **kwargs):
        """Log info message"""
        JangiraLogger.get_logger().info(msg, *args, **kwargs)
    
    @staticmethod
    def debug(msg: str, *args, **kwargs):
        """Log debug message"""
        JangiraLogger.get_logger().debug(msg, *args, **kwargs)
    
    @staticmethod
    def warning(msg: str, *args, **kwargs):
        """Log warning message"""
        JangiraLogger.get_logger().warning(msg, *args, **kwargs)
    
    @staticmethod
    def error(msg: str, *args, **kwargs):
        """Log error message"""
        JangiraLogger.get_logger().error(msg, *args, **kwargs)
    
    @staticmethod
    def critical(msg: str, *args, **kwargs):
        """Log critical message"""
        JangiraLogger.get_logger().critical(msg, *args, **kwargs)

# Convenience functions
def get_logger():
    """Get logger instance"""
    return JangiraLogger.get_logger()

def log_info(msg: str):
    """Log info"""
    JangiraLogger.info(msg)

def log_error(msg: str):
    """Log error"""
    JangiraLogger.error(msg)

def log_debug(msg: str):
    """Log debug"""
    JangiraLogger.debug(msg)
