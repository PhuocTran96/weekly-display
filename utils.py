#!/usr/bin/env python3
"""
Utility functions for Weekly Display Tracking Web Application
"""

import os
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.utils import secure_filename

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())

def generate_session_id():
    """Generate unique session ID"""
    return str(uuid.uuid4())

def secure_filename_with_session(filename, session_id, prefix=''):
    """Create secure filename with session ID"""
    original_filename = secure_filename(filename)
    if prefix:
        return f"{session_id}_{prefix}_{original_filename}"
    return f"{session_id}_{original_filename}"

def validate_file_size(file):
    """Validate file size"""
    if hasattr(file, 'content_length') and file.content_length:
        return file.content_length <= MAX_FILE_SIZE

    # If content_length is not available, read and check
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size <= MAX_FILE_SIZE

def validate_csv_structure(file_path, expected_columns=None):
    """Validate CSV file structure"""
    try:
        import pandas as pd

        # Try to read the first few rows
        df = pd.read_csv(file_path, nrows=5)

        # Basic validation
        if df.empty:
            return False, "CSV file is empty"

        if expected_columns:
            missing_columns = set(expected_columns) - set(df.columns)
            if missing_columns:
                return False, f"Missing columns: {missing_columns}"

        return True, "CSV structure is valid"

    except Exception as e:
        return False, f"CSV validation error: {str(e)}"

def cleanup_old_files(directories, max_age_hours=24):
    """Remove files older than specified hours"""
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cleaned_files = []

    for directory in directories:
        if not os.path.exists(directory):
            continue

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception as e:
                        print(f"Error cleaning up {file_path}: {e}")

    return cleaned_files

def ensure_directories(directories):
    """Ensure all required directories exist"""
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def get_file_hash(file_path):
    """Get SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)

    return hash_sha256.hexdigest()

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"

def save_processing_metadata(job_id, session_id, metadata):
    """Save processing metadata to JSON file"""
    metadata_file = f"processing_metadata_{job_id}.json"

    full_metadata = {
        'job_id': job_id,
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        **metadata
    }

    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)
        return metadata_file
    except Exception as e:
        print(f"Error saving metadata: {e}")
        return None

def load_processing_metadata(job_id):
    """Load processing metadata from JSON file"""
    metadata_file = f"processing_metadata_{job_id}.json"

    try:
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading metadata: {e}")

    return None

def validate_week_number(week_num):
    """Validate week number"""
    try:
        week = int(week_num)
        return 1 <= week <= 53
    except (ValueError, TypeError):
        return False

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    return {
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }, status_code

def create_success_response(data=None, message=None):
    """Create standardized success response"""
    response = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }

    if data:
        response.update(data)

    if message:
        response['message'] = message

    return response

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace problematic characters
    import re

    # Remove path components
    filename = os.path.basename(filename)

    # Replace problematic characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)

    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)

    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]

    return f"{name}{ext}"

def get_safe_path(base_path, filename):
    """Get safe file path preventing directory traversal"""
    filename = sanitize_filename(filename)
    return os.path.join(base_path, filename)

def log_request(request_type, details=None):
    """Log request for monitoring"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': request_type,
        'details': details or {}
    }

    log_file = 'request_log.json'

    try:
        # Load existing logs
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)

        # Add new log
        logs.append(log_entry)

        # Keep only last 1000 entries
        if len(logs) > 1000:
            logs = logs[-1000:]

        # Save logs
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Error logging request: {e}")

def check_system_resources():
    """Check system resources (disk space, memory)"""
    import shutil
    import psutil

    try:
        # Check disk space
        disk_usage = shutil.disk_usage('.')
        free_space_gb = disk_usage.free / (1024**3)

        # Check memory
        memory = psutil.virtual_memory()
        available_memory_gb = memory.available / (1024**3)

        return {
            'disk_free_gb': round(free_space_gb, 2),
            'memory_available_gb': round(available_memory_gb, 2),
            'memory_percent': memory.percent
        }
    except Exception as e:
        print(f"Error checking system resources: {e}")
        return None