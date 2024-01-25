#!/bin/bash

#Run as root
if [[ $EUID -ne 0 ]]; then
  echo "Script needs to run as root. Elevating permissions now."
  exec sudo /bin/bash "$0" "$@"
fi

# Install required packages for e-ink display
apt update
apt -y dist-upgrade
apt install -y python3-pip

# Enable SPI interface
raspi-config nonint do_spi 0

# Install Waveshare e-Paper library
git clone https://github.com/waveshare/e-Paper.git
pip3 install ./e-Paper/RaspberryPi_JetsonNano/python/
pip3 install requests python-gnupg stem pytz qrcode

# Install other Python packages
pip3 install RPi.GPIO spidev python-dateutil
apt -y autoremove

# Enable SPI interface
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" | tee -a /boot/config.txt
    echo "SPI interface enabled."
else
    echo "SPI interface is already enabled."
fi

cd /var/www/html/frontpage/

cat > /etc/systemd/system/frontpage-display.service << EOF
[Unit]
Description=Frontpage
After=network.target

[Service]
ExecStart=/usr/bin/python3 /var/www/html/frontpage/frontpage/display.py
WorkingDirectory=/var/www/html/frontpage/frontpage/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl enable frontpage-display.service
systemctl start frontpage-display.service

echo "✅ E-ink display configuration complete. Rebooting your Raspberry Pi..."
sleep 3

#reboot
