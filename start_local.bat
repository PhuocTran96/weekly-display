@echo off
echo Starting Weekly Display Tracking Web Application...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask application...
echo Visit http://localhost:5000 in your browser
echo Press Ctrl+C to stop the application
echo.
python app.py