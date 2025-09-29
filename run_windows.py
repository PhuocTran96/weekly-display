#!/usr/bin/env python3
"""
Windows-friendly server runner for Weekly Display Tracking
Uses waitress server to avoid Windows socket issues
"""

try:
    from waitress import serve
    from app import app

    if __name__ == '__main__':
        print("Starting Weekly Display Tracking Web Application...")
        print("Visit http://localhost:5000 to access the dashboard")
        print("Using Waitress server (Windows-optimized)")
        serve(app, host='127.0.0.1', port=5000, threads=4)

except ImportError:
    print("Waitress not installed. Installing...")
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])

    from waitress import serve
    from app import app

    if __name__ == '__main__':
        print("Starting Weekly Display Tracking Web Application...")
        print("Visit http://localhost:5000 to access the dashboard")
        print("Using Waitress server (Windows-optimized)")
        serve(app, host='127.0.0.1', port=5000, threads=4)