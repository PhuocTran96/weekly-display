# Weekly Display Tracking - Web Application

## 🚀 Quick Start Guide

Your weekly display tracking system has been converted into a web application! Here's how to use it:

### Local Testing

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the web interface:**
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

## 📁 Directory Structure

```
weekly-display/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── utils.py                  # Utility functions
├── templates/                # HTML templates
│   ├── dashboard.html        # Main dashboard
│   ├── upload.html           # Upload page
│   └── results.html          # Results page
├── static/                   # Static assets
│   ├── css/style.css         # Enhanced stylesheet
│   └── js/                   # JavaScript files
├── uploads/                  # Temporary uploaded files
├── reports/                  # Generated reports
├── charts/                   # Generated charts
├── logs/                     # Application logs
├── deploy.sh                 # VPS deployment script
├── nginx.conf                # Nginx configuration
├── weekly_display.service    # Systemd service
└── [existing files]          # Your original scripts
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
5. Click "Process Data"
6. View results and download reports

### API Endpoints
- `GET /` - Main dashboard
- `POST /upload` - File upload
- `POST /process` - Start processing
- `GET /status/<job_id>` - Processing status
- `GET /download/<filename>` - File downloads
- `GET /charts/<type>/<filename>` - Chart serving

## 🔧 Configuration

### Environment Variables (.env)
```bash
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=5000
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

## 📞 Quick Reference

- **Local URL:** http://localhost:5000
- **VPS URL:** http://your-vps-ip
- **Upload limit:** 50MB per file
- **Supported formats:** CSV only
- **File retention:** 24 hours (uploads)

---

**Your weekly display tracking system is now accessible from anywhere with an internet connection!** 🎉