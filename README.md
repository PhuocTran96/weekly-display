# Weekly Display Tracking - Web Application

## 🚀 Quick Start Guide

A modern, refactored web application for weekly display tracking with enhanced architecture, modular design, and improved maintainability.

### Local Testing

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

4. **Access the web interface:**
   Open your browser and go to `http://localhost:5000`

### VPS Deployment

1. **Upload files to your VPS:**
   ```bash
   scp -r /local/path/to/weekly-display/* user@your-vps:/var/www/weekly-display/
   ```

2. **Run the deployment script:**
   ```bash
   sudo chmod +x deploy.sh
   sudo ./deploy.sh
   ```

3. **Access your web application:**
   Visit `http://your-vps-ip` in your browser

## 📁 Refactored Directory Structure

```
weekly-display/
├── run.py                           # Application entry point (new)
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template (new)
│
├── app/                             # Main application package (new)
│   ├── __init__.py                  # Application factory
│   ├── routes/                      # Route blueprints (new)
│   │   ├── __init__.py
│   │   ├── main.py                  # Dashboard & download routes
│   │   ├── upload.py                # File upload routes
│   │   ├── process.py               # Data processing routes
│   │   └── contacts.py              # Contact management API
│   ├── services/                    # Business logic (new)
│   │   ├── __init__.py
│   │   └── processor.py             # Background processing service
│   └── utils/                       # Utility modules (new)
│       ├── __init__.py
│       ├── file_utils.py            # File operations
│       └── validators.py            # Input validation
│
├── static/                          # Static assets
│   ├── css/
│   │   ├── style.css                # Main stylesheet
│   │   └── components/              # Component styles (new)
│   └── js/
│       ├── app.js                   # Main application (new)
│       └── modules/                 # JavaScript modules (new)
│           ├── upload.module.js     # Upload functionality
│           ├── processor.module.js  # Processing logic
│           └── results.module.js    # Results display
│
├── templates/                       # HTML templates
│   ├── dashboard.html               # Main dashboard
│   ├── upload.html                  # Upload page
│   ├── results.html                 # Results page
│   └── contacts.html                # Contacts management
│
├── uploads/                         # Temporary uploaded files
├── reports/                         # Generated reports
├── charts/                          # Generated charts
├── logs/                            # Application logs
│
├── Core Processing Files            # Backend processing logic
│   ├── unified_scripts.py           # Core tracking logic
│   ├── display_tracking_system.py   # Display tracking system
│   ├── chart_generator.py           # Chart generation
│   ├── email_notifier.py            # Email notifications
│   └── db_manager.py                # Database operations
│
├── deploy.sh                        # VPS deployment script
├── nginx.conf                       # Nginx configuration
└── weekly_display.service           # Systemd service
```

## 🌐 Web Interface Features

### Dashboard Features
- **Drag & drop file upload** - Easy CSV file uploading
- **Real-time processing** - Live progress tracking
- **Interactive charts** - View increases/decreases
- **Download reports** - CSV and JSON exports
- **Mobile responsive** - Works on all devices

### Upload Process
1. Select raw display data CSV
2. Select previous week report CSV
3. Set week number
4. Upload files
5. Click "Process Data" (emails are NOT sent automatically)
6. View results and download reports
7. Click "📧 Send Email Notifications" button to send emails (optional)

### API Endpoints

**Main Routes:**
- `GET /` - Main dashboard
- `GET /download/<filename>` - File downloads
- `GET /charts/<type>/<filename>` - Chart serving

**Upload Routes:**
- `POST /upload/` - File upload endpoint

**Process Routes:**
- `POST /process/` - Start data processing (emails disabled)
- `GET /process/status/<job_id>` - Check processing status
- `GET /process/results/<job_id>` - View processing results
- `POST /process/send-emails` - Manually trigger email notifications

**Contact API Routes:**
- `GET /api/contacts/all` - Get all contacts
- `GET /api/contacts/<elux_id>` - Get single contact
- `POST /api/contacts/add` - Add new contact
- `PUT /api/contacts/<elux_id>` - Update contact
- `DELETE /api/contacts/<elux_id>` - Delete contact
- `GET /api/contacts/search` - Search contacts
- `GET /api/contacts/export` - Export contacts to CSV
- `POST /api/contacts/import` - Import contacts from CSV

## 🔧 Configuration

