#!/usr/bin/env python3
"""
Configuration settings for Weekly Display Tracking Web Application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-secret-key-in-production'

    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    REPORTS_FOLDER = 'reports'
    CHARTS_FOLDER = 'charts'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'csv'}

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # File cleanup settings
    CLEANUP_AFTER_HOURS = 24

    # Processing settings
    MAX_PROCESSING_TIME = 300  # 5 minutes timeout
    BACKGROUND_JOBS_LIMIT = 5  # Maximum concurrent jobs

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-set'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}