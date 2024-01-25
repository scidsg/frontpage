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
sudo apt install -y \
    git \
    nginx \
    python3 \
    python3-pip \
    python3-venv \
    tor

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH in the profile file
echo 'export PATH="$HOME/.local/bin:$PATH"' >> $HOME/.profile

# Source the profile file to update PATH
source $HOME/.profile

# Change to the project directory
cd /var/www/html
git clone https://github.com/scidsg/frontpage
cd frontpage
git switch device


# Install mkcert and its dependencies
echo "Installing mkcert and its dependencies..."
apt install -y libnss3-tools
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-arm
sleep 10
chmod +x mkcert-v1.4.4-linux-arm
mv mkcert-v1.4.4-linux-arm /usr/local/bin/mkcert
export CAROOT="/var/www/html/frontpage/.local/share/mkcert"
mkdir -p "$CAROOT"  # Ensure the directory exists
mkcert -install

# Create a certificate for hushline.local
echo "Creating certificate for ddosecrets.local..."
mkcert ddosecrets.local

# Move and link the certificates to Nginx's directory (optional, modify as needed)
mv ddosecrets.local.pem /etc/nginx/
mv ddosecrets.local-key.pem /etc/nginx/
echo "Certificate and key for ddosecrets.local have been created and moved to /etc/nginx/."

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Now run poetry install
poetry install

# Generate and export Flask secret key
FLASK_SECRET_KEY=$(openssl rand -hex 32)
export FLASK_SECRET_KEY
echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" > /var/www/html/frontpage/.env

# Initialize the Flask app and create the database within application context
python /var/www/html/frontpage/init_db.py

# Change owner and permissions of the SQLite database file
sudo chown -R www-data:www-data /var/www/html/frontpage

# Add upload directory
mkdir /var/www/html/frontpage/frontpage/static/uploads
sudo chown -R www-data:www-data /var/www/html/frontpage/frontpage/static/uploads
sudo chmod -R 755 /var/www/html/frontpage/frontpage/static/uploads

# Install Nginx
sudo apt install nginx -y

# Set up Nginx to proxy requests to Flask
sudo tee /etc/nginx/sites-available/frontpage <<EOF
server {
    listen 80;
    server_name localhost ddosecrets.local;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ddosecrets.local;

    ssl_certificate /etc/nginx/ddosecrets.local.pem;
    ssl_certificate_key /etc/nginx/ddosecrets.local-key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'none'";
    add_header Permissions-Policy "geolocation=(), midi=(), notifications=(), push=(), sync-xhr=(), microphone=(), camera=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=(), fullscreen=(), payment=(), interest-cohort=()";
    add_header Referrer-Policy "no-referrer";
    add_header X-XSS-Protection "1; mode=block";
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
ExecStart=/var/www/html/frontpage/venv/bin/gunicorn -w 1 -b 127.0.0.1:5000 frontpage:app

[Install]
WantedBy=multi-user.target
EOF

# Tor Setup

sudo tee /etc/tor/torrc <<EOF
RunAsDaemon 1
HiddenServiceDir /var/lib/tor/hidden_service/
HiddenServicePort 80 127.0.0.1:5000
EOF

systemctl restart tor.service
sleep 10

# Get the Onion address
ONION_ADDRESS=$(cat /var/lib/tor/hidden_service/hostname)

cd /var/www/html/frontpage/frontpage
sed -i "s|ONION_ADDRESS|$ONION_ADDRESS|g" display.py

sudo ln -s /etc/nginx/sites-available/frontpage /etc/nginx/sites-enabled
rm -f /etc/nginx/sites-available/default
rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

sudo systemctl enable frontpage.service
sudo systemctl start frontpage.service
sudo systemctl restart frontpage.service

cd /var/www/html/frontpage/frontpage/
chmod +x install_display.sh
./install_display.sh

