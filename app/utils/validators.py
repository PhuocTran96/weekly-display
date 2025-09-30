#!/usr/bin/env python3
"""
Validation utility functions
"""

import os
import pandas as pd


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file_size(file):
    """Validate file size"""
    if hasattr(file, 'content_length') and file.content_length:
        return file.content_length <= MAX_FILE_SIZE

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE


def validate_csv_structure(file_path, expected_columns=None):
    """Validate CSV file structure"""
    try:
        df = pd.read_csv(file_path, nrows=5)

        if df.empty:
            return False, "CSV file is empty"

        if expected_columns:
            missing_columns = set(expected_columns) - set(df.columns)
            if missing_columns:
                return False, f"Missing columns: {missing_columns}"

        return True, "CSV structure is valid"

    except Exception as e:
        return False, f"CSV validation error: {str(e)}"


def validate_week_number(week_num):
    """Validate week number"""
    try:
        week = int(week_num)
        return 1 <= week <= 53
    except (ValueError, TypeError):
        return False