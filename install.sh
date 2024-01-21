#!/bin/bash

#Run as root
if [[ $EUID -ne 0 ]]; then
  echo "Script needs to run as root. Elevating permissions now."
  exec sudo /bin/bash "$0" "$@"
fi

# Welcome message and ASCII art
cat <<"EOF"
  _____                _                          
 |  ___| __ ___  _ __ | |_ _ __   __ _  __ _  ___ 
 | |_ | '__/ _ \| '_ \| __| '_ \ / _` |/ _` |/ _ \
 |  _|| | | (_) | | | | |_| |_) | (_| | (_| |  __/
 |_|  |_|  \___/|_| |_|\__| .__/ \__,_|\__, |\___|
                          |_|          |___/      

📰 A self-hosted, privacy-focused publishing platform for independent and autonomous newsrooms.
https://github.com/scidsg/frontpage

A free tool by Science & Design - https://scidsg.org

EOF
sleep 3

# Function to display error message and exit
error_exit() {
    echo "An error occurred during installation. Please check the output above for more details."
    exit 1
}

# Trap any errors and call the error_exit function
trap error_exit ERR

# Update and upgrade the system
export DEBIAN_FRONTEND=noninteractive
sudo apt update && sudo apt -y dist-upgrade

# Install Python and pip
sudo apt install -y python3 python3-pip git python3-venv nginx

cd /var/www/html
git clone https://github.com/scidsg/frontpage
cd frontpage

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask and other dependencies
pip3 install Flask Flask-SQLAlchemy gunicorn Flask-Login python-dotenv Flask-Migrate Flask-WTF markdown pycountry python-slugify passlib

# Generate and export Flask secret key
FLASK_SECRET_KEY=$(openssl rand -hex 32)
export FLASK_SECRET_KEY
echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" > /var/www/html/frontpage/.env

# Initialize the Flask app and create the database within application context
python /var/www/html/frontpage/init_db.py

# Change owner and permissions of the SQLite database file
sudo chown -R www-data:www-data /var/www/html/frontpage
sudo chown www-data:www-data /var/www/html/frontpage/blog.db
sudo chmod 664 /var/www/html/frontpage/blog.db

# Add upload directory
mkdir /var/www/html/frontpage/static/uploads
sudo chown -R www-data:www-data /var/www/html/frontpage/static/uploads
sudo chmod -R 755 /var/www/html/frontpage/static/uploads

# Install Nginx
sudo apt install nginx -y

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
User=www-data
Group=www-data
WorkingDirectory=/var/www/html/frontpage/
ExecStart=/var/www/html/frontpage/venv/bin/gunicorn -w 1 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

sudo ln -s /etc/nginx/sites-available/frontpage /etc/nginx/sites-enabled
rm -f /etc/nginx/sites-available/default
rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

sudo systemctl enable frontpage.service
sudo systemctl start frontpage.service
sudo systemctl restart frontpage.service