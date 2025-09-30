#!/usr/bin/env python3
"""
Flask Application Factory
"""

import os
from flask import Flask
from pathlib import Path


def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    from config import config
    app.config.from_object(config[config_name])

    # Additional Flask configs
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    # Ensure required directories exist
    from app.utils.file_utils import ensure_directories
    ensure_directories([
        app.config['UPLOAD_FOLDER'],
        app.config['REPORTS_FOLDER'],
        app.config['CHARTS_FOLDER'],
        'logs',
        'templates',
        'static'
    ])

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.upload import upload_bp
    from app.routes.process import process_bp
    from app.routes.contacts import contacts_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(process_bp, url_prefix='/process')
    app.register_blueprint(contacts_bp, url_prefix='/api/contacts')

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import jsonify, render_template

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

    @app.errorhandler(404)
    def not_found(e):
        return render_template('dashboard.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Internal error: {e}')
        return jsonify({'error': 'Internal server error'}), 500