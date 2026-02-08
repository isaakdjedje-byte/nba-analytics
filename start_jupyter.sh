#!/bin/bash
# NBA Analytics - Start Jupyter with Virtual Environment

set -e

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: ./setup_venv.sh"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/Scripts/activate

# Set local runtime directory (avoids Windows permission issues)
export JUPYTER_RUNTIME_DIR="$(pwd)/.jupyter_runtime"
mkdir -p "$JUPYTER_RUNTIME_DIR"

# Find available port
PORT=8888
while netstat -an | grep -q ":$PORT "; do
    ((PORT++))
done

echo ""
echo "=================================="
echo "Starting Jupyter Notebook"
echo "=================================="
echo ""
echo "Virtual Environment: $(python --version)"
echo "Runtime Directory: $JUPYTER_RUNTIME_DIR"
echo "Port: $PORT"
echo ""
echo "Opening browser..."
echo ""
echo "URL: http://127.0.0.1:$PORT"
echo ""
echo "To stop: Press Ctrl+C twice"
echo ""
echo "=================================="

# Start Jupyter
jupyter notebook --no-browser --ip=127.0.0.1 --port=$PORT "$@"