### Environment Variables (.env)

Copy [.env.example](.env.example) to `.env` and configure:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-secret-key-change-in-production
HOST=0.0.0.0
PORT=5000

# Email Configuration
EMAIL_ENABLED=False
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
BOSS_EMAILS=boss1@example.com,boss2@example.com
SEND_PIC_EMAILS=True
SEND_BOSS_EMAILS=True

# Display Tracking Configuration
MIN_DECREASE_THRESHOLD=1

# MongoDB Configuration
USE_MONGODB=True
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=display_tracking
```

### File Limits
- Maximum file size: 50MB
- Allowed formats: CSV only
- File retention: 24 hours (uploads), 7 days (reports)

## 🛠️ VPS Deployment Details

### System Requirements
- Ubuntu 18.04+ or CentOS 7+
- Python 3.8+
- 1GB+ RAM (your 2GB is perfect)
- 10GB+ disk space

### Services Configured
- **Gunicorn** - WSGI server for Python app
- **Nginx** - Reverse proxy and static file serving
- **Systemd** - Service management
- **UFW** - Firewall configuration

### Useful Commands

**Check application status:**
```bash
sudo systemctl status weekly-display
```

**View application logs:**
```bash
sudo journalctl -u weekly-display -f
```

**Restart application:**
```bash
sudo systemctl restart weekly-display
```

**Check Nginx logs:**
```bash
sudo tail -f /var/log/nginx/weekly_display_error.log
```

**Update application:**
```bash
cd /var/www/weekly-display
sudo systemctl stop weekly-display
# Upload new files
sudo systemctl start weekly-display
```

## 🔒 Security Features

- File upload validation
- CSRF protection
- Secure file handling
- Automatic cleanup
- Rate limiting (optional)
- Security headers
- Firewall configuration

## 📈 Monitoring

### Log Files
- Application logs: `/var/log/nginx/weekly_display_*.log`
- System logs: `sudo journalctl -u weekly-display`

### Health Check
Visit `http://your-domain/health` to check application status

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo systemctl status weekly-display
   sudo journalctl -u weekly-display --no-pager
   ```

2. **Permission errors:**
   ```bash
   sudo chown -R www-data:www-data /var/www/weekly-display
   sudo chmod -R 755 /var/www/weekly-display
   ```

3. **Nginx errors:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **File upload issues:**
   Check file size limits in both Nginx and Flask configuration

### Support
- Check system logs: `sudo journalctl -f`
- Monitor resources: `htop` or `sudo systemctl status`
- Test connectivity: `curl http://localhost:5000`

## 🎯 Next Steps

1. **Set up domain name** (optional)
2. **Configure SSL certificate:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **Set up backup** (optional)
4. **Monitor performance** and optimize if needed

## 🎯 Refactoring Improvements

### Architecture Enhancements
- ✅ **Application Factory Pattern** - Modular app initialization
- ✅ **Blueprint Architecture** - Separated route concerns
- ✅ **Service Layer** - Business logic isolation
- ✅ **Utility Modules** - Reusable helper functions
- ✅ **ES6 JavaScript Modules** - Modern client-side architecture
- ✅ **Environment Configuration** - Flexible deployment settings

### Code Quality
- ✅ **Separation of Concerns** - Clear module boundaries
- ✅ **DRY Principles** - Reduced code duplication
- ✅ **Error Handling** - Comprehensive logging
- ✅ **Type Safety** - Input validation
- ✅ **Maintainability** - Easier to extend and debug
- ✅ **Manual Email Control** - Send emails only when you choose

### Performance
- ✅ **Lazy Loading** - Module-based JavaScript
- ✅ **Background Processing** - Non-blocking operations
- ✅ **Resource Cleanup** - Automatic file management

## 📞 Quick Reference

- **Local URL:** http://localhost:5000
- **VPS URL:** http://your-vps-ip
- **Upload limit:** 50MB per file
- **Supported formats:** CSV only
- **File retention:** 24 hours (uploads)
- **Main entry:** `python run.py`

## 🔄 Running the Application

To run the refactored application:

1. Use `python run.py` as the main entry point
2. Configure environment variables in `.env` file
3. Access the application at http://localhost:5000
4. All routes are now organized under blueprints

---

**Your weekly display tracking system has been refactored with modern architecture and best practices!** 🎉