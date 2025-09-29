#!/bin/bash
# Weekly Display Tracking Web Application - VPS Deployment Script

set -e  # Exit on any error

echo "🚀 Starting Weekly Display Tracking App Deployment"

# Configuration
APP_NAME="weekly-display"
APP_DIR="/var/www/${APP_NAME}"
APP_USER="www-data"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx git supervisor ufw

# Create application directory
print_status "Setting up application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# If this is initial deployment and app files aren't here yet
if [ ! -f "$APP_DIR/app.py" ]; then
    print_warning "Application files not found. Please upload your files to $APP_DIR"
    print_warning "You can use: scp -r /local/path/to/weekly-display/* user@your-vps:$APP_DIR/"
    exit 1
fi

# Set up Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Create necessary directories
print_status "Creating application directories..."
mkdir -p uploads reports charts logs

# Set proper permissions
print_status "Setting file permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/uploads $APP_DIR/reports $APP_DIR/charts $APP_DIR/logs

# Create systemd service file
print_status "Creating systemd service..."
cat > $SYSTEMD_DIR/${APP_NAME}.service << EOF
[Unit]
Description=Weekly Display Tracking Web Application
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 300 app:app
Restart=always
RestartSec=3

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${APP_NAME}

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR/uploads $APP_DIR/reports $APP_DIR/charts $APP_DIR/logs

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
cat > $NGINX_AVAILABLE/${APP_NAME} << EOF
server {
    listen 80;
    server_name _;  # Replace with your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # File upload size
    client_max_body_size 50M;

    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Logging
    access_log /var/log/nginx/${APP_NAME}_access.log;
    error_log /var/log/nginx/${APP_NAME}_error.log;
}
EOF

# Enable Nginx site
print_status "Enabling Nginx site..."
ln -sf $NGINX_AVAILABLE/${APP_NAME} $NGINX_ENABLED/${APP_NAME}

# Remove default Nginx site if it exists
if [ -f "$NGINX_ENABLED/default" ]; then
    rm -f $NGINX_ENABLED/default
fi

# Configure firewall
print_status "Configuring firewall..."
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS (for future SSL)
ufw --force enable

# Start and enable services
print_status "Starting services..."
systemctl daemon-reload
systemctl enable ${APP_NAME}
systemctl start ${APP_NAME}
systemctl enable nginx
systemctl restart nginx

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet ${APP_NAME}; then
    print_status "✅ ${APP_NAME} service is running"
else
    print_error "❌ ${APP_NAME} service failed to start"
    systemctl status ${APP_NAME}
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx failed to start"
    systemctl status nginx
    exit 1
fi

# Create log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/${APP_NAME} << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 $APP_USER $APP_USER
}
EOF

# Create cleanup cron job
print_status "Setting up cleanup cron job..."
cat > /etc/cron.daily/${APP_NAME}-cleanup << EOF
#!/bin/bash
# Clean up old files
find $APP_DIR/uploads -type f -mtime +1 -delete
find $APP_DIR/reports -type f -mtime +7 -delete
find $APP_DIR/charts -type f -mtime +7 -delete
EOF
chmod +x /etc/cron.daily/${APP_NAME}-cleanup

print_status "🎉 Deployment completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Update the server_name in $NGINX_AVAILABLE/${APP_NAME} with your domain"
print_status "2. Consider setting up SSL with Let's Encrypt:"
print_status "   apt install certbot python3-certbot-nginx"
print_status "   certbot --nginx -d your-domain.com"
print_status "3. Test the application by visiting http://your-server-ip"
print_status ""
print_status "Useful commands:"
print_status "- Check app status: systemctl status ${APP_NAME}"
print_status "- View app logs: journalctl -u ${APP_NAME} -f"
print_status "- Restart app: systemctl restart ${APP_NAME}"
print_status "- Check nginx logs: tail -f /var/log/nginx/${APP_NAME}_error.log"