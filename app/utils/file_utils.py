#!/usr/bin/env python3
"""
File utility functions
"""

import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path


def ensure_directories(directories):
    """Ensure all required directories exist"""
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


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


def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re

    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)

    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]

    return f"{name}{ext}"


def get_safe_path(base_path, filename):
    """Get safe file path preventing directory traversal"""
    filename = sanitize_filename(filename)
    return os.path.join(base_path, filename)