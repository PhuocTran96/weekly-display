#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
from app import create_app

# Determine environment from environment variable
env = os.environ.get('FLASK_ENV', 'production')

# Create application instance
app = create_app(env)

if __name__ == '__main__':
    app.run()
