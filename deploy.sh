#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVICE_NAME="smartmirrord.service"
INSTALL_DIR="/opt/smartmirrord"

echo -e "${GREEN}=== SmartMirror Daemon Deploy ===${NC}"

# Check if we're in the right directory
if [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
    echo -e "${RED}Error: Must be run from $INSTALL_DIR or requirements.txt not found${NC}"
    exit 1
fi

# Check if running in install directory
if [ "$PWD" != "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Changing to $INSTALL_DIR${NC}"
    cd $INSTALL_DIR
fi

# Pull latest code
echo -e "${YELLOW}Pulling latest code from git...${NC}"
if [ -d ".git" ]; then
    git fetch
    git reset --hard origin/master
    echo -e "${GREEN}Code updated${NC}"
else
    echo -e "${YELLOW}Not a git repository, skipping git pull${NC}"
fi

# Update virtual environment dependencies
echo -e "${YELLOW}Updating dependencies...${NC}"
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q
echo -e "${GREEN}Dependencies updated${NC}"

# Check if service file changed
SERVICE_CHANGED=false
if ! cmp -s smartmirrord.service /etc/systemd/system/smartmirrord.service 2>/dev/null; then
    SERVICE_CHANGED=true
fi

# Reload systemd if service file changed
if [ "$SERVICE_CHANGED" = true ]; then
    echo -e "${YELLOW}Service file changed, reloading systemd...${NC}"
    sudo cp smartmirrord.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo -e "${GREEN}systemd reloaded${NC}"
fi

# Restart service
echo -e "${YELLOW}Restarting service...${NC}"
sudo systemctl restart $SERVICE_NAME
sleep 2

# Show service status
echo -e "${YELLOW}Service status:${NC}"
sudo systemctl status --no-pager $SERVICE_NAME

echo -e "${GREEN}=== Deploy Complete ===${NC}"
echo -e "Service status: ${GREEN}$(systemctl is-active $SERVICE_NAME)${NC}"
echo -e "To view logs: ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
