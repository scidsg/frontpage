#!/bin/bash

# Update and upgrade the system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

git clone https://github.com/glenn-sorrentino/frontpage
cd frontpage

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask
pip3 install Flask Flask-SQLAlchemy

# Install Nginx
sudo apt install nginx -y

# Create a basic Flask app
mkdir ~/frontpage
cd ~/frontpage

# Set up Nginx to proxy requests to Flask
sudo tee /etc/nginx/sites-available/frontpage <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-NginX-Proxy true;
    }
}
EOF

# Set up Nginx to proxy requests to Flask
sudo tee /etc/systemd/system/frontpage.service <<EOF
[Unit]
Description=My Flask App
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/html/frontpage/
ExecStart=/var/www/html/frontpage/python/venv/bin/gunicorn -w 1 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

sudo ln -s /etc/nginx/sites-available/frontpage /etc/nginx/sites-enabled
sudo systemctl restart nginx

# Start the Flask app
python3 ~/frontpage/app.py
