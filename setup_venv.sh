#!/bin/bash
# NBA Analytics - Setup Virtual Environment
# Solution définitive pour éviter les conflits Python

set -e  # Stop on error

echo "=================================="
echo "NBA Analytics - Setup Environment"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    echo "Please run this script from the nba-analytics directory"
    exit 1
fi

# Check Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}Error: python3.11 not found${NC}"
    echo "Please install Python 3.11 with pyenv:"
    echo "  pyenv install 3.11.9"
    exit 1
fi

echo -e "${GREEN}✓ Python 3.11 found${NC}"

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Removing old virtual environment...${NC}"
    rm -rf .venv
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv .venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install requirements
echo "Installing requirements..."
python -m pip install -r requirements.txt --quiet

# Install additional packages for notebooks
echo "Installing Jupyter packages..."
python -m pip install ipykernel --quiet

# Create Jupyter kernel
echo "Creating Jupyter kernel..."
python -m ipykernel install --user --name=nba-venv --display-name="NBA Analytics (Python 3.11)"

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "To activate the environment:"
echo "  source .venv/Scripts/activate"
echo ""
echo "To start Jupyter:"
echo "  ./start_jupyter.sh"
echo ""
echo "Or manually:"
echo "  source .venv/Scripts/activate"
echo "  jupyter notebook"
echo ""
