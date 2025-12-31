#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/smartmirrord"
LOG_DIR="/var/log/smartmirrord"
USER="smartmirror"
GROUP="smartmirror"
SERVICE_NAME="smartmirrord.service"

echo -e "${GREEN}=== SmartMirror Daemon Installer ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Create user and group if they don't exist
echo -e "${YELLOW}Creating user and group...${NC}"
if ! id -u $USER > /dev/null 2>&1; then
    useradd --system --home-dir $INSTALL_DIR --shell /usr/sbin/nologin --user-group $USER
    echo -e "${GREEN}User '$USER' created${NC}"
else
    echo -e "${YELLOW}User '$USER' already exists${NC}"
fi

# Add user to gpio, dialout, and video groups for hardware access
usermod -a -G gpio,dialout,video $USER 2>/dev/null || echo -e "${YELLOW}Some hardware groups may not exist yet${NC}"

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/log
mkdir -p $LOG_DIR
chown -R $USER:$GROUP $INSTALL_DIR
chown -R $USER:$GROUP $LOG_DIR
echo -e "${GREEN}Directories created${NC}"

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r $SCRIPT_DIR/smartmirrord $INSTALL_DIR/
cp $SCRIPT_DIR/requirements.txt $INSTALL_DIR/
cp $SCRIPT_DIR/deploy.sh $INSTALL_DIR/
chmod +x $INSTALL_DIR/deploy.sh

# Copy .env if it exists, otherwise copy .env.example
if [ -f "$SCRIPT_DIR/.env" ]; then
    cp $SCRIPT_DIR/.env $INSTALL_DIR/
    echo -e "${GREEN}.env file copied${NC}"
elif [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp $SCRIPT_DIR/.env.example $INSTALL_DIR/.env
    echo -e "${YELLOW}.env.example copied to .env - please edit $INSTALL_DIR/.env${NC}"
fi

chown -R $USER:$GROUP $INSTALL_DIR
echo -e "${GREEN}Application files copied${NC}"

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt update
apt install -y python3-picamera2 python3-venv
echo -e "${GREEN}System dependencies installed${NC}"

# Create Python virtual environment with system packages
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
sudo -u $USER python3 -m venv --system-site-packages $INSTALL_DIR/venv
echo -e "${GREEN}Virtual environment created${NC}"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
sudo -u $USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
sudo -u $USER $INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/requirements.txt
echo -e "${GREEN}Dependencies installed${NC}"

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
cp $SCRIPT_DIR/$SERVICE_NAME /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
echo -e "${GREEN}Service installed and enabled${NC}"

# Start the service
echo -e "${YELLOW}Starting service...${NC}"
systemctl start $SERVICE_NAME
sleep 2
systemctl status --no-pager $SERVICE_NAME

echo -e "${GREEN}=== Installation Complete ===${NC}"
echo -e "Service status: ${GREEN}$(systemctl is-active $SERVICE_NAME)${NC}"
echo -e "To view logs: ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "To deploy updates: ${YELLOW}cd $INSTALL_DIR && ./deploy.sh${NC}"
