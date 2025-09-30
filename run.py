#!/usr/bin/env python3
"""
Main entry point for Weekly Display Tracking Web Application
"""

import os
import sys
from app import create_app


if __name__ == '__main__':
    # Determine environment
    env = os.environ.get('FLASK_ENV', 'development')

    # Create application
    app = create_app(env)

    print("="*60)
    print("Weekly Display Tracking Web Application")
    print("="*60)
    print(f"Environment: {env}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print("="*60)
    print("Visit http://localhost:5000 to access the dashboard")
    print("="*60)

    # Platform-specific settings
    if sys.platform.startswith('win'):
        # Windows-specific settings
        app.run(
            debug=app.config['DEBUG'],
            host='127.0.0.1',
            port=5000,
            threaded=True,
            use_reloader=False
        )
    else:
        # Linux/Unix settings (for VPS)
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))

        app.run(
            debug=app.config['DEBUG'],
            host=host,
            port=port,
            threaded=True
        )