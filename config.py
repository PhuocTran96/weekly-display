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

    # Email notification settings
    EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_ENABLED', 'False').lower() == 'true'
    GMAIL_EMAIL = os.environ.get('GMAIL_EMAIL', '')
    GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
    BOSS_EMAILS = os.environ.get('BOSS_EMAILS', '').split(',') if os.environ.get('BOSS_EMAILS') else []
    SHOP_CONTACTS_FILE = 'shop_contacts.csv'
    MIN_DECREASE_THRESHOLD = int(os.environ.get('MIN_DECREASE_THRESHOLD', '1'))  # Minimum decrease to trigger email
    SEND_PIC_EMAILS = os.environ.get('SEND_PIC_EMAILS', 'True').lower() == 'true'
    SEND_BOSS_EMAILS = os.environ.get('SEND_BOSS_EMAILS', 'True').lower() == 'true'

    # MongoDB settings
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'display_tracking')
    USE_MONGODB = os.environ.get('USE_MONGODB', 'True').lower() == 'true'

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